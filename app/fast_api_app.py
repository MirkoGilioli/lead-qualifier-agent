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
import logging

import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.app_utils.config import config
from app.app_utils.firestore_session_service import FirestoreSessionService
import google.adk.cli.fast_api

# Monkey patch diretto nel modulo dove viene usata la funzione
def custom_session_factory(base_dir, session_service_uri=None, **kwargs):
    if session_service_uri and session_service_uri.startswith("firestore://"):
        db_id = config.get("sessions.database_id")
        col = config.get("sessions.collection", "chat_sessions")
        _, project_id_local = google.auth.default()
        return FirestoreSessionService(
            project_id=project_id_local,
            database_id=db_id,
            collection_name=col
        )
    from google.adk.cli.utils.service_factory import create_session_service_from_options as original_factory
    return original_factory(base_dir, session_service_uri, **kwargs)

# Sovrascriviamo il riferimento nel modulo fast_api dell'ADK
google.adk.cli.fast_api.create_session_service_from_options = custom_session_factory

from google.adk.cli.fast_api import get_fast_api_app

# Configura il logging di base prima di qualsiasi chiamata
logging.basicConfig(level=logging.INFO)

logs_bucket_name = setup_telemetry()
_, project_id = google.auth.default()

# Cloud Logging attivo solo se NON siamo in locale (dev)
if os.getenv("APP_ENV", "dev") != "dev":
    try:
        logging_client = google_cloud_logging.Client(project=project_id)
        handler = CloudLoggingHandler(logging_client, name="randstad-adk-logs")
        logging.getLogger().addHandler(handler)
        logging.info(f"Cloud Logging integration started for project: {project_id}")
    except Exception as e:
        logging.warning(f"Cloud Logging failed to initialize: {e}")

logger = logging.getLogger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
# Note: logs_bucket_name is already set by setup_telemetry() above, 
# but we re-read it here to ensure it's available for artifact_service_uri
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Firestore session configuration from config.yaml
session_db_id = config.get("sessions.database_id")
session_collection = config.get("sessions.collection", "chat_sessions")

# Costruiamo un URI che il nostro factory personalizzato intercetterà
session_service_uri = f"firestore://{session_collection}" if session_db_id else None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

# Check if web UI should be enabled (defaults to True if not specified)
enable_web_ui = config.get("fastapi.enable_web_ui", True)

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
    logger.info(feedback.model_dump())
    return {"status": "success"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status OK
    """
    return {"status": "ok"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
