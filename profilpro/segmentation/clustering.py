"""Segmentation des profils familiaux : reproduit le notebook `preprocessing_clustering_profilpro.ipynb`.

Pipeline : nettoyage -> StandardScaler + OneHotEncoder -> ACP -> K-Means (k choisi par silhouette entre 3 et 8).
Le modèle est ajusté ici même (préprocesseur, ACP et K-Means dans la même exécution), donc toujours cohérent.
Les graphiques sont générés avec matplotlib/seaborn et renvoyés en PNG base64 pour être affichés par le front.
"""
import base64
import io
import os
import threading
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # pas d'interface graphique côté serveur

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from django.conf import settings  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

COLUMNS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", "occupation",
           "relationship", "race", "sex", "capital-gain", "capital-loss", "hours-per-week",
           "native-country", "income"]
NUM_FEATURES = ["age", "education-num"]
CAT_FEATURES = ["marital-status", "relationship", "sex"]
FEATURES = NUM_FEATURES + CAT_FEATURES
K_RANGE = range(2, 11)
SEED = 42
_LOCK = threading.Lock()


# --------------------------------------------------------------------------- libellés en français (pour les RH)
FR = {
    "relationship": {"Husband": "Époux", "Wife": "Épouse", "Not-in-family": "Hors cercle familial",
                     "Own-child": "Enfant au foyer", "Unmarried": "Non marié(e) en foyer", "Other-relative": "Autre parent"},
    "marital-status": {"Divorced": "Divorcé(e)", "Married-AF-spouse": "Marié(e) (conjoint militaire)", "Married-civ-spouse": "Marié(e)",
                       "Married-spouse-absent": "Marié(e), conjoint absent", "Never-married": "Célibataire",
                       "Separated": "Séparé(e)", "Widowed": "Veuf / veuve"},
    "sex": {"Female": "Femmes", "Male": "Hommes"},
}


def _fr(col, value):
    return FR[col].get(value, value)


def _composition(g, col):
    vc = g[col].value_counts(normalize=True) * 100
    return [{"label": _fr(col, k), "pct": round(float(v), 1)} for k, v in vc.items() if v >= 1]


# --------------------------------------------------------------------------- données
def _read_adult_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLUMNS, skipinitialspace=True, comment="|",
                     skip_blank_lines=True, na_values=["?"], keep_default_na=False)
    return df.dropna(subset=["age"])


