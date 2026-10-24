import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import candidates, clustering, cv, hours, income, ml, occupation, report, salary


@require_GET
def health(request):
    model, consistent = ml.get_model()
    return JsonResponse({
        "status": "ok", "k": model["K"], "model_consistent": consistent,
        "warning": None if consistent else "Le .pkl est incohérent : les segments renvoyés ne sont pas fiables.",
    })


@require_GET
def profiles(request):
    model, _ = ml.get_model()
    return JsonResponse([{"cluster": int(k), "name": v} for k, v in sorted(model["noms_profils"].items())], safe=False)


@csrf_exempt  # API appelée en same-origin par le front ; à protéger (CSRF/auth) avant toute mise en production
@require_POST
def predict(request):
    try:
        d = json.loads(request.body)
        age, edu = int(d["age"]), int(d["education_num"])
        marital, rel, sex = d["marital_status"], d["relationship"], d["sex"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Champs requis : age, education_num, marital_status, relationship, sex."}, status=400)
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        return JsonResponse({"error": "age doit être entre 17 et 90, education_num entre 1 et 16."}, status=400)
    for value, allowed, label in ((marital, ml.MARITAL, "marital_status"), (rel, ml.RELATIONSHIP, "relationship"), (sex, ml.SEX, "sex")):
        if value not in allowed:
            return JsonResponse({"error": f"{label} invalide. Valeurs possibles : {', '.join(allowed)}."}, status=400)
    result = ml.predict(age, edu, marital, rel, sex)
    cid = candidates.save_candidate("segmentation", d, result.get("cluster"), result.get("profile_name"), result,
                                    name=str(d.get("candidate_name") or ""))
    result["candidate_id"] = cid
    return JsonResponse(result)


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def analyze(request):
    """Clustering du notebook : classe le candidat + renvoie fiches de clusters et graphiques (PNG base64)."""
    try:
        d = json.loads(request.body)
        age, edu = int(d["age"]), int(d["education_num"])
        marital, rel, sex = d["marital_status"], d["relationship"], d["sex"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Champs requis : age, education_num, marital_status, relationship, sex."}, status=400)
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        return JsonResponse({"error": "age doit être entre 17 et 90, education_num entre 1 et 16."}, status=400)
    for value, allowed, label in ((marital, ml.MARITAL, "marital_status"), (rel, ml.RELATIONSHIP, "relationship"), (sex, ml.SEX, "sex")):
        if value not in allowed:
            return JsonResponse({"error": f"{label} invalide. Valeurs possibles : {', '.join(allowed)}."}, status=400)
    try:
        result = clustering.analyze(age, edu, marital, rel, sex)
    except FileNotFoundError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    cand = result.get("candidate") or {}
    cid = candidates.save_candidate("segmentation", d, cand.get("cluster"), cand.get("profile_name"), result,
                                    name=str(d.get("candidate_name") or ""))
    result["candidate_id"] = cid
    return JsonResponse(result)


class _BadInput(Exception):
    pass


def _json_body(request) -> dict:
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        raise _BadInput("Corps JSON invalide.")


def _income_args(d: dict) -> dict:
    try:
        age, edu = int(d["age"]), int(d["education_num"])
        rel, sex = d["relationship"], d["sex"]
        hours = int(d.get("hours_per_week") or 40)
        gain, loss = int(d.get("capital_gain") or 0), int(d.get("capital_loss") or 0)
        occupation, occupation_text = str(d.get("occupation") or ""), str(d.get("occupation_text") or "")
    except (ValueError, KeyError, TypeError):
        raise _BadInput("Champs requis : age, education_num, relationship, sex "
                        "(facultatifs : hours_per_week, capital_gain, capital_loss, occupation, occupation_text).")
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        raise _BadInput("age doit être entre 17 et 90, education_num entre 1 et 16.")
    if not (1 <= hours <= 99):
        raise _BadInput("hours_per_week doit être entre 1 et 99.")
    if not (0 <= gain <= 99999 and 0 <= loss <= 99999):
        raise _BadInput("capital_gain et capital_loss doivent être entre 0 et 99999.")
    for value, allowed, label in ((rel, ml.RELATIONSHIP, "relationship"), (sex, ml.SEX, "sex")):
        if value not in allowed:
            raise _BadInput(f"{label} invalide. Valeurs possibles : {', '.join(allowed)}.")
    return {"age": age, "education_num": edu, "relationship": rel, "sex": sex, "hours": hours,
            "gain": gain, "loss": loss, "occupation": occupation, "occupation_text": occupation_text}


def _salary_args(d: dict) -> dict:
    try:
        role = str(d.get("role") or "") or salary.match_role(d.get("occupation_text") or "") or None
        years = None if d.get("years") in (None, "") else int(d["years"])
        if years is not None and not (0 <= years <= 60):
            raise _BadInput("years doit être entre 0 et 60.")
        level = d.get("level") or None
        level = None if level in (None, "auto") else level
        if level is not None and level not in salary.LEVELS:
            raise _BadInput("level doit valoir junior, confirme ou senior.")
        expected = None if d.get("expected_monthly") in (None, "") else float(d["expected_monthly"])
        if expected is not None and not (0 <= expected <= 1_000_000):
            raise _BadInput("expected_monthly doit être entre 0 et 1 000 000 USD.")
    except (ValueError, TypeError):
        raise _BadInput("Paramètres salariaux invalides (years, expected_monthly).")
    return {"role": role, "years": years, "level": level, "expected": expected}


def _income_error(exc):
    if exc.name and exc.name.startswith("catboost"):
        return JsonResponse({"error": "Le paquet « catboost » n'est pas installé : exécutez "
                                      "pip install -r requirements.txt puis relancez le serveur."}, status=503)
    raise exc


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def income_analyze(request):
    """Classification des revenus (CatBoost) + analyses RH : probabilité, facteurs, comparaisons, graphiques, leviers."""
    try:
        a = _income_args(_json_body(request))
    except _BadInput as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    try:
        result = income.analyze(a["age"], a["education_num"], a["relationship"], a["sex"], a["hours"],
                                a["gain"], a["loss"], a["occupation"], a["occupation_text"])
    except ModuleNotFoundError as exc:
        return _income_error(exc)
    except FileNotFoundError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    pred = result.get("prediction") or {}
    cid = candidates.save_candidate("income", a, pred.get("label"), pred.get("label_fr"), result)
    result["candidate_id"] = cid
    return JsonResponse(result)


def _occupation_args(d: dict) -> dict:
    try:
        age, edu = int(d["age"]), int(d["education_num"])
        workclass, marital, rel, race, sex = d["workclass"], d["marital_status"], d["relationship"], d["race"], d["sex"]
        hrs = int(d.get("hours_per_week") or 40)
        gain, loss = int(d.get("capital_gain") or 0), int(d.get("capital_loss") or 0)
        income_high = d.get("income_high")
        income_high = None if income_high in (None, "") else int(income_high)
    except (ValueError, KeyError, TypeError):
        raise _BadInput("Champs requis : age, education_num, workclass, marital_status, relationship, race, sex "
                        "(facultatifs : hours_per_week, capital_gain, capital_loss, income_high).")
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        raise _BadInput("age doit être entre 17 et 90, education_num entre 1 et 16.")
    if not (1 <= hrs <= 99):
        raise _BadInput("hours_per_week doit être entre 1 et 99.")
    if not (0 <= gain <= 99999 and 0 <= loss <= 99999):
        raise _BadInput("capital_gain et capital_loss doivent être entre 0 et 99999.")
    if income_high not in (None, 0, 1):
        raise _BadInput("income_high doit valoir 0, 1 ou être absent.")
    checks = ((workclass, [v for v, _ in occupation.WORKCLASS], "workclass"), (marital, ml.MARITAL, "marital_status"),
              (rel, ml.RELATIONSHIP, "relationship"), (race, [v for v, _ in occupation.RACE], "race"), (sex, ml.SEX, "sex"))
    for value, allowed, label in checks:
        if value not in allowed:
            raise _BadInput(f"{label} invalide. Valeurs possibles : {', '.join(allowed)}.")
    return {"age": age, "education_num": edu, "workclass": workclass, "marital_status": marital, "relationship": rel,
            "race": race, "sex": sex, "hours_per_week": hrs, "capital_gain": gain, "capital_loss": loss,
            "income_high": income_high}


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def occupation_analyze(request):
    """Prédiction de la catégorie de poste (CatBoost fourni par l'utilisateur, models/catboost_model.pkl)."""
    try:
        a = _occupation_args(_json_body(request))
    except _BadInput as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    try:
        result = occupation.analyze(a["age"], a["education_num"], a["workclass"], a["marital_status"], a["relationship"],
                                    a["race"], a["sex"], a["hours_per_week"], a["capital_gain"], a["capital_loss"],
                                    a["income_high"])
    except FileNotFoundError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    except Exception as exc:  # ne jamais laisser une erreur inattendue renvoyer une page HTML au front
        logging.getLogger(__name__).exception("Echec de la prédiction du métier (CatBoost)")
        return JsonResponse({"error": f"Erreur serveur pendant la prédiction : {exc}"}, status=500)
    pred = result.get("prediction") or {}
    cid = candidates.save_candidate("occupation", a, pred.get("code"), pred.get("label"), result)
    result["candidate_id"] = cid
    return JsonResponse(result)


@require_GET
def occupation_options(request):
    return JsonResponse(occupation.options())


def _hours_args(d: dict) -> dict:
    try:
        age, edu = int(d["age"]), int(d["education_num"])
        marital, rel, sex = d["marital_status"], d["relationship"], d["sex"]
        occupation, occupation_text = str(d.get("occupation") or ""), str(d.get("occupation_text") or "")
        income = d.get("income_sup50k")
        income = None if income in (None, "") else int(income)
    except (ValueError, KeyError, TypeError):
        raise _BadInput("Champs requis : age, education_num, marital_status, relationship, sex "
                        "(facultatifs : occupation, occupation_text, income_sup50k).")
    if not (17 <= age <= 90 and 1 <= edu <= 16):
        raise _BadInput("age doit être entre 17 et 90, education_num entre 1 et 16.")
    if income not in (None, 0, 1):
        raise _BadInput("income_sup50k doit valoir 0, 1 ou être absent.")
    for value, allowed, label in ((marital, hours.MARITAL, "marital_status"), (rel, hours.RELATIONSHIP, "relationship"),
                                  (sex, ml.SEX, "sex")):
        if value not in allowed:
            raise _BadInput(f"{label} invalide. Valeurs possibles : {', '.join(allowed)}.")
    return {"age": age, "education_num": edu, "marital_status": marital, "relationship": rel, "sex": sex,
            "occupation": occupation, "occupation_text": occupation_text, "income_high": income}


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def hours_analyze(request):
    """Régression des heures de travail (XGBoost) + analyses RH : heures prédites, facteurs, comparaisons, leviers."""
    try:
        a = _hours_args(_json_body(request))
    except _BadInput as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    try:
        result = hours.analyze(a["age"], a["education_num"], a["marital_status"], a["relationship"], a["sex"],
                               a["occupation"], a["occupation_text"], a["income_high"])
        pred = result.get("prediction") or {}
        cid = candidates.save_candidate("hours", a, pred.get("hours"), pred.get("category_label"), result)
        result["candidate_id"] = cid
        return JsonResponse(result)
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("xgboost"):
            return JsonResponse({"error": "Le paquet « xgboost » n'est pas installé : exécutez "
                                          "pip install -r requirements.txt puis relancez le serveur."}, status=503)
        raise
    except FileNotFoundError as exc:
        return JsonResponse({"error": str(exc)}, status=503)


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def salary_recommend(request):
    """Recommandation salariale en USD à partir du référentiel BLS (aucun montant inventé)."""
    try:
        d = _json_body(request)
        s = _salary_args(d)
    except _BadInput as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(salary.recommend(s["role"], s["years"], s["level"], s["expected"]))


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def income_report(request):
    """Rapport PDF : analyse du profil + recommandation salariale + comparaison éventuelle."""
    try:
        d = _json_body(request)
        a = _income_args(d)
        s = _salary_args(d)
    except _BadInput as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    try:
        analysis = income.analyze(a["age"], a["education_num"], a["relationship"], a["sex"], a["hours"],
                                  a["gain"], a["loss"], a["occupation"], a["occupation_text"])
    except ModuleNotFoundError as exc:
        return _income_error(exc)
    except FileNotFoundError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    rec = salary.recommend(s["role"], s["years"], s["level"], s["expected"])
    candidate = str(d.get("candidate_name") or "Candidat")[:120]
    pdf = report.build_pdf(analysis, rec, candidate, a["occupation_text"] or a["occupation"])
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="rapport-candidat-profilpro.pdf"'
    return response


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def cv_analyze(request):
    """Reçoit un CV PDF (multipart, champ « file ») et renvoie les informations extraites (IA ou règles)."""
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"error": "Aucun fichier reçu (champ « file »)."}, status=400)
    if f.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "Fichier trop volumineux (10 Mo maximum)."}, status=400)
    data = f.read()
    if not data.startswith(b"%PDF"):
        return JsonResponse({"error": "Ce fichier n'est pas un PDF valide."}, status=400)
    return JsonResponse(cv.analyze(data))


