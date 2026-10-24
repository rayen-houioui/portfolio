"""Chargement et utilisation du modèle de segmentation (modele_profilpro.pkl)."""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django.conf import settings

MARITAL = ["Divorced", "Married-AF-spouse", "Married-civ-spouse", "Married-spouse-absent",
           "Never-married", "Separated", "Widowed"]
RELATIONSHIP = ["Husband", "Not-in-family", "Other-relative", "Own-child", "Unmarried", "Wife"]
SEX = ["Female", "Male"]


def check(model: dict, tol: float = 0.05):
    """Les centres K-Means, ramenés dans l'espace d'origine, doivent avoir des groupes
    one-hot qui somment à ~1. Sinon K-Means, ACP et préprocesseur sont incohérents."""
    names = model["feature_names"]
    inv = model["kmeans"].cluster_centers_ @ model["pca"].components_ + model["pca"].mean_
    ok = True
    for feat in model["cat_features"]:
        idx = [i for i, n in enumerate(names) if n.startswith(f"cat__{feat}_")]
        ok &= bool(np.all(np.abs(inv[:, idx].sum(axis=1) - 1) <= tol))
    return ok


@lru_cache(maxsize=1)
def get_model():
    model = joblib.load(settings.MODEL_PATH)
    return model, check(model)


def predict(age, education_num, marital_status, relationship, sex):
    model, consistent = get_model()
    row = pd.DataFrame([{"age": age, "education-num": education_num, "marital-status": marital_status,
                         "relationship": relationship, "sex": sex}])[model["features"]]
    z = model["pca"].transform(model["preprocessor"].transform(row))
    raw = int(model["kmeans"].predict(z)[0])
    mapping = model["mapping_clusters"]
    cluster = int(mapping[raw])
    dist = np.linalg.norm(model["kmeans"].cluster_centers_ - z, axis=1)
    distances = {int(mapping[i]): round(float(d), 3) for i, d in enumerate(dist)}
    return {"cluster": cluster, "profile_name": model["noms_profils"][cluster],
            "distances": dict(sorted(distances.items())), "model_consistent": consistent}
