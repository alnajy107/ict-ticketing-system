import unittest
import os
import tempfile

from app import create_app, init_db


class TicketingSystemTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd)
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path})
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.remove(self.db_path)

    def test_ticket_submission_and_status_update(self):
        response = self.client.post(
            "/api/tickets",
            json={
                "school_name": "San Isidro NHS",
                "requestor_designation": "Teacher",
                "issue_category": "Internet/Connectivity",
                "description": "Wi-Fi dropping during class",
                "consent": True,
            },
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertTrue(payload["tracking_id"])

        self.client.post(
            "/login",
            data={"username": "itdepartment", "password": "ITDept2026!"},
            follow_redirects=True,
        )

        ticket_id = payload["ticket_id"]
        update_response = self.client.post(
            f"/api/tickets/{ticket_id}/status",
            json={"status": "Resolved"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.get_json()["status"], "Resolved")

    def test_it_dashboard_requires_login(self):
        response = self.client.get("/api/tickets")
        self.assertEqual(response.status_code, 403)

        login_response = self.client.post(
            "/login",
            data={"username": "itdepartment", "password": "ITDept2026!"},
            follow_redirects=True,
        )
        self.assertEqual(login_response.status_code, 200)

        dashboard_response = self.client.get("/api/tickets")
        self.assertEqual(dashboard_response.status_code, 200)

    def test_ticket_submission_requires_consent(self):
        response = self.client.post(
            "/api/tickets",
            json={
                "school_name": "San Isidro NHS",
                "requestor_designation": "Teacher",
                "issue_category": "Internet/Connectivity",
                "description": "Wi-Fi dropping during class",
                "consent": False,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("consent", response.get_json()["error"])

    def test_analytics_handles_zero_tickets(self):
        response = self.client.get("/api/analytics")
        self.assertEqual(response.status_code, 403)
        payload = response.get_json()
        self.assertEqual(payload["error"], "IT Department access required")


if __name__ == "__main__":
    unittest.main()
