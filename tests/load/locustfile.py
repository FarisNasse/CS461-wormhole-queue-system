from __future__ import annotations

import os
import random
import string
from typing import Optional

from locust import HttpUser, LoadTestShape, constant_pacing, task

COURSES = [
    "PH 201",
    "PH 202",
    "PH 211",
    "PH 212",
    "PH 213",
    "PH 251",
    "PH 252",
    "PH 253",
]


def random_student_name(prefix: str = "student") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


class PublicPagesUser(HttpUser):
    # More stable pacing than a random wait, so the test is easier to compare run to run
    wait_time = constant_pacing(4)
    weight = 5

    @task(5)
    def homepage(self):
        with self.client.get("/", name="GET /", catch_response=True) as response:
            body = response.text
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
            elif "Wormhole" not in body:
                response.failure(
                    "Homepage loaded but expected Wormhole branding was missing"
                )

    @task(3)
    def live_queue(self):
        with self.client.get(
            "/livequeue", name="GET /livequeue", catch_response=True
        ) as response:
            body = response.text
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
            elif "Live Queue" not in body:
                response.failure(
                    "Live Queue page loaded but expected heading was missing"
                )

    @task(2)
    def wiki(self):
        with self.client.get(
            "/wiki", name="GET /wiki", catch_response=True
        ) as response:
            body = response.text
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
            elif "Wiki" not in body and "Documentation" not in body:
                response.failure("Wiki page loaded but expected content was missing")

    @task(1)
    def check_session(self):
        with self.client.get(
            "/api/check-session",
            name="GET /api/check-session",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")


class StudentTicketUser(HttpUser):
    wait_time = constant_pacing(6)
    weight = 3

    def on_start(self) -> None:
        self.student_name = random_student_name()

    @task(4)
    def create_ticket_and_verify_queue(self):
        payload = {
            "student_name": self.student_name,
            "class_name": random.choice(COURSES),
            "table_number": random.randint(1, 12),
        }

        with self.client.post(
            "/api/tickets",
            json=payload,
            name="POST /api/tickets",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(
                    f"Expected 201 creating ticket, got {response.status_code}: {response.text}"
                )
                return

        with self.client.get(
            "/api/opentickets",
            name="GET /api/opentickets",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Expected 200 fetching open tickets, got {response.status_code}: {response.text}"
                )
                return

            try:
                tickets = response.json()
            except Exception as exc:
                response.failure(f"Open tickets did not return valid JSON: {exc}")
                return

            if not any(
                ticket.get("student_name") == self.student_name for ticket in tickets
            ):
                response.failure(
                    f"Created ticket for {self.student_name} was not visible in /api/opentickets"
                )

    @task(3)
    def watch_live_queue(self):
        with self.client.get(
            "/livequeue", name="GET /livequeue", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(1)
    def inspect_open_tickets(self):
        with self.client.get(
            "/api/opentickets",
            name="GET /api/opentickets",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Expected 200 fetching open tickets, got {response.status_code}: {response.text}"
                )


class AssistantWorkflowUser(HttpUser):
    wait_time = constant_pacing(7)
    weight = 2

    username = os.getenv("LOCUST_ASSISTANT_USERNAME", "ci_test_assistant").strip()
    password = os.getenv("LOCUST_ASSISTANT_PASSWORD", "ci_test_password").strip()

    def on_start(self) -> None:
        if not self.username or not self.password:
            return

        with self.client.post(
            "/api/login",
            json={"username": self.username, "password": self.password},
            name="POST /api/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Assistant login failed: {response.status_code} {response.text}"
                )

    def _claim_next_ticket(self) -> Optional[int]:
        if not self.username:
            return None

        with self.client.get(
            f"/getnewticket/{self.username}",
            name="GET /getnewticket/[username]",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code not in (302, 303):
                response.failure(
                    f"Expected redirect when claiming ticket, got {response.status_code}"
                )
                return None

            location = response.headers.get("Location", "")

            if "/currentticket/" not in location:
                # No ticket available; not a failure
                response.success()
                return None

            try:
                ticket_id = int(location.rstrip("/").split("/")[-1].split("?")[0])
            except ValueError:
                response.failure(f"Could not parse ticket id from redirect: {location}")
                return None

            response.success()
            return ticket_id

    @task(2)
    def queue_dashboard(self):
        with self.client.get(
            "/queue", name="GET /queue", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")

    @task(4)
    def claim_and_resolve_ticket(self):
        if not self.username or not self.password:
            return

        ticket_id = self._claim_next_ticket()
        if ticket_id is None:
            return

        with self.client.get(
            f"/currentticket/{ticket_id}",
            name="GET /currentticket/[id]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Expected 200 loading current ticket, got {response.status_code}"
                )
                return

        with self.client.post(
            f"/api/resolveticket/{ticket_id}",
            data={"resolve": "helped"},
            name="POST /api/resolveticket/[id]",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code not in (302, 303):
                response.failure(
                    f"Expected redirect after resolving ticket, got {response.status_code}: {response.text}"
                )
                return

        # Verify resolved ticket no longer appears in open tickets
        with self.client.get(
            "/api/opentickets",
            name="GET /api/opentickets",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Expected 200 fetching open tickets after resolve, got {response.status_code}"
                )
                return

            try:
                tickets = response.json()
            except Exception as exc:
                response.failure(
                    f"Open tickets did not return valid JSON after resolve: {exc}"
                )
                return

            if any(ticket.get("id") == ticket_id for ticket in tickets):
                response.failure(
                    f"Resolved ticket {ticket_id} still appears in open tickets"
                )

    def on_stop(self) -> None:
        if self.username and self.password:
            self.client.post("/api/logout", name="POST /api/logout")


class WormholeStages(LoadTestShape):
    """
    Warm up -> steady state -> spike -> cool down
    """

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 25, "spawn_rate": 5},
        {"duration": 300, "users": 50, "spawn_rate": 10},
        {"duration": 390, "users": 75, "spawn_rate": 15},
        {"duration": 480, "users": 25, "spawn_rate": 15},
        {"duration": 540, "users": 0, "spawn_rate": 20},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None
