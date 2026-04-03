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

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.app_utils.firestore_session_service import FirestoreSessionService
from google.adk.sessions.session import Session
from google.adk.events.event import Event

@pytest.fixture
def mock_otel_span():
    with patch("opentelemetry.trace.get_current_span") as mock_get_span:
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_get_span.return_value = mock_span
        yield mock_span

@pytest.fixture
def firestore_service():
    with patch("google.cloud.firestore.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        service = FirestoreSessionService(
            project_id="test-project",
            database_id="test-db",
            collection_name="test-sessions"
        )
        yield service, mock_client

@pytest.mark.asyncio
async def test_create_session_success(firestore_service, mock_otel_span):
    service, mock_client = firestore_service
    
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_document.set = AsyncMock()
    
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
    session = await service.create_session(
        app_name="test-app",
        user_id="test-user",
        session_id="session-123"
    )
    
    # Verifiche
    assert session.id == "session-123"
    assert session.app_name == "test-app"
    
    # Verifica OTel tagging
    mock_otel_span.set_attribute.assert_called_with("session_id", "session-123")
    
    # Verifica Firestore call
    mock_client.collection.assert_called_with("test-sessions")
    mock_collection.document.assert_called_with("session-123")
    mock_document.set.assert_called_once()
    
    # Verifica dati salvati (alias Pydantic)
    args, _ = mock_document.set.call_args
    saved_data = args[0]
    assert saved_data["id"] == "session-123"
    assert saved_data["appName"] == "test-app"
    assert saved_data["userId"] == "test-user"

@pytest.mark.asyncio
async def test_get_session_found(firestore_service, mock_otel_span):
    service, mock_client = firestore_service
    
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        "id": "session-123",
        "appName": "test-app",
        "userId": "test-user",
        "state": {},
        "events": [],
        "lastUpdateTime": 123456789.0
    }
    
    mock_document = MagicMock()
    mock_document.get = AsyncMock(return_value=mock_doc_snapshot)
    
    mock_client.collection.return_value.document.return_value = mock_document
    
    session = await service.get_session(
        app_name="test-app",
        user_id="test-user",
        session_id="session-123"
    )
    
    assert session is not None
    assert session.id == "session-123"
    mock_otel_span.set_attribute.assert_called_with("session_id", "session-123")

@pytest.mark.asyncio
async def test_get_session_validation_failure(firestore_service):
    service, mock_client = firestore_service
    
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    # Dati per un utente diverso
    mock_doc_snapshot.to_dict.return_value = {
        "id": "session-123",
        "appName": "test-app",
        "userId": "WRONG-USER"
    }
    
    mock_document = MagicMock()
    mock_document.get = AsyncMock(return_value=mock_doc_snapshot)
    mock_client.collection.return_value.document.return_value = mock_document
    
    session = await service.get_session(
        app_name="test-app",
        user_id="test-user",
        session_id="session-123"
    )
    
    # Deve restituire None se l'utente non coincide
    assert session is None

@pytest.mark.asyncio
async def test_append_event_persists(firestore_service):
    service, mock_client = firestore_service
    
    session = Session(id="s1", app_name="app", user_id="u1")
    # L'evento richiede un contenuto strutturato (role e parts)
    event = Event(
        author="user", 
        content={"role": "user", "parts": [{"text": "hello"}]}
    )
    
    mock_document = MagicMock()
    mock_document.set = AsyncMock()
    mock_client.collection.return_value.document.return_value = mock_document
    
    await service.append_event(session, event)
    
    # Verifica che l'evento sia stato aggiunto all'oggetto in memoria
    assert len(session.events) == 1
    # Verifica che sia stato chiamato il salvataggio su Firestore
    mock_document.set.assert_called_once()
