"""Analyse d'un CV (PDF) : extraction des informations utiles aux services d'analyse.

Fournisseurs, par ordre de priorité (le premier configuré est utilisé) :
1. Google Gemini (GRATUIT, sans carte bancaire) : variable GEMINI_API_KEY (clé sur https://aistudio.google.com/apikey).
2. Claude (Anthropic, payant) : variable ANTHROPIC_API_KEY (+ `pip install anthropic`).
3. Sans clé, ou si l'API échoue : extraction locale simplifiée (pypdf + expressions régulières).

Éthique RH : le sexe, la situation matrimoniale et le rôle familial ne sont JAMAIS déduits (ni du prénom, ni d'une photo) ;
ils ne sont renseignés que s'ils sont écrits explicitement dans le CV, sinon ils restent vides pour saisie par le RH.
Confidentialité : avec Gemini, on envoie par défaut le TEXTE du CV après suppression des e-mails, téléphones et liens ;
le PDF brut n'est envoyé que s'il est scanné (aucun texte extractible).
"""
import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

EDUCATION_NUM = {
    "Preschool": 1, "1st-4th": 2, "5th-6th": 3, "7th-8th": 4, "9th": 5, "10th": 6, "11th": 7, "12th": 8,
    "HS-grad": 9, "Some-college": 10, "Assoc-voc": 11, "Assoc-acdm": 12, "Bachelors": 13, "Masters": 14,
    "Prof-school": 15, "Doctorate": 16,
}
MARITAL = ["Divorced", "Married-AF-spouse", "Married-civ-spouse", "Married-spouse-absent", "Never-married", "Separated", "Widowed"]
RELATIONSHIP = ["Husband", "Not-in-family", "Other-relative", "Own-child", "Unmarried", "Wife"]
SEX = ["Female", "Male"]

SYSTEM = (
    "Tu es un assistant RH expert en lecture de CV. Tu extrais uniquement des faits présents dans le document, "
    "sans rien inventer. Tu réponds exclusivement par un objet JSON valide, sans texte autour."
)

PROMPT = """Date du jour : {today}.
Analyse ce CV et renvoie un objet JSON avec exactement ces clés :
- "formation" : diplôme le plus élevé, en français (ex. "Master en informatique"), ou "" si absent.
- "education_category" : catégorie du dataset Adult la plus proche du diplôme le plus élevé, parmi :
  {cats}. Équivalences : bac = "HS-grad" ; bac+1/études supérieures non diplômantes = "Some-college" ;
  BTS/DUT/BUT/bac+2 professionnel = "Assoc-voc", bac+2 général = "Assoc-acdm" ; licence/bac+3 = "Bachelors" ;
  master/ingénieur/bac+5 = "Masters" ; doctorat = "Doctorate" ; école professionnelle (médecine, droit, pharmacie) = "Prof-school".
  Mets "" si aucun diplôme n'est identifiable.
- "occupation" : métier ou domaine principal (ex. "Développement logiciel"), ou "".
- "experience_years" : nombre d'années d'expérience professionnelle cumulées (entier), ou null.
- "skills" : liste de 3 à 10 compétences clés (chaînes courtes).
- "age" : âge en années, UNIQUEMENT s'il est écrit ou calculable depuis une date de naissance explicite, sinon null.
- "marital_status" : parmi {marital} UNIQUEMENT si explicitement écrit dans le CV, sinon null.
- "sex" : "Female" ou "Male" UNIQUEMENT si explicitement écrit (jamais déduit du prénom, de la photo ou de la civilité), sinon null.
- "relationship" : toujours null (non déductible d'un CV).
- "notes" : une phrase courte signalant toute ambiguïté ou information manquante importante.
Réponds uniquement par le JSON."""


# --------------------------------------------------------------------------- utilitaires
def extract_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:8])
    except Exception:
        return ""


def _years_label(n):
    if n is None:
        return ""
    if n < 1:
        return "Moins d'1 an"
    if n <= 2:
        return "1 à 2 ans"
    if n <= 5:
        return "3 à 5 ans"
    if n <= 10:
        return "6 à 10 ans"
    return "Plus de 10 ans"


