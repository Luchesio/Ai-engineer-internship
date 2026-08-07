from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from agent import MAX_STEPS, MODEL_NAME, build_agent, run_agent
from documents import SUPPORTED_EXTENSIONS, UnsupportedDocument, Workspace, load_bytes, load_text
from models import ExtractTextRequest, InsightReport

MAX_FILE_BYTES = 10 * 1024 * 1024

model = None
reports: dict[str, InsightReport] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = build_agent()
    yield


app = FastAPI(title="Document Insight Extraction Agent", lifespan=lifespan)


async def run(workspace: Workspace, focus: str | None) -> InsightReport:
    try:
        report = await run_agent(model, workspace, focus)
    except Exception as exc:
        raise HTTPException(500, str(exc))
    reports[report.report_id] = report
    return report


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "POST files to /extract or raw text to /extract/text.",
        "model": MODEL_NAME,
        "max_agent_steps": MAX_STEPS,
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "max_file_mb": MAX_FILE_BYTES // (1024 * 1024),
    }


@app.post("/extract", response_model=InsightReport)
async def extract(files: list[UploadFile] = File(...), focus: str | None = Form(default=None)):
    documents = []
    for i, upload in enumerate(files, 1):
        data = await upload.read()
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(413, f"'{upload.filename}' exceeds the {MAX_FILE_BYTES // 1024 // 1024} MB limit")
        try:
            documents.append(load_bytes(f"doc{i}", upload.filename, data))
        except UnsupportedDocument as exc:
            raise HTTPException(415, str(exc))

    return await run(Workspace(documents), focus)


@app.post("/extract/text", response_model=InsightReport)
async def extract_text(req: ExtractTextRequest):
    try:
        documents = [load_text(f"doc{i}", d.filename, d.text) for i, d in enumerate(req.documents, 1)]
    except UnsupportedDocument as exc:
        raise HTTPException(415, str(exc))

    return await run(Workspace(documents), req.focus)


@app.get("/reports")
def list_reports():
    return {
        "reports": [
            {
                "report_id": r.report_id,
                "title": r.summary.title,
                "documents": [d.filename for d in r.documents],
                "insights": len(r.insights),
            }
            for r in reports.values()
        ]
    }


@app.get("/reports/{report_id}", response_model=InsightReport)
def get_report(report_id: str):
    if report_id not in reports:
        raise HTTPException(404, f"No report '{report_id}'")
    return reports[report_id]