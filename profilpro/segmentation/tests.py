import json

from django.test import SimpleTestCase, TestCase

from . import salary


class SalaryRules(SimpleTestCase):
    def test_match_role_from_cv_titles(self):
        self.assertEqual(salary.match_role("Développeur Python Backend"), "software_developer")
        self.assertEqual(salary.match_role("Comptable senior"), "accountant")
        self.assertEqual(salary.match_role("Data Scientist"), "data_scientist")
        self.assertEqual(salary.match_role("Chargée RH"), "hr_specialist")

    def test_no_false_positive_on_partial_words(self):
        self.assertIsNone(salary.match_role("Chef de projet marketing"))
        self.assertIsNone(salary.match_role(""))

    def test_unknown_role_returns_no_salary(self):
        rec = salary.recommend(None, years=5)
        self.assertFalse(rec["available"])
        self.assertIsNone(rec["annual"])
        self.assertIsNone(rec["monthly"])
        self.assertIn("Aucun salaire", rec["message"])

    def test_levels_from_experience(self):
        self.assertEqual(salary.level_from_years(1), "junior")
        self.assertEqual(salary.level_from_years(5), "confirme")
        self.assertEqual(salary.level_from_years(10), "senior")

    def test_bands_for_software_developer(self):
        junior = salary.recommend("software_developer", years=1)
        confirmed = salary.recommend("software_developer", years=5)
        senior = salary.recommend("software_developer", years=10)
        self.assertEqual(junior["annual"]["advised"], 109220)   # (82 460 + 135 980) / 2
        self.assertEqual(confirmed["annual"]["advised"], 135980)  # médiane
        self.assertEqual(senior["annual"]["advised"], 175325)   # (135 980 + 214 670) / 2
        self.assertEqual(confirmed["monthly"]["advised"], round(135980 / 12))
        self.assertEqual(senior["annual"]["max"], 214670)

    def test_manual_level_overrides_years(self):
        rec = salary.recommend("accountant", years=1, level="senior")
        self.assertEqual(rec["level"], "senior")

    def test_comparison_positions(self):
        rec = salary.recommend("hr_specialist", years=5)
        monthly = rec["monthly"]
        self.assertEqual(salary.recommend("hr_specialist", 5, None, monthly["min"] - 100)["comparison"]["position"], "below")
        self.assertEqual(salary.recommend("hr_specialist", 5, None, monthly["advised"])["comparison"]["position"], "within")
        self.assertEqual(salary.recommend("hr_specialist", 5, None, monthly["max"] + 100)["comparison"]["position"], "above")


class SalaryApi(TestCase):
    def test_recommend_endpoint(self):
        r = self.client.post("/api/salary/recommend/", data=json.dumps({"occupation_text": "Comptable", "years": 4,
                                                                         "expected_monthly": 5000}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["available"])
        self.assertEqual(body["role"]["key"], "accountant")
        self.assertEqual(body["currency"], "USD")
        self.assertIn("comparison", body)

    def test_recommend_rejects_bad_years(self):
        r = self.client.post("/api/salary/recommend/", data=json.dumps({"role": "accountant", "years": 200}),
                             content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_report_returns_pdf(self):
        payload = {"age": 44, "education_num": 13, "relationship": "Husband", "sex": "Male", "hours_per_week": 45,
                   "occupation_text": "Data Scientist", "years": 6, "expected_monthly": 9000,
                   "candidate_name": "Candidat test"}
        r = self.client.post("/api/income/report/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

    def test_income_analyze_still_works(self):
        payload = {"age": 44, "education_num": 13, "relationship": "Husband", "sex": "Male", "hours_per_week": 45}
        r = self.client.post("/api/income/analyze/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertIn(r.json()["prediction"]["label"], (">50K", "<=50K"))

    def test_income_analyze_rejects_missing_fields(self):
        r = self.client.post("/api/income/analyze/", data=json.dumps({"age": 44}), content_type="application/json")
        self.assertEqual(r.status_code, 400)
