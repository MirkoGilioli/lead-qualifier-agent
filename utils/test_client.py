import asyncio
import json
from api_client import RandstadAgentClient

async def test():
    client = RandstadAgentClient("http://localhost:8003", "app")
    
    print("--- Testing Version ---")
    version = await client.get_version()
    print(json.dumps(version, indent=2))
    
    print("\n--- Testing Chat (Non-Streaming) ---")
    response = await client.chat("Ciao, chi sei?")
    print("Full Response Keys:", list(response.keys()))
    if "events" in response:
        print(f"Events count: {len(response['events'])}")
        for i, event in enumerate(response['events']):
            print(f"Event {i}: {event.get('type', 'unknown')}")
            if "modelContent" in event:
                print(f"  Content: {event['modelContent']}")
    
    print("\n--- Testing Chat (Streaming) ---")
    print("Chunks:")
    async for chunk in client.chat_stream("Raccontami una barzelletta"):
        print(f"Chunk: {json.dumps(chunk)}")
    
    print("\n--- Testing Feedback ---")
    feedback = await client.send_feedback(4.5, "Ottimo lavoro!")
    print(json.dumps(feedback, indent=2))
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test())
