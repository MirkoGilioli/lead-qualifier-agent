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
import google.auth

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from .tools import salva_qualificazione
from .prompts import INSTRUCTION
from .agents.researcher import ricercatore_azienda
from .app_utils.config import config

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
)

app = App(
    root_agent=root_agent,
    name=config.get("app.name", "app"),
)
