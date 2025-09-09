from fastapi import FastAPI, Depends, File, UploadFile, Query, HTTPException
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from docx import Document
import asyncio
import re
import tempfile
import os
import logging
import json
import hashlib

from .database import get_db
from .task_queue import task_queue, TaskStatus, TaskStep
from .utils import (
    parse_filename,
    parse_docx_rows,
    seed_projects_from_csv,
    get_project_code_by_name_db,
)
from .routes import project, project_history, analysis, project_candidates

# Set up logger
logger = logging.getLogger(__name__)

app = FastAPI(title="QEnergy Platform Backend")

# Include routers
app.include_router(project.router, prefix="/api")
app.include_router(project_history.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(project_candidates.router, prefix="/api")

@app.on_event("startup")
def seed_projects():
    """Load `data/project.csv` into DB on startup (idempotent)."""
    try:
        db = next(get_db())
        count = seed_projects_from_csv(db)
        logger.info(f"Seeded/updated {count} projects from CSV")
    except Exception as e:
        logger.error(f"Project seeding failed: {e}")
    finally:
        try:
            db.close()
        except Exception:
            pass

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


@app.get("/api/tasks/{task_id}/stream")
async def stream_task_updates(task_id: str):
    """Stream task updates via Server-Sent Events"""
    async def event_stream():
        # Subscribe to task updates
        queue = task_queue.subscribe_to_task(task_id)
        
        # Send current status first
        current_status = task_queue.get_task_status(task_id)
        if current_status:
            yield f"data: {json.dumps(current_status)}\n\n"
        
        try:
            while True:
                # Wait for updates with timeout
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(update)}\n\n"
                    
                    # If task is completed or failed, send final message and break
                    if update.get('status') in ['completed', 'failed']:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"Task stream cancelled for {task_id}")
        except Exception as e:
            logger.error(f"Error in task stream for {task_id}: {e}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get current task status"""
    status = task_queue.get_task_status(task_id)
    if not status:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return status


@app.get("/api/tasks")
async def get_all_tasks():
    """Get all task statuses"""
    return {"tasks": task_queue.get_all_tasks()}


@app.get("/api/reports/uploads")
async def get_report_uploads(db: Session = Depends(get_db)):
    """Get all report uploads with summary statistics"""
    try:
        uploads = db.execute(text("""
            SELECT 
                ru.id,
                ru.original_filename,
                ru.status,
                ru.cw_label,
                ru.uploaded_at,
                ru.parsed_at,
                ru.created_by,
                COUNT(ph.id) as project_count
            FROM report_uploads ru
            LEFT JOIN project_history ph ON ph.source_upload_id = ru.id
            GROUP BY ru.id, ru.original_filename, ru.status, ru.cw_label, 
                     ru.uploaded_at, ru.parsed_at, ru.created_by
            ORDER BY ru.uploaded_at DESC
        """)).fetchall()
        
        result = []
        for upload in uploads:
            result.append({
                "id": str(upload.id),
                "originalFilename": upload.original_filename,
                "status": upload.status,
                "cwLabel": upload.cw_label,
                "uploadedAt": upload.uploaded_at.isoformat(),
                "parsedAt": upload.parsed_at.isoformat() if upload.parsed_at else None,
                "createdBy": upload.created_by,
                "projectCount": upload.project_count
            })
        
        return {"uploads": result}
        
    except Exception as e:
        logger.error(f"Failed to get report uploads: {e}")
        return _error("FETCH_FAILED", str(e))


@app.get("/api/reports/uploads/{upload_id}/history")
async def get_upload_project_history(upload_id: str, db: Session = Depends(get_db)):
    """Get project history records for a specific upload"""
    try:
        # First verify the upload exists
        upload = db.execute(text("""
            SELECT id, original_filename, status, cw_label, uploaded_at, parsed_at
            FROM report_uploads 
            WHERE id = :upload_id
        """), {"upload_id": upload_id}).first()
        
        if not upload:
            return _error("NOT_FOUND", f"Upload {upload_id} not found")
        
        # Get project history records
        history_records = db.execute(text("""
            SELECT 
                ph.id,
                ph.project_code,
                ph.project_name,
                ph.category,
                ph.entry_type,
                ph.log_date,
                ph.cw_label,
                ph.title,
                ph.summary,
                ph.next_actions,
                ph.owner,
                ph.source_text,
                ph.created_at,
                p.project_name AS joined_project_name
            FROM project_history ph
            LEFT JOIN projects p ON p.project_code = ph.project_code
            WHERE ph.source_upload_id = :upload_id
            ORDER BY ph.created_at DESC
        """), {"upload_id": upload_id}).fetchall()
        
        upload_info = {
            "id": str(upload.id),
            "originalFilename": upload.original_filename,
            "status": upload.status,
            "cwLabel": upload.cw_label,
            "uploadedAt": upload.uploaded_at.isoformat(),
            "parsedAt": upload.parsed_at.isoformat() if upload.parsed_at else None
        }
        
        history_list = []
        for record in history_records:
            history_list.append({
                "id": str(record.id),
                "projectCode": record.project_code,
                "projectName": record.project_name or record.joined_project_name,
                "category": record.category,
                "entryType": record.entry_type,
                "logDate": record.log_date.isoformat() if record.log_date else None,
                "cwLabel": record.cw_label,
                "title": record.title,
                "summary": record.summary,
                "nextActions": record.next_actions,
                "owner": record.owner,
                "sourceText": record.source_text,
                "createdAt": record.created_at.isoformat()
            })
        
        return {
            "upload": upload_info,
            "projectHistory": history_list,
            "totalRecords": len(history_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get project history for upload {upload_id}: {e}")
        return _error("FETCH_FAILED", str(e))


@app.get("/api/project-history")
async def get_project_history(
    year: Optional[int] = Query(None, description="Filter by year"),
    cw_label: Optional[str] = Query(None, description="Filter by calendar week (e.g., CW01)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get project history records with optional filters"""
    try:
        # Build the query dynamically based on filters
        query = """
            SELECT 
                ph.id,
                ph.project_code,
                ph.project_name,
                ph.category,
                ph.entry_type,
                ph.log_date,
                ph.cw_label,
                ph.title,
                ph.summary,
                ph.next_actions,
                ph.owner,
                ph.source_text,
                ph.created_at,
                ph.updated_at,
                p.project_name AS joined_project_name,
                p.portfolio_cluster
            FROM project_history ph
            LEFT JOIN projects p ON p.project_code = ph.project_code
            WHERE 1=1
        """
        
        params = {}
        
        # Add filters
        if year:
            query += " AND EXTRACT(YEAR FROM ph.log_date) = :year"
            params["year"] = year
            
        if cw_label:
            query += " AND ph.cw_label = :cw_label"
            params["cw_label"] = cw_label
            
        if category:
            query += " AND ph.category = :category"
            params["category"] = category
            
        query += " ORDER BY ph.log_date DESC, ph.project_code ASC"
        
        history_records = db.execute(text(query), params).fetchall()
        
        history_list = []
        for record in history_records:
            history_list.append({
                "id": str(record.id),
                "projectCode": record.project_code,
                "projectName": record.project_name or record.joined_project_name,
                "category": record.category,
                "entryType": record.entry_type,
                "logDate": record.log_date.isoformat() if record.log_date else None,
                "cwLabel": record.cw_label,
                "title": record.title,
                "summary": record.summary,
                "nextActions": record.next_actions,
                "owner": record.owner,
                "sourceText": record.source_text,
                "createdAt": record.created_at.isoformat(),
                "updatedAt": record.updated_at.isoformat(),
                "portfolioCluster": record.portfolio_cluster
            })
        
        return {
            "projectHistory": history_list,
            "totalRecords": len(history_list),
            "filters": {
                "year": year,
                "cwLabel": cw_label,
                "category": category
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get project history: {e}")
        return _error("FETCH_FAILED", str(e))


# Moved to utils.py to avoid circular imports


def _error(code: str, message: str):
    return JSONResponse(status_code=400, content={"errors": [{"code": code, "message": message}]})


@app.post("/api/reports/upload")
async def upload_single(
    file: UploadFile = File(...),
    use_llm: bool = Query(False, description="Use LLM parser for advanced extraction")
):
    filename = file.filename or ""
    if not filename.lower().endswith(".docx"):
        return _error("UNSUPPORTED_TYPE", "Only .docx is supported")
    
    try:
        year, cw_label, category_raw, category = parse_filename(filename)
    except ValueError as e:
        return _error("INVALID_NAME", f"Filename '{filename}' must contain a calendar week (e.g., CW01) and category (DEV, EPC, FINANCE, or INVESTMENT). Details: {str(e)}")
    
    # Create task for tracking
    task_id = task_queue.create_task(filename, use_llm)
    
    try:
        # Update progress: file received
        await task_queue.update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            current_step=TaskStep.DOCUMENT_LOADING,
            progress=10,
            message=f"Loading document: {filename}"
        )
        
        # Parse rows from .docx using either LLM or simple parser
        try:
            file.file.seek(0)
        except Exception:
            pass
        
        if use_llm:
            try:
                # Update progress: preparing for LLM
                await task_queue.update_task(
                    task_id,
                    current_step=TaskStep.TEXT_EXTRACTION,
                    progress=20,
                    message="Extracting text content..."
                )
                
                # Save uploaded file temporarily for LLM processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_file.flush()
                    
                    # Update progress: LLM processing
                    await task_queue.update_task(
                        task_id,
                        current_step=TaskStep.LLM_PROCESSING,
                        progress=40,
                        message="AI analyzing document structure and content..."
                    )
                    
                    # Try to import LLM parser (might fail due to missing dependencies)
                    try:
                        from .llm_parser import extract_rows_from_docx
                        
                        # Use LLM parser
                        rows = extract_rows_from_docx(tmp_file.name, cw_label=cw_label, category_from_filename=category)
                        
                        # Update progress: validation
                        await task_queue.update_task(
                            task_id,
                            current_step=TaskStep.DATA_VALIDATION,
                            progress=80,
                            message=f"Validating extracted data ({len(rows)} entries found)..."
                        )
                        
                    except ImportError as import_error:
                        logger.error(f"LLM parser import failed: {import_error}")
                        # Fallback to simple parser
                        await task_queue.update_task(
                            task_id,
                            progress=50,
                            message="AI parser unavailable, falling back to basic parsing..."
                        )
                        file.file.seek(0)
                        simple_rows = parse_docx_rows(file, cw_label=cw_label, category=category)
                        rows = []
                        for row in simple_rows:
                            rows.append({
                                "project_name": row.get("summary", "")[:50] + "..." if len(row.get("summary", "")) > 50 else row.get("summary", ""),
                                "category": category,
                                "title": None,
                                "summary": row.get("summary", ""),
                                "next_actions": None,
                                "owner": None,
                                "source_text": row.get("summary", "")
                            })
                        
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                    
                    # Convert to expected format
                    formatted_rows = []
                    for row in rows:
                        formatted_rows.append({
                            "project_name": row.get("project_name", ""),
                            "category": row.get("category", category),
                            "entry_type": "Report",
                            "cw_label": cw_label,
                            "title": row.get("title"),
                            "summary": row.get("summary", ""),
                            "next_actions": row.get("next_actions"),
                            "owner": row.get("owner"),
                            "attachment_url": None,
                            "source_text": row.get("source_text"),
                        })
                    
                    logger.info(f"LLM parser extracted {len(formatted_rows)} rows from {filename}")
                    
            except Exception as e:
                logger.error(f"LLM parsing failed for {filename}: {e}")
                await task_queue.update_task(
                    task_id,
                    progress=60,
                    message="AI parsing failed, using basic parser..."
                )
                # Fallback to simple parser
                file.file.seek(0)
                formatted_rows = parse_docx_rows(file, cw_label=cw_label, category=category)
                
        else:
            # Use simple parser
            await task_queue.update_task(
                task_id,
                current_step=TaskStep.TEXT_EXTRACTION,
                progress=50,
                message="Using basic text extraction..."
            )
            formatted_rows = parse_docx_rows(file, cw_label=cw_label, category=category)
        
        # Final completion
        await task_queue.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            current_step=TaskStep.COMPLETED,
            progress=100,
            message=f"Successfully processed {len(formatted_rows)} entries",
            result_count=len(formatted_rows)
        )
        
        return {
            "taskId": task_id,
            "fileName": filename,
            "mimeType": file.content_type,
            "size": len(content) if 'content' in locals() else None,
            "year": year,
            "cw_label": cw_label,
            "category_raw": category_raw,
            "category": category,
            "rows": formatted_rows,
            "parsedWith": "llm" if use_llm else "simple",
            "errors": [],
        }
        
    except Exception as e:
        logger.error(f"Upload processing failed for {filename}: {e}")
        await task_queue.update_task(
            task_id,
            status=TaskStatus.FAILED,
            progress=0,
            message="Upload processing failed",
            error_message=str(e)
        )
        return _error("PROCESSING_FAILED", f"Failed to process {filename}: {str(e)}")


@app.post("/api/reports/upload/check-duplicate")
async def check_duplicate_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Check if a file already exists in the database by SHA256 hash
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".docx"):
        return _error("UNSUPPORTED_TYPE", "Only .docx is supported")
    
    try:
        # Calculate file hash
        content = await file.read()
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Check if upload already exists by SHA256
        existing = db.execute(
            text("SELECT id, original_filename, uploaded_at, status FROM report_uploads WHERE sha256 = :sha256"),
            {"sha256": sha256_hash}
        ).first()
        
        if existing:
            return {
                "isDuplicate": True,
                "existingFile": {
                    "id": existing.id,
                    "filename": existing.original_filename,
                    "uploadedAt": existing.uploaded_at.isoformat(),
                    "status": existing.status
                },
                "currentFile": {
                    "filename": filename,
                    "sha256": sha256_hash
                }
            }
        else:
            return {
                "isDuplicate": False,
                "currentFile": {
                    "filename": filename,
                    "sha256": sha256_hash
                }
            }
    except Exception as e:
        logger.error(f"Failed to check duplicate for {filename}: {e}")
        return _error("CHECK_FAILED", f"Failed to check duplicate: {str(e)}")


@app.post("/api/reports/upload/persist")
async def persist_upload_to_database(
    file: UploadFile = File(...),
    use_llm: bool = Query(False, description="Use LLM parser for advanced extraction"),
    force_import: bool = Query(False, description="Force import even if file already exists"),
    db: Session = Depends(get_db)
):
    """
    Upload and immediately persist file to database (report_uploads + project_history)
    """
    filename = file.filename or ""
    if not filename.lower().endswith(".docx"):
        return _error("UNSUPPORTED_TYPE", "Only .docx is supported")
    
    try:
        year, cw_label, category_raw, category = parse_filename(filename)
    except ValueError as e:
        logger.error(f"Failed to parse filename '{filename}': {e}")
        return _error("INVALID_NAME", f"Filename '{filename}' must contain a calendar week (e.g., CW01) and category (DEV, EPC, FINANCE, or INVESTMENT). Details: {str(e)}")
    
    # If not forcing import, we still allow reuse of existing upload via importer logic.
    # So we don't block here; we only compute sha for logging/debug if needed.
    
    # Create task for tracking
    task_id = task_queue.create_task(filename, use_llm)
    
    try:
        # Update progress: file received
        await task_queue.update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            current_step=TaskStep.DOCUMENT_LOADING,
            progress=10,
            message=f"Saving file: {filename}"
        )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            try:
                # Update progress: processing
                await task_queue.update_task(
                    task_id,
                    current_step=TaskStep.LLM_PROCESSING if use_llm else TaskStep.TEXT_EXTRACTION,
                    progress=30,
                    message="Processing and saving to database..."
                )
                
                # Use report importer to save to database
                if use_llm:
                    # Import here to avoid circular import
                    from .report_importer import import_single_docx_llm_with_metadata

                    # DB-backed project code mapper (using seeded projects)
                    def db_mapper(project_name: str) -> str | None:
                        return get_project_code_by_name_db(db, project_name)
                    
                    result = import_single_docx_llm_with_metadata(
                        db=db,
                        file_path=tmp_file.name,
                        original_filename=filename,
                        project_code_mapper=db_mapper,
                        created_by="web_user",
                        force_import=force_import
                    )
                else:
                    # Simple parsing path delegated to importer
                    from .report_importer import import_single_docx_simple_with_metadata
                    result = import_single_docx_simple_with_metadata(
                        db=db,
                        file_path=tmp_file.name,
                        original_filename=filename,
                        created_by="web_user",
                        force_import=force_import
                    )
                
                # Update progress: completion
                await task_queue.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    current_step=TaskStep.COMPLETED,
                    progress=100,
                    message=f"Successfully saved {result.get('rows_created', 0)} entries to database",
                    result_count=result.get('rows_created', 0)
                )
                
                return {
                    "taskId": task_id,
                    "uploadId": result.get("upload_id"),
                    "fileName": filename,
                    "year": year,
                    "cw_label": cw_label,
                    "category": category,
                    "rowsCreated": result.get("rows_created", 0),
                    "parsedWith": "llm" if use_llm else "simple",
                    "status": "persisted"
                }
                
            finally:
                # Clean up temp file
                os.unlink(tmp_file.name)
                
    except Exception as e:
        logger.error(f"Database persistence failed for {filename}: {e}")
        await task_queue.update_task(
            task_id,
            status=TaskStatus.FAILED,
            progress=0,
            message="Database persistence failed",
            error_message=str(e)
        )
        return _error("PERSISTENCE_FAILED", f"Failed to persist {filename}: {str(e)}")


@app.post("/api/reports/upload/bulk")
async def upload_bulk(
    files: list[UploadFile] = File(...),
    use_llm: bool = Query(False, description="Use LLM parser for advanced extraction")
):
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
            year, cw_label, category_raw, category = parse_filename(name)
        except ValueError as e:
            results.append({
                "fileName": name,
                "status": "error",
                "errors": [{"code": "INVALID_NAME", "message": f"Filename '{name}' must contain a calendar week (e.g., CW01) and category (DEV, EPC, FINANCE, or INVESTMENT). Details: {str(e)}"}],
            })
            continue
        
        # Parse rows from .docx using either LLM or simple parser
        try:
            f.file.seek(0)
        except Exception:
            pass
        
        if use_llm:
            try:
                # Save uploaded file temporarily for LLM processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                    content = await f.read()
                    tmp_file.write(content)
                    tmp_file.flush()
                    
                    # Use LLM parser (import locally to avoid circular issues)
                    try:
                        from .llm_parser import extract_rows_from_docx
                    except Exception as _e:
                        logger.error(f"LLM parser import failed in bulk upload: {_e}")
                        raise

                    rows = extract_rows_from_docx(tmp_file.name, cw_label=cw_label, category_from_filename=category)
                    
                    # Clean up temp file
                    os.unlink(tmp_file.name)
                    
                    # Convert to expected format
                    formatted_rows = []
                    for row in rows:
                        formatted_rows.append({
                            "project_name": row.get("project_name", ""),
                            "category": row.get("category", category),
                            "entry_type": "Report",
                            "cw_label": cw_label,
                            "title": row.get("title"),
                            "summary": row.get("summary", ""),
                            "next_actions": row.get("next_actions"),
                            "owner": row.get("owner"),
                            "attachment_url": None,
                            "source_text": row.get("source_text"),
                        })
                    
                    logger.info(f"LLM parser extracted {len(formatted_rows)} rows from {name}")
                    
            except Exception as e:
                logger.error(f"LLM parsing failed for {name}: {e}")
                # Fallback to simple parser
                f.file.seek(0)
                formatted_rows = parse_docx_rows(f, cw_label=cw_label, category=category)
                
        else:
            # Use simple parser
            formatted_rows = parse_docx_rows(f, cw_label=cw_label, category=category)
        
        results.append({
            "fileName": name,
            "status": "ok",
            "year": year,
            "cw_label": cw_label,
            "category_raw": category_raw,
            "category": category,
            "rows": formatted_rows,
            "parsedWith": "llm" if use_llm else "simple",
            "errors": [],
        })
        rows_total += len(formatted_rows)
    
    summary = {
        "filesAccepted": len([r for r in results if r.get("status") == "ok"]),
        "filesRejected": len([r for r in results if r.get("status") == "error"]),
        "rowsTotal": rows_total,
        "parsedWith": "llm" if use_llm else "simple"
    }
    return {"results": results, "summary": summary}


# Analysis endpoints for Phase 2D
from .services.analysis_service import AnalysisService
from .schemas.analysis import (
    AnalysisRequest, AnalysisResponse, ProjectCandidateResponse, 
    WeeklyReportAnalysisRead, Language, Category
)

analysis_service = AnalysisService()

@app.post("/api/reports/analyze", response_model=AnalysisResponse)
async def analyze_reports(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """Trigger sync analysis for reports between two calendar weeks"""
    try:
        # Get candidate projects
        candidates = analysis_service.get_projects_by_cw_pair(
            db, request.past_cw, request.latest_cw, request.category
        )
        
        if not candidates:
            return AnalysisResponse(
                message="No projects found for the specified calendar weeks",
                analyzed_count=0,
                skipped_count=0,
                results=[]
            )
        
        analyzed_count = 0
        skipped_count = 0
        results = []
        
        # Analyze each project
        for candidate in candidates:
            try:
                analysis, was_created = await analysis_service.analyze_project_pair(
                    db=db,
                    project_code=candidate["project_code"],
                    past_cw=request.past_cw,
                    latest_cw=request.latest_cw,
                    language=request.language,
                    category=request.category,
                    created_by=request.created_by
                )
                
                results.append(analysis)
                if was_created:
                    analyzed_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to analyze {candidate['project_code']}: {e}")
                skipped_count += 1
        
        return AnalysisResponse(
            message=f"Analysis completed: {analyzed_count} new, {skipped_count} cached/skipped",
            analyzed_count=analyzed_count,
            skipped_count=skipped_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/weekly-analysis", response_model=List[WeeklyReportAnalysisRead])
def get_weekly_analysis(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    language: Optional[Language] = Query(None, description="Filter by language"),
    category: Optional[Category] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """List existing analysis results"""
    try:
        results = analysis_service.get_analysis_results(
            db, past_cw, latest_cw, language, category
        )
        return results
    except Exception as e:
        logger.error(f"Failed to get analysis results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis results: {str(e)}")


@app.get("/api/projects/by-cw-pair", response_model=List[ProjectCandidateResponse])
def get_projects_by_cw_pair(
    past_cw: str = Query(..., description="Past calendar week (e.g., CW31)"),
    latest_cw: str = Query(..., description="Latest calendar week (e.g., CW32)"),
    category: Optional[Category] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """List candidate projects present in either calendar week"""
    try:
        candidates = analysis_service.get_projects_by_cw_pair(db, past_cw, latest_cw, category)
        return [
            ProjectCandidateResponse(
                project_code=candidate["project_code"],
                project_name=candidate["project_name"],
                categories=candidate["categories"],
                cw_labels=candidate["cw_labels"]
            )
            for candidate in candidates
        ]
    except Exception as e:
        logger.error(f"Failed to get project candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project candidates: {str(e)}")


# Moved to utils.py