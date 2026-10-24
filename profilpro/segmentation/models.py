from django.db import models


class Person(models.Model):
    """Une ligne du jeu de données Adult / Census Income."""
    age = models.PositiveSmallIntegerField()
    workclass = models.CharField(max_length=30, blank=True)
    fnlwgt = models.IntegerField()
    education = models.CharField(max_length=20)
    education_num = models.PositiveSmallIntegerField()
    marital_status = models.CharField(max_length=30)
    occupation = models.CharField(max_length=30, blank=True)
    relationship = models.CharField(max_length=20)
    race = models.CharField(max_length=30)
    sex = models.CharField(max_length=10)
    capital_gain = models.IntegerField()
    capital_loss = models.IntegerField()
    hours_per_week = models.PositiveSmallIntegerField()
    native_country = models.CharField(max_length=40, blank=True)
    income = models.CharField(max_length=5)          # "<=50K" ou ">50K"
    source = models.CharField(max_length=10)         # "train" (adult.data) ou "test" (adult.test)

    class Meta:
        db_table = "adult_person"
        ordering = ["id"]


class Candidate(models.Model):
    """Un candidat passé par une des pages d'analyse (segmentation, éducation, revenu, heures).

    `predicted_*` est rempli automatiquement juste après la prédiction.
    `actual_*` reste vide tant que personne ne l'a renseigné : c'est le résultat réel
    (constaté plus tard, ex. le candidat est effectivement embauché / son vrai niveau
    d'études / son vrai salaire) qu'un RH saisit via PATCH /api/candidates/<id>/outcome/.
    """

    KIND_CHOICES = [
        ("segmentation", "Segmentation familiale"),
        ("professional", "Segmentation professionnelle"),
        ("education", "Niveau d'éducation"),
        ("income", "Classe de revenu"),
        ("hours", "Heures de travail"),
        ("occupation", "Catégorie de poste"),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    name = models.CharField(max_length=120, blank=True)        # nom/repère du candidat (facultatif)
    inputs = models.JSONField(default=dict)                    # ce qui a été envoyé au modèle

    predicted_code = models.CharField(max_length=60, blank=True)    # ex: "Higher_Education", ">50K", "2"
    predicted_label = models.CharField(max_length=200, blank=True)  # libellé lisible
    predicted = models.JSONField(default=dict)                 # réponse complète renvoyée par le modèle

    actual_code = models.CharField(max_length=60, blank=True)       # valeur réellement observée (saisie manuelle)
    actual_label = models.CharField(max_length=200, blank=True)
    actual_note = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"
        ordering = ["-created_at"]

    @property
    def has_outcome(self) -> bool:
        return bool(self.actual_code)

    @property
    def is_correct(self):
        """None tant que le résultat réel n'est pas connu, sinon True/False."""
        if not self.has_outcome:
            return None
        return self.actual_code == self.predicted_code

    def to_dict(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "name": self.name, "inputs": self.inputs,
            "predicted_code": self.predicted_code, "predicted_label": self.predicted_label,
            "actual_code": self.actual_code, "actual_label": self.actual_label, "actual_note": self.actual_note,
            "is_correct": self.is_correct,
            "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat(),
        }
