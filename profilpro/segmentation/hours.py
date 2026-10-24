"""Régression des heures de travail par semaine (XGBoost, modèle `models/xgboost_hours.pkl`).

Reprend le modèle de régression du notebook « hours_per_week » : XGBRegressor avec les meilleurs hyperparamètres
trouvés par GridSearch (learning_rate=0.05, max_depth=7, n_estimators=100, subsample=0.8), variable cible
`hours-per-week`, encodage one-hot des variables catégorielles.

Le modèle n'utilise que les variables que l'application collecte à l'étape « Vérification » du CV :
âge, niveau d'études, sexe, statut marital, rôle familial, métier et (facultatif) revenu > 50 000 $.
Les valeurs inconnues (métier, revenu) sont gérées nativement : le revenu est masqué au hasard dans 25 % des
lignes d'entraînement pour que le modèle apprenne à prédire sans lui.

Si `models/xgboost_hours.pkl` n'existe pas (ou n'est pas lisible avec les versions installées), le modèle est
entraîné automatiquement au premier appel (quelques secondes) puis sauvegardé. Forcer : `python manage.py train_hours`.

`analyze()` renvoie, en français et prêt pour l'affichage : la prédiction (heures + fourchette), les facteurs qui
l'expliquent (effet de chaque caractéristique, en heures), la comparaison avec des profils réels, des graphiques
(répartition des horaires, heures moyennes par métier / études / âge), des leviers (« et si… ») et les limites du modèle.
"""
import threading
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .income import (AGE_BINS, EDU_BINS, OCCUPATIONS, RELATIONSHIP_FR, SEX_FR, UNKNOWN_FR, _bin_label, _population,
                     infer_occupation)

MARITAL = ["Divorced", "Married-AF-spouse", "Married-civ-spouse", "Married-spouse-absent",
           "Never-married", "Separated", "Widowed"]
RELATIONSHIP = ["Husband", "Not-in-family", "Other-relative", "Own-child", "Unmarried", "Wife"]
MARITAL_FR = {"Divorced": "Divorcé(e)", "Married-AF-spouse": "Marié(e) (conjoint militaire)",
              "Married-civ-spouse": "Marié(e)", "Married-spouse-absent": "Marié(e), conjoint absent",
              "Never-married": "Célibataire", "Separated": "Séparé(e)", "Widowed": "Veuf / veuve"}
SENSITIVE = {"sex", "marital-status", "relationship"}  # à ne jamais utiliser pour décider d'une embauche ou d'un horaire

BEST_PARAMS = dict(learning_rate=0.05, max_depth=7, n_estimators=100, subsample=0.8,
                   objective="reg:squarederror", random_state=42)
SEED = 42
INCOME_MASK = 0.25
N_REFERENCE = 150

HOURS_BINS = [(1, 19, "< 20 h"), (20, 34, "20-34 h"), (35, 39, "35-39 h"), (40, 40, "40 h"),
              (41, 49, "41-49 h"), (50, 59, "50-59 h"), (60, 99, "60 h et +")]
FEATURE_FR = {"age": "Âge", "education-num": "Niveau d'études", "occupation": "Métier", "sex": "Sexe",
              "marital-status": "Statut marital", "relationship": "Rôle dans la famille",
              "income_high": "Revenu annuel"}

_LOCK = threading.Lock()
_ARTIFACT = None


# --------------------------------------------------------------------------- encodage
def _encode(df: pd.DataFrame) -> pd.DataFrame:
    """Lignes brutes -> colonnes du modèle. Colonnes attendues : age, education-num, sex, marital-status,
    relationship, occupation (None = inconnu), income_high (None = inconnu, 0 ou 1)."""
    out = pd.DataFrame(index=df.index)
    out["age"] = df["age"].astype(float)
    out["education-num"] = df["education-num"].astype(float)
    out["sex_male"] = df["sex"].map({"Male": 1.0, "Female": 0.0}).astype(float)
    for col, values, prefix in (("marital-status", MARITAL, "marital"), ("relationship", RELATIONSHIP, "rel"),
                                ("occupation", list(OCCUPATIONS), "occ")):
        text = df[col].fillna("").astype(str)
        for v in values:
            out[f"{prefix}_{v}"] = text.eq(v).astype(float)  # métier inconnu -> toutes les colonnes à 0
    out["income_high"] = pd.to_numeric(df["income_high"], errors="coerce").astype(float)
    return out


