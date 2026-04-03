# ruff: noqa
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
Entry point dell'applicazione ADK.
Qui viene definito l'agente principale (Root Agent) e orchestrata la delegazione.
"""

import os
import time
import logging
import google.auth

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types
from opentelemetry import trace

from .tools import salva_qualificazione
from .prompts import INSTRUCTION
from .agents.researcher import ricercatore_azienda
from .app_utils.config import config
from .rai_service import ResponsibleAIPlugin

logger = logging.getLogger(__name__)

# Callback per misurare la latenza (SRE Logic)
async def track_start_time(callback_context: CallbackContext) -> None:
    callback_context.state["_sre_start_time"] = time.time()
    # Aggiungiamo un attributo allo span iniziale
    current_span = trace.get_current_span()
    current_span.set_attribute("sre.start_time", time.time())

async def log_sre_metrics(callback_context: CallbackContext) -> None:
    start_time = callback_context.state.get("_sre_start_time")
    if start_time:
        duration_ms = (time.time() - start_time) * 1000
        
        # 1. Log Strutturato (Stile RAI/NLP)
        # Questo verrà catturato da Cloud Run e trasformato in jsonPayload
        logger.info({
            "message": f"SRE_METRIC: agent_run_duration_ms={duration_ms:.2f}",
            "event": "sre_metric",
            "metric_name": "agent_run_duration_ms",
            "value": float(f"{duration_ms:.2f}"),
            "unit": "ms"
        })

        # 2. Integrazione Cloud Trace (Stile RAI/NLP)
        current_span = trace.get_current_span()
        current_span.set_attribute("sre.agent_run_duration_ms", duration_ms)
        current_span.set_attribute("sre.status", "success")

# Configurazione ambiente GCP
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id

# Caricamento variabili d'ambiente configurate nel YAML
for k, v in config.get("env", {}).items():
    os.environ[k] = str(v)

# Safety settings comuni
def get_safety_settings():
    conf_safety = config.get("agents.root.safety_settings", {})
    settings = []
    for category, threshold in conf_safety.items():
        settings.append(
            types.SafetySetting(
                category=getattr(types.HarmCategory, f"HARM_CATEGORY_{category}"),
                threshold=getattr(types.HarmBlockThreshold, threshold),
            )
        )
    return settings

# Root Agent: Il "Direttore d'orchestra"
root_agent = Agent(
    name=config.get("agents.root.name", "qualificatore_commerciale"),
    model=Gemini(
        model=config.get("agents.root.model", "gemini-3-flash-preview"),
        config=types.GenerateContentConfig(
            temperature=config.get("agents.root.temperature", 0.2),
            safety_settings=get_safety_settings(),
        )
    ),
    instruction=INSTRUCTION,
    tools=[
        salva_qualificazione,
        AgentTool(ricercatore_azienda) # Delegazione modulare
    ],
    before_agent_callback=track_start_time,
    after_agent_callback=log_sre_metrics,
)

app = App(
    root_agent=root_agent,
    name=config.get("app.name", "app"),
    plugins=[ResponsibleAIPlugin()],
)