def load_dataframe() -> tuple[pd.DataFrame, str]:
    """Lit d'abord la table MySQL `adult_person` ; sinon les fichiers adult.data / adult.test du dossier data/."""
    try:
        from .models import Person

        if Person.objects.exists():
            fields = ["age", "workclass", "fnlwgt", "education", "education_num", "marital_status", "occupation",
                      "relationship", "race", "sex", "capital_gain", "capital_loss", "hours_per_week",
                      "native_country", "income"]
            df = pd.DataFrame(list(Person.objects.values(*fields)))
            df.columns = COLUMNS
            return df.replace("", np.nan), "base MySQL (table adult_person)"
    except Exception:  # base absente / non migrée / MySQL arrêté -> repli sur les fichiers
        pass
    parts = [_read_adult_file(p) for p in (Path(settings.BASE_DIR) / "data" / n for n in ("adult.data", "adult.test"))
             if p.exists()]
    if not parts:
        raise FileNotFoundError("Aucune donnée : importez adult.test dans MySQL (python manage.py import_adult ...) "
                                "ou placez adult.data / adult.test dans le dossier data/.")
    return pd.concat(parts, ignore_index=True), "fichiers adult.data / adult.test"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Sections 3 et 4 du notebook."""
    df = df.replace(r"^\s*\?\s*$", np.nan, regex=True)
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].str.strip()
    df["income"] = df["income"].str.replace(".", "", regex=False)
    df = df.drop_duplicates().reset_index(drop=True)
    return df.dropna(subset=FEATURES).reset_index(drop=True)


# --------------------------------------------------------------------------- modèle
def _pistes(age_m, edu_m, role):
    p = []
    if age_m < 30:
        p.append("insertion / premier emploi, orientation vers une formation")
    elif age_m < 50:
        p.append("évolution ou reconversion professionnelle")
    else:
        p.append("maintien dans l'emploi, transition de fin de carrière")
    if edu_m < 9:
        p.append("remise à niveau, formation qualifiante")
    elif edu_m >= 13:
        p.append("accès à des postes qualifiés, formation continue")
    if role in ("Husband", "Wife"):
        p.append("conciliation vie familiale / vie professionnelle")
    elif role == "Own-child":
        p.append("accompagnement vers l'autonomie")
    elif role == "Not-in-family":
        p.append("mobilité géographique envisageable")
    return p


def _b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@lru_cache(maxsize=1)
def _fit():
    """Ajuste tout le pipeline une seule fois par processus (puis réutilisé par chaque requête)."""
    raw, source = load_dataframe()
    df = clean(raw)

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUM_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_FEATURES),
    ])
    X = preprocessor.fit_transform(df[FEATURES])
    feature_names = preprocessor.get_feature_names_out()
    pca = PCA()
    scores = pca.fit_transform(X)

    # 12.1 choix de k
    sil_idx = np.random.RandomState(SEED).choice(len(X), size=min(5000, len(X)), replace=False)
    inertias, sils, dbs = [], [], []
    for k in K_RANGE:
        km_k = KMeans(n_clusters=k, n_init=10, random_state=SEED)
        lab = km_k.fit_predict(X)
        inertias.append(km_k.inertia_)
        sils.append(silhouette_score(X[sil_idx], lab[sil_idx]))
        dbs.append(davies_bouldin_score(X, lab))
    k_auto = max((k for k in K_RANGE if 3 <= k <= 8), key=lambda k: sils[list(K_RANGE).index(k)])
    K = int(os.getenv("PROFILPRO_K", k_auto))

    # 12.2 K-Means final, clusters renumérotés par taille décroissante
    kmeans = KMeans(n_clusters=K, n_init=20, random_state=SEED)
    raw_labels = kmeans.fit_predict(X)
    order = pd.Series(raw_labels).value_counts().index
    mapping = {old: new for new, old in enumerate(order)}
    df["cluster"] = pd.Series(raw_labels).map(mapping).values
    centers = kmeans.cluster_centers_[order]
    sil_final = float(silhouette_score(X[sil_idx], df["cluster"].values[sil_idx]))
    ari = float(np.mean([adjusted_rand_score(df["cluster"], KMeans(n_clusters=K, n_init=10, random_state=s).fit_predict(X))
                         for s in range(1, 4)]))

    # 12.6 fiches d'identité (libellés français)
    fiches = []
    for c, g in df.groupby("cluster"):
        rel = g["relationship"].value_counts(normalize=True)
        mar = g["marital-status"].value_counts(normalize=True)
        sex = g["sex"].value_counts(normalize=True)
        age_m, edu_m = g["age"].mean(), g["education-num"].mean()
        fiches.append({
            "cluster": int(c),
            "short": f"Profil {c + 1}",
            "name": f"Profil {c + 1} : {_fr('relationship', rel.index[0])} · {_fr('marital-status', mar.index[0])} · ~{age_m:.0f} ans",
            "count": int(len(g)), "pct": round(len(g) / len(df) * 100, 1),
            "age_mean": round(age_m, 1), "education_mean": round(edu_m, 1),
            "hours_mean": round(g["hours-per-week"].mean(), 1),
            "pct_high_income": round((g["income"] == ">50K").mean() * 100, 1),
            "dominant_role": f"{_fr('relationship', rel.index[0])} ({rel.iloc[0] * 100:.0f} %)",
            "dominant_status": f"{_fr('marital-status', mar.index[0])} ({mar.iloc[0] * 100:.0f} %)",
            "dominant_sex": f"{_fr('sex', sex.index[0])} ({sex.iloc[0] * 100:.0f} %)",
            "composition": {"relationship": _composition(g, "relationship"), "marital": _composition(g, "marital-status"),
                            "sex": _composition(g, "sex")},
            "pistes": _pistes(age_m, edu_m, rel.index[0]),
        })
    overall = {"age_mean": round(float(df["age"].mean()), 1), "education_mean": round(float(df["education-num"].mean()), 1),
               "hours_mean": round(float(df["hours-per-week"].mean()), 1),
               "pct_high_income": round(float((df["income"] == ">50K").mean() * 100), 1)}

    return dict(df=df, X=X, scores=scores, preprocessor=preprocessor, feature_names=feature_names, pca=pca,
                kmeans=kmeans, mapping=mapping, centers=centers, K=K, k_auto=k_auto, inertias=inertias, sils=sils,
                dbs=dbs, sil_final=sil_final, ari=ari, fiches=fiches, overall=overall, source=source, sil_idx=sil_idx)


# --------------------------------------------------------------------------- graphique de clustering
def _graphs(m, cand_xy=None):
    """Un seul graphique : la carte des profils (plan ACP) avec des légendes lisibles par un non-spécialiste."""
    df, scores, pca, K = m["df"], m["scores"], m["pca"], m["K"]
    pal = dict(zip(range(K), sns.color_palette("tab10", K)))
    var = pca.explained_variance_ratio_
    idx = np.random.RandomState(SEED).choice(len(df), size=min(5000, len(df)), replace=False)
    names = {f["cluster"]: f["name"] for f in m["fiches"]}
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for c in range(K):
        sel = idx[df.loc[idx, "cluster"].values == c]
        ax.scatter(scores[sel, 0], scores[sel, 1], s=18, alpha=.45, color=pal[c], label=names[c])
    cp = pca.transform(m["centers"])
    ax.scatter(cp[:, 0], cp[:, 1], marker="X", s=220, c="black", zorder=4)
    for c in range(K):
        ax.annotate(f"P{c + 1}", (cp[c, 0], cp[c, 1]), xytext=(8, 10), textcoords="offset points", fontsize=12,
                    fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=.9), zorder=5)
    if cand_xy is not None:
        ax.scatter(*cand_xy, marker="*", s=750, c="gold", edgecolors="black", linewidths=1.5, zorder=6, label="Ce candidat")
    ax.axhline(0, color="grey", lw=1); ax.axvline(0, color="grey", lw=1)
    ax.set_xlabel(f"Axe 1 ({var[0] * 100:.0f} % de l'information)"); ax.set_ylabel(f"Axe 2 ({var[1] * 100:.0f} % de l'information)")
    ax.set_title("Carte des profils : plus deux personnes sont proches, plus elles se ressemblent", fontsize=12)
    ax.legend(title="Profils", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    return [{"id": "plan", "title": "Carte des profils",
             "caption": "Chaque point est une personne, chaque couleur un profil. Les croix P1, P2… sont les centres des profils"
                        + (" ; l'étoile dorée est le candidat." if cand_xy is not None else "."),
             "image": _b64(fig)}]


# --------------------------------------------------------------------------- API
def analyze(age, education_num, marital_status, relationship, sex) -> dict:
    """Classe le candidat dans un cluster et renvoie tous les résultats + graphiques du notebook."""
    with _LOCK:
        m = _fit()
        row = pd.DataFrame([{"age": age, "education-num": education_num, "marital-status": marital_status,
                             "relationship": relationship, "sex": sex}])[FEATURES]
        x = m["preprocessor"].transform(row)
        raw = int(m["kmeans"].predict(x)[0])
        cluster = int(m["mapping"][raw])
        dist = np.linalg.norm(m["centers"] - x, axis=1)
        cand_xy = m["pca"].transform(x)[0, :2]
        fiche = next(f for f in m["fiches"] if f["cluster"] == cluster)
        graphs = _graphs(m, cand_xy=cand_xy)
    var = m["pca"].explained_variance_ratio_
    return {
        "candidate": {"cluster": cluster, "profile_name": fiche["name"], "fiche": fiche,
                      "distances": {str(i): round(float(d), 3) for i, d in enumerate(dist)}},
        "clusters": m["fiches"],
        "overall": m["overall"],
        "model": {"k": m["K"], "individuals": int(len(m["df"])), "source": m["source"],
                  "silhouette": round(m["sil_final"], 3), "stability_ari": round(m["ari"], 3),
                  "pc1_pct": round(float(var[0]) * 100, 1), "pc2_pct": round(float(var[1]) * 100, 1)},
        "graphs": graphs,
    }
