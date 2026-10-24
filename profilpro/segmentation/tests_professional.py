"""Tests de la segmentation professionnelle (modèle kmeans_profils_socio_economiques.pkl).

Lancer : python manage.py test segmentation.tests_professional
"""
import json

from django.test import SimpleTestCase

from . import professional


class ProfessionalSegmentation(SimpleTestCase):
    def test_four_example_profiles(self):
        """Les 4 personnes du notebook (A à D) tombent dans les clusters 0 à 3."""
        cases = {0: (55, 8, 38, 0), 1: (37, 12, 48, 0), 2: (25, 9, 30, 0), 3: (45, 12, 46, 1)}
        for expected, (age, edu, hours, income) in cases.items():
            r = professional.analyze(age, edu, hours, income)
            self.assertEqual(r["candidate"]["cluster"], expected)
            self.assertEqual(len(r["clusters"]), 4)
            self.assertTrue(r["graph"]["image"].startswith("data:image/png;base64,"))

    def test_unknown_income_is_estimated(self):
        r = professional.analyze(30, 13, 40, None)
        inputs = r["candidate"]["inputs"]
        self.assertEqual(inputs["income_source"], "estimated")
        self.assertTrue(0 <= inputs["income_sup50k"] <= 1)

    def test_cluster_cards_have_means(self):
        for card in professional.overview()["clusters"]:
            for key in ("age_mean", "education_mean", "hours_mean", "pct_high_income", "count", "occupations"):
                self.assertIn(key, card)


class ProfessionalApi(SimpleTestCase):
    def post(self, payload):
        return self.client.post("/api/professional/analyze/", data=json.dumps(payload), content_type="application/json")

    def test_analyze_ok(self):
        res = self.post({"age": 45, "education_num": 12, "hours_per_week": 46, "income_sup50k": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["candidate"]["cluster"], 3)

    def test_analyze_rejects_bad_input(self):
        self.assertEqual(self.post({"age": 10, "education_num": 12, "hours_per_week": 40}).status_code, 400)
        self.assertEqual(self.post({"age": 30, "education_num": 12, "hours_per_week": 200}).status_code, 400)
        self.assertEqual(self.post({"age": 30, "education_num": 12, "hours_per_week": 40, "income_sup50k": 7}).status_code, 400)
        self.assertEqual(self.post({"age": 30}).status_code, 400)

    def test_clusters_endpoint(self):
        res = self.client.get("/api/professional/clusters/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["clusters"]), 4)
