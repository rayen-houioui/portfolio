"""Segmentation professionnelle : utilise le modèle K-Means `models/kmeans_profils_socio_economiques.pkl`.

Le .pkl est un dictionnaire : {model: KMeans(k=4), scaler: StandardScaler, features, n_clusters, random_state}
avec les variables d'entrée : age, education-num, hours-per-week, income_sup50k (1 si revenu > 50K $, sinon 0).

Ce module :
  - charge le modèle et le jeu de données Adult de l'application (base MySQL/SQLite ou fichiers data/) ;
  - classe un candidat dans l'un des 4 profils (cluster) ;
  - calcule, pour chaque profil, les moyennes qui le caractérisent (âge, études, heures, revenu, métiers dominants) ;
  - produit UN seul graphique : la carte des individus (ACP 2D) avec la position du candidat.

Le modèle n'est jamais ré-entraîné : on applique le scaler et le K-Means du .pkl tels quels.
"""
import base64
import io
import threading
from functools import lru_cache
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # pas d'interface graphique côté serveur

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import silhouette_score  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

MODEL_FILE = "kmeans_profils_socio_economiques.pkl"
INCOME_COL = "income_sup50k"
SEED = 42
_LOCK = threading.Lock()

# Couleurs identiques à la carte du notebook (palette matplotlib « tab10 » : bleu, orange, vert, rouge).
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]

# --------------------------------------------------------------------------- libellés des profils
# Nom complet / nom court / pistes RH, par numéro de cluster du .pkl (voir `_names_match_centers`).
PROFILES = {
    0: {"name": "Seniors peu diplômés, métiers manuels et services", "short": "profil des seniors peu diplômés",
        "pistes": ["maintien dans l'emploi et transmission des savoir-faire",
                   "formation de mise à niveau ou certification des acquis",
                   "aménagement de la fin de carrière"]},
    1: {"name": "Actifs à plein temps, professions qualifiées, revenu modéré", "short": "profil des actifs qualifiés à plein temps",
        "pistes": ["évolution vers des postes à responsabilité",
                   "formation continue et spécialisation",
                   "vigilance sur la charge de travail (environ 48 h par semaine)"]},
    2: {"name": "Jeunes à activité réduite, services et emplois administratifs", "short": "profil des jeunes à activité réduite",
        "pistes": ["insertion et montée en compétences",
                   "formation qualifiante ou alternance",
                   "augmentation progressive du temps de travail"]},
    3: {"name": "Cadres et professions intellectuelles à revenu élevé", "short": "profil des cadres à revenu élevé",
        "pistes": ["fidélisation et gestion des talents",
                   "parcours de management ou d'expertise",
                   "mentorat des profils plus jeunes"]},
}

OCCUPATIONS_FR = {
    "Adm-clerical": "Administratif / secrétariat", "Armed-Forces": "Forces armées", "Craft-repair": "Artisanat / réparation",
    "Exec-managerial": "Direction / management", "Farming-fishing": "Agriculture / pêche",
    "Handlers-cleaners": "Manutention / nettoyage", "Machine-op-inspct": "Opérateur machine / contrôle",
    "Other-service": "Autres services", "Priv-house-serv": "Services à domicile",
    "Prof-specialty": "Profession spécialisée / intellectuelle", "Protective-serv": "Sécurité / protection",
    "Sales": "Vente / commerce", "Tech-support": "Support technique", "Transport-moving": "Transport / logistique",
}


class ModelNotFound(FileNotFoundError):
    pass


def _model_path() -> Path:
    from django.conf import settings

    return Path(settings.BASE_DIR) / "models" / MODEL_FILE


def _load_artifact() -> dict:
    path = _model_path()
    if not path.exists():
        raise ModelNotFound(f"Modèle introuvable : placez « {MODEL_FILE} » dans le dossier models/.")
    art = joblib.load(path)
    for key in ("model", "scaler", "features"):
        if key not in art:
            raise ValueError(f"Le fichier {MODEL_FILE} doit contenir la clé « {key} ».")
    return art


def _load_dataframe() -> tuple[pd.DataFrame, str]:
    """Même source de données que le reste de l'application (MySQL/SQLite puis fichiers data/)."""
    from .clustering import load_dataframe

    return load_dataframe()


