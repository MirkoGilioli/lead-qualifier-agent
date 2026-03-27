# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import time
import uuid

import urllib3
from locust import HttpUser, between, task

# Suppress InsecureRequestWarning if SSL verification is disabled
if os.environ.get("LOCUST_SKIP_CERT_VERIFY", "").lower() == "true":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ENDPOINT = "/run_sse"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChatStreamUser(HttpUser):
    """Simulates a user interacting with the multi-agent B2B qualifier."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task
    def chat_stream(self) -> None:
        """Simulates a multi-agent interaction flow."""
        headers = {"Content-Type": "application/json"}
        if os.environ.get("_ID_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['_ID_TOKEN']}"

        # SSL Verification toggle
        verify_ssl = os.environ.get("LOCUST_SKIP_CERT_VERIFY", "").lower() != "true"

        # Create session first
        user_id = f"user_{uuid.uuid4()}"
        session_data = {"state": {"preferred_language": "Italian", "visit_count": 1}}

        with self.client.post(
            f"/apps/app/users/{user_id}/sessions",
            headers=headers,
            json=session_data,
            verify=verify_ssl,
            catch_response=True,
            name="Create Session"
        ) as session_response:
            if session_response.status_code != 200 and session_response.status_code != 201:
                session_response.failure(f"Failed to create session: {session_response.status_code}")
                return

            try:
                session_id = session_response.json()["id"]
            except (json.JSONDecodeError, KeyError):
                session_response.failure("Invalid JSON in session response")
                return

        # Send chat message that triggers the researcher sub-agent
        data = {
            "app_name": "app",
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": "Buongiorno, lavoro per Barilla Spa."}],
            },
            "streaming": True,
        }
        start_time = time.time()

        with self.client.post(
            ENDPOINT,
            name=f"{ENDPOINT} multi-agent trigger",
            headers=headers,
            json=data,
            catch_response=True,
            stream=True,
            params={"alt": "sse"},
            verify=verify_ssl,
        ) as response:
            if response.status_code == 200:
                events = []
                has_error = False
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        events.append(line_str)

                        # Check for error responses in the JSON payload
                        try:
                            # Handling the 'data: ' prefix if present in the line
                            clean_line = line_str[6:] if line_str.startswith("data: ") else line_str
                            event_data = json.loads(clean_line)
                            if isinstance(event_data, dict) and "code" in event_data:
                                if event_data["code"] >= 400:
                                    has_error = True
                                    response.failure(f"Error in response: {event_data.get('message')}")
                        except json.JSONDecodeError:
                            pass

                end_time = time.time()
                total_time = end_time - start_time

                if not has_error:
                    self.environment.events.request.fire(
                        request_type="POST",
                        name=f"{ENDPOINT} complete",
                        response_time=total_time * 1000,
                        response_length=len(events),
                        response=response,
                        context={},
                    )
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
