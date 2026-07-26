import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile

from chain import MAX_CONCURRENCY, MODEL_NAME, analyze_document, build_chain, synthesize
from loaders import SUPPORTED_EXTENSIONS, UnsupportedDocument, extract_text
from models import AnalyzeTextRequest, CorpusReport

MAX_FILE_BYTES = 5 * 1024 * 1024

chain = None
reports: dict[str, CorpusReport] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    chain = build_chain()
    yield


app = FastAPI(title="Document Summarization & Analysis Chain", lifespan=lifespan)


async def run_pipeline(documents: list[tuple[str, str]]) -> CorpusReport:
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def one(source: str, text: str):
        async with semaphore:
            return await analyze_document(chain, source, text)

    results = await asyncio.gather(*(one(source, text) for source, text in documents))
    synthesis = await synthesize(chain, results) if len(results) > 1 else None

    report = CorpusReport(
        report_id=uuid.uuid4().hex[:12],
        document_count=len(results),
        documents=results,
        synthesis=synthesis,
    )
    reports[report.report_id] = report
    return report


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "POST files to /analyze or raw text to /analyze/text.",
        "model": MODEL_NAME,
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "max_file_mb": MAX_FILE_BYTES // (1024 * 1024),
    }


@app.post("/analyze", response_model=CorpusReport)
async def analyze(files: list[UploadFile] = File(...)):
    documents = []
    for upload in files:
        data = await upload.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(413, f"'{upload.filename}' exceeds the {MAX_FILE_BYTES // 1024 // 1024} MB limit")
        try:
            documents.append((upload.filename, extract_text(upload.filename, data)))
        except UnsupportedDocument as exc:
            raise HTTPException(415, str(exc))

    try:
        return await run_pipeline(documents)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/analyze/text", response_model=CorpusReport)
async def analyze_text(req: AnalyzeTextRequest):
    try:
        return await run_pipeline([(d.source, d.text) for d in req.documents])
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/reports")
def list_reports():
    return {
        "reports": [
            {
                "report_id": r.report_id,
                "document_count": r.document_count,
                "sources": [d.source for d in r.documents],
            }
            for r in reports.values()
        ]
    }


@app.get("/reports/{report_id}", response_model=CorpusReport)
def get_report(report_id: str):
    if report_id not in reports:
        raise HTTPException(404, f"No report '{report_id}'")
    return reports[report_id]