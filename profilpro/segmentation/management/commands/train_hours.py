from django.core.management.base import BaseCommand

from segmentation import hours


class Command(BaseCommand):
    help = "(Ré)entraîne le modèle XGBoost de régression des heures et écrit models/xgboost_hours.pkl."

    def handle(self, *args, **opts):
        art = hours.retrain()
        m = art["metrics"]
        self.stdout.write(self.style.SUCCESS(
            f"Modèle enregistré — MAE {m['mae']} h · RMSE {m['rmse']} h · R² {m['r2']} "
            f"(référence « toujours la médiane » : MAE {m['baseline_mae']} h) · {m['n_train']} lignes d'entraînement."))