def _normalize(raw: dict, source: str, warning: str = "", provider: str = "") -> dict:
    """Valide et nettoie la réponse (IA ou règles) pour le front."""
    cat = raw.get("education_category") or ""
    cat = cat if cat in EDUCATION_NUM else ""
    years = raw.get("experience_years")
    years = int(years) if isinstance(years, (int, float)) and 0 <= years <= 60 else None
    age = raw.get("age")
    age = int(age) if isinstance(age, (int, float)) and 14 <= age <= 100 else None
    skills = raw.get("skills") or []
    if isinstance(skills, str):
        skills = [x.strip() for x in re.split(r"[,;•\n]", skills) if x.strip()]
    skills = [str(x).strip()[:40] for x in skills if str(x).strip()][:10]
    pick = lambda v, allowed: v if v in allowed else None  # noqa: E731
    return {
        "source": source,  # "ia" ou "simplifiee"
        "provider": provider or ("gemini" if source == "ia" else "local"),
        "warning": warning,
        "formation": str(raw.get("formation") or "")[:120],
        "education_category": cat,
        "education_num": EDUCATION_NUM.get(cat),
        "occupation": str(raw.get("occupation") or "")[:120],
        "experience": _years_label(years),
        "experience_years": years,
        "skills": skills,
        "age": age,
        "marital_status": pick(raw.get("marital_status"), MARITAL),
        "sex": pick(raw.get("sex"), SEX),
        "relationship": None,
        "notes": str(raw.get("notes") or "")[:300],
    }


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("Réponse IA sans JSON.")
    return json.loads(text[start:end + 1])


# --------------------------------------------------------------------------- IA (API Anthropic)
def analyze_with_claude(pdf_bytes: bytes) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=90.0, max_retries=2)
    message = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                            "data": base64.b64encode(pdf_bytes).decode()}},
            {"type": "text", "text": PROMPT.format(today=date.today().isoformat(), cats=", ".join(EDUCATION_NUM),
                                                   marital=", ".join(MARITAL))},
        ]}],
    )
    text = "".join(b.text for b in message.content if getattr(b, "type", "") == "text")
    return _normalize(_parse_json(text), "ia", provider="claude")


# --------------------------------------------------------------------------- IA gratuite : Google Gemini
_GEMINI_BASE = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
_model_cache: list = []


