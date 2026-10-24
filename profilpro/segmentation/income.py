"""Classification des revenus (modèle CatBoost `models/catboost_adult.pkl`) + analyses pour les RH.

Le .pkl est un dictionnaire : {model, features, cols_log, cols_num, cols_cat, bornes, valeur_inconnue, classes, ...}.
Prétraitement reproduit ici à l'identique de l'entraînement :
  1. log1p sur capital-gain et capital-loss ;
  2. écrêtage (clip) de age et hours-per-week sur les bornes sauvegardées ;
  3. variables catégorielles manquantes -> « Inconnu » (valeur_inconnue).

Ce que renvoie `analyze()` (tout en français, prêt pour l'affichage) :
  - la prédiction (classe, probabilité, niveau de confiance, phrase de synthèse) ;
  - les facteurs qui expliquent la prédiction (valeurs SHAP de CatBoost) ;
  - la comparaison avec des profils réels du jeu Adult (même métier, même niveau d'études, même tranche d'âge) ;
  - les taux de revenu élevé par niveau d'études / âge / heures / métier (graphiques) ;
  - des leviers théoriques (« et si… ») calculés en re-prédisant des variantes du profil.
"""
import re
import unicodedata
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django.conf import settings

# --------------------------------------------------------------------------- libellés
OCCUPATIONS = {
    "Adm-clerical": "Administratif / secrétariat",
    "Armed-Forces": "Forces armées",
    "Craft-repair": "Artisanat / réparation",
    "Exec-managerial": "Direction / management",
    "Farming-fishing": "Agriculture / pêche",
    "Handlers-cleaners": "Manutention / nettoyage",
    "Machine-op-inspct": "Opérateur machine / contrôle",
    "Other-service": "Autres services",
    "Priv-house-serv": "Services à domicile",
    "Prof-specialty": "Profession spécialisée / intellectuelle",
    "Protective-serv": "Sécurité / protection",
    "Sales": "Vente / commerce",
    "Tech-support": "Support technique",
    "Transport-moving": "Transport / logistique",
}
UNKNOWN_FR = "Métier non identifié"

FEATURE_FR = {
    "capital-gain": "Gains en capital", "capital-loss": "Pertes en capital", "age": "Âge",
    "education-num": "Niveau d'études", "hours-per-week": "Heures travaillées par semaine",
    "occupation": "Métier", "relationship": "Rôle dans la famille", "sex": "Sexe",
}
SENSITIVE = {"sex", "relationship"}  # variables sensibles : à ne jamais utiliser pour décider d'une embauche ou d'un salaire

RELATIONSHIP_FR = {"Husband": "Époux", "Wife": "Épouse", "Not-in-family": "Hors cercle familial",
                   "Own-child": "Enfant au foyer", "Unmarried": "Non marié(e) en foyer", "Other-relative": "Autre parent"}
SEX_FR = {"Female": "Femme", "Male": "Homme"}

# Règles de déduction métier (texte du CV -> catégorie Adult). Ordre = priorité.
_RULES = [
    ("Tech-support", ["support technique", "support informatique", "helpdesk", "help desk", "technicien informatique",
                      "administrateur systeme", "administrateur reseau", "sysadmin", "it support", "technical support",
                      "maintenance informatique", "assistance utilisateur"]),
    ("Exec-managerial", ["directeur", "directrice", "direction", "manager", "management", "responsable", "chef de",
                         "chef d'", "gerant", "gestion de", "dirigeant", "pdg", "ceo", "entrepreneur", "executive",
                         "head of", "director"]),
    ("Prof-specialty", ["developp", "ingenieur", "informatique", "logiciel", "data", "scientist", "analyste", "chercheu",
                        "enseignant", "professeur", "medecin", "avocat", "juriste", "architecte", "comptab", "financ",
                        "consultant", "infirmi", "pharmac", "designer", "journalis", "software", "engineer", "developer",
                        "research", "teacher", "lawyer", "doctor", "nurse", "accountant", "statisti", "biolog", "chimi",
                        "psycholog", "formateur", "redacteur", "graphiste", "intelligence artificielle", "machine learning"]),
    ("Sales", ["vente", "commercial", "vendeu", "sales", "marketing", "chargé de clientele", "charge de clientele",
               "conseiller clientele", "business developer", "retail", "caissier", "agent immobilier"]),
    ("Adm-clerical", ["administratif", "secretaire", "assistant", "assistante", "gestionnaire", "comptable", "accueil",
                      "clerk", "standard", "saisie", "back office", "office"]),
    ("Craft-repair", ["artisan", "mecanicien", "electricien", "plombier", "menuisier", "macon", "soudeur", "reparation",
                      "technicien", "maintenance", "carrossier", "peintre en batiment"]),
    ("Farming-fishing", ["agricult", "agriculteur", "ferme", "elevage", "peche", "viticult", "jardinier", "farming"]),
    ("Protective-serv", ["police", "pompier", "gendarme", "securite", "agent de securite", "surveillant", "protective"]),
    ("Transport-moving", ["chauffeur", "transport", "livreur", "logisti", "routier", "conducteur", "cariste", "driver"]),
    ("Handlers-cleaners", ["manutention", "nettoyage", "agent d'entretien", "entretien", "magasinier", "cleaner", "preparateur de commandes"]),
    ("Machine-op-inspct", ["operateur", "production", "usine", "controle qualite", "machine", "assemblage", "ouvrier"]),
    ("Priv-house-serv", ["aide a domicile", "femme de menage", "garde d'enfants", "nounou", "employe de maison", "domestique"]),
    ("Armed-Forces", ["armee", "militaire", "forces armees", "marine nationale", "armed forces"]),
    ("Other-service", ["serveur", "serveuse", "restaurat", "hotel", "cuisinier", "coiffeu", "service", "barman", "accueil clientele"]),
]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", text).strip()


