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

"""
Questo modulo definisce l'applicazione FastAPI per servire l'agente ADK.
Include il setup della telemetria, l'esposizione degli endpoint e il logging su Cloud Logging.
"""

import os

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Build Cloud SQL URL from environment variables for session storage
# Uses the pg8000 driver and the Cloud Run unix socket
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_NAME")
db_conn = os.environ.get("DB_CONNECTION_NAME")

if all([db_user, db_pass, db_name, db_conn]):
    # Note: asyncpg format for unix sockets is postgresql+asyncpg://user:password@/dbname?host=/cloudsql/connection_name
    session_service_uri = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{db_conn}"
else:
    # Fallback to local SQLite if running outside Cloud Run or missing env vars
    session_service_uri = "sqlite+aiosqlite:///app/.adk/session.db"

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

# Check if web UI should be enabled (defaults to True if not specified)
enable_web_ui = os.getenv("ENABLE_WEB_UI", "True").lower() == "true"

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=enable_web_ui,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=True,
)
app.title = "randstad-adk"
app.description = "API for interacting with the Agent randstad-adk"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
