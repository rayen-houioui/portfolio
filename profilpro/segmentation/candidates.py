"""Enregistrement des candidats analysés + comparaison prédiction / résultat réel.

Appelé juste après chaque prédiction (segmentation, éducation, revenu, heures) pour garder
une trace en base : les entrées envoyées au modèle et ce qu'il a prédit. Le résultat réel
(`actual_*`) est saisi plus tard par un RH, quand il est connu, via set_outcome().
"""
import logging

from .models import Candidate

log = logging.getLogger(__name__)


def save_candidate(kind: str, inputs: dict, predicted_code, predicted_label: str, predicted_payload: dict,
                    name: str = "") -> int | None:
    """Enregistre un candidat juste après une prédiction. Ne lève jamais d'exception :
    si la base est indisponible, la prédiction déjà renvoyée au front n'est pas perdue."""
    try:
        c = Candidate.objects.create(
            kind=kind, name=(name or "")[:120], inputs=inputs or {},
            predicted_code=str(predicted_code if predicted_code is not None else "")[:60],
            predicted_label=str(predicted_label or "")[:200],
            predicted=predicted_payload or {},
        )
        return c.id
    except Exception:
        log.exception("Impossible d'enregistrer le candidat en base (prédiction non bloquée)")
        return None


def set_outcome(candidate_id: int, actual_code: str, actual_label: str = "", actual_note: str = "") -> Candidate:
    c = Candidate.objects.get(pk=candidate_id)
    c.actual_code = str(actual_code or "")[:60]
    c.actual_label = str(actual_label or "")[:200]
    c.actual_note = str(actual_note or "")[:300]
    c.save(update_fields=["actual_code", "actual_label", "actual_note", "updated_at"])
    return c


def compare_stats(kind: str | None = None) -> dict:
    """Taux de réussite prédit vs réel, pour les candidats dont le résultat réel est connu."""
    qs = Candidate.objects.exclude(actual_code="")
    if kind:
        qs = qs.filter(kind=kind)
    total = qs.count()
    correct = sum(1 for c in qs if c.predicted_code == c.actual_code)
    rows = [{
        "id": c.id, "kind": c.kind, "name": c.name,
        "predicted_code": c.predicted_code, "predicted_label": c.predicted_label,
        "actual_code": c.actual_code, "actual_label": c.actual_label,
        "is_correct": c.predicted_code == c.actual_code, "created_at": c.created_at.isoformat(),
    } for c in qs.order_by("-created_at")[:200]]
    return {
        "total_with_outcome": total, "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total else None,
        "rows": rows,
    }
