import asyncio
import os
import sys
from pathlib import Path

import httpx

BASE_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8000")
SAMPLES = Path(__file__).parent / "samples"
FOCUS = os.getenv("AGENT_FOCUS")

LABELS = {
    "key_fact": "FACT",
    "figure": "FIGURE",
    "date": "DATE",
    "obligation": "OBLIGATION",
    "risk": "RISK",
    "decision": "DECISION",
    "open_question": "QUESTION",
    "contradiction": "CONFLICT",
}


def show(report: dict) -> None:
    summary = report["summary"]
    print(f"\n{'=' * 78}")
    print(summary["title"])
    print("=" * 78)
    print(f"\n{summary['overview']}\n")

    for doc in report["documents"]:
        read = ", ".join(doc["segments_read"]) or "none"
        print(f"  {doc['doc_id']}  {doc['filename']}  ({doc['kind']}, {doc['words']}w, "
              f"{doc['segments']} segments, cited: {read})")

    print(f"\n{'-' * 78}\nINSIGHTS ({len(report['insights'])})\n{'-' * 78}")
    for item in report["insights"]:
        flag = "" if item["verified"] else "  [unverified quote]"
        print(f"\n[{LABELS.get(item['category'], item['category'].upper())}] "
              f"({item['doc_id']} {item['location']}, {item['confidence']}){flag}")
        print(f"  {item['statement']}")
        print(f"  > {' '.join(item['evidence'].split())[:180]}")

    for label, key in [("Entities", "entities"), ("Timeline", "timeline"),
                       ("Open questions", "open_questions"),
                       ("Recommended actions", "recommended_actions")]:
        values = summary[key]
        if not values:
            continue
        print(f"\n{label}:")
        for value in values:
            if key == "entities":
                print(f"  - {value['name']} ({value['type']}) — {value['role']}")
            elif key == "timeline":
                print(f"  - {value['date']}: {value['event']}")
            else:
                print(f"  - {value}")

    stats = report["stats"]
    print(f"\n{'-' * 78}")
    print(f"{stats['steps']} steps, {stats['tool_calls']} tool calls "
          f"({', '.join(f'{k}×{v}' for k, v in stats['tools_used'].items())}), "
          f"{stats['insights_verified']}/{stats['insights_recorded']} quotes verified")
    print("\nAgent trace:")
    for i, entry in enumerate(report["trace"], 1):
        print(f"  {i:2}. {entry}")
    print(f"\nReport saved as: {report['report_id']}")


async def run(paths: list[Path]) -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=600) as client:
        try:
            await client.get("/")
        except httpx.ConnectError:
            sys.exit(f"Server not reachable at {BASE_URL}. Start it with: uvicorn main:app --reload")

        files = [("files", (p.name, p.read_bytes())) for p in paths]
        data = {"focus": FOCUS} if FOCUS else None
        print(f"Extracting from {len(files)} document(s): {', '.join(p.name for p in paths)}")
        if FOCUS:
            print(f"Focus: {FOCUS}")

        resp = await client.post("/extract", files=files, data=data)
        if resp.status_code != 200:
            sys.exit(f"Request failed [{resp.status_code}]: {resp.text}")
        show(resp.json())


if __name__ == "__main__":
    targets = [Path(a) for a in sys.argv[1:]] or sorted(p for p in SAMPLES.iterdir() if p.is_file())
    missing = [p for p in targets if not p.exists()]
    if missing:
        sys.exit(f"Not found: {', '.join(str(p) for p in missing)}")
    asyncio.run(run(targets))