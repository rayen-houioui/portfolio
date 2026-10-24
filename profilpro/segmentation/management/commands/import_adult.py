"""Importe adult.data et/ou adult.test dans la base (MySQL XAMPP).

    python manage.py import_adult adult.test adult.data --reset
"""
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from segmentation.models import Person

COLS = ["age", "workclass", "fnlwgt", "education", "education_num", "marital_status", "occupation",
        "relationship", "race", "sex", "capital_gain", "capital_loss", "hours_per_week",
        "native_country", "income"]


def lire(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, header=None, names=COLS, skipinitialspace=True, comment="|",
                     skip_blank_lines=True, na_values=["?"], keep_default_na=False)
    df = df.dropna(subset=["age"])                       # ligne de commentaire "|1x3 Cross validator"
    df["income"] = df["income"].str.rstrip(".")           # adult.test : "<=50K." -> "<=50K"
    for c in ("workclass", "occupation", "native_country"):
        df[c] = df[c].fillna("")                          # "?" -> valeur vide
    df["source"] = "test" if path.name.endswith(".test") else "train"
    return df


class Command(BaseCommand):
    help = "Importe adult.data / adult.test dans la table adult_person (relancer remplace, ne double pas)."

    def add_arguments(self, parser):
        parser.add_argument("fichiers", nargs="+")
        parser.add_argument("--reset", action="store_true", help="vide la table avant l'import")

    def handle(self, *args, **opts):
        if opts["reset"]:
            Person.objects.all().delete()
        for f in opts["fichiers"]:
            p = Path(f)
            if not p.exists():
                raise CommandError(f"Fichier introuvable : {p}")
            df = lire(p)
            # Idempotent : relancer l'import REMPLACE les lignes de la même source (plus de doublons)
            Person.objects.filter(source=df["source"].iloc[0]).delete()
            Person.objects.bulk_create([Person(**r) for r in df.to_dict("records")], batch_size=2000)
            self.stdout.write(self.style.SUCCESS(f"{p.name} : {len(df)} lignes importées"))
        self.stdout.write(f"Total en base : {Person.objects.count()}")
