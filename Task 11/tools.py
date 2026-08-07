from langchain_core.tools import tool

from documents import Workspace
from models import Category, Confidence

MAX_SEGMENTS_PER_READ = 4


def build_tools(ws: Workspace) -> list:
    @tool
    def list_documents() -> str:
        """List every loaded document with its segment labels, sizes, and a preview of each
        segment. Always call this first — it is the only way to learn what is available."""
        ws.tool_log.append("list_documents()")
        return ws.outline()

    @tool
    def search_documents(query: str, doc_id: str = "") -> str:
        """Find segments containing given keywords. Returns the location and a snippet for each
        hit. Use this to locate a topic before reading. Leave doc_id empty to search everything."""
        ws.tool_log.append(f"search_documents(query={query!r}, doc_id={doc_id or 'all'})")
        return ws.search(query, doc_id or None)

    @tool
    def read_segments(doc_id: str, labels: list[str]) -> str:
        """Read the full text of up to four segments, given their labels from list_documents or
        search_documents. Read a segment before recording any insight from it."""
        selected = labels[:MAX_SEGMENTS_PER_READ]
        ws.tool_log.append(f"read_segments(doc_id={doc_id!r}, labels={selected})")
        return ws.read(doc_id, selected)

    @tool
    def record_insight(
        category: Category,
        statement: str,
        evidence: str,
        doc_id: str,
        location: str,
        confidence: Confidence,
    ) -> str:
        """Save one structured insight. category is one of key_fact, figure, date, obligation,
        risk, decision, open_question, contradiction. evidence must be copied word for word from
        the segment you read; quotes that are not found in the source are flagged unverified."""
        ws.tool_log.append(f"record_insight({category}, {doc_id} {location})")
        verified = ws.verify(doc_id, location, evidence)
        ws.insights.append(
            {
                "category": category,
                "statement": statement,
                "evidence": evidence,
                "doc_id": doc_id,
                "location": location,
                "confidence": confidence,
                "verified": verified,
            }
        )
        status = "verified" if verified else "UNVERIFIED — quote not found there, re-read and record it again"
        return f"Recorded insight {len(ws.insights)} ({category}, {doc_id} {location}): {status}."

    return [list_documents, search_documents, read_segments, record_insight]