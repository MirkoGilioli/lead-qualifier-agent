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

import logging
import os
from app.app_utils.config import config


def setup_telemetry() -> str | None:
    """Configure OpenTelemetry and GenAI telemetry with GCS upload using config file."""

    telemetry_config = config.get("telemetry", {})
    enabled = telemetry_config.get("enabled", False)
    bucket = telemetry_config.get("bucket")

    if enabled and bucket:
        capture_content = telemetry_config.get("capture_content", "NO_CONTENT")
        logging.info(
            f"Prompt-response logging enabled - mode: {capture_content} (uploading to gs://{bucket})"
        )
        
        # Impostiamo le variabili d'ambiente richieste dalla strumentazione GenAI
        os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = capture_content
        os.environ["OTEL_INSTRUMENTATION_GENAI_UPLOAD_FORMAT"] = telemetry_config.get("format", "jsonl")
        os.environ["OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK"] = telemetry_config.get("hook", "upload")
        os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = telemetry_config.get("stability_opt_in", "gen_ai_latest_experimental")
        
        # Percorso di upload
        path = telemetry_config.get("path", "completions")
        os.environ["OTEL_INSTRUMENTATION_GENAI_UPLOAD_BASE_PATH"] = f"gs://{bucket}/{path}"
        
        # Resource Attributes (Namespace e Versione)
        namespace = telemetry_config.get("resource_namespace", "randstad-adk")
        commit_sha = os.environ.get("COMMIT_SHA", "dev")
        os.environ["OTEL_RESOURCE_ATTRIBUTES"] = f"service.namespace={namespace},service.version={commit_sha}"
        
    else:
        logging.info(
            "Prompt-response logging disabled (check 'telemetry' section in config.yaml)"
        )

    return bucket
