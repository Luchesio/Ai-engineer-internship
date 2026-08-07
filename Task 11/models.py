from typing import Literal

from pydantic import BaseModel, Field

Category = Literal[
    "key_fact",
    "figure",
    "date",
    "obligation",
    "risk",
    "decision",
    "open_question",
    "contradiction",
]

Confidence = Literal["high", "medium", "low"]


class Insight(BaseModel):
    category: Category
    statement: str = Field(..., description="The insight in one self-contained sentence")
    evidence: str = Field(..., description="Verbatim quote from the document that supports it")
    doc_id: str
    location: str = Field(..., description="Segment label the evidence came from, e.g. p3 or s2")
    confidence: Confidence
    verified: bool = Field(
        default=False, description="True when the quote was found in the cited segment"
    )


class Entity(BaseModel):
    name: str
    type: str = Field(..., description="person, organization, product, location, or other")
    role: str = Field(..., description="Why this entity matters, in one short clause")


class TimelineItem(BaseModel):
    date: str
    event: str


class ExtractionSummary(BaseModel):
    title: str = Field(..., description="A short title for this set of documents")
    document_types: list[str] = Field(..., description="What each document is, in order")
    overview: str = Field(..., description="What the documents collectively say, in 3-5 sentences")
    entities: list[Entity] = Field(..., description="Up to 8 notable entities")
    timeline: list[TimelineItem] = Field(..., description="Dated events in chronological order; empty if none")
    open_questions: list[str] = Field(..., description="What the documents leave unresolved; empty if none")
    recommended_actions: list[str] = Field(..., description="Prioritised next steps; empty if none")


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    kind: str
    segments: int
    words: int
    segments_read: list[str] = Field(default_factory=list)


class RunStats(BaseModel):
    steps: int
    tool_calls: int
    tools_used: dict[str, int]
    insights_recorded: int
    insights_verified: int


class InsightReport(BaseModel):
    report_id: str
    focus: str | None = None
    documents: list[DocumentInfo]
    summary: ExtractionSummary
    insights: list[Insight]
    insights_by_category: dict[str, int]
    stats: RunStats
    trace: list[str] = Field(..., description="Ordered log of the agent's tool calls")


class InlineDocument(BaseModel):
    filename: str = Field(default="inline.txt")
    text: str = Field(..., min_length=1)


class ExtractTextRequest(BaseModel):
    documents: list[InlineDocument] = Field(..., min_length=1)
    focus: str | None = None