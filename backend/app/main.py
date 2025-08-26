from fastapi import FastAPI, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from docx import Document
import re

from .database import get_db

app = FastAPI(title="QEnergy Platform Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/db/ping")
def db_ping(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception:
        return {"db": "fail"}


_FILENAME_RE = re.compile(r"^(?P<year>\d{4})_CW(?P<cw>\d{2})_(?P<cat>DEV|EPC|FINANCE|INVESTMENT)\.docx$", re.IGNORECASE)
_CAT_MAP = {
    "DEV": "Development",
    "EPC": "EPC",
    "FINANCE": "Finance",
    "INVESTMENT": "Investment",
}


def _parse_filename(filename: str):
    m = _FILENAME_RE.match(filename)
    if not m:
        raise ValueError("INVALID_NAME")
    year = int(m.group("year"))
    cw_label = f"CW{m.group('cw').upper()}"
    raw = m.group("cat").upper()
    category = _CAT_MAP.get(raw, raw)
    return year, cw_label, raw, category


def _error(code: str, message: str):
    return JSONResponse(status_code=400, content={"errors": [{"code": code, "message": message}]})


@app.post("/api/reports/upload")
async def upload_single(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith(".docx"):
        return _error("UNSUPPORTED_TYPE", "Only .docx is supported")
    try:
        year, cw_label, category_raw, category = _parse_filename(filename)
    except ValueError:
        return _error("INVALID_NAME", "Filename must match YYYY_CW##_{DEV|EPC|FINANCE|INVESTMENT}.docx")
    # parse rows from .docx
    try:
        file.file.seek(0)
    except Exception:
        pass
    rows = _parse_docx_rows(file, cw_label=cw_label, category=category)
    return {
        "fileName": filename,
        "mimeType": file.content_type,
        "size": None,
        "year": year,
        "cw_label": cw_label,
        "category_raw": category_raw,
        "category": category,
        "rows": rows,
        "errors": [],
    }


@app.post("/api/reports/upload/bulk")
async def upload_bulk(files: list[UploadFile] = File(...)):
    results = []
    rows_total = 0
    for f in files:
        name = f.filename or ""
        if not name.lower().endswith(".docx"):
            results.append({
                "fileName": name,
                "status": "error",
                "errors": [{"code": "UNSUPPORTED_TYPE", "message": "Only .docx is supported"}],
            })
            continue
        try:
            year, cw_label, category_raw, category = _parse_filename(name)
        except ValueError:
            results.append({
                "fileName": name,
                "status": "error",
                "errors": [{"code": "INVALID_NAME", "message": "Filename must match YYYY_CW##_{DEV|EPC|FINANCE|INVESTMENT}.docx"}],
            })
            continue
        # parse rows from .docx
        try:
            f.file.seek(0)
        except Exception:
            pass
        rows = _parse_docx_rows(f, cw_label=cw_label, category=category)
        results.append({
            "fileName": name,
            "status": "ok",
            "year": year,
            "cw_label": cw_label,
            "category_raw": category_raw,
            "category": category,
            "rows": rows,
            "errors": [],
        })
        rows_total += len(rows)
    summary = {"filesAccepted": len([r for r in results if r.get("status") == "ok"]),
               "filesRejected": len([r for r in results if r.get("status") == "error"]),
               "rowsTotal": rows_total}
    return {"results": results, "summary": summary}


def _parse_docx_rows(file: UploadFile, cw_label: str, category: str) -> list[dict]:
    """Very simple parser: collect all paragraph texts and table cell texts; return a single row summary.

    Later we can split by headings or tables into multiple rows. For now, ensure at least one row.
    """
    rows: list[dict] = []
    try:
        document = Document(file.file)
    except Exception:
        # parsing failed -> return one empty row to avoid crashing, but realistically we could report PARSE_FAILED
        rows.append({
            "category": category,
            "entry_type": "Report",
            "cw_label": cw_label,
            "title": None,
            "summary": "",
            "next_actions": None,
            "owner": None,
            "attachment_url": None,
        })
        return rows

    texts: list[str] = []
    for p in document.paragraphs:
        t = (p.text or "").strip()
        if t:
            texts.append(t)
    for table in document.tables:
        for row in table.rows:
            cells = [ (cell.text or "").strip() for cell in row.cells ]
            cells = [c for c in cells if c]
            if cells:
                texts.append(" | ".join(cells))

    summary = "\n".join(texts).strip()
    rows.append({
        "category": category,
        "entry_type": "Report",
        "cw_label": cw_label,
        "title": None,
        "summary": summary,
        "next_actions": None,
        "owner": None,
        "attachment_url": None,
    })
    return rows