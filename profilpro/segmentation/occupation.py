"""Prédiction de la catégorie de poste (modèle CatBoost fourni par l'utilisateur :
`models/catboost_model.pkl` + `models/catboost_features.pkl`).

Contrairement à `income.py` (qui prend le métier en entrée pour prédire le revenu), ce modèle
prédit le métier lui-même : il classe le candidat dans l'une de 3 catégories de qualification
professionnelle à partir de variables socio-démographiques (pas du texte libre du métier).

Le .pkl du modèle est un CatBoostClassifier dont les features attendues (dans l'ordre, stocké
dans catboost_features.pkl) sont : age, workclass, education_num, marital, relationship, race,
sex, cap_gain, cap_loss, hours, income (les 6 dernières sont catégorielles, gérées nativement
par CatBoost : aucun encodage à faire côté Django).
"""
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

from .education import RACE, WORKCLASS  # listes (valeur, libellé) déjà utilisées par la prédiction d'éducation

CLASS_INFO = {
    "Peu_Qualifie_Service": {
        "label": "Poste peu qualifié / services",
        "text": "Emplois de service ou manuels peu qualifiés : manutention, nettoyage, autres services, agriculture, "
                "sécurité de base...",
    },
    "Qualifie_Bureau_Gestion": {
        "label": "Poste qualifié — bureau / gestion",
        "text": "Emplois administratifs, de gestion ou de direction : administratif, cadre dirigeant, support "
                "technique, vente...",
    },
    "Qualifie_Metier_Technique": {
        "label": "Poste qualifié — métier technique",
        "text": "Métiers techniques ou spécialisés : artisanat, réparation, opérateur machine, transport, "
                "profession spécialisée...",
    },
}

INCOME = [("<=50K", "Revenu annuel ≤ 50 000 $"), (">50K", "Revenu annuel > 50 000 $")]


def options() -> dict:
    """Valeurs des listes déroulantes propres à ce modèle (workclass/race viennent de la prédiction d'éducation)."""
    pack = lambda pairs: [{"value": v, "label": l} for v, l in pairs]
    return {"workclass": pack(WORKCLASS), "race": pack(RACE)}


@lru_cache(maxsize=1)
def get_artifact() -> dict:
    """Charge les deux .pkl de l'utilisateur une seule fois (fichiers de confiance du dépôt)."""
    model_path, features_path = settings.OCCUPATION_MODEL_PATH, settings.OCCUPATION_FEATURES_PATH
    if not model_path.exists() or not features_path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {model_path} / {features_path}")
    model = joblib.load(model_path)
    features = list(joblib.load(features_path))
    return {"model": model, "features": features}


def analyze(age, education_num, workclass, marital_status, relationship, race, sex,
            hours_per_week=40, capital_gain=0, capital_loss=0, income_high=None) -> dict:
    art = get_artifact()
    income_estimated = income_high is None
    income_value = ">50K" if income_high else "<=50K"  # valeur par défaut la plus fréquente si inconnu

    row = pd.DataFrame([{
        "age": age, "workclass": workclass, "education_num": education_num, "marital": marital_status,
        "relationship": relationship, "race": race, "sex": sex, "cap_gain": capital_gain,
        "cap_loss": capital_loss, "hours": hours_per_week, "income": income_value,
    }])[art["features"]]

    proba = art["model"].predict_proba(row)[0]
    classes = list(art["model"].classes_)
    best = int(proba.argmax())
    code = str(classes[best])
    info = CLASS_INFO.get(code, {"label": code, "text": ""})

    probabilities = sorted(
        ({"code": str(c), "label": CLASS_INFO.get(str(c), {"label": str(c)})["label"], "probability": round(float(p) * 100, 1)}
         for c, p in zip(classes, proba)),
        key=lambda x: -x["probability"],
    )

    return {
        "prediction": {"code": code, "label": info["label"], "description": info.get("text", ""),
                       "probability": round(float(proba[best]) * 100, 1)},
        "probabilities": probabilities,
        "inputs": {"age": age, "education_num": education_num, "workclass": workclass,
                   "marital_status": marital_status, "relationship": relationship, "race": race, "sex": sex,
                   "hours_per_week": hours_per_week, "capital_gain": capital_gain, "capital_loss": capital_loss,
                   "income": income_value, "income_estimated": income_estimated},
        "model": {"name": "CatBoost (MultiClass)", "classes": classes, "n_features": len(art["features"])},
        "warnings": [
            "Modèle fourni séparément (non ré-entraîné par ProfilPro), entraîné sur des variables "
            "socio-démographiques : à valider avant toute décision RH.",
            "Le sexe et le rôle familial sont des variables sensibles du modèle : ne jamais les utiliser seuls "
            "pour une décision d'embauche ou de rémunération.",
        ] + (["Revenu non renseigné : estimé automatiquement à « ≤ 50 000 $ » pour la prédiction."]
             if income_estimated else []),
    }