def redact(text: str) -> str:
    """Supprime les identifiants directs (e-mail, téléphone, liens) avant envoi à un service tiers."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"https?://\S+|www\.\S+|linkedin\.com/\S+", "[lien]", text)
    text = re.sub(r"(?<!\d)(?:\+?\d[\s.()-]?){9,14}\d(?!\d)", "[tel]", text)
    return text


def _gemini_call(model: str, key: str, parts: list) -> str:
    body = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }).encode()
    req = urllib.request.Request(f"{_GEMINI_BASE}/models/{model}:generateContent", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    cands = data.get("candidates") or []
    if not cands:
        raise ValueError(f"Réponse vide ({data.get('promptFeedback', '')})")
    return "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))


def _gemini_models(key: str) -> list:
    """Modèles « flash » disponibles pour cette clé (noms qui changent souvent : on les découvre), Lite en premier."""
    req = urllib.request.Request(f"{_GEMINI_BASE}/models?pageSize=200", headers={"x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        items = json.loads(resp.read().decode()).get("models", [])
    names = [m["name"].split("/")[-1] for m in items if "generateContent" in m.get("supportedGenerationMethods", [])]
    bad = ("image", "tts", "live", "audio", "embed", "vision", "robotics", "computer", "learnlm", "gemma")
    flash = [n for n in names if "flash" in n and not any(b in n for b in bad)]
    return sorted(flash, key=lambda n: (0 if "lite" in n else 1, 0 if "latest" in n else 1, n))


def analyze_with_gemini(pdf_bytes: bytes) -> dict:
    key = os.environ["GEMINI_API_KEY"]
    text = extract_text(pdf_bytes)
    if len(text.strip()) > 200 and os.getenv("GEMINI_SEND_PDF", "0") != "1":
        content = [{"text": "CV (texte, coordonnées supprimées) :\n" + redact(text)[:20000]}]
    else:  # PDF scanné : on envoie le document pour que l'IA le lise visuellement
        content = [{"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode()}}]
    content.append({"text": PROMPT.format(today=date.today().isoformat(), cats=", ".join(EDUCATION_NUM),
                                          marital=", ".join(MARITAL))})
    candidates = ([os.environ["GEMINI_MODEL"]] if os.getenv("GEMINI_MODEL") else []) + list(_model_cache)
    tried, last = set(), None
    for attempt in range(2):  # 1) modèle configuré / déjà trouvé  2) découverte automatique
        for model in candidates:
            if model in tried:
                continue
            tried.add(model)
            try:
                out = _gemini_call(model, key, content)
                if model not in _model_cache:
                    _model_cache.insert(0, model)
                return _normalize(_parse_json(out), "ia")
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code in (400, 401, 403):  # clé invalide / non autorisée : inutile d'essayer d'autres modèles
                    raise
                continue  # 404 (modèle retiré) ou 429 (quota de ce modèle) : modèle suivant
        if attempt == 0:
            candidates = _gemini_models(key)[:4]
    raise last or RuntimeError("Aucun modèle Gemini disponible.")


# --------------------------------------------------------------------------- repli local (sans clé API)
_DEGREES = [  # du plus élevé au plus bas
    ("Doctorate", r"doctorat|ph\.?d"), ("Masters", r"master|ing[ée]nieur|bac\s*\+\s*5|\bmba\b|\bm[12]\b|\bmsc\b"),
    ("Bachelors", r"licence|bachelor|bac\s*\+\s*3|\bbut\b|\bl3\b"), ("Assoc-voc", r"\bbts\b|\bdut\b|bac\s*\+\s*2|\bdeug\b"),
    ("Some-college", r"bac\s*\+\s*1|classe pr[ée]paratoire"), ("HS-grad", r"baccalaur[ée]at|\bbac\b"),
]
_JOBS = ["développeur", "développeuse", "ingénieur", "ingénieure", "data scientist", "data analyst", "analyste", "comptable",
         "technicien", "chef de projet", "consultant", "consultante", "commercial", "responsable", "gestionnaire",
         "infirmier", "infirmière", "enseignant", "professeur", "assistant", "assistante", "designer", "architecte",
         "juriste", "avocat", "médecin", "chargé", "chargée", "directeur", "directrice", "manager", "administrateur"]


def analyze_simple(text: str) -> dict:
    low = text.lower()
    cat = next((c for c, rx in _DEGREES if re.search(rx, low)), "")
    formation = ""
    if cat:
        rx = dict(_DEGREES)[cat]
        for line in text.splitlines():
            if re.search(rx, line.lower()):
                formation = re.sub(r"^\s*(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|\w+)\s*[:\-–]?\s*", "", line).strip()
                break
    occupation = ""
    for line in text.splitlines()[:25]:
        if any(j in line.lower() for j in _JOBS):
            occupation = line.strip()
            break
    years = None
    m = [int(x) for x in re.findall(r"(\d{1,2})\s*(?:\+\s*)?(?:ans|années|years)\s*d['e ]\s*(?:exp[ée]rience|experience)", low)]
    if m:
        years = max(m)
    else:  # somme des périodes « 2019 - 2022 », en ignorant les lignes de formation
        edu_rx = "|".join(rx for _, rx in _DEGREES) + r"|universit|[ée]cole|lyc[ée]e|\biut\b|facult|dipl[oô]m|formation|[ée]tudes"
        total = 0
        for line in text.lower().splitlines():
            if re.search(edu_rx, line):
                continue
            for a, b in re.findall(r"((?:19|20)\d{2})\s*[-–à]\s*((?:19|20)\d{2}|pr[ée]sent|aujourd)", line):
                end = int(b) if b[:2] in ("19", "20") else date.today().year
                total += max(0, min(end - int(a), 40))
        years = min(total, 45) if total else None
    skills = []
    sec = re.search(r"(?:comp[ée]tences|skills)[^\n]*\n((?:.+\n?){1,8})", text, flags=re.I)
    if sec:
        skills = [x.strip(" -•*·") for x in re.split(r"[,;•·|\n]", sec.group(1)) if 1 < len(x.strip(" -•*·")) < 40]
    age = None
    mb = re.search(r"n[ée]e?\s*(?:le)?\s*:?\s*(\d{1,2})[/.\- ](\d{1,2})[/.\- ]((?:19|20)\d{2})", low)
    if mb:
        age = date.today().year - int(mb.group(3))
    else:
        ma = re.search(r"[âa]ge\s*:?\s*(\d{2})\s*ans|\b(\d{2})\s*ans\b(?!\s*d['e])", low)
        if ma:
            age = int(ma.group(1) or ma.group(2))
    notes = "Extraction locale simplifiée (sans IA) : vérifiez chaque champ." if text.strip() else \
        "Aucun texte lisible dans ce PDF (document scanné ?). Renseignez les champs à la main ou activez l'IA."
    return _normalize({"formation": formation, "education_category": cat, "occupation": occupation,
                       "experience_years": years, "skills": skills, "age": age, "notes": notes}, "simplifiee")


# --------------------------------------------------------------------------- point d'entrée
def analyze(pdf_bytes: bytes) -> dict:
    provider = ("gemini", analyze_with_gemini) if os.getenv("GEMINI_API_KEY") else \
               ("claude", analyze_with_claude) if os.getenv("ANTHROPIC_API_KEY") else None
    if provider:
        try:
            return provider[1](pdf_bytes)
        except Exception as exc:  # clé invalide, quota gratuit atteint, réseau… -> repli local, avec avertissement visible
            reason = {429: "quota gratuit atteint, réessayez plus tard", 401: "clé refusée", 403: "clé refusée", 400: "clé ou requête refusée"}
            why = reason.get(getattr(exc, "code", None), type(exc).__name__)
            res = analyze_simple(extract_text(pdf_bytes))
            res["warning"] = f"L'IA ({provider[0]}) n'a pas pu analyser ce CV ({why}) : extraction locale simplifiée utilisée."
            return res
    res = analyze_simple(extract_text(pdf_bytes))
    res["warning"] = "Aucune clé d'API configurée : extraction locale simplifiée (voir le README pour activer l'IA gratuite Gemini)."
    return res