def infer_occupation(text: str):
    """Déduit une catégorie Adult à partir du métier écrit dans le CV (None si rien ne correspond)."""
    t = _norm(text)
    if not t:
        return None
    for cat, words in _RULES:
        if any(_norm(w) in t for w in words):
            return cat
    return None


# --------------------------------------------------------------------------- modèle
@lru_cache(maxsize=1)
def get_artifact() -> dict:
    return joblib.load(settings.INCOME_MODEL_PATH)


def _frame(rows: list[dict], art: dict) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for c in art["cols_log"]:
        df[c] = np.log1p(df[c].astype(float))
    for c, (lo, hi) in art["bornes"].items():
        df[c] = df[c].astype(float).clip(lo, hi)
    for c in art["cols_cat"]:
        df[c] = df[c].where(df[c].notna(), art["valeur_inconnue"]).astype(str)
    return df[art["features"]]


def _proba(rows: list[dict]) -> np.ndarray:
    art = get_artifact()
    return np.asarray(art["model"].predict_proba(_frame(rows, art)))[:, 1]


def _shap(row: dict) -> tuple[list[float], float]:
    """Contributions de chaque variable (log-odds) pour ce profil. Renvoie ([], 0) si indisponible."""
    art = get_artifact()
    try:
        from catboost import Pool

        df = _frame([row], art)
        sv = art["model"].get_feature_importance(Pool(df, cat_features=art["cols_cat"]), type="ShapValues")
        sv = np.asarray(sv)[0]
        return [float(x) for x in sv[:-1]], float(sv[-1])
    except Exception:
        return [], 0.0


# --------------------------------------------------------------------------- population de référence
EDU_BINS = [(0, 8, "Avant le bac"), (9, 9, "Bac"), (10, 12, "Bac à bac+2"), (13, 13, "Licence"),
            (14, 14, "Master"), (15, 16, "Doctorat / écoles pro.")]
AGE_BINS = [(0, 24, "< 25 ans"), (25, 34, "25-34 ans"), (35, 44, "35-44 ans"), (45, 54, "45-54 ans"),
            (55, 64, "55-64 ans"), (65, 200, "65 ans et +")]
HOURS_BINS = [(0, 34, "< 35 h"), (35, 40, "35-40 h"), (41, 50, "41-50 h"), (51, 200, "> 50 h")]


def _bin_label(value, bins):
    for lo, hi, label in bins:
        if lo <= value <= hi:
            return label
    return bins[-1][2]


@lru_cache(maxsize=1)
def _population():
    from .clustering import load_dataframe  # import tardif : évite de charger matplotlib/seaborn inutilement

    raw, source = load_dataframe()
    df = raw.copy()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype("string").str.strip()
    df["income"] = df["income"].astype("string").str.replace(".", "", regex=False)
    df = df.dropna(subset=["age", "education-num", "income"]).drop_duplicates().reset_index(drop=True)
    df["high"] = (df["income"] == ">50K").astype(int)
    df["edu_bin"] = df["education-num"].astype(int).map(lambda v: _bin_label(v, EDU_BINS))
    df["age_bin"] = df["age"].astype(int).map(lambda v: _bin_label(v, AGE_BINS))
    df["hours_bin"] = df["hours-per-week"].astype(int).map(lambda v: _bin_label(v, HOURS_BINS))
    return df, source


