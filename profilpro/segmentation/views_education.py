"""API de la prédiction du niveau d'éducation (modèle XGBoost `xgboost_education.pkl`)."""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import candidates, education

log = logging.getLogger(__name__)


@require_GET
def options(request):
    """Valeurs des listes déroulantes (identiques aux catégories connues du modèle)."""
    return JsonResponse(education.options())


@csrf_exempt  # même convention que les autres endpoints de l'API (appel same-origin) ; à protéger avant toute mise en production
@require_POST
def predict(request):
    """POST {age, sex, race, native_country, marital_status, relationship, workclass, occupation, hours_per_week, income}."""
    try:
        data = json.loads(request.body or b"{}")
        if not isinstance(data, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "Corps de requête JSON invalide."}, status=400)
    try:
        result = education.predict(data)
        pred = result.get("prediction") or {}
        cid = candidates.save_candidate("education", data, pred.get("code"), pred.get("label"), result,
                                        name=str(data.get("candidate_name") or ""))
        result["candidate_id"] = cid
        return JsonResponse(result)
    except education.EducationInputError as exc:
        return JsonResponse({"error": "Certaines valeurs sont invalides.", "fields": exc.errors}, status=400)
    except FileNotFoundError as exc:
        log.error("%s", exc)
        return JsonResponse({"error": "Le modèle de prédiction est introuvable sur le serveur."}, status=503)
    except Exception:  # dépendance manquante (xgboost), .pkl incompatible, etc. : aucun détail interne n'est exposé
        log.exception("Échec de la prédiction du niveau d'éducation")
        return JsonResponse({"error": "La prédiction a échoué côté serveur. Vérifiez que « xgboost » est installé (pip install -r requirements.txt)."}, status=500)