COLUMNS = list(_encode(pd.DataFrame([{"age": 30, "education-num": 9, "sex": "Male", "marital-status": "Divorced",
                                      "relationship": "Husband", "occupation": None, "income_high": None}])).columns)


# --------------------------------------------------------------------------- entraînement / chargement
def fit() -> dict:
    """Entraîne le XGBRegressor du notebook sur la population de l'application et renvoie l'artefact."""
    from xgboost import XGBRegressor

    pop, source = _population()
    pop = pop.dropna(subset=["sex", "marital-status", "relationship"]).reset_index(drop=True)
    rows = pd.DataFrame({
        "age": pop["age"], "education-num": pop["education-num"], "sex": pop["sex"],
        "marital-status": pop["marital-status"], "relationship": pop["relationship"], "occupation": pop["occupation"],
        "income_high": pop["high"].astype(float),
    })
    y = pop["hours-per-week"].astype(float)

    rng = np.random.default_rng(SEED)
    reference = rows.sample(min(N_REFERENCE, len(rows)), random_state=SEED)  # profils réels (revenu connu) pour expliquer
    reference = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in reference.to_dict("records")]
    masked = rows.copy()
    masked.loc[rng.random(len(masked)) < INCOME_MASK, "income_high"] = np.nan

    X = _encode(masked)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    model = XGBRegressor(**BEST_PARAMS)
    model.fit(X_train, y_train)

    pred = np.clip(model.predict(X_test), 1, 99)
    resid = y_test.to_numpy() - pred
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 2),
        "r2": round(float(r2_score(y_test, pred)), 3),
        "baseline_mae": round(float(mean_absolute_error(y_test, np.full(len(y_test), y_train.median()))), 2),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    }
    return {"model": model, "columns": COLUMNS, "metrics": metrics,
            "resid_q": (round(float(np.quantile(resid, 0.10)), 2), round(float(np.quantile(resid, 0.90)), 2)),
            "reference": reference, "source": source, "params": {k: v for k, v in BEST_PARAMS.items() if k != "objective"}}


def get_artifact() -> dict:
    global _ARTIFACT
    with _LOCK:
        if _ARTIFACT is None:
            path = Path(settings.HOURS_MODEL_PATH)
            if path.exists():
                try:
                    art = joblib.load(path)
                    if art.get("columns") == COLUMNS:
                        _ARTIFACT = art
                except Exception:  # pkl illisible (autre version de xgboost / scikit-learn) -> on ré-entraîne
                    _ARTIFACT = None
            if _ARTIFACT is None:
                _ARTIFACT = fit()
                try:
                    joblib.dump(_ARTIFACT, path)
                except OSError:
                    pass
        return _ARTIFACT


def retrain() -> dict:
    """Ré-entraîne et remplace le .pkl (commande `train_hours`)."""
    global _ARTIFACT
    with _LOCK:
        _ARTIFACT = fit()
        joblib.dump(_ARTIFACT, Path(settings.HOURS_MODEL_PATH))
        return _ARTIFACT


def _predict(rows: pd.DataFrame) -> np.ndarray:
    art = get_artifact()
    return np.clip(art["model"].predict(_encode(rows)[art["columns"]]), 1, 99)


# --------------------------------------------------------------------------- analyse
def _fmt_value(feature: str, row: dict) -> str:
    v = row[feature]
    if feature == "age":
        return f"{int(v)} ans"
    if feature == "education-num":
        return f"{_bin_label(int(v), EDU_BINS)} ({int(v)} ans d'études)"
    if feature == "occupation":
        return OCCUPATIONS.get(v, UNKNOWN_FR)
    if feature == "sex":
        return SEX_FR.get(v, v)
    if feature == "marital-status":
        return MARITAL_FR.get(v, v)
    if feature == "relationship":
        return RELATIONSHIP_FR.get(v, v)
    if feature == "income_high":
        return "Plus de 50 000 $" if v == 1 else "50 000 $ ou moins"
    return str(v)