def _rate(g) -> float:
    return round(float(g["high"].mean()) * 100, 1) if len(g) else 0.0


def _chart(df, col, order, mine):
    out = []
    for label in order:
        g = df[df[col] == label]
        if len(g) >= 20:
            out.append({"label": label, "rate": _rate(g), "n": int(len(g)), "mine": label == mine})
    return out


# --------------------------------------------------------------------------- analyse principale
def _fmt_value(feature: str, row: dict) -> str:
    v = row[feature]
    if feature == "age":
        return f"{int(v)} ans"
    if feature == "education-num":
        return f"{_bin_label(int(v), EDU_BINS)} ({int(v)} ans d'études)"
    if feature == "hours-per-week":
        return f"{int(v)} h"
    if feature in ("capital-gain", "capital-loss"):
        return f"{int(v):,} $".replace(",", " ")
    if feature == "occupation":
        return OCCUPATIONS.get(v, UNKNOWN_FR)
    if feature == "relationship":
        return RELATIONSHIP_FR.get(v, v)
    if feature == "sex":
        return SEX_FR.get(v, v)
    return str(v)


def _confidence(p_high: float) -> str:
    c = max(p_high, 1 - p_high)
    return "faible" if c < 0.6 else "moyenne" if c < 0.8 else "élevée"


