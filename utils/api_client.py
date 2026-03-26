import asyncio
import json
import uuid
from typing import Any, AsyncGenerator

import httpx


class RandstadAgentClient:
    """Client for interacting with the Randstad Agent FastAPI application."""

    def __init__(self, base_url: str = "http://localhost:8000", app_name: str = "app"):
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def get_version(self) -> dict[str, Any]:
        """Get version information."""
        try:
            response = await self.client.get("/version")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def chat(self, message: str, user_id: str = "test-user", session_id: str | None = None) -> dict[str, Any]:
        """Send a message to the agent and get a complete response."""
        session_id = session_id or str(uuid.uuid4())
        url = f"/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        payload = {
            "appName": self.app_name,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}]
            },
            "streaming": False
        }
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def chat_stream(
        self, message: str, user_id: str = "test-user", session_id: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Send a message to the agent and stream the response."""
        session_id = session_id or str(uuid.uuid4())
        url = f"/apps/{self.app_name}/users/{user_id}/sessions/{session_id}"
        payload = {
            "appName": self.app_name,
            "userId": user_id,
            "sessionId": session_id,
            "newMessage": {
                "role": "user",
                "parts": [{"text": message}]
            },
            "streaming": True
        }
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        yield {"text": data}

    async def send_feedback(
        self, score: float, text: str = "", session_id: str | None = None
    ) -> dict[str, Any]:
        """Send feedback to the /feedback endpoint."""
        payload = {
            "score": score,
            "text": text,
            "session_id": session_id or str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
        }
        response = await self.client.post("/feedback", json=payload)
        response.raise_for_status()
        return response.json()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Randstad Agent API Client")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--app", default="app", help="App name")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Version command
    subparsers.add_parser("version", help="Get version info")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a message")
    chat_parser.add_argument("message", help="Message to send")
    chat_parser.add_argument("--user-id", default="test-user", help="User ID")
    chat_parser.add_argument("--session-id", help="Optional session ID")
    chat_parser.add_argument("--stream", action="store_true", help="Use streaming")

    # Feedback command
    feedback_parser = subparsers.add_parser("feedback", help="Send feedback")
    feedback_parser.add_argument("score", type=float, help="Feedback score")
    feedback_parser.add_argument("--text", default="", help="Feedback text")
    feedback_parser.add_argument("--session-id", help="Optional session ID")

    args = parser.parse_args()

    client = RandstadAgentClient(args.url, args.app)
    try:
        if args.command == "version":
            version = await client.get_version()
            print(json.dumps(version, indent=2))
        elif args.command == "chat":
            if args.stream:
                print("Streaming response:")
                async for chunk in client.chat_stream(args.message, args.user_id, args.session_id):
                    try:
                        # Handle ADK ServerContent structure
                        if "modelContent" in chunk:
                            for part in chunk["modelContent"].get("parts", []):
                                if "text" in part:
                                    print(part["text"], end="", flush=True)
                        elif "text" in chunk:
                            print(chunk["text"], end="", flush=True)
                    except Exception:
                        pass
                print()
            else:
                response = await client.chat(args.message, args.user_id, args.session_id)
                # Try to extract text for cleaner output
                try:
                    if "events" in response and len(response["events"]) > 0:
                        last_event = response["events"][-1]
                        if "modelContent" in last_event:
                            for part in last_event["modelContent"].get("parts", []):
                                if "text" in part:
                                    print(part["text"])
                        else:
                            print(json.dumps(response, indent=2))
                    else:
                        print(json.dumps(response, indent=2))
                except Exception:
                    print(json.dumps(response, indent=2))
        elif args.command == "feedback":
            response = await client.send_feedback(args.score, args.text, args.session_id)
            print(json.dumps(response, indent=2))
        else:
            parser.print_help()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
