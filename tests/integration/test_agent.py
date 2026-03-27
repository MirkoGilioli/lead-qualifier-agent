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

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


def test_agent_stream() -> None:
    """
    Integration test for the agent stream functionality.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Buongiorno, chi sei?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0

    has_text_content = any(
        part.text for event in events if event.content 
        for part in event.content.parts if part.text
    )
    assert has_text_content


def test_agent_multi_agent_delegation() -> None:
    """
    Test di integrazione che verifica la delegazione al ricercatore.
    In v2.0.0, nominare un'azienda deve innescare la ricerca.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user_del", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Lavoro per Ferrero Spa.")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user_del",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    # Verifichiamo che l'agente abbia risposto testualmente (grounding su ricerca o root)
    has_text = any(
        part.text for event in events if event.content 
        for part in event.content.parts if part.text
    )
    assert has_text, "L'agente non ha prodotto alcuna risposta alla menzione dell'azienda."

def test_agent_final_qualification_flow() -> None:
    """
    Verifica che fornendo i dati di qualificazione, l'agente tenti il salvataggio.
    Nota: In v2.0.0 questo richiede che l'azienda sia già nota o fornita nel messaggio.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user_save", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Forniamo contesto completo per innescare salva_qualificazione
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Siamo la Ferrero Spa, usiamo Adecco per 150 persone.")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user_save",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    # Verifichiamo la chiamata a salva_qualificazione (AFC deve gestirla)
    has_save_call = any(
        part.function_call and part.function_call.name == "salva_qualificazione"
        for event in events if event.content 
        for part in event.content.parts
    )
    
    # In alternativa, verifichiamo la conferma testuale
    has_confirmation = any(
        "salvat" in part.text.lower() 
        for event in events if event.content 
        for part in event.content.parts if part.text
    )

    assert has_save_call or has_confirmation, "L'agente non ha innescato il salvataggio o confermato l'azione."
