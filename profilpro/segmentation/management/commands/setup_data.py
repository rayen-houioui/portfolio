"""Prépare tout en une commande : migrations + import des données si la table est vide (idempotent)."""
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from segmentation.models import Person


class Command(BaseCommand):
    help = "migrate + import de data/adult.test (et adult.data s'il existe) si la base est vide."

    def handle(self, *args, **opts):
        call_command("migrate", interactive=False, verbosity=0)
        if Person.objects.exists():
            self.stdout.write(f"Base déjà prête : {Person.objects.count()} lignes.")
            return
        files = [str(Path(settings.BASE_DIR) / "data" / n) for n in ("adult.data", "adult.test")
                 if (Path(settings.BASE_DIR) / "data" / n).exists()]
        if not files:
            self.stdout.write("Aucun fichier dans data/ : l'analyse lira la base une fois importée.")
            return
        call_command("import_adult", *files)
