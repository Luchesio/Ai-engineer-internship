"""Task 8 — Accuracy test harness.

Runs the test cases in test_cases.json against the Task 7 chatbot,
scores each answer against the expected result, and writes
results.csv plus "Accuracy Test Report.pdf".

Usage:
    python run_accuracy_test.py           # live run (needs OPENAI_API_KEY)
    python run_accuracy_test.py --mock    # pipeline check with simulated answers
"""

import argparse
import asyncio
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK7 = HERE.parent / "Task 7"

MOCK_ANSWERS = {
    "GK-01": "The capital of France is Paris.",
    "GK-02": "Romeo and Juliet was written by William Shakespeare.",
    "GK-03": "The chemical symbol for gold is Au.",
    "GK-04": "Jupiter is the largest planet in our solar system.",
    "GK-05": "There are seven continents on Earth.",
    "MR-01": "15% of 240 is 36.",
    "MR-02": "A leap year has 366 days.",
    "MR-03": "12 multiplied by 12 is 144.",
    "MR-04": "The next prime number after 13 is 17.",
    "TW-01": "It's currently 29.4°C in Lagos, Nigeria — partly cloudy with 74% humidity.",
    "TW-02": "Tokyo is currently 31.1°C, mainly clear, humidity 60%.",
    "TW-03": "I could not find a place called 'Zzyzxville', so I can't report its weather.",
    "TC-01": "100 USD is about 92.15 EUR at the current rate.",
    "TC-02": "50 USD is approximately 76,500 NGN at today's rate.",
    "TC-03": "I couldn't convert that — 'XQZ' is not a valid currency code. Please check it.",
    "MEM-01": "Your name is Ada.",
    "MEM-02": "Your meeting is at 3pm on Friday.",
    "RB-01": "The Moon does not have a president — it has no government or population.",
}


def evaluate(answer: str, checks: dict) -> tuple[bool, list[str]]:
    text = answer.lower()
    failures = []

    for kw in checks.get("contains_all", []):
        if kw.lower() not in text:
            failures.append(f"missing required keyword '{kw}'")

    any_kws = checks.get("contains_any", [])
    if any_kws and not any(kw.lower() in text for kw in any_kws):
        failures.append(f"none of the expected keywords present: {any_kws}")

    for kw in checks.get("not_contains", []):
        if kw.lower() in text:
            failures.append(f"forbidden keyword '{kw}' present")

    pattern = checks.get("regex")
    if pattern and not re.search(pattern, answer):
        failures.append(f"pattern '{pattern}' not matched")

    absent = checks.get("regex_absent")
    if absent and re.search(absent, answer):
        failures.append(f"pattern '{absent}' should not appear")

    return (not failures), failures


async def run_case(case: dict, mock: bool, model) -> dict:
    if mock:
        answer = MOCK_ANSWERS.get(case["id"], "")
    else:
        sys.path.insert(0, str(TASK7))
        from chatbot import ask, reset_session

        session = f"eval-{case['id']}"
        reset_session(session)
        answer = ""
        for turn in case["turns"]:
            answer = await ask(model, turn, session)
        reset_session(session)

    passed, failures = evaluate(answer, case["checks"])
    return {
        "id": case["id"],
        "category": case["category"],
        "question": " → ".join(case["turns"]),
        "expected": case["expected_answer"],
        "actual": answer.strip(),
        "passed": passed,
        "failures": "; ".join(failures),
    }


async def run_suite(mock: bool) -> list[dict]:
    cases = json.loads((HERE / "test_cases.json").read_text(encoding="utf-8"))
    model = None
    if not mock:
        sys.path.insert(0, str(TASK7))
        from chatbot import build_model

        model = build_model()

    results = []
    for case in cases:
        result = await run_case(case, mock, model)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['id']} ({result['category']})")
        results.append(result)
    return results


def write_csv(results: list[dict]) -> Path:
    path = HERE / "results.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    return path


def summarize(results: list[dict]) -> dict:
    total = len(results)
    passed = sum(r["passed"] for r in results)
    by_cat = {}
    for r in results:
        cat = by_cat.setdefault(r["category"], {"total": 0, "passed": 0})
        cat["total"] += 1
        cat["passed"] += r["passed"]
    return {"total": total, "passed": passed, "accuracy": passed / total, "by_category": by_cat}


