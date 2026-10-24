"""Recommandation salariale (USD) à partir d'un référentiel sourcé (BLS, mai 2025).

Le score du modèle de revenu (CatBoost, > / <= 50 000 $) n'entre PAS dans le calcul du salaire :
il est entraîné sur des données de 1994 et ne donne pas de salaire. Les montants viennent uniquement
du référentiel `data/salary_reference.json`. Si un métier n'y figure pas, rien n'est inventé.
"""
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from django.conf import settings

REFERENCE_PATH = Path(settings.BASE_DIR) / "data" / "salary_reference.json"
LEVELS = {"junior": "Junior", "confirme": "Confirmé", "senior": "Senior"}
LEVEL_TEXT = {
    "junior": "Positionnement entre le 10e percentile et la médiane du marché : profil en début de parcours, "
              "missions d'exécution avec encadrement.",
    "confirme": "Positionnement autour de la médiane du marché : autonomie sur les missions courantes.",
    "senior": "Positionnement entre la médiane et le 90e percentile : expertise reconnue, responsabilités élargies.",
}


@lru_cache(maxsize=1)
def load_reference() -> dict:
    with open(REFERENCE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _norm(text) -> str:
    t = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t).strip()


def roles() -> list[dict]:
    return [{"key": r["key"], "label": r["label"]} for r in load_reference()["roles"]]


def match_role(text: str) -> str | None:
    """Associe l'intitulé libre du CV à un métier du référentiel (mots entiers, sans accents)."""
    t = _norm(text)
    if not t:
        return None
    for role in load_reference()["roles"]:
        for alias in role["aliases"]:
            if re.search(rf"(?<![a-z]){re.escape(_norm(alias))}(?![a-z])", t):
                return role["key"]
    return None


def level_from_years(years) -> str:
    if years is None:
        return "confirme"
    return "junior" if years < 3 else "confirme" if years <= 7 else "senior"


def _compare(expected_monthly: float, rec_monthly: dict) -> dict:
    lo, advised, hi = rec_monthly["min"], rec_monthly["advised"], rec_monthly["max"]
    if expected_monthly < lo:
        position, text = "below", "En dessous de la fourchette recommandée."
    elif expected_monthly > hi:
        position, text = "above", "Au-dessus de la fourchette recommandée."
    else:
        position, text = "within", "Dans la fourchette recommandée."
    diff = expected_monthly - advised
    return {"expected_monthly": round(expected_monthly), "position": position, "text": text,
            "diff_vs_advised": round(diff), "diff_pct": round(diff / advised * 100, 1) if advised else None}


def recommend(role_key, years=None, level=None, expected_monthly=None) -> dict:
    ref = load_reference()
    base = {"currency": "USD", "source": ref["source"], "reference_date": ref["reference_date"],
            "method": ref["method"], "roles": roles()}
    role = next((r for r in ref["roles"] if r["key"] == role_key), None)
    if role is None:
        return {**base, "available": False, "role": None, "level": None, "years": years,
                "message": "Aucune donnée salariale fiable n'est disponible pour ce métier. Choisissez un métier "
                           "dans la liste ou ajoutez-le au référentiel salarial. Aucun salaire n'a été estimé.",
                "annual": None, "monthly": None, "justification": [], "comparison": None}

    lvl = level if level in LEVELS else level_from_years(years)
    p10, med, p90 = role["p10"], role["median"], role["p90"]
    lo_mid, hi_mid = (p10 + med) / 2, (med + p90) / 2
    lo, advised, hi = {"junior": (p10, lo_mid, med), "confirme": (lo_mid, med, hi_mid),
                       "senior": (med, hi_mid, p90)}[lvl]
    annual = {"min": round(lo), "advised": round(advised), "max": round(hi)}
    monthly = {k: round(v / 12) for k, v in annual.items()}

    if years is None:
        exp_text = "expérience non renseignée : niveau confirmé retenu par défaut"
    else:
        exp_text = f"{years} an{'s' if years > 1 else ''} d'expérience"
    justification = [
        f"Métier : {role['label']}. Référence BLS (mai 2025) : salaire médian de ${med:,.0f} par an aux "
        f"États-Unis, marché entre ${p10:,.0f} (10e percentile) et ${p90:,.0f} (90e percentile).",
        f"Niveau retenu : {LEVELS[lvl]} ({exp_text}).",
        LEVEL_TEXT[lvl],
        "Limite : données américaines nationales, non ajustées au lieu de travail, à la taille de l'entreprise "
        "ni à l'inflation depuis 2025. Valider avant toute offre.",
        "Le score du modèle de revenu n'est pas utilisé pour fixer ce salaire.",
    ]
    return {**base, "available": True, "message": None,
            "role": {"key": role["key"], "label": role["label"], "url": role["url"]},
            "level": lvl, "level_label": LEVELS[lvl], "years": years,
            "annual": {**annual, "market_p10": round(p10), "market_median": round(med), "market_p90": round(p90)},
            "monthly": monthly, "justification": justification,
            "comparison": _compare(float(expected_monthly), monthly) if expected_monthly is not None else None}
