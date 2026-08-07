import os
import uuid

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from documents import Workspace
from models import (
    DocumentInfo,
    ExtractionSummary,
    Insight,
    InsightReport,
    RunStats,
)
from tools import build_tools

load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
MAX_STEPS = int(os.getenv("MAX_AGENT_STEPS", "14"))

SYSTEM_PROMPT = """You are a document analyst. You cannot see the documents directly — you can \
only reach them through tools, so every claim you make must come from something you actually read.

Work in this order:
1. Call list_documents to see what exists and how it is segmented.
2. Decide which segments matter. Use search_documents to locate specific topics, amounts, dates, \
or obligations rather than reading everything.
3. Call read_segments on the segments that look substantive, then record what you find.
4. Call record_insight once per distinct finding, with a quote copied exactly from the segment you \
just read. If a recorded insight comes back UNVERIFIED, read that segment again and re-record it \
with the exact wording.

What counts as an insight: concrete facts, figures and amounts, dates and deadlines, obligations \
and commitments, risks, decisions taken, questions the document leaves open, and contradictions \
either inside one document or between two documents. Record contradictions only when two passages \
genuinely conflict on the same point, and cite the passage that shows the conflict.

Aim for 8-16 insights across the whole set, weighted toward whatever is most consequential. \
Do not record trivia, and do not record anything you have not read. Stop calling tools once you \
have covered the substantive material, then reply with a short plain-text note on what you covered \
and anything you deliberately skipped."""

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write the final summary of a document set from an analyst's verified notes. "
            "Use only what the notes contain. Keep names, figures, and dates exactly as recorded, "
            "and return empty lists rather than inventing entries for fields the notes do not cover.",
        ),
        ("human", "Documents:\n{documents}\n\nAnalyst notes:\n{notes}\n\nRequested focus: {focus}"),
    ]
)


def build_agent():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. See README for setup.")
    return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)


def _summary_chain(model: ChatOpenAI):
    return SUMMARY_PROMPT | model.with_structured_output(ExtractionSummary)


async def run_agent(model: ChatOpenAI, ws: Workspace, focus: str | None = None) -> InsightReport:
    tools = build_tools(ws)
    tools_by_name = {t.name: t for t in tools}
    bound = model.bind_tools(tools)

    task = f"Analyse the loaded documents and extract structured insights.\n\nFocus: {focus}" if focus else (
        "Analyse the loaded documents and extract structured insights."
    )
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(task)]

    steps = 0
    tool_calls = 0
    tools_used: dict[str, int] = {}

    while steps < MAX_STEPS:
        steps += 1
        ai: AIMessage = await bound.ainvoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            break

        for call in ai.tool_calls:
            tool_calls += 1
            tools_used[call["name"]] = tools_used.get(call["name"], 0) + 1
            try:
                result = await tools_by_name[call["name"]].ainvoke(call["args"])
            except Exception as exc:
                result = f"Tool error: {exc}"
            messages.append(ToolMessage(str(result), tool_call_id=call["id"]))

    insights = [Insight(**item) for item in ws.insights]
    verified = [i for i in insights if i.verified]

    notes = "\n".join(
        f"- [{i.category}] {i.statement} ({i.doc_id} {i.location}, confidence {i.confidence})"
        for i in (verified or insights)
    ) or "No insights were recorded."

    documents = [
        DocumentInfo(
            doc_id=doc.doc_id,
            filename=doc.filename,
            kind=doc.kind,
            segments=len(doc.segments),
            words=doc.words,
            segments_read=sorted({i.location for i in insights if i.doc_id == doc.doc_id}),
        )
        for doc in ws.documents.values()
    ]

    summary = await _summary_chain(model).ainvoke(
        {
            "documents": "\n".join(f"{d.doc_id}: {d.filename} ({d.kind}, {d.words} words)" for d in documents),
            "notes": notes,
            "focus": focus or "none given — cover the documents broadly",
        }
    )

    by_category: dict[str, int] = {}
    for insight in insights:
        by_category[insight.category] = by_category.get(insight.category, 0) + 1

    return InsightReport(
        report_id=uuid.uuid4().hex[:12],
        focus=focus,
        documents=documents,
        summary=summary,
        insights=insights,
        insights_by_category=by_category,
        stats=RunStats(
            steps=steps,
            tool_calls=tool_calls,
            tools_used=tools_used,
            insights_recorded=len(insights),
            insights_verified=len(verified),
        ),
        trace=ws.tool_log,
    )