def _effects(row: dict, base: float) -> list[dict]:
    """Effet de chaque caractéristique, en heures : prédiction du profil moins la prédiction moyenne obtenue en
    remplaçant cette seule caractéristique par celle de profils réels (toutes choses égales par ailleurs)."""
    art = get_artifact()
    ref = pd.DataFrame(art["reference"])
    features = ["age", "education-num", "sex", "marital-status", "relationship"]
    if row["occupation"] is not None:
        features.append("occupation")
    if row["income_high"] is not None:
        features.append("income_high")
    out = []
    for f in features:
        variants = pd.DataFrame([row] * len(ref))
        variants[f] = ref[f].to_numpy()
        effect = base - float(_predict(variants).mean())
        out.append({"feature": f, "label": FEATURE_FR[f], "value": _fmt_value(f, row), "impact": round(effect, 1),
                    "direction": "up" if effect > 0 else "down", "sensitive": f in SENSITIVE})
    total = sum(abs(o["impact"]) for o in out) or 1.0
    for o in out:
        o["weight_pct"] = round(100 * abs(o["impact"]) / total, 1)
    return sorted(out, key=lambda o: -abs(o["impact"]))


def _mean_hours(g) -> float:
    return round(float(g["hours-per-week"].mean()), 1) if len(g) else 0.0


def _category(hours: float) -> tuple[str, str]:
    if hours < 35:
        return "partiel", "Temps partiel probable (moins de 35 h)"
    if hours <= 40.5:
        return "standard", "Temps plein standard (35 à 40 h)"
    if hours < 50:
        return "etendu", "Horaires étendus (41 à 49 h)"
    return "long", "Longues semaines (50 h et plus)"