def write_pdf(results: list[dict], summary: dict, mock: bool) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    path = HERE / "Accuracy Test Report.pdf"
    styles = getSampleStyleSheet()
    h1 = styles["Title"]
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14)
    body = ParagraphStyle("Body", parent=styles["Normal"], leading=14, spaceAfter=6)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10)

    run_label = (
        "MOCK RUN — simulated chatbot responses used to validate the pipeline. "
        "Re-run <b>python run_accuracy_test.py</b> with a live OPENAI_API_KEY to regenerate this report with real results."
        if mock
        else "Live run against the Task 7 chatbot (gpt-4o-mini via LangChain tool calling)."
    )
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3864")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f8")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
    )

    story = [
        Paragraph("Task 8 — Chatbot Accuracy Test Report", h1),
        Paragraph(f"Run date: {run_date} &nbsp;&nbsp;|&nbsp;&nbsp; {run_label}", small),
        Spacer(1, 10),
        Paragraph("1. Objective", h2),
        Paragraph(
            "Measure how accurately the Task 7 chatbot answers user questions by comparing its "
            "responses against a suite of test cases with predefined expected answers. The suite "
            "covers factual knowledge, arithmetic reasoning, live tool calls (weather and currency), "
            "conversation memory, and robustness against invalid or trick inputs.",
            body,
        ),
        Paragraph("2. System Under Test", h2),
        Paragraph(
            "The Task 7 chatbot: an OpenAI gpt-4o-mini model (temperature 0.2) bound via LangChain to "
            "two live tools — <b>get_weather</b> (Open-Meteo) and <b>convert_currency</b> (open.er-api.com) — "
            "with per-session conversation history. The harness calls the chatbot's <b>ask()</b> function "
            "directly, one fresh session per test case, so cases cannot contaminate each other.",
            body,
        ),
        Paragraph("3. Methodology", h2),
        Paragraph(
            "Each test case defines one or more user turns, a human-readable expected answer, and a set of "
            "machine-checkable assertions. A case <b>passes</b> only if every assertion holds. Because tool-backed "
            "answers change with real-world data (today's temperature, today's exchange rate), those cases assert "
            "structure rather than a fixed number: the answer must name the right entity and contain a value of the "
            "right shape sourced from the tool, and must <i>not</i> contain fabricated values when the tool fails.",
            body,
        ),
    ]

    method_rows = [
        ["Check", "Passes when"],
        ["contains_all", "Every listed keyword appears in the answer (case-insensitive)"],
        ["contains_any", "At least one listed keyword appears"],
        ["not_contains", "None of the listed keywords appear"],
        ["regex", "The pattern matches (e.g. a temperature like 29.4°C, or the exact number 36)"],
        ["regex_absent", "The pattern does not match (guards against invented values)"],
    ]
    t = Table([[Paragraph(c, small) for c in row] for row in method_rows], colWidths=[3 * cm, 13.5 * cm])
    t.setStyle(header)
    story += [t, Spacer(1, 6)]

    story.append(Paragraph("4. Results Summary", h2))
    acc = summary["accuracy"]
    story.append(
        Paragraph(
            f"<b>Overall accuracy: {summary['passed']}/{summary['total']} test cases passed "
            f"({acc:.0%}).</b>",
            body,
        )
    )
    cat_rows = [["Category", "Passed", "Total", "Accuracy"]]
    for cat, s in summary["by_category"].items():
        cat_rows.append([cat.replace("_", " ").title(), str(s["passed"]), str(s["total"]), f"{s['passed'] / s['total']:.0%}"])
    t = Table([[Paragraph(c, small) for c in row] for row in cat_rows], colWidths=[6 * cm, 3 * cm, 3 * cm, 4.5 * cm])
    t.setStyle(header)
    story += [t, Spacer(1, 6)]

    story.append(Paragraph("5. Detailed Results", h2))
    detail_rows = [["ID", "Question", "Expected", "Chatbot Answer", "Result"]]
    for r in results:
        detail_rows.append(
            [
                r["id"],
                r["question"],
                r["expected"],
                r["actual"][:320] + ("…" if len(r["actual"]) > 320 else ""),
                "PASS" if r["passed"] else "FAIL — " + r["failures"],
            ]
        )
    t = Table(
        [[Paragraph(str(c), small) for c in row] for row in detail_rows],
        colWidths=[1.4 * cm, 4.4 * cm, 4.2 * cm, 5.0 * cm, 1.5 * cm],
        repeatRows=1,
    )
    t.setStyle(header)
    for i, r in enumerate(results, start=1):
        color = colors.HexColor("#1e7a34") if r["passed"] else colors.HexColor("#b02a2a")
        t.setStyle(TableStyle([("TEXTCOLOR", (4, i), (4, i), color)]))
    story += [t, Spacer(1, 6)]

    failures = [r for r in results if not r["passed"]]
    story.append(Paragraph("6. Analysis", h2))
    if failures:
        story.append(
            Paragraph(
                f"{len(failures)} case(s) failed: " + ", ".join(f"{r['id']} ({r['failures']})" for r in failures) + ". "
                "Failures in the tool categories usually indicate the model answered without calling the tool or "
                "invented a value; keyword failures in knowledge categories usually indicate a wrong or evasive answer.",
                body,
            )
        )
    else:
        story.append(
            Paragraph(
                "All test cases passed. The chatbot answered factual and arithmetic questions correctly, grounded "
                "weather and currency answers in live tool results, recalled earlier turns from session memory, and "
                "declined gracefully instead of hallucinating when given an unknown place, an invalid currency code, "
                "or a nonsensical premise.",
                body,
            )
        )
    story.append(
        Paragraph(
            "Keyword and pattern assertions were chosen over exact-string matching because an LLM phrases the same "
            "correct answer differently on every run; asserting on the decisive fact keeps the evaluation deterministic "
            "while tolerating harmless wording variation.",
            body,
        )
    )

    story.append(Paragraph("7. Limitations & Next Steps", h2))
    story.append(
        Paragraph(
            "Keyword checks can be gamed by an answer that mentions the right word in a wrong sentence, and they cannot "
            "grade nuance or completeness. Natural extensions: score semantic similarity between answer and reference "
            "with the Task 5 embedding model, add an LLM-as-judge pass for open-ended answers, repeat each case N times "
            "to measure consistency, and track latency and token cost per case alongside accuracy.",
            body,
        )
    )

    SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title="Task 8 — Chatbot Accuracy Test Report",
    ).build(story)
    return path


def main():
    parser = argparse.ArgumentParser(description="Task 8 chatbot accuracy evaluation")
    parser.add_argument("--mock", action="store_true", help="use simulated answers (no API key needed)")
    args = parser.parse_args()

    results = asyncio.run(run_suite(mock=args.mock))
    summary = summarize(results)
    csv_path = write_csv(results)
    pdf_path = write_pdf(results, summary, mock=args.mock)

    print(f"\nAccuracy: {summary['passed']}/{summary['total']} ({summary['accuracy']:.0%})")
    print(f"Wrote {csv_path.name} and {pdf_path.name}")


if __name__ == "__main__":
    main()