import asyncio
import os
import sys
from pathlib import Path

import httpx

BASE_URL = os.getenv("ANALYZER_URL", "http://127.0.0.1:8000")
SAMPLES = Path(__file__).parent / "samples"


def show(report: dict) -> None:
    for doc in report["documents"]:
        analysis = doc["analysis"]
        print(f"\n{'=' * 78}")
        print(f"{doc['source']}  —  {analysis['document_type']}")
        print(f"{doc['words']} words, {doc['chunks']} chunk(s), sentiment: {analysis['sentiment']}")
        print("=" * 78)
        print(f"\n{doc['summary']}\n")
        print(f"Topics: {', '.join(analysis['topics'])}")
        print(f"Entities: {', '.join(e['name'] for e in analysis['entities'])}")

        for label, key in [("Key points", "key_points"), ("Action items", "action_items"),
                           ("Risks", "risks"), ("Open questions", "open_questions")]:
            if analysis[key]:
                print(f"\n{label}:")
                for item in analysis[key]:
                    print(f"  - {item}")

    synthesis = report.get("synthesis")
    if synthesis:
        print(f"\n{'=' * 78}")
        print(f"CROSS-DOCUMENT SYNTHESIS  ({report['document_count']} documents)")
        print("=" * 78)
        print(f"\n{synthesis['overview']}\n")
        for label, key in [("Shared themes", "shared_themes"),
                           ("Contradictions", "contradictions"),
                           ("Combined action items", "combined_action_items")]:
            if synthesis[key]:
                print(f"{label}:")
                for item in synthesis[key]:
                    print(f"  - {item}")
                print()

    print(f"Report saved as: {report['report_id']}")


async def run(paths: list[Path]) -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300) as client:
        try:
            await client.get("/")
        except httpx.ConnectError:
            sys.exit(f"Server not reachable at {BASE_URL}. Start it with: uvicorn main:app --reload")

        files = [("files", (p.name, p.read_bytes())) for p in paths]
        print(f"Analyzing {len(files)} document(s): {', '.join(p.name for p in paths)}\n")

        resp = await client.post("/analyze", files=files)
        if resp.status_code != 200:
            sys.exit(f"Request failed [{resp.status_code}]: {resp.text}")
        show(resp.json())


if __name__ == "__main__":
    targets = [Path(a) for a in sys.argv[1:]] or sorted(
        p for p in SAMPLES.iterdir() if p.is_file()
    )
    missing = [p for p in targets if not p.exists()]
    if missing:
        sys.exit(f"Not found: {', '.join(str(p) for p in missing)}")
    asyncio.run(run(targets))