def prepare(raw: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Nettoyage minimal : espaces, doublons, valeurs manquantes, création de `income_sup50k`."""
    df = raw.replace(r"^\s*\?\s*$", np.nan, regex=True).copy()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].str.strip()
    df["income"] = df["income"].astype(str).str.replace(".", "", regex=False).str.strip()
    df = df.drop_duplicates().reset_index(drop=True)
    df[INCOME_COL] = (df["income"] == ">50K").astype(int)
    for c in features:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=features).reset_index(drop=True)


def _names_match_centers(centers: np.ndarray, features: list[str]) -> bool:
    """Les noms ci-dessus ne valent que pour le .pkl d'origine : on vérifie qu'ils collent aux centres."""
    if centers.shape[0] != 4 or features != ["age", "education-num", "hours-per-week", INCOME_COL]:
        return False
    age, income, hours = centers[:, 0], centers[:, 3], centers[:, 2]
    low_income = [i for i in range(4) if income[i] < 0.5]
    return bool(income[3] > 0.5 and np.argmax(income) == 3 and np.argmin(age) == 2 and np.argmax(age) == 0
                and max(low_income, key=lambda i: hours[i]) == 1)


def _share(series: pd.Series, mapping: dict | None = None, top: int = 3) -> list[dict]:
    vc = series.dropna().value_counts(normalize=True) * 100
    return [{"label": (mapping or {}).get(k, k), "pct": round(float(v), 1)} for k, v in vc.head(top).items()]


# --------------------------------------------------------------------------- ajustement (une fois par processus)
@lru_cache(maxsize=1)
def _fit() -> dict:
    with _LOCK:
        art = _load_artifact()
        model, scaler, features = art["model"], art["scaler"], list(art["features"])
        raw, source = _load_dataframe()
        df = prepare(raw, features)
        if df.empty:
            raise FileNotFoundError("Aucune donnée exploitable pour calculer les profils.")

        X = scaler.transform(df[features])
        labels = model.predict(X)
        df["cluster"] = labels
        k = int(model.n_clusters)

        pca = PCA(n_components=2, random_state=SEED).fit(X)
        Z = pca.transform(X)
        evr = pca.explained_variance_ratio_ * 100

        sample = min(5000, len(df))
        sil = float(silhouette_score(X, labels, sample_size=sample, random_state=SEED)) if len(df) > 10 and k > 1 else 0.0

        # Estimation du revenu quand il n'est pas connu : régression logistique sur âge / études / heures.
        est_cols = ["age", "education-num", "hours-per-week"]
        income_lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(df[est_cols], df[INCOME_COL])

        centers = scaler.inverse_transform(model.cluster_centers_)
        named = _names_match_centers(centers, features)
        overall = {
            "age_mean": round(float(df["age"].mean()), 1), "education_mean": round(float(df["education-num"].mean()), 1),
            "hours_mean": round(float(df["hours-per-week"].mean()), 1),
            "pct_high_income": round(float(df[INCOME_COL].mean() * 100), 1),
        }
        cards = []
        for c in range(k):
            g = df[df["cluster"] == c]
            base = PROFILES.get(c) if named else None
            if base is None:
                a, e, h = centers[c][0], centers[c][1], centers[c][2]
                base = {"name": f"Profil {c} (âge ≈ {a:.0f} ans, études ≈ {e:.0f}, ≈ {h:.0f} h/semaine)",
                        "short": f"profil {c}", "pistes": ["analyse à compléter avec un conseiller RH"]}
            cards.append({
                "cluster": c, "name": base["name"], "short": base["short"], "color": COLORS[c % len(COLORS)],
                "count": int(len(g)), "pct": round(100 * len(g) / len(df), 1),
                "age_mean": round(float(g["age"].mean()), 1),
                "age_p10": int(np.percentile(g["age"], 10)), "age_p90": int(np.percentile(g["age"], 90)),
                "education_mean": round(float(g["education-num"].mean()), 1),
                "hours_mean": round(float(g["hours-per-week"].mean()), 1),
                "pct_high_income": round(float(g[INCOME_COL].mean() * 100), 1),
                "occupations": _share(g["occupation"], OCCUPATIONS_FR, 4) if "occupation" in g else [],
                "pistes": base["pistes"],
            })
        rng = np.random.default_rng(SEED)
        idx = rng.choice(len(df), size=min(9000, len(df)), replace=False)
        return {"art": art, "features": features, "df_n": len(df), "source": source, "labels": labels, "pca": pca, "Z": Z, "plot_idx": idx,
                "evr": evr, "silhouette": sil, "inertia": float(model.inertia_), "k": k, "cards": cards,
                "overall": overall, "income_lr": income_lr, "est_cols": est_cols}


# --------------------------------------------------------------------------- graphique
def _png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _map(fit: dict, point: tuple[float, float] | None = None) -> str:
    """Carte des individus (ACP 2D) colorée par cluster, avec le candidat en étoile noire."""
    Z, labels, idx, evr, k = fit["Z"], fit["labels"], fit["plot_idx"], fit["evr"], fit["k"]
    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    for c in range(k):
        sel = idx[labels[idx] == c]
        ax.scatter(Z[sel, 0], Z[sel, 1], s=20, alpha=0.6, color=COLORS[c % len(COLORS)], label=f"Cluster {c}", linewidths=0)
    ax.axhline(0, color="#9ca3af", lw=0.8)
    ax.axvline(0, color="#9ca3af", lw=0.8)
    if point is not None:
        ax.scatter([point[0]], [point[1]], marker="*", s=520, color="black", edgecolor="white", linewidth=1.6,
                   zorder=10, label="Candidat")
        ax.annotate("Candidat", point, xytext=(14, 14), textcoords="offset points", fontsize=11, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="black", lw=0.8), zorder=11)
    ax.set_title(f"Carte des individus - Clustering K-Means ({k} clusters)", fontsize=13)
    ax.set_xlabel(f"PC1 ({evr[0]:.2f} %)")
    ax.set_ylabel(f"PC2 ({evr[1]:.2f} %)")
    ax.grid(alpha=0.2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(title="Clusters", loc="upper right", frameon=True)
    return _png(fig)


@lru_cache(maxsize=1)
def _base_map() -> str:
    return _map(_fit())


@lru_cache(maxsize=64)
def _candidate_map(x: float, y: float) -> str:
    return _map(_fit(), (x, y))


# --------------------------------------------------------------------------- API publique
def _model_info(fit: dict) -> dict:
    return {"k": fit["k"], "individuals": fit["df_n"], "source": fit["source"], "silhouette": round(fit["silhouette"], 3),
            "inertia": round(fit["inertia"], 1), "pc1_pct": round(float(fit["evr"][0]), 2), "pc2_pct": round(float(fit["evr"][1]), 2),
            "features": fit["features"]}


def overview() -> dict:
    """Tous les profils + la carte (sans candidat) : alimente la page « Segmentation RH »."""
    fit = _fit()
    return {"clusters": fit["cards"], "overall": fit["overall"], "model": _model_info(fit),
            "graph": {"id": "map", "title": f"Carte des individus - Clustering K-Means ({fit['k']} clusters)",
                      "caption": "Chaque point est une personne du jeu de données, projetée en 2 dimensions (ACP) ; la couleur indique son profil.",
                      "image": _base_map()}}


def analyze(age: int, education_num: int, hours_per_week: int, income_sup50k: int | None = None) -> dict:
    """Classe un candidat. `income_sup50k` : 1 / 0 si connu, None -> estimé à partir de l'âge, des études et des heures."""
    fit = _fit()
    art, features = fit["art"], fit["features"]
    model, scaler = art["model"], art["scaler"]

    if income_sup50k is None:
        est = pd.DataFrame([[age, education_num, hours_per_week]], columns=fit["est_cols"])
        income_value = float(fit["income_lr"].predict_proba(est)[0, 1])
        income_source = "estimated"
    else:
        income_value, income_source = float(income_sup50k), "declared"

    values = {"age": age, "education-num": education_num, "hours-per-week": hours_per_week, INCOME_COL: income_value}
    x = pd.DataFrame([[values[f] for f in features]], columns=features)
    z_scaled = scaler.transform(x)
    cluster = int(model.predict(z_scaled)[0])
    dist = np.linalg.norm(model.cluster_centers_ - z_scaled, axis=1)
    order = np.argsort(dist)
    ratio = float(dist[order[0]] / dist[order[1]]) if len(order) > 1 and dist[order[1]] > 0 else 0.0
    confidence = "forte" if ratio < 0.6 else "moyenne" if ratio < 0.85 else "limite"

    pt = fit["pca"].transform(z_scaled)  # position du candidat sur la carte (mêmes axes que les individus)
    px, py = float(pt[0, 0]), float(pt[0, 1])

    cards = fit["cards"]
    return {
        "candidate": {
            "cluster": cluster, "profile_name": cards[cluster]["name"], "fiche": cards[cluster], "color": cards[cluster]["color"],
            "inputs": {"age": age, "education_num": education_num, "hours_per_week": hours_per_week,
                       "income_sup50k": round(income_value, 3), "income_source": income_source},
            "distances": {str(int(i)): round(float(d), 3) for i, d in enumerate(dist)},
            "second_cluster": int(order[1]) if len(order) > 1 else None,
            "confidence": confidence, "closeness_ratio": round(ratio, 2),
        },
        "clusters": cards, "overall": fit["overall"], "model": _model_info(fit),
        "graph": {"id": "map", "title": f"Carte des individus - Clustering K-Means ({fit['k']} clusters)",
                  "caption": "L'étoile noire est le candidat ; chaque point coloré est une personne du jeu de données.",
                  "image": _candidate_map(round(px, 3), round(py, 3))},
    }
