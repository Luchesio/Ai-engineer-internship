from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative", "mixed"]


class Entity(BaseModel):
    name: str = Field(..., description="Name exactly as it appears in the document")
    type: str = Field(..., description="person, organization, product, location, date, or other")
    mention: str = Field(..., description="Why this entity matters, in one short clause")


class DocumentAnalysis(BaseModel):
    document_type: str = Field(..., description="e.g. meeting notes, incident report, survey, contract")
    topics: list[str] = Field(..., description="3-6 topics the document actually covers")
    entities: list[Entity] = Field(..., description="Up to 8 notable entities")
    key_points: list[str] = Field(..., description="3-7 substantive takeaways")
    action_items: list[str] = Field(..., description="Concrete next steps stated or clearly implied; empty if none")
    risks: list[str] = Field(..., description="Risks, blockers, or concerns raised; empty if none")
    sentiment: Sentiment
    sentiment_rationale: str = Field(..., description="One sentence grounding the sentiment label")
    open_questions: list[str] = Field(..., description="Questions the document leaves unanswered; empty if none")


class DocumentReport(BaseModel):
    source: str
    characters: int
    words: int
    chunks: int
    summary: str
    analysis: DocumentAnalysis


class CorpusSynthesis(BaseModel):
    overview: str = Field(..., description="What the documents collectively say, in 3-5 sentences")
    shared_themes: list[str] = Field(..., description="Themes appearing in more than one document")
    contradictions: list[str] = Field(..., description="Points where documents disagree; empty if none")
    combined_action_items: list[str] = Field(..., description="Deduplicated, prioritised next steps across all documents")


class CorpusReport(BaseModel):
    report_id: str
    document_count: int
    documents: list[DocumentReport]
    synthesis: CorpusSynthesis | None = None


class InlineDocument(BaseModel):
    source: str = Field(default="inline.txt")
    text: str = Field(..., min_length=1)


class AnalyzeTextRequest(BaseModel):
    documents: list[InlineDocument] = Field(..., min_length=1)