def analyze(age, education_num, relationship, sex, hours_per_week=40, capital_gain=0, capital_loss=0,
            occupation="", occupation_text=""):
    art = get_artifact()

    # --- métier : choisi par le RH, sinon déduit du CV, sinon « Inconnu » (valeur gérée nativement par le modèle)
    if occupation in OCCUPATIONS:
        occ, occ_src = occupation, "choisi"
    else:
        occ = infer_occupation(occupation_text)
        occ_src = "déduit du CV" if occ else "inconnu"
    occ_value = occ or art["valeur_inconnue"]

    row = {"capital-gain": capital_gain, "capital-loss": capital_loss, "age": age, "education-num": education_num,
           "hours-per-week": hours_per_week, "occupation": occ_value, "relationship": relationship, "sex": sex}

    p_high = float(_proba([row])[0])
    is_high = p_high >= 0.5

    # --- facteurs explicatifs (SHAP)
    shap_vals, _base = _shap(row)
    factors = []
    if shap_vals:
        total = sum(abs(x) for x in shap_vals) or 1.0
        for feat, val in zip(art["features"], shap_vals):
            factors.append({"feature": feat, "label": FEATURE_FR.get(feat, feat), "value": _fmt_value(feat, row),
                            "impact": round(val, 3), "weight_pct": round(100 * abs(val) / total, 1),
                            "direction": "up" if val > 0 else "down", "sensitive": feat in SENSITIVE})
        factors.sort(key=lambda f: -abs(f["impact"]))

    # --- comparaison avec la population réelle
    pop, source = _population()
    edu_bin, age_bin, hours_bin = (_bin_label(int(education_num), EDU_BINS), _bin_label(int(age), AGE_BINS),
                                   _bin_label(int(hours_per_week), HOURS_BINS))
    overall_rate = _rate(pop)
    comparisons = [{"label": "Ensemble de la population", "rate": overall_rate, "n": int(len(pop))}]
    if occ:
        g = pop[pop["occupation"] == occ]
        if len(g) >= 20:
            comparisons.append({"label": f"Même métier ({OCCUPATIONS[occ]})", "rate": _rate(g), "n": int(len(g))})
    g = pop[pop["edu_bin"] == edu_bin]
    comparisons.append({"label": f"Même niveau d'études ({edu_bin})", "rate": _rate(g), "n": int(len(g))})
    g = pop[pop["age_bin"] == age_bin]
    comparisons.append({"label": f"Même tranche d'âge ({age_bin})", "rate": _rate(g), "n": int(len(g))})
    g = pop[pop["hours_bin"] == hours_bin]
    comparisons.append({"label": f"Mêmes horaires ({hours_bin})", "rate": _rate(g), "n": int(len(g))})

    # profils similaires : on relâche les critères tant qu'il y a moins de 30 personnes
    criteria = [("edu_bin", edu_bin, f"études : {edu_bin}"), ("age_bin", age_bin, f"âge : {age_bin}")]
    if occ:
        criteria.insert(0, ("occupation", occ, f"métier : {OCCUPATIONS[occ]}"))
    similar = None
    for cut in range(len(criteria), 0, -1):
        g = pop
        for col, val, _ in criteria[:cut]:
            g = g[g[col] == val]
        if len(g) >= 30:
            similar = {"n": int(len(g)), "rate": _rate(g), "criteria": [c[2] for c in criteria[:cut]]}
            break

    charts = {
        "education": _chart(pop, "edu_bin", [b[2] for b in EDU_BINS], edu_bin),
        "age": _chart(pop, "age_bin", [b[2] for b in AGE_BINS], age_bin),
        "hours": _chart(pop, "hours_bin", [b[2] for b in HOURS_BINS], hours_bin),
    }
    occ_rows = [{"label": OCCUPATIONS.get(o, o), "rate": _rate(g), "n": int(len(g)), "mine": o == occ}
                for o, g in pop.dropna(subset=["occupation"]).groupby("occupation") if len(g) >= 20]
    charts["occupation"] = sorted(occ_rows, key=lambda r: -r["rate"])

    # --- leviers théoriques : on re-prédit des variantes du profil
    scenarios = []
    if education_num < 16:
        scenarios.append(("Un niveau d'études supplémentaire", {**row, "education-num": education_num + 1}))
    if hours_per_week < 45:
        scenarios.append(("Travailler 45 h par semaine", {**row, "hours-per-week": 45}))
    for o, lbl in OCCUPATIONS.items():
        if o != occ:
            scenarios.append((f"Évoluer vers un métier de type « {lbl} »", {**row, "occupation": o}))
    levers = []
    if scenarios:
        probs = _proba([s[1] for s in scenarios])
        levers = [{"label": s[0], "proba": round(float(p) * 100, 1), "delta": round((float(p) - p_high) * 100, 1)}
                  for s, p in zip(scenarios, probs)]
        levers = sorted([l for l in levers if l["delta"] >= 1.0], key=lambda l: -l["delta"])[:5]

    # --- phrase de synthèse
    pct = round(p_high * 100)
    up = [f["label"].lower() for f in factors if f["direction"] == "up" and not f["sensitive"]][:2]
    down = [f["label"].lower() for f in factors if f["direction"] == "down" and not f["sensitive"]][:2]
    summary = (f"Le modèle estime à {pct} % la probabilité que ce profil gagne plus de 50 000 $ par an "
               f"(confiance {_confidence(p_high)}).")
    if up:
        summary += " Facteurs favorables : " + ", ".join(up) + "."
    if down:
        summary += " Facteurs défavorables : " + ", ".join(down) + "."

    try:
        params = art["model"].get_params()
    except Exception:
        params = {}
    return {
        "prediction": {
            "label": ">50K" if is_high else "<=50K",
            "label_fr": "Revenu élevé (> 50 000 $ / an)" if is_high else "Revenu standard (≤ 50 000 $ / an)",
            "proba_high": round(p_high * 100, 1), "confidence": _confidence(p_high), "summary": summary,
        },
        "occupation": {"value": occ_value, "label": OCCUPATIONS.get(occ, UNKNOWN_FR), "source": occ_src},
        "inputs": {"age": age, "education_num": education_num, "hours_per_week": hours_per_week,
                   "capital_gain": capital_gain, "capital_loss": capital_loss,
                   "relationship": RELATIONSHIP_FR.get(relationship, relationship), "sex": SEX_FR.get(sex, sex)},
        "factors": factors, "comparisons": comparisons, "similar": similar, "charts": charts, "levers": levers,
        "overall": {"rate": overall_rate, "n": int(len(pop))},
        "model": {"name": "CatBoost", "iterations": params.get("iterations"), "depth": params.get("depth"),
                  "version": art.get("catboost_version"), "source": source, "explanations": bool(factors)},
        "warnings": [
            "Estimation statistique fondée sur le recensement américain de 1994 (seuil de 50 000 $ de l'époque) : "
            "elle est indicative et ne remplace pas une évaluation individuelle.",
            "Le sexe et le rôle familial sont des variables du modèle mais sont sensibles : ne les utilisez jamais "
            "pour décider d'une embauche ou d'une rémunération.",
        ],
    }