def analyze(age, education_num, marital_status, relationship, sex, occupation="", occupation_text="",
            income_high=None) -> dict:
    art = get_artifact()

    if occupation in OCCUPATIONS:
        occ, occ_src = occupation, "choisi"
    else:
        occ = infer_occupation(occupation_text)
        occ_src = "déduit du CV" if occ else "inconnu"
    row = {"age": age, "education-num": education_num, "sex": sex, "marital-status": marital_status,
           "relationship": relationship, "occupation": occ, "income_high": income_high}

    hours = float(_predict(pd.DataFrame([row]))[0])
    lo_q, hi_q = art["resid_q"]
    low, high = max(1.0, hours + lo_q), min(99.0, hours + hi_q)
    cat_key, cat_label = _category(hours)

    factors = _effects(row, hours)

    # --- comparaison avec la population réelle
    pop, source = _population()
    edu_bin, age_bin = _bin_label(int(education_num), EDU_BINS), _bin_label(int(age), AGE_BINS)
    overall = _mean_hours(pop)
    comparisons = [{"label": "Ensemble de la population", "mean": overall, "n": int(len(pop))}]
    if occ:
        g = pop[pop["occupation"] == occ]
        if len(g) >= 20:
            comparisons.append({"label": f"Même métier ({OCCUPATIONS[occ]})", "mean": _mean_hours(g), "n": int(len(g))})
    g = pop[pop["edu_bin"] == edu_bin]
    comparisons.append({"label": f"Même niveau d'études ({edu_bin})", "mean": _mean_hours(g), "n": int(len(g))})
    g = pop[pop["age_bin"] == age_bin]
    comparisons.append({"label": f"Même tranche d'âge ({age_bin})", "mean": _mean_hours(g), "n": int(len(g))})

    criteria = [("edu_bin", edu_bin, f"études : {edu_bin}"), ("age_bin", age_bin, f"âge : {age_bin}")]
    if occ:
        criteria.insert(0, ("occupation", occ, f"métier : {OCCUPATIONS[occ]}"))
    similar = None
    for cut in range(len(criteria), 0, -1):
        g = pop
        for col, val, _ in criteria[:cut]:
            g = g[g[col] == val]
        if len(g) >= 30:
            similar = {"n": int(len(g)), "mean": _mean_hours(g), "criteria": [c[2] for c in criteria[:cut]],
                       "pct_40_plus": round(float((g["hours-per-week"] >= 40).mean()) * 100, 1)}
            break

    # --- graphiques
    mine_bin = _bin_label(int(round(hours)), HOURS_BINS)
    total = len(pop)
    distribution = []
    for lo_h, hi_h, label in HOURS_BINS:
        n = int(((pop["hours-per-week"] >= lo_h) & (pop["hours-per-week"] <= hi_h)).sum())
        distribution.append({"label": label, "pct": round(100 * n / total, 1), "n": n, "mine": label == mine_bin})

    def chart(col, order, mine):
        rows_ = []
        for label in order:
            g = pop[pop[col] == label]
            if len(g) >= 20:
                rows_.append({"label": label, "mean": _mean_hours(g), "n": int(len(g)), "mine": label == mine})
        return rows_

    occ_rows = [{"label": OCCUPATIONS.get(o, o), "mean": _mean_hours(g), "n": int(len(g)), "mine": o == occ}
                for o, g in pop.dropna(subset=["occupation"]).groupby("occupation") if len(g) >= 20]
    charts = {
        "distribution": distribution,
        "education": chart("edu_bin", [b[2] for b in EDU_BINS], edu_bin),
        "age": chart("age_bin", [b[2] for b in AGE_BINS], age_bin),
        "occupation": sorted(occ_rows, key=lambda r: -r["mean"]),
    }

    # --- leviers : on re-prédit des variantes non sensibles du profil
    scenarios = []
    if education_num < 16:
        scenarios.append(("Un niveau d'études supplémentaire", {**row, "education-num": education_num + 1}))
    for o, lbl in OCCUPATIONS.items():
        if o != occ:
            scenarios.append((f"Un métier de type « {lbl} »", {**row, "occupation": o}))
    levers = []
    if scenarios:
        preds = _predict(pd.DataFrame([s[1] for s in scenarios]))
        items = [{"label": s[0], "hours": round(float(p), 1), "delta": round(float(p) - hours, 1)}
                 for s, p in zip(scenarios, preds)]
        levers = (sorted([i for i in items if i["delta"] >= 1.0], key=lambda i: -i["delta"])[:3]
                  + sorted([i for i in items if i["delta"] <= -1.0], key=lambda i: i["delta"])[:3])

    # --- synthèse
    diff = hours - overall
    summary = (f"Le modèle estime à environ {hours:.0f} h par semaine la durée de travail de ce profil "
               f"(fourchette indicative : {low:.0f} à {high:.0f} h), soit {abs(diff):.0f} h "
               f"{'de plus' if diff > 0 else 'de moins'} que la moyenne de la population ({overall:.0f} h).")
    up = [f["label"].lower() for f in factors if f["direction"] == "up" and not f["sensitive"] and f["impact"] >= 0.5][:2]
    down = [f["label"].lower() for f in factors if f["direction"] == "down" and not f["sensitive"] and f["impact"] <= -0.5][:2]
    if up:
        summary += " Facteurs qui allongent la durée : " + ", ".join(up) + "."
    if down:
        summary += " Facteurs qui la raccourcissent : " + ", ".join(down) + "."

    m = art["metrics"]
    return {
        "prediction": {"hours": round(hours, 1), "low": round(low, 1), "high": round(high, 1), "category": cat_key,
                       "category_label": cat_label, "vs_population": round(diff, 1), "reliability": "limitée",
                       "summary": summary},
        "occupation": {"value": occ, "label": OCCUPATIONS.get(occ, UNKNOWN_FR), "source": occ_src},
        "inputs": {"age": age, "education_num": education_num, "sex": SEX_FR.get(sex, sex),
                   "marital_status": MARITAL_FR.get(marital_status, marital_status),
                   "relationship": RELATIONSHIP_FR.get(relationship, relationship),
                   "income": None if income_high is None else _fmt_value("income_high", row)},
        "factors": factors, "comparisons": comparisons, "similar": similar, "charts": charts, "levers": levers,
        "overall": {"mean": overall, "n": int(len(pop))},
        "model": {"name": "XGBoost (régression)", **m, "params": art["params"], "source": source,
                  "interval": "80 % des cas observés"},
        "warnings": [
            f"Le modèle explique une part limitée des horaires réels (R² = {m['r2']:.2f}) : l'erreur moyenne est de "
            f"{m['mae']:.0f} h (contre {m['baseline_mae']:.0f} h en prédisant toujours la médiane). Utilisez la "
            "fourchette, pas la valeur seule.",
            "Estimation statistique fondée sur le recensement américain de 1994 : elle décrit des tendances de "
            "population, pas la disponibilité réelle ou la charge de travail souhaitée du candidat.",
            "Le sexe, le statut marital et le rôle familial sont des variables du modèle mais sont sensibles : ne les "
            "utilisez jamais pour décider d'une embauche, d'un horaire ou d'une rémunération.",
        ],
    }