# ---------- Données réelles lues dans MySQL (table adult_person) ----------
from django.db.models import Avg, Count, Q  # noqa: E402

from .models import Person  # noqa: E402

NIVEAUX = [("Licence", ["Bachelors"]), ("Master / Doctorat", ["Masters", "Doctorate", "Prof-school"]),
           ("Bac / études sup. partielles", ["HS-grad", "Some-college"]),
           ("Autres", None)]


@require_GET
def stats(request):
    qs = Person.objects.all()
    total = qs.count()
    if total == 0:
        return JsonResponse({"total": 0, "message": "Base vide : lancez python manage.py import_adult adult.test"})
    niveaux, deja = [], []
    for label, vals in NIVEAUX:
        n = qs.filter(education__in=vals).count() if vals else qs.exclude(education__in=deja).count()
        deja += vals or []
        niveaux.append({"label": label, "count": n, "pct": round(100 * n / total, 1)})
    metiers = (qs.exclude(occupation="").values("occupation").annotate(n=Count("id")).order_by("-n")[:8])
    return JsonResponse({
        "total": total,
        "avg_hours": round(qs.aggregate(h=Avg("hours_per_week"))["h"], 1),
        "avg_age": round(qs.aggregate(a=Avg("age"))["a"], 1),
        "high_income_pct": round(100 * qs.filter(income=">50K").count() / total, 1),
        "education": niveaux,
        "occupations": [{"label": m["occupation"], "count": m["n"]} for m in metiers],
    })


