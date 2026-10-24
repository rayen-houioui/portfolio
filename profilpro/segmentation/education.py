"""Prédiction du niveau d'éducation (XGBoost : `models/xgboost_education.pkl`).

Le .pkl est un dictionnaire {model, features, target, classes, xgboost_version}. Le modèle attend
79 colonnes dans l'ordre de `features` : age, sex (0/1), hours-per-week, income_>50K, puis des indicateurs
one-hot (pandas.get_dummies(drop_first=True)) pour workclass, marital-status, occupation, relationship,
race et native-country. Aucune mise à l'échelle (arbres de décision). Les catégories de référence
(colonne supprimée à l'entraînement) correspondent à des indicateurs tous à 0.
"""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django.conf import settings

MODEL_FILE = "xgboost_education.pkl"

# ---- Ordre des classes -----------------------------------------------------------------------
# Le .pkl contient classes = {0: 'Below_HS', 1: 'Higher_Education', 2: 'HS_Graduate'}, mais ce dictionnaire est
# incohérent avec le comportement du modèle : sur adult.test, l'indice 2 est prédit pour Bachelors/Masters/Doctorate
# et l'indice 1 pour HS-grad/Some-college (≈ 64 % d'exactitude avec l'ordre ci-dessous, ≈ 33 % avec l'ordre du .pkl).
# L'ordre alphabétique (LabelEncoder) 0 = Below_HS, 1 = HS_Graduate, 2 = Higher_Education est donc utilisé.
# Si vous ré-exportez le modèle avec un dictionnaire `classes` corrigé, mettez simplement ce dictionnaire à jour.
CLASS_ORDER = {0: "Below_HS", 1: "HS_Graduate", 2: "Higher_Education"}

LEVELS = {
    "Below_HS": {
        "label": "Inférieur au baccalauréat",
        "short": "Niveau infra-bac",
        "text": "Études secondaires non terminées (au plus la 12e année sans diplôme du secondaire).",
    },
    "HS_Graduate": {
        "label": "Baccalauréat / études supérieures non diplômantes",
        "short": "Niveau bac",
        "text": "Diplôme de fin d'études secondaires (« HS-grad »), éventuellement suivi d'études supérieures sans diplôme (« Some-college »).",
    },
    "Higher_Education": {
        "label": "Enseignement supérieur",
        "short": "Enseignement supérieur",
        "text": "Diplôme de l'enseignement supérieur : associate, licence (bachelor), master, école professionnelle ou doctorat.",
    },
}
LEVEL_ORDER = ["Below_HS", "HS_Graduate", "Higher_Education"]

# ---- Valeurs valides (alignées sur les colonnes du modèle) : (valeur du dataset, libellé français) ----
WORKCLASS = [("Federal-gov", "Fonction publique fédérale"), ("Local-gov", "Collectivité locale"),
             ("State-gov", "Administration d'État"), ("Private", "Secteur privé"),
             ("Self-emp-inc", "Indépendant (société)"), ("Self-emp-not-inc", "Indépendant (hors société)"),
             ("Without-pay", "Bénévole / sans rémunération"), ("Never-worked", "Jamais travaillé")]
MARITAL = [("Never-married", "Célibataire"), ("Married-civ-spouse", "Marié(e), conjoint présent"),
           ("Married-spouse-absent", "Marié(e), conjoint absent"), ("Married-AF-spouse", "Marié(e) à un militaire"),
           ("Separated", "Séparé(e)"), ("Divorced", "Divorcé(e)"), ("Widowed", "Veuf / veuve")]
OCCUPATION = [("Adm-clerical", "Administratif"), ("Armed-Forces", "Forces armées"), ("Craft-repair", "Artisanat / réparation"),
              ("Exec-managerial", "Cadre dirigeant"), ("Farming-fishing", "Agriculture / pêche"),
              ("Handlers-cleaners", "Manutention / nettoyage"), ("Machine-op-inspct", "Opérateur machine / contrôle"),
              ("Other-service", "Autres services"), ("Priv-house-serv", "Employé de maison"),
              ("Prof-specialty", "Profession spécialisée"), ("Protective-serv", "Services de protection"),
              ("Sales", "Vente"), ("Tech-support", "Support technique"), ("Transport-moving", "Transport")]
