from django.core.management.base import BaseCommand

from segmentation import income


class Command(BaseCommand):
    help = "Vérifie que le modèle CatBoost (models/catboost_adult.pkl) se charge et prédit."

    def handle(self, *args, **opts):
        art = income.get_artifact()
        self.stdout.write(f"Modèle chargé — variables : {art['features']} (catboost {art.get('catboost_version')})")
        r = income.analyze(age=44, education_num=13, relationship="Husband", sex="Male", hours_per_week=45,
                           occupation="Exec-managerial")
        p = r["prediction"]
        self.stdout.write(self.style.SUCCESS(f"Prédiction : {p['label_fr']} — {p['proba_high']} % ({p['confidence']})"))
        self.stdout.write(f"Facteurs SHAP : {len(r['factors'])} · leviers : {len(r['levers'])} · population : {r['overall']['n']}")
