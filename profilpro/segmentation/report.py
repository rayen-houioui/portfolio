"""Rapport PDF de l'analyse candidat (analyse du profil + recommandation salariale en USD)."""
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#0f172a")
BLUE = colors.HexColor("#1e3a8a")
GREY = colors.HexColor("#64748b")
LINE = colors.HexColor("#cbd5e1")
TINT = colors.HexColor("#f1f5f9")


def usd(value) -> str:
    return f"${value:,.0f}"


def build_pdf(analysis: dict, rec: dict, candidate: str, occupation: str) -> bytes:
    ss = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=ss["Title"], fontSize=18, leading=22, alignment=0, textColor=INK)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, spaceBefore=12, spaceAfter=6, textColor=BLUE)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5, textColor=GREY)

    def p(text, style=body):
        return Paragraph(escape(str(text)), style)

    def grid(rows, widths):
        t = Table([[p(a), p(b)] for a, b in rows], colWidths=widths)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 0), (0, -1), TINT),
                               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        return t

    pred = analysis["prediction"]
    high = pred["label"] == ">50K"
    story = [
        p("Rapport d'analyse candidat", title),
        p(f"ProfilPro RH · généré le {datetime.now():%d/%m/%Y %H:%M}", small),
        Spacer(1, 10),
        grid([("Candidat", candidate), ("Métier déclaré", occupation or "Non renseigné")], [4 * cm, 13 * cm]),
        p("1. Analyse du profil", h2),
        grid([
            ("Catégorie prédite", "Revenu supérieur à 50 000 $ / an" if high else "50 000 $ / an ou moins"),
            ("Probabilité estimée", f"{pred['proba_high']:.1f} % de revenu élevé"),
            ("Fiabilité du modèle", pred["confidence"]),
        ], [4 * cm, 13 * cm]),
    ]
    if abs(pred["proba_high"] - 50) <= 10:
        story.append(Spacer(1, 6))
        story.append(p("Résultat incertain : les deux catégories sont presque équiprobables. "
                       "Une analyse complémentaire est recommandée.", body))
    factors = [f for f in analysis.get("factors", []) if not f["sensitive"]][:4]
    if factors:
        story.append(Spacer(1, 6))
        story.append(p("Principaux facteurs :", body))
        for f in factors:
            effect = "favorable à un revenu élevé" if f["direction"] == "up" else "favorable à un revenu standard"
            story.append(p(f"• {f['label']} : {f['value']} ({effect})", body))

    story.append(p("2. Recommandation salariale (USD)", h2))
    if not rec.get("available"):
        story.append(p(rec.get("message") or "Aucune donnée salariale disponible.", body))
    else:
        m, a, ann = rec["monthly"], rec["annual"], rec["annual"]
        story.append(grid([
            ("Métier de référence", rec["role"]["label"]),
            ("Niveau retenu", f"{rec['level_label']}" + ("" if rec["years"] is None else f" ({rec['years']} ans d'expérience)")),
            ("Fourchette mensuelle", f"{usd(m['min'])} – {usd(m['max'])}"),
            ("Salaire conseillé (mensuel)", usd(m["advised"])),
            ("Estimation annuelle", usd(a["advised"])),
            ("Marché (annuel, 10e / médiane / 90e)",
             f"{usd(a['market_p10'])} / {usd(a['market_median'])} / {usd(a['market_p90'])}"),
        ], [6 * cm, 11 * cm]))
        story.append(p("3. Justification", h2))
        for line in rec["justification"]:
            story.append(p(f"• {line}", body))
        if rec.get("comparison"):
            c = rec["comparison"]
            diff = f"{'+' if c['diff_vs_advised'] >= 0 else '−'}{usd(abs(c['diff_vs_advised']))}"
            story.append(p("4. Comparaison salariale", h2))
            story.append(grid([
                ("Salaire proposé (mensuel)", usd(c["expected_monthly"])),
                ("Position", c["text"]),
                ("Écart vs salaire conseillé", f"{diff} par mois" + ("" if c["diff_pct"] is None else f" ({c['diff_pct']:+.1f} %)")),
            ], [6 * cm, 11 * cm]))

    story.append(p("5. Points de vigilance", h2))
    for w in analysis.get("warnings", []):
        story.append(p(f"• {w}", body))
    if rec.get("source"):
        story.append(Spacer(1, 6))
        story.append(p(f"Source salariale : {rec['source']}, {rec['reference_date']}. Montants en dollars américains (USD).", small))

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                      bottomMargin=1.8 * cm, title="Rapport d'analyse candidat", author="ProfilPro RH").build(story)
    return buf.getvalue()