RELATIONSHIP = [("Husband", "Époux"), ("Wife", "Épouse"), ("Own-child", "Enfant du ménage"),
                ("Not-in-family", "Hors famille"), ("Other-relative", "Autre parent"), ("Unmarried", "Non marié(e) (autre)")]
RACE = [("White", "Blanc"), ("Black", "Noir"), ("Asian-Pac-Islander", "Asiatique / Îles du Pacifique"),
        ("Amer-Indian-Eskimo", "Amérindien / Esquimau"), ("Other", "Autre")]
SEX = [("Female", "Femme"), ("Male", "Homme")]
INCOME = [("<=50K", "Revenu annuel ≤ 50 000 $"), (">50K", "Revenu annuel > 50 000 $")]
COUNTRY = [("Cambodia", "Cambodge"), ("Canada", "Canada"), ("China", "Chine"), ("Columbia", "Colombie"), ("Cuba", "Cuba"),
           ("Dominican-Republic", "République dominicaine"), ("Ecuador", "Équateur"), ("El-Salvador", "Salvador"),
           ("England", "Angleterre"), ("France", "France"), ("Germany", "Allemagne"), ("Greece", "Grèce"),
           ("Guatemala", "Guatemala"), ("Haiti", "Haïti"), ("Holand-Netherlands", "Pays-Bas"), ("Honduras", "Honduras"),
           ("Hong", "Hong Kong"), ("Hungary", "Hongrie"), ("India", "Inde"), ("Iran", "Iran"), ("Ireland", "Irlande"),
           ("Italy", "Italie"), ("Jamaica", "Jamaïque"), ("Japan", "Japon"), ("Laos", "Laos"), ("Mexico", "Mexique"),
           ("Nicaragua", "Nicaragua"), ("Outlying-US(Guam-USVI-etc)", "Territoires américains (Guam, îles Vierges…)"),
           ("Peru", "Pérou"), ("Philippines", "Philippines"), ("Poland", "Pologne"), ("Portugal", "Portugal"),
           ("Puerto-Rico", "Porto Rico"), ("Scotland", "Écosse"), ("South", "South (non précisé)"),
           ("Taiwan", "Taïwan"), ("Thailand", "Thaïlande"), ("Trinadad&Tobago", "Trinité-et-Tobago"),
           ("United-States", "États-Unis"), ("Vietnam", "Viêt Nam"), ("Yugoslavia", "Yougoslavie")]

# colonne du formulaire -> (préfixe des colonnes one-hot, valeurs autorisées)
CATEGORICAL = {"workclass": WORKCLASS, "marital_status": MARITAL, "occupation": OCCUPATION,
               "relationship": RELATIONSHIP, "race": RACE, "native_country": COUNTRY}
PREFIX = {"workclass": "workclass", "marital_status": "marital-status", "occupation": "occupation",
          "relationship": "relationship", "race": "race", "native_country": "native-country"}
SEX_CODE = {"Female": 0, "Male": 1}  # encodage supposé (ordre alphabétique) : non vérifiable dans le .pkl
AGE_RANGE, HOURS_RANGE = (17, 90), (1, 99)


class EducationInputError(ValueError):
    """Entrée invalide : `errors` associe un champ à un message en français."""

    def __init__(self, errors: dict):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


def options() -> dict:
    """Listes déroulantes du formulaire (valeur envoyée au modèle + libellé affiché)."""
    pack = lambda pairs: [{"value": v, "label": l} for v, l in pairs]
    return {"workclass": pack(WORKCLASS), "marital_status": pack(MARITAL), "occupation": pack(OCCUPATION),
            "relationship": pack(RELATIONSHIP), "race": pack(RACE), "sex": pack(SEX),
            "native_country": pack(COUNTRY), "income": pack(INCOME),
            "age": {"min": AGE_RANGE[0], "max": AGE_RANGE[1]}, "hours": {"min": HOURS_RANGE[0], "max": HOURS_RANGE[1]}}


@lru_cache(maxsize=1)
def get_artifact() -> dict:
    """Charge le .pkl du projet une seule fois (fichier de confiance du dépôt, jamais un fichier envoyé par un utilisateur)."""
    path = settings.BASE_DIR / "models" / MODEL_FILE
    if not path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {path}")
    art = joblib.load(path)
    feats = list(art["features"])
    expected = {"age", "sex", "hours-per-week", "income_>50K"}
    expected |= {f"{PREFIX[k]}_{v}" for k, pairs in CATEGORICAL.items() for v, _ in pairs}
    unknown = [f for f in feats if f not in expected]
    if len(feats) != 79 or unknown or getattr(art["model"], "n_classes_", 3) != 3:
        raise RuntimeError(f"Le fichier {MODEL_FILE} ne correspond pas aux variables attendues ({unknown[:3]}).")
    return art


