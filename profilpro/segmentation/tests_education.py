"""Tests de la prédiction du niveau d'éducation (modèle xgboost_education.pkl).

Lancer : python manage.py test segmentation.tests_education
Les tests d'inférence exigent le paquet `xgboost` ; ils sont ignorés s'il n'est pas installé.
"""
import json
import unittest

from django.test import SimpleTestCase

from . import education

try:
    import xgboost  # noqa: F401
    HAS_XGB = True
except ImportError:  # pragma: no cover
    HAS_XGB = False

VALID = {"age": 38, "sex": "Male", "race": "White", "native_country": "United-States", "marital_status": "Married-civ-spouse",
         "relationship": "Husband", "workclass": "Private", "occupation": "Exec-managerial", "hours_per_week": 45, "income": ">50K"}


class EducationInput(SimpleTestCase):
    def post(self, payload, raw=None):
        return self.client.post("/api/education/predict/", raw if raw is not None else json.dumps(payload), content_type="application/json")

    def test_options_cover_every_model_column(self):
        opts = education.options()
        self.assertEqual(len(opts["native_country"]), 41)
        self.assertEqual(len(opts["occupation"]), 14)
        self.assertEqual([o["value"] for o in opts["sex"]], ["Female", "Male"])

    def test_missing_fields_are_reported_per_field(self):
        r = self.post({"age": 30})
        self.assertEqual(r.status_code, 400)
        fields = r.json()["fields"]
        for key in ("sex", "race", "native_country", "marital_status", "relationship", "workclass", "occupation", "hours_per_week", "income"):
            self.assertIn(key, fields)
        self.assertNotIn("age", fields)

    def test_out_of_range_and_unknown_values(self):
        for bad in ({"age": 10}, {"age": 200}, {"age": "abc"}, {"age": 30.5}, {"hours_per_week": 0}, {"hours_per_week": 150},
                    {"sex": "Other"}, {"native_country": "Atlantis"}, {"occupation": "?"}, {"income": "yes"}):
            r = self.post({**VALID, **bad})
            self.assertEqual(r.status_code, 400, bad)

    def test_invalid_json_and_method(self):
        self.assertEqual(self.post(None, raw="{nope").status_code, 400)
        self.assertEqual(self.post(None, raw="[1,2]").status_code, 400)
        self.assertEqual(self.client.get("/api/education/predict/").status_code, 405)

    def test_frame_matches_training_layout(self):
        """Ordre des colonnes, types et catégories de référence (indicateurs tous à 0)."""
        feats = ["age", "sex", "hours-per-week", "workclass_Private", "income_>50K", "occupation_Sales", "native-country_Canada"]
        df = education.build_frame(education._clean({**VALID, "occupation": "Adm-clerical", "native_country": "Cambodia"}), feats)
        self.assertEqual(list(df.columns), feats)
        row = df.iloc[0]
        self.assertEqual((row["age"], row["sex"], row["hours-per-week"]), (38, 1, 45.0))
        self.assertTrue(row["workclass_Private"] and row["income_>50K"])
        self.assertFalse(row["occupation_Sales"] or row["native-country_Canada"])  # références : Adm-clerical, Cambodia


@unittest.skipUnless(HAS_XGB, "xgboost non installé")
class EducationInference(SimpleTestCase):
    def test_valid_prediction_has_consistent_probabilities(self):
        r = self.client.post("/api/education/predict/", json.dumps(VALID), content_type="application/json")
        self.assertEqual(r.status_code, 200, r.content)
        d = r.json()
        self.assertAlmostEqual(sum(p["probability"] for p in d["probabilities"]), 100, delta=0.5)
        top = max(d["probabilities"], key=lambda p: p["probability"])
        self.assertEqual(top["code"], d["prediction"]["code"])
        self.assertEqual(len(d["summary"]), 10)

    def test_repeated_predictions_use_same_loaded_model(self):
        self.assertIs(education.get_artifact(), education.get_artifact())
        a = education.predict(VALID)
        b = education.predict(VALID)
        self.assertEqual(a["probabilities"], b["probabilities"])
