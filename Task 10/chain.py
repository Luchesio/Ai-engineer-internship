import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_openai import ChatOpenAI

from loaders import chunk_text
from models import CorpusSynthesis, DocumentAnalysis, DocumentReport

load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "5"))
COLLAPSE_BATCH = int(os.getenv("COLLAPSE_BATCH", "5"))

MAP_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You compress one excerpt of a longer document. Capture its facts, figures, names, "
            "decisions, and stated concerns. Do not add anything that is not in the excerpt, and "
            "do not mention that this is an excerpt. Reply with dense prose under 150 words.",
        ),
        ("human", "Excerpt {index} of {total}:\n\n{chunk}"),
    ]
)

COLLAPSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You merge consecutive notes from one document into a single continuous note. "
            "Preserve every fact, figure, and name. Remove only repetition. Reply with prose.",
        ),
        ("human", "{notes}"),
    ]
)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You write the final summary of a document from working notes. Open with one sentence "
            "stating what the document is and what it is for, then cover its substance in flowing "
            "paragraphs. Keep concrete figures and names. Stay under 300 words. Use only what the "
            "notes contain, and never speculate.",
        ),
        ("human", "Document: {source}\n\nNotes:\n{condensed}"),
    ]
)

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You extract structured analysis from a document. Ground every field in the text: if "
            "the document states no action items, risks, or open questions, return empty lists "
            "rather than inventing them. Judge sentiment by the document's own tone toward its "
            "subject, not by how pleasant the topic is.",
        ),
        ("human", "Document: {source}\n\nContent:\n{condensed}"),
    ]
)

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You compare several documents that were summarised independently. Identify what they "
            "share, where they disagree, and what should happen next across all of them. Only "
            "report a contradiction when two documents genuinely conflict on the same point.",
        ),
        ("human", "{briefs}"),
    ]
)


def _model(temperature: float | None = None) -> ChatOpenAI:
    return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE if temperature is None else temperature)


def build_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. See README for setup.")

    model = _model()
    map_chain = MAP_PROMPT | model | StrOutputParser()
    collapse_chain = COLLAPSE_PROMPT | model | StrOutputParser()
    summary_chain = SUMMARY_PROMPT | model | StrOutputParser()
    analysis_chain = ANALYSIS_PROMPT | model.with_structured_output(DocumentAnalysis)
    synthesis_chain = SYNTHESIS_PROMPT | model.with_structured_output(CorpusSynthesis)

    async def condense(payload: dict) -> dict:
        chunks = payload["chunks"]
        if len(chunks) == 1:
            return {**payload, "condensed": chunks[0]}

        total = len(chunks)
        notes = await map_chain.abatch(
            [{"chunk": chunk, "index": i, "total": total} for i, chunk in enumerate(chunks, 1)],
            config={"max_concurrency": MAX_CONCURRENCY},
        )

        while len(notes) > COLLAPSE_BATCH:
            batches = [notes[i : i + COLLAPSE_BATCH] for i in range(0, len(notes), COLLAPSE_BATCH)]
            notes = await collapse_chain.abatch(
                [{"notes": "\n\n".join(batch)} for batch in batches],
                config={"max_concurrency": MAX_CONCURRENCY},
            )

        return {**payload, "condensed": "\n\n".join(notes)}

    document_chain = RunnableLambda(condense) | RunnableParallel(
        summary=summary_chain,
        analysis=analysis_chain,
    )

    return {"document": document_chain, "synthesis": synthesis_chain}


async def analyze_document(chain: dict, source: str, text: str) -> DocumentReport:
    chunks = chunk_text(text)
    result = await chain["document"].ainvoke({"source": source, "chunks": chunks})
    return DocumentReport(
        source=source,
        characters=len(text),
        words=len(text.split()),
        chunks=len(chunks),
        summary=result["summary"],
        analysis=result["analysis"],
    )


async def synthesize(chain: dict, reports: list[DocumentReport]) -> CorpusSynthesis:
    briefs = "\n\n".join(
        f"### Document {i}: {r.source}\n"
        f"Type: {r.analysis.document_type}\n"
        f"Sentiment: {r.analysis.sentiment}\n"
        f"Topics: {', '.join(r.analysis.topics)}\n"
        f"Summary: {r.summary}\n"
        f"Key points: {'; '.join(r.analysis.key_points)}\n"
        f"Action items: {'; '.join(r.analysis.action_items) or 'none'}\n"
        f"Risks: {'; '.join(r.analysis.risks) or 'none'}"
        for i, r in enumerate(reports, 1)
    )
    return await chain["synthesis"].ainvoke({"briefs": briefs})