def _clean(data: dict) -> dict:
    """Valide et normalise les champs du formulaire."""
    errors, out = {}, {}
    for key, (lo, hi), label in (("age", AGE_RANGE, "L'âge"), ("hours_per_week", HOURS_RANGE, "Le nombre d'heures par semaine")):
        raw = data.get(key)
        try:
            number = float(raw)
            if raw in (None, "") or isinstance(raw, bool) or number != int(number):
                raise ValueError
            number = int(number)
        except (TypeError, ValueError, OverflowError):
            errors[key] = f"{label} doit être un nombre entier."
            continue
        if not lo <= number <= hi:
            errors[key] = f"{label} doit être compris entre {lo} et {hi}."
        out[key] = number
    for key, pairs in (*CATEGORICAL.items(), ("sex", SEX), ("income", INCOME)):
        value = data.get(key)
        if value in (None, ""):
            errors[key] = "Ce champ est obligatoire."
        elif value not in {v for v, _ in pairs}:
            errors[key] = "Valeur non reconnue par le modèle."
        else:
            out[key] = value
    if errors:
        raise EducationInputError(errors)
    return out


def build_frame(clean: dict, features: list[str]) -> pd.DataFrame:
    """Une ligne, colonnes dans l'ordre exact de l'entraînement, avec les mêmes types (int / float / indicateur booléen)."""
    row = {f: False for f in features}
    row.update({"age": clean["age"], "sex": SEX_CODE[clean["sex"]], "hours-per-week": float(clean["hours_per_week"]),
                "income_>50K": clean["income"] == ">50K"})
    for key in CATEGORICAL:
        column = f"{PREFIX[key]}_{clean[key]}"
        if column in row:  # absent = catégorie de référence (drop_first) -> tous les indicateurs à 0
            row[column] = True
    df = pd.DataFrame([row], columns=features)
    return df.astype({"age": "int64", "sex": "int64", "hours-per-week": "float64"})


def _label(options_list, value):
    return dict(options_list).get(value, value)


def predict(data: dict) -> dict:
    clean = _clean(data)
    art = get_artifact()
    frame = build_frame(clean, list(art["features"]))
    proba = np.asarray(art["model"].predict_proba(frame))[0]
    if proba.shape != (len(CLASS_ORDER),) or not np.isclose(proba.sum(), 1.0, atol=1e-3):
        raise RuntimeError("Probabilités inattendues renvoyées par le modèle.")
    best = int(np.argmax(proba))
    code = CLASS_ORDER[best]
    probabilities = [{"code": c, "label": LEVELS[c]["label"], "probability": round(float(proba[i]) * 100, 1)}
                     for i, c in sorted(CLASS_ORDER.items(), key=lambda kv: LEVEL_ORDER.index(kv[1]))]
    summary = [("Âge", f"{clean['age']} ans"), ("Sexe", _label(SEX, clean["sex"])), ("Origine ethnique", _label(RACE, clean["race"])),
               ("Pays d'origine", _label(COUNTRY, clean["native_country"])),
               ("Statut marital", _label(MARITAL, clean["marital_status"])), ("Rôle familial", _label(RELATIONSHIP, clean["relationship"])),
               ("Catégorie d'emploi", _label(WORKCLASS, clean["workclass"])), ("Métier", _label(OCCUPATION, clean["occupation"])),
               ("Heures par semaine", f"{clean['hours_per_week']} h"), ("Revenu annuel", _label(INCOME, clean["income"]))]
    return {
        "prediction": {"code": code, "label": LEVELS[code]["label"], "short": LEVELS[code]["short"],
                       "description": LEVELS[code]["text"], "probability": round(float(proba[best]) * 100, 1)},
        "probabilities": probabilities,
        "summary": [{"label": k, "value": v} for k, v in summary],
        "model": {"name": "XGBoost (multi:softprob)", "n_features": len(art["features"]), "n_classes": len(CLASS_ORDER),
                  "xgboost_version_trained": art.get("xgboost_version")},
    }
