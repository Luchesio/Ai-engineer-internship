import io
import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}

SEGMENT_WORDS = 250
SNIPPET_CHARS = 320


class UnsupportedDocument(ValueError):
    pass


class Segment:
    def __init__(self, label: str, text: str):
        self.label = label
        self.text = text
        self.words = len(text.split())

    def preview(self, chars: int = 90) -> str:
        flat = " ".join(self.text.split())
        return flat[:chars] + ("…" if len(flat) > chars else "")


class Document:
    def __init__(self, doc_id: str, filename: str, kind: str, segments: list[Segment]):
        self.doc_id = doc_id
        self.filename = filename
        self.kind = kind
        self.segments = segments
        self.words = sum(s.words for s in segments)

    def segment(self, label: str) -> Segment | None:
        target = label.strip().lower()
        for seg in self.segments:
            if seg.label.lower() == target:
                return seg
        return None


def _pdf_segments(data: bytes) -> list[Segment]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    segments = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            segments.append(Segment(f"p{i}", text))
    return segments


def _text_segments(data: bytes) -> list[Segment]:
    text = data.decode("utf-8", errors="replace")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    segments, buffer, count = [], [], 0
    for para in paragraphs:
        size = len(para.split())
        if buffer and count + size > SEGMENT_WORDS:
            segments.append(Segment(f"s{len(segments) + 1}", "\n\n".join(buffer)))
            buffer, count = [], 0
        buffer.append(para)
        count += size
    if buffer:
        segments.append(Segment(f"s{len(segments) + 1}", "\n\n".join(buffer)))
    return segments


LOADERS = {
    ".pdf": ("pdf", _pdf_segments),
    ".txt": ("text", _text_segments),
    ".md": ("markdown", _text_segments),
    ".markdown": ("markdown", _text_segments),
}


def load_bytes(doc_id: str, filename: str, data: bytes) -> Document:
    suffix = Path(filename).suffix.lower()
    if suffix not in LOADERS:
        raise UnsupportedDocument(
            f"'{suffix or filename}' is not supported. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    kind, loader = LOADERS[suffix]
    segments = loader(data)
    if not segments:
        raise UnsupportedDocument(
            f"No readable text in '{filename}'. Scanned PDFs need OCR before this agent can read them."
        )
    return Document(doc_id, filename, kind, segments)


def load_text(doc_id: str, filename: str, text: str) -> Document:
    segments = _text_segments(text.encode("utf-8"))
    if not segments:
        raise UnsupportedDocument(f"'{filename}' contained no text.")
    return Document(doc_id, filename, "text", segments)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


class Workspace:
    def __init__(self, documents: list[Document]):
        self.documents = {d.doc_id: d for d in documents}
        self.insights: list[dict] = []
        self.tool_log: list[str] = []

    def outline(self) -> str:
        lines = []
        for doc in self.documents.values():
            lines.append(
                f"{doc.doc_id} | {doc.filename} | {doc.kind} | "
                f"{len(doc.segments)} segments | {doc.words} words"
            )
            for seg in doc.segments:
                lines.append(f"    {seg.label} ({seg.words}w): {seg.preview()}")
        return "\n".join(lines)

    def read(self, doc_id: str, labels: list[str]) -> str:
        doc = self.documents.get(doc_id)
        if not doc:
            return f"No document '{doc_id}'. Available: {', '.join(self.documents)}"

        blocks = []
        for label in labels:
            seg = doc.segment(label)
            if seg is None:
                blocks.append(f"[{label}] not found in {doc_id}")
            else:
                blocks.append(f"--- {doc_id} {seg.label} ---\n{seg.text}")
        return "\n\n".join(blocks)

    def search(self, query: str, doc_id: str | None = None, limit: int = 6) -> str:
        terms = [t for t in re.findall(r"[a-z0-9$%.,-]+", query.lower()) if len(t) > 2]
        if not terms:
            return "Query too short. Use meaningful keywords."

        targets = [self.documents[doc_id]] if doc_id in self.documents else list(self.documents.values())
        hits = []
        for doc in targets:
            for seg in doc.segments:
                haystack = seg.text.lower()
                score = sum(haystack.count(term) for term in terms)
                matched = sum(1 for term in terms if term in haystack)
                if score:
                    hits.append((matched, score, doc, seg, terms))

        if not hits:
            return f"No matches for '{query}'" + (f" in {doc_id}." if doc_id else " in any document.")

        hits.sort(key=lambda h: (h[0], h[1]), reverse=True)
        lines = []
        for matched, score, doc, seg, terms in hits[:limit]:
            position = min(
                (seg.text.lower().find(t) for t in terms if t in seg.text.lower()),
                default=0,
            )
            start = max(position - SNIPPET_CHARS // 3, 0)
            snippet = " ".join(seg.text[start : start + SNIPPET_CHARS].split())
            lines.append(f"[{doc.doc_id} {seg.label}] score {score}: …{snippet}…")
        return "\n\n".join(lines)

    def verify(self, doc_id: str, location: str, evidence: str) -> bool:
        doc = self.documents.get(doc_id)
        if not doc:
            return False
        seg = doc.segment(location)
        pool = seg.text if seg else "\n".join(s.text for s in doc.segments)
        return normalize(evidence) in normalize(pool)