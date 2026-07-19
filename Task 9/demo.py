import asyncio
import os
import sys
import httpx

BASE_URL = os.getenv("CHATBOT_URL", "http://127.0.0.1:8000")

TURNS = [
    "Hi! My name is Ada, I live in Lagos, and my favourite language is Python.",
    "I'm building a FastAPI chatbot for a work assignment.",
    "What's my name, and where do I live?",
    "Which language should I use for the assignment, given what I told you I like?",
    "Summarise everything you know about me from this conversation.",
]


async def run():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        try:
            await client.get("/")
        except httpx.ConnectError:
            sys.exit(f"Server not reachable at {BASE_URL}. Start it with: uvicorn main:app --reload")

        session_id = None
        for i, question in enumerate(TURNS, 1):
            payload = {"question": question}
            if session_id:
                payload["session_id"] = session_id
            resp = await client.post("/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            session_id = data["session_id"]
            print(f"\n--- Turn {i} (session: {session_id}) ---")
            print(f"User: {question}")
            print(f"Bot:  {data['answer']}")

        resp = await client.get(f"/sessions/{session_id}/history")
        messages = resp.json()["messages"]
        print(f"\n=== Stored transcript: {len(messages)} messages persisted for '{session_id}' ===")
        print("Restart the server and re-run this demo with the same session to prove")
        print(f"persistence:  CHATBOT_SESSION={session_id}")


async def resume(session_id: str):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        resp = await client.post(
            "/chat",
            json={"question": "Do you still remember my name and city?", "session_id": session_id},
        )
        resp.raise_for_status()
        print(f"Bot: {resp.json()['answer']}")


if __name__ == "__main__":
    existing = os.getenv("CHATBOT_SESSION")
    asyncio.run(resume(existing) if existing else run())