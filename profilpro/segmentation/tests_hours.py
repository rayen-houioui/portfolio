"""Tests de la régression des heures de travail (XGBoost).

Lancer : python manage.py test segmentation.tests_hours
(le premier appel entraîne le modèle si models/xgboost_hours.pkl est absent)
"""
import json

from django.test import SimpleTestCase

from . import hours


class HoursRegression(SimpleTestCase):
    def test_prediction_and_range(self):
        r = hours.analyze(44, 13, "Married-civ-spouse", "Husband", "Male", occupation="Exec-managerial", income_high=1)
        p = r["prediction"]
        self.assertTrue(1 <= p["low"] <= p["hours"] <= p["high"] <= 99)
        self.assertTrue(r["factors"] and r["comparisons"] and r["charts"]["distribution"])

    def test_unknown_occupation_and_income(self):
        r = hours.analyze(30, 9, "Never-married", "Own-child", "Female")
        self.assertEqual(r["occupation"]["source"], "inconnu")
        self.assertNotIn("income_high", [f["feature"] for f in r["factors"]])


class HoursApi(SimpleTestCase):
    def post(self, payload):
        return self.client.post("/api/hours/analyze/", data=json.dumps(payload), content_type="application/json")

    def test_ok(self):
        res = self.post({"age": 35, "education_num": 13, "marital_status": "Married-civ-spouse",
                         "relationship": "Husband", "sex": "Male", "occupation_text": "Développeur logiciel"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("hours", res.json()["prediction"])

    def test_bad_input(self):
        self.assertEqual(self.post({"age": 5}).status_code, 400)
        self.assertEqual(self.post({"age": 35, "education_num": 13, "marital_status": "x",
                                    "relationship": "Husband", "sex": "Male"}).status_code, 400)
