"""API de la segmentation professionnelle (modèle K-Means `kmeans_profils_socio_economiques.pkl`)."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import professional


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


@require_GET
def clusters(request):
    """Les profils (clusters) du modèle avec leurs moyennes + la carte des individus."""
    try:
        return JsonResponse(professional.overview())
    except FileNotFoundError as exc:
        return _error(str(exc), 503)


@csrf_exempt  # API appelée en same-origin par le front ; à protéger (CSRF/auth) avant toute mise en production
@require_POST
def analyze(request):
    """Classe un candidat : {age, education_num, hours_per_week, income_sup50k?} -> profil, moyennes, carte."""
    try:
        d = json.loads(request.body or b"{}")
        age, edu, hours = int(d["age"]), int(d["education_num"]), int(d["hours_per_week"])
    except (ValueError, KeyError, TypeError):
        return _error("Champs requis : age, education_num, hours_per_week (facultatif : income_sup50k = 0 ou 1).")
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        return _error("age doit être entre 17 et 90, education_num entre 1 et 16.")
    if not (1 <= hours <= 99):
        return _error("hours_per_week doit être entre 1 et 99.")
    raw = d.get("income_sup50k")
    if raw in (None, ""):
        income = None
    elif str(raw).lower() in ("0", "1", "true", "false"):
        income = 1 if str(raw).lower() in ("1", "true") else 0
    else:
        return _error("income_sup50k doit valoir 0 (revenu ≤ 50K $), 1 (revenu > 50K $) ou être absent.")
    try:
        return JsonResponse(professional.analyze(age, edu, hours, income))
    except FileNotFoundError as exc:  # modèle ou données introuvables
        return _error(str(exc), 503)