@require_GET
def people(request):
    page = max(int(request.GET.get("page", 1) or 1), 1)
    size = min(max(int(request.GET.get("size", 10) or 10), 1), 100)
    q = request.GET.get("q", "").strip()
    qs = Person.objects.all().order_by("-id")
    if q:
        cond = Q(occupation__icontains=q) | Q(education__icontains=q) | Q(workclass__icontains=q)
        if q.upper().startswith("PRF-") and q[4:].isdigit():
            cond |= Q(id=int(q[4:]))
        qs = qs.filter(cond)
    total = qs.count()
    rows = qs[(page - 1) * size: page * size]
    return JsonResponse({"total": total, "page": page, "size": size, "results": [
        {"id": f"PRF-{p.id}", "age": p.age, "education": p.education, "workclass": p.workclass or "—",
         "occupation": p.occupation or "—", "hours": p.hours_per_week, "income": p.income} for p in rows]})


# ---------- Candidats sauvegardés (prédiction + résultat réel saisi plus tard) ----------
from .models import Candidate  # noqa: E402


@require_GET
def candidates_list(request):
    """GET /api/candidates/?kind=education&page=1&size=20 — liste des candidats analysés."""
    page = max(int(request.GET.get("page", 1) or 1), 1)
    size = min(max(int(request.GET.get("size", 20) or 20), 1), 100)
    qs = Candidate.objects.all()
    kind = request.GET.get("kind")
    if kind:
        qs = qs.filter(kind=kind)
    total = qs.count()
    rows = qs[(page - 1) * size: page * size]
    return JsonResponse({"total": total, "page": page, "size": size, "results": [c.to_dict() for c in rows]})


@csrf_exempt  # même remarque que predict : à protéger (CSRF/auth) avant toute mise en production
@require_POST
def candidate_outcome(request, candidate_id):
    """PATCH/POST /api/candidates/<id>/outcome/ {"actual_code": "...", "actual_label": "...", "actual_note": "..."}
    Saisie, par le RH, du résultat réellement observé pour ce candidat (une fois connu)."""
    try:
        d = json.loads(request.body or b"{}")
        actual_code = d["actual_code"]
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Champ requis : actual_code (facultatifs : actual_label, actual_note)."}, status=400)
    try:
        c = candidates.set_outcome(candidate_id, actual_code, d.get("actual_label", ""), d.get("actual_note", ""))
    except Candidate.DoesNotExist:
        return JsonResponse({"error": "Candidat introuvable."}, status=404)
    return JsonResponse(c.to_dict())


@require_GET
def candidates_compare(request):
    """GET /api/candidates/compare/?kind=income — taux de réussite prédit vs réel."""
    return JsonResponse(candidates.compare_stats(request.GET.get("kind")))
