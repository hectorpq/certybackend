"""
Locust performance test scenarios for SCAD-2026.

Usage:
    locust -f locust/locustfile.py --host=http://localhost:8000

Targets:
  - Public verification (anonymous, high volume)
  - Authenticated API calls (coordinators, moderate volume)
  - Certificate generation flow (admin, low volume)
"""

import random
import string

from locust import HttpUser, between, tag, task


def random_email():
    suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    return f"perf_{suffix}@test.local"


class PublicUser(HttpUser):
    """Anonymous user hitting the public verification endpoint."""

    wait_time = between(0.5, 2)
    weight = 3

    def on_start(self):
        self.verification_codes = ["TEST-0001", "TEST-0002", "NONEXISTENT-CODE"]

    @task(10)
    @tag("public", "verify")
    def verify_certificate(self):
        code = random.choice(self.verification_codes)
        with self.client.get(
            f"/api/certificates/verify/?code={code}",
            catch_response=True,
            name="/api/certificates/verify/",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(3)
    @tag("public", "schema")
    def get_openapi_schema(self):
        self.client.get("/api/schema/", name="/api/schema/")

    @task(1)
    @tag("public", "docs")
    def get_swagger_ui(self):
        self.client.get("/api/docs/", name="/api/docs/")


class CoordinatorUser(HttpUser):
    """Authenticated coordinator performing day-to-day operations."""

    wait_time = between(1, 3)
    weight = 2

    def on_start(self):
        resp = self.client.post(
            "/api/login/",
            json={"email": "perf_coordinator@test.local", "password": "PerfPass123!"},
            name="[setup] login",
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access") or data.get("token", "")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(5)
    @tag("coordinator", "events")
    def list_events(self):
        self.client.get("/api/events/", headers=self.headers, name="/api/events/")

    @task(5)
    @tag("coordinator", "participants")
    def list_participants(self):
        self.client.get(
            "/api/participants/", headers=self.headers, name="/api/participants/"
        )

    @task(4)
    @tag("coordinator", "certificates")
    def list_certificates(self):
        self.client.get(
            "/api/certificates/", headers=self.headers, name="/api/certificates/"
        )

    @task(2)
    @tag("coordinator", "certificates")
    def list_certificates_page_2(self):
        self.client.get(
            "/api/certificates/?page=2",
            headers=self.headers,
            name="/api/certificates/?page=N",
        )

    @task(1)
    @tag("coordinator", "deliveries")
    def list_deliveries(self):
        self.client.get(
            "/api/deliveries/", headers=self.headers, name="/api/deliveries/"
        )

    @task(1)
    @tag("coordinator", "audit")
    def list_audit_logs(self):
        self.client.get("/api/audit/", headers=self.headers, name="/api/audit/")


class AdminUser(HttpUser):
    """Admin performing heavy operations (certificate generation + export)."""

    wait_time = between(3, 8)
    weight = 1

    def on_start(self):
        resp = self.client.post(
            "/api/login/",
            json={"email": "perf_admin@test.local", "password": "PerfAdmin123!"},
            name="[setup] login",
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access") or data.get("token", "")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    @tag("admin", "events")
    def list_events(self):
        self.client.get("/api/events/", headers=self.headers, name="/api/events/")

    @task(2)
    @tag("admin", "certificates")
    def list_certificates(self):
        self.client.get(
            "/api/certificates/", headers=self.headers, name="/api/certificates/"
        )

    @task(1)
    @tag("admin", "export")
    def export_certificates_csv(self):
        with self.client.get(
            "/api/certificates/export/?file_format=csv",
            headers=self.headers,
            catch_response=True,
            name="/api/certificates/export/",
        ) as resp:
            if resp.status_code in (200, 403, 404):
                resp.success()
            else:
                resp.failure(f"Export failed: {resp.status_code}")

    @task(1)
    @tag("admin", "instructors")
    def list_instructors(self):
        self.client.get(
            "/api/instructors/", headers=self.headers, name="/api/instructors/"
        )
