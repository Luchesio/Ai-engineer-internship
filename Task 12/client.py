import asyncio
import json
import os
import sys

import httpx

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")

TURNS = [
    "Hi, my name is Ada and I work in Lagos.",
    "I'm building a REST API that wraps a chatbot.",
    "What is my name, and what am I building?",
]


def headers() -> dict:
    return {"X-API-Key": API_KEY} if API_KEY else {}


def unwrap(resp: httpx.Response) -> dict:
    body = resp.json()
    if not body["success"]:
        error = body["error"]
        sys.exit(f"[{resp.status_code}] {error['code']}: {error['message']}\n{json.dumps(error.get('details'), indent=2)}")
    return body


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers(), timeout=120) as client:
        try:
            health = unwrap(await client.get("/healthz"))
        except httpx.ConnectError:
            sys.exit(f"Server not reachable at {BASE_URL}. Start it with: ./run.sh")

        info = health["data"]
        print(f"Connected to {BASE_URL} — v{info['version']}, model {info['model']}\n")

        session_id = None
        for i, message in enumerate(TURNS, 1):
            payload = {"message": message}
            if session_id:
                payload["session_id"] = session_id

            body = unwrap(await client.post("/v1/chat", json=payload))
            data, meta = body["data"], body["meta"]
            session_id = data["session_id"]

            print(f"--- turn {i} | session {session_id} | {meta['duration_ms']} ms | "
                  f"{data['usage']['total_tokens']} tokens ---")
            print(f"user: {message}")
            print(f"bot:  {data['reply']}\n")

        print("--- streaming ---")
        print("user: Summarise what you know about me.")
        print("bot:  ", end="", flush=True)
        async with client.stream(
            "POST", "/v1/chat/stream",
            json={"message": "Summarise what you know about me.", "session_id": session_id},
        ) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event["type"] == "token":
                    print(event["text"], end="", flush=True)
                elif event["type"] == "error":
                    print(f"\n[stream error] {event['message']}")
        print("\n")

        print("--- error shape (empty message) ---")
        resp = await client.post("/v1/chat", json={"message": ""})
        print(f"HTTP {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))

        history = unwrap(await client.get(f"/v1/sessions/{session_id}"))["data"]
        print(f"\n{history['message_count']} messages stored for session {session_id}")

        stats = unwrap(await client.get("/v1/metrics"))["data"]
        print(f"{stats['requests_total']} requests, {stats['errors_total']} errors, "
              f"{stats['average_latency_ms']} ms average")


if __name__ == "__main__":
    asyncio.run(main())