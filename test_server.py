#!/usr/bin/env python3
"""
SchemeSathi AI - Comprehensive Automated Test Suite
Covers all required test scenarios:
- Health endpoint
- Scheme listing & search
- Scheme details & 404 unknown ID
- Categories and States endpoints
- Valid & invalid eligibility evaluations
- Grounded AI assistant fallback & validation
- Database demo mode behavior
"""

import unittest
import json
import server

class SchemeSathiTestCase(unittest.TestCase):
    def setUp(self):
        server.app.config["TESTING"] = True
        self.client = server.app.test_client()

    def test_health_endpoint(self):
        """Verify GET /api/health returns 200 and healthy status structure."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertEqual(data["data"]["service"], "SchemeSathi AI")
        self.assertIn("database_mode", data["data"])

    def test_get_states(self):
        """Verify GET /api/states returns Indian states and UTs."""
        response = self.client.get("/api/states")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)
        self.assertTrue(len(data["data"]) >= 28)
        codes = [s["code"] for s in data["data"]]
        self.assertIn("ALL", codes)
        self.assertIn("AP", codes)
        self.assertIn("TG", codes)

    def test_get_categories(self):
        """Verify GET /api/categories returns categories with counts."""
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)
        cat_names = [c["name"] for c in data["data"]]
        self.assertIn("Agriculture", cat_names)
        self.assertIn("Education", cat_names)

    def test_get_all_schemes(self):
        """Verify GET /api/schemes returns list of active schemes."""
        response = self.client.get("/api/schemes")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)
        self.assertGreaterEqual(len(data["data"]), 10)

    def test_schemes_search_keyword(self):
        """Verify search by keyword 'kisan'."""
        response = self.client.get("/api/schemes?q=kisan")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        schemes = data["data"]
        self.assertTrue(any("kisan" in s["name"].lower() for s in schemes))

    def test_schemes_search_category_filter(self):
        """Verify filtering by category 'Education'."""
        response = self.client.get("/api/schemes?category=Education")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        for s in data["data"]:
            cats = [c.lower() for c in s.get("categories", [])]
            self.assertTrue(any("education" in c for c in cats))

    def test_schemes_search_empty_results(self):
        """Verify empty search results for non-existent query."""
        response = self.client.get("/api/schemes?q=nonexistent_scheme_query_12345")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 0)

    def test_scheme_detail_valid(self):
        """Verify GET /api/schemes/<id> for valid ID."""
        response = self.client.get("/api/schemes/pm-kisan")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        scheme = data["data"]
        self.assertEqual(scheme["id"], "pm-kisan")
        self.assertIn("https://pmkisan.gov.in/", scheme["official_url"])
        self.assertIn("required_documents", scheme)
        self.assertIn("application_steps", scheme)

    def test_scheme_detail_unknown(self):
        """Verify GET /api/schemes/<id> returns 404 for unknown scheme."""
        response = self.client.get("/api/schemes/invalid-scheme-id-999")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("not found", data["message"].lower())

    def test_eligibility_valid_student(self):
        """Verify POST /api/eligibility with valid student inputs."""
        payload = {
            "age": 20,
            "state": "AP",
            "income": 150000,
            "is_student": True,
            "is_farmer": False,
            "beneficiary_category": "SC",
            "occupation": "student"
        }
        response = self.client.post("/api/eligibility", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        evaluations = data["data"]["evaluations"]
        self.assertGreater(len(evaluations), 0)
        # Post-Matric Scholarship or Amma Vodi should be potentially eligible
        student_schemes = [e for e in evaluations if e["scheme_id"] in ["post-matric-scholarship", "ap-amma-vodi"]]
        self.assertTrue(any(e["status"] == "Potentially eligible" for e in student_schemes))

    def test_eligibility_invalid_age(self):
        """Verify POST /api/eligibility rejects invalid age."""
        payload = {"age": -5}
        response = self.client.post("/api/eligibility", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_eligibility_invalid_income(self):
        """Verify POST /api/eligibility rejects negative income."""
        payload = {"income": -1000}
        response = self.client.post("/api/eligibility", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_assistant_chat_without_api_key(self):
        """Verify POST /api/assistant operates in grounded fallback mode when key is absent."""
        payload = {"query": "I am a farmer, what schemes can help me?"}
        response = self.client.post("/api/assistant", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("answer", data["data"])
        self.assertIn("citations", data["data"])
        # Should cite official links
        self.assertTrue(len(data["data"]["citations"]) > 0)
        first_citation = data["data"]["citations"][0]
        self.assertTrue(first_citation["url"].startswith("http"))

    def test_assistant_chat_empty_query(self):
        """Verify POST /api/assistant rejects empty query."""
        payload = {"query": "   "}
        response = self.client.post("/api/assistant", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_frontend_serving(self):
        """Verify GET / serves index.html."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SchemeSathi AI", response.data)

if __name__ == "__main__":
    unittest.main()
