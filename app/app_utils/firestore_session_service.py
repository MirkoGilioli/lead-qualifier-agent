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

import time
import uuid
from typing import Any, Optional

from google.cloud import firestore
from opentelemetry import trace
from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.sessions.session import Session

# Otteniamo il tracer
tracer = trace.get_tracer(__name__)


class FirestoreSessionService(BaseSessionService):
    """Custom Session Service using Google Cloud Firestore."""

    def __init__(
        self,
        project_id: str,
        database_id: str,
        collection_name: str = "chat_sessions",
    ):
        """Initializes the Firestore session service."""
        self.client = firestore.AsyncClient(project=project_id, database=database_id)
        self.collection_name = collection_name

    def _tag_span_with_session(self, session_id: str):
        """Helper to tag the current OTel span with the session ID."""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            current_span.set_attribute("session_id", session_id)

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        """Creates a new session in Firestore."""
        sid = session_id or str(uuid.uuid4())
        self._tag_span_with_session(sid)
        
        session = Session(
            id=sid,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            last_update_time=time.time(),
        )
        
        doc_ref = self.client.collection(self.collection_name).document(sid)
        await doc_ref.set(session.model_dump(by_alias=True))
        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        """Gets a session from Firestore."""
        self._tag_span_with_session(session_id)
        
        doc_ref = self.client.collection(self.collection_name).document(session_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            return None
            
        data = doc.to_dict()
        if data.get("appName") != app_name or data.get("userId") != user_id:
            return None
            
        return Session.model_validate(data)

    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        """Lists sessions from Firestore."""
        query = self.client.collection(self.collection_name).where("appName", "==", app_name)
        if user_id:
            query = query.where("userId", "==", user_id)
            
        docs = query.stream()
        sessions = []
        async for doc in docs:
            sessions.append(Session.model_validate(doc.to_dict()))
            
        return ListSessionsResponse(sessions=sessions)

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        """Deletes a session from Firestore."""
        doc_ref = self.client.collection(self.collection_name).document(session_id)
        await doc_ref.delete()

    # We also need to override append_event to persist the update
    async def append_event(self, session: Session, event: Any) -> Any:
        """Appends an event and persists the session state to Firestore."""
        # Use the base class logic to update the in-memory session object
        updated_event = await super().append_event(session, event)
        
        # Persist the whole session (including the new event) back to Firestore
        # For production with very long histories, you'd want a more granular update,
        # but for session state, this is the standard ADK pattern.
        session.last_update_time = time.time()
        doc_ref = self.client.collection(self.collection_name).document(session.id)
        await doc_ref.set(session.model_dump(by_alias=True))
        
        return updated_event
