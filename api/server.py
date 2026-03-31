"""
FastAPI server for the Form Extractor AI Engine.
Provides REST API endpoints for document analysis and report generation.
All persistence backed by Supabase (database + storage).
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("digital_ink")

from src.services.pdf_processor import PDFProcessor
from src.services.extraction_pipeline import ExtractionPipeline
from src.generators.schema_generator import SchemaGenerator
from src.services import job_manager, storage_manager
from src.services.supabase_client import get_supabase

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()] if os.getenv("ALLOWED_ORIGINS") else []
ALLOWED_ORIGINS += [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
]

app = FastAPI(
    title="Form Extractor API",
    description="AI-powered medical form extraction",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Auth Dependencies
# =============================================================================

_bearer = HTTPBearer(auto_error=False)


async def _get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[str]:
    """Return the user_id from a valid JWT, or None when no token is present."""
    if not credentials:
        return None
    try:
        sb = get_supabase()
        res = sb.auth.get_user(credentials.credentials)
        return res.user.id if res and res.user else None
    except Exception:
        return None


async def _require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    """Return the user_id from a valid JWT, or raise 401."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        sb = get_supabase()
        res = sb.auth.get_user(credentials.credentials)
        if not res or not res.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return res.user.id
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")


# =============================================================================
# Request/Response Models
# =============================================================================

class AnalyzeResponse(BaseModel):
    job_id: str
    document_id: str = ""
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    total_pages: Optional[int] = None
    percentage: Optional[float] = None
    current_stage: Optional[str] = None
    message: Optional[str] = None


class ExtractionResultSummary(BaseModel):
    job_id: str
    patient_name: Optional[str] = None
    patient_dob: Optional[str] = None
    form_date: Optional[str] = None
    overall_confidence: float
    total_pages: int
    total_items_needing_review: int
    extraction_timestamp: str


# =============================================================================
# Background Task Functions
# =============================================================================

def _load_schema(schema_path: Optional[str]):
    """Load form schema and blank templates if available."""
    if not schema_path:
        return None, None

    fe_root = Path(__file__).resolve().parent.parent
    resolved = fe_root / schema_path
    if not resolved.exists():
        resolved = Path(schema_path)
    if not resolved.exists():
        logger.warning("Schema not found at %s or %s", fe_root / schema_path, schema_path)
        return None, None

    schema_dir = resolved.parent
    schema_gen = SchemaGenerator(schema_dir)
    form_schema = schema_gen.load_form_schema(resolved)

    blank_image_paths = None
    if form_schema and form_schema.blank_images:
        blank_image_paths = []
        for i in range(1, form_schema.total_pages + 1):
            blank_filename = form_schema.get_blank_image_filename(i)
            if blank_filename:
                blank_path = schema_dir / blank_filename
                blank_image_paths.append(blank_path if blank_path.exists() else None)
            else:
                blank_image_paths.append(None)

        valid_blanks = sum(1 for p in blank_image_paths if p)
        if valid_blanks > 0:
            logger.info("Using %d blank templates for differential extraction", valid_blanks)

    return form_schema, blank_image_paths


def _save_results_to_db(job_id: str, document_id: str, result, start_time: datetime, model_used: str = "unknown"):
    """Persist extraction results to Supabase and create derived records."""
    page_dicts = []
    for page in result.pages:
        page_data = page.model_dump(mode="json")
        page_dicts.append(page_data)
        job_manager.save_page_result(
            job_id=job_id,
            document_id=document_id,
            page_number=page.page_number,
            page_data=page_data,
        )

    elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    job_manager.update_job(
        job_id,
        status="completed",
        current_stage="Completed",
        percentage=100,
        processing_time_ms=elapsed_ms,
        ai_model_used=model_used,
    )
    job_manager.update_document(document_id, status="analyzed")

    job_manager.write_audit_log(
        action="extraction_completed",
        resource_type="extraction_job",
        resource_id=job_id,
        details={"document_id": document_id, "model": model_used, "pages": len(page_dicts), "elapsed_ms": elapsed_ms},
    )


def run_extraction(
    job_id: str,
    document_id: str,
    file_path: Path,
    name: str,
    schema_path: Optional[str] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
):
    """Run the extraction pipeline as a background task."""
    start_time = datetime.utcnow()
    logger.info("[BG] run_extraction started: job=%s, file=%s", job_id[:8], file_path.name)
    try:
        job_manager.update_job(job_id, status="processing", current_stage="Initializing")

        pdf_processor = PDFProcessor(dpi=150)
        pipeline = ExtractionPipeline()

        form_schema, blank_image_paths = _load_schema(schema_path)

        job_manager.update_job(job_id, current_stage="Converting PDF to images")

        if file_path.suffix.lower() == ".pdf":
            image_paths = pdf_processor.convert_pdf_to_images(
                file_path, prefix=name, start_page=start_page, end_page=end_page,
            )
        else:
            image_paths = [file_path]

        if blank_image_paths and (start_page is not None or end_page is not None):
            actual_start = (start_page or 1) - 1
            actual_end = end_page if end_page else len(blank_image_paths)
            blank_image_paths = blank_image_paths[actual_start:actual_end]

        job_manager.update_job(job_id, total_pages=len(image_paths), current_stage="Running AI extraction")

        result = pipeline.extract_form(
            image_paths=image_paths,
            form_schema=form_schema,
            form_name=name,
            blank_image_paths=blank_image_paths,
        )

        job_manager.update_job(job_id, current_stage="Saving results", percentage=95)
        _save_results_to_db(job_id, document_id, result, start_time, pipeline.model_used)

        pdf_processor.cleanup()
        logger.info("[BG] run_extraction DONE: job=%s, model=%s", job_id[:8], pipeline.model_used)

    except Exception as e:
        logger.error("[BG] run_extraction FAILED: job=%s — %s", job_id[:8], e, exc_info=True)
        job_manager.update_job(
            job_id, status="failed", error_message=str(e), current_stage="Failed", percentage=0,
        )
        job_manager.update_document(document_id, status="failed")


def run_extraction_images(
    job_id: str,
    document_id: str,
    image_paths: List[Path],
    name: str,
    page_info: List[str],
    schema_path: Optional[str] = None,
):
    """Run the extraction pipeline on a batch of images with parallel processing."""
    start_time = datetime.utcnow()
    logger.info("[BG] run_extraction_images started: job=%s, %d pages", job_id[:8], len(image_paths))
    try:
        job_manager.update_job(job_id, status="processing", current_stage="Initializing", percentage=0)

        if page_info:
            for i, info in enumerate(page_info):
                logger.info("  Page %d: %s", i + 1, info)

        pipeline = ExtractionPipeline()
        form_schema, blank_image_paths = _load_schema(schema_path)

        job_manager.update_job(job_id, total_pages=len(image_paths), progress=0)

        completed_pages = 0
        total = len(image_paths)

        def _update_progress(done, tot, pct):
            nonlocal completed_pages
            completed_pages = done
            label = page_info[done - 1] if (done - 1) < len(page_info) else f"Page {done}"
            job_manager.update_job(
                job_id, progress=done, percentage=pct,
                current_stage=f"Analyzing: {label} ({pct}% complete)",
            )

        job_manager.update_job(job_id, current_stage=f"Extracting {total} page(s)")
        result = pipeline.extract_form(
            image_paths=image_paths,
            form_schema=form_schema,
            form_name=name,
            max_workers=4,
            progress_callback=_update_progress,
            blank_image_paths=blank_image_paths,
        )

        job_manager.update_job(job_id, current_stage="Saving results", percentage=95)

        for page in result.pages:
            page_data = page.model_dump(mode="json")
            job_manager.save_page_result(
                job_id=job_id,
                document_id=document_id,
                page_number=page_data.get("page_number", 0),
                page_data=page_data,
            )

        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        job_manager.update_job(
            job_id, status="completed", current_stage="Completed",
            percentage=100, processing_time_ms=elapsed_ms,
            ai_model_used=pipeline.model_used,
        )
        job_manager.update_document(document_id, status="analyzed")
        job_manager.write_audit_log(
            action="extraction_completed",
            resource_type="extraction_job",
            resource_id=job_id,
            details={
                "document_id": document_id,
                "model": pipeline.model_used,
                "pages": len(result.pages),
                "elapsed_ms": elapsed_ms,
            },
        )

        logger.info("[BG] run_extraction_images DONE: job=%s, model=%s, %d pages",
                     job_id[:8], pipeline.model_used, len(result.pages))

    except Exception as e:
        logger.error("[BG] run_extraction_images FAILED: job=%s — %s", job_id[:8], e, exc_info=True)
        job_manager.update_job(
            job_id, status="failed", error_message=str(e), current_stage="Failed", percentage=0,
        )
        job_manager.update_document(document_id, status="failed")


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health")
async def health_check():
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    return {
        "status": "healthy",
        "fireworks_configured": bool(fireworks_key),
        "anthropic_configured": bool(anthropic_key),
        "supabase_configured": bool(supabase_url),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    schema_path: Optional[str] = Form(None),
    start_page: Optional[int] = Form(None),
    end_page: Optional[int] = Form(None),
    user_id: str = Depends(_require_user),
):
    """Upload and analyze a single document (PDF or image)."""
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    if not name:
        name = Path(file.filename).stem.lower().replace(" ", "_")

    content = await file.read()
    logger.info("POST /api/analyze — file=%s, size=%d bytes", file.filename, len(content))

    storage_path = f"{name}/{file.filename}"
    storage_manager.upload_file(
        storage_manager.BUCKET_ORIGINALS, storage_path, content,
        content_type="application/pdf" if file_ext == ".pdf" else f"image/{file_ext.lstrip('.')}",
    )

    document_id = job_manager.create_document(
        file_name=file.filename,
        file_type=file_ext.lstrip("."),
        storage_path=f"originals/{storage_path}",
        file_size_bytes=len(content),
    )

    job_id = job_manager.create_job(document_id=document_id, total_pages=None)
    logger.info("Queued extraction: job=%s, document=%s", job_id[:8], document_id[:8])

    tmp_dir = Path(tempfile.mkdtemp(prefix="di_"))
    tmp_path = tmp_dir / file.filename
    tmp_path.write_bytes(content)

    job_manager.update_document(document_id, status="processing")

    background_tasks.add_task(
        run_extraction, job_id, document_id, tmp_path, name, schema_path, start_page, end_page,
    )

    return AnalyzeResponse(job_id=job_id, document_id=document_id, status="pending", message=f"Analysis started for {file.filename}")


@app.post("/api/analyze-images", response_model=AnalyzeResponse)
async def analyze_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    name: Optional[str] = Form(None),
    schema_path: Optional[str] = Form(None),
    page_metadata: Optional[str] = Form(None),
    parent_document_id: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    user_id: str = Depends(_require_user),
):
    """Upload and analyze multiple page images as a batch."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    logger.info("analyze_images received: patient_id=%s, parent_document_id=%s, name=%s", patient_id, parent_document_id, name)

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    for f in files:
        file_ext = Path(f.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")

    parsed_metadata = None
    if page_metadata:
        try:
            parsed_metadata = json.loads(page_metadata)
        except json.JSONDecodeError:
            pass

    if not name:
        name = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    logger.info("POST /api/analyze-images — %d files, name=%s, patient=%s", len(files), name, patient_id[:8])

    document_id = job_manager.create_document(
        file_name=f"{len(files)} page images",
        file_type="image_batch",
        storage_path=f"annotated/{name}/",
        total_pages=len(files),
        parent_document_id=parent_document_id,
        patient_id=patient_id,
    )

    job_id = job_manager.create_job(document_id=document_id, total_pages=len(files))
    logger.info("Queued batch extraction: job=%s, document=%s, pages=%d", job_id[:8], document_id[:8], len(files))

    tmp_dir = Path(tempfile.mkdtemp(prefix="di_"))
    image_paths = []
    page_info = []

    for i, file in enumerate(files):
        meta = parsed_metadata[i] if parsed_metadata and i < len(parsed_metadata) else None

        if meta:
            doc_name = meta.get("documentName", "unknown").replace(" ", "_")
            orig_page = meta.get("originalPageNumber", i + 1)
            filename = f"{doc_name}_page_{orig_page:03d}.png"
            page_info.append(f"{meta.get('documentName', 'Unknown')} page {orig_page}")
        else:
            filename = f"page_{i + 1:03d}.png"
            page_info.append(f"Page {i + 1}")

        content = await file.read()

        # Save temp copy for pipeline processing
        tmp_path = tmp_dir / filename
        tmp_path.write_bytes(content)
        image_paths.append(tmp_path)

        # Upload annotated page to Supabase Storage
        annotated_storage_path = f"{name}/{filename}"
        storage_manager.upload_file(
            storage_manager.BUCKET_ANNOTATED, annotated_storage_path, content, content_type="image/png",
        )

        # Track page in DB
        job_manager.save_document_page(
            document_id=document_id,
            page_number=i + 1,
            annotated_image_path=f"annotated/{annotated_storage_path}",
        )

    job_manager.update_document(document_id, status="processing")

    job_manager.write_audit_log(
        action="extraction_started",
        resource_type="extraction_job",
        resource_id=job_id,
        user_id=user_id,
        details={"document_id": document_id, "pages": len(files), "name": name},
    )

    background_tasks.add_task(
        run_extraction_images, job_id, document_id, image_paths, name, page_info, schema_path,
    )

    pages_detail = ", ".join(page_info[:3])
    if len(page_info) > 3:
        pages_detail += f" ...and {len(page_info) - 3} more"

    return AnalyzeResponse(
        job_id=job_id, document_id=document_id, status="pending",
        message=f"Analysis started for {len(files)} pages: {pages_detail}",
    )


@app.post("/api/save-annotated-pdfs")
async def save_annotated_pdfs(
    files: List[UploadFile] = File(...),
    job_id: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    user_id: str = Depends(_require_user),
):
    """Save complete annotated PDF documents to Supabase Storage and link to document record."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Only PDF files allowed. Got: {f.filename}")

    saved_paths: list[str] = []
    batch_name = job_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for file in files:
        content = await file.read()
        storage_path = f"{batch_name}/{file.filename}"
        storage_manager.upload_file(
            storage_manager.BUCKET_ORIGINALS, storage_path, content, content_type="application/pdf",
        )
        saved_paths.append(storage_path)
        logger.info("Saved annotated PDF to Storage: originals/%s", storage_path)

    if not document_id and job_id:
        job = job_manager.get_job(job_id)
        if job:
            document_id = job.get("document_id")

    if document_id:
        sb = get_supabase()
        sb.table("documents").update({"pdf_storage_paths": saved_paths}).eq("id", document_id).execute()
        logger.info("Linked %d PDFs to document %s", len(saved_paths), document_id[:8])

    job_manager.write_audit_log(
        action="document_uploaded",
        resource_type="document",
        resource_id=document_id,
        user_id=user_id,
        details={"files": [f.filename for f in files], "batch": batch_name},
    )

    return {"success": True, "savedFiles": saved_paths, "document_id": document_id}


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, user_id: str = Depends(_require_user)):
    """Get the status of an analysis job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        progress=job.get("progress"),
        total_pages=job.get("total_pages"),
        percentage=float(job["percentage"]) if job.get("percentage") is not None else None,
        current_stage=job.get("current_stage"),
        message=job.get("error_message"),
    )


def _collect_review_reasons(pages: list[dict]) -> list[str]:
    """Collect review reasons from free_form_annotations and low-confidence fields."""
    reasons = []
    for p in pages:
        page_num = p.get("page_number", "?")
        for ann in p.get("free_form_annotations", []):
            if isinstance(ann, dict) and ann.get("needs_review") and ann.get("review_reason"):
                reasons.append(f"Page {page_num}: {ann['review_reason']}")
        for field_id, fv in (p.get("field_values") or {}).items():
            if isinstance(fv, dict) and fv.get("confidence", 1) < 0.5 and fv.get("value"):
                reasons.append(f"Page {page_num}: Low confidence on '{field_id}'")
    return reasons


@app.get("/api/results/{job_id}")
async def get_results(job_id: str, user_id: str = Depends(_require_user)):
    """Get the extraction results for a completed job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {job['status']}")

    pages = job_manager.get_extraction_results(job_id)

    total_items_needing_review = sum(p.get("items_needing_review", 0) for p in pages)
    all_review_reasons = _collect_review_reasons(pages)
    patient_info = job_manager.extract_patient_summary(pages)
    avg_confidence = sum(float(p.get("overall_confidence", 0)) for p in pages) / len(pages) if pages else 0

    return {
        "form_id": job.get("document_id", ""),
        "form_name": job_id,
        "extraction_timestamp": job.get("completed_at", job.get("created_at", "")),
        "patient_name": patient_info.get("patient_name"),
        "patient_dob": patient_info.get("patient_dob"),
        "form_date": patient_info.get("form_date"),
        "overall_confidence": avg_confidence,
        "total_items_needing_review": total_items_needing_review,
        "all_review_reasons": all_review_reasons,
        "pages": [
            {
                "page_number": p["page_number"],
                "field_values": p.get("field_values", {}),
                "annotation_groups": p.get("annotation_groups", []),
                "free_form_annotations": p.get("free_form_annotations", []),
                "spatial_connections": p.get("spatial_connections", []),
                "cross_page_references": p.get("cross_page_references", []),
                "overall_confidence": float(p.get("overall_confidence", 0)),
                "items_needing_review": p.get("items_needing_review", 0),
                "review_reasons": _collect_review_reasons([p]),
            }
            for p in pages
        ],
    }


@app.get("/api/results/{job_id}/summary")
async def get_results_summary(job_id: str, user_id: str = Depends(_require_user)):
    """Get a summary of the extraction results."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {job['status']}")

    pages = job_manager.get_extraction_results(job_id)
    total_items = sum(p.get("items_needing_review", 0) for p in pages)
    avg_confidence = (
        sum(float(p.get("overall_confidence", 0)) for p in pages) / len(pages) if pages else 0
    )
    patient_info = job_manager.extract_patient_summary(pages)

    return ExtractionResultSummary(
        job_id=job_id,
        patient_name=patient_info.get("patient_name"),
        patient_dob=patient_info.get("patient_dob"),
        form_date=patient_info.get("form_date"),
        overall_confidence=avg_confidence,
        total_pages=len(pages),
        total_items_needing_review=total_items,
        extraction_timestamp=job.get("completed_at", job.get("created_at", "")),
    )


@app.get("/api/results/{job_id}/page/{page_number}")
async def get_page_results(job_id: str, page_number: int, user_id: str = Depends(_require_user)):
    """Get results for a specific page."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {job['status']}")

    pages = job_manager.get_extraction_results(job_id)
    for p in pages:
        if p["page_number"] == page_number:
            return p

    raise HTTPException(status_code=404, detail=f"Page {page_number} not found")


@app.get("/api/schemas")
async def list_schemas(user_id: str = Depends(_require_user)):
    """List available form schemas."""
    schemas = []
    if TEMPLATES_DIR.exists():
        for schema_file in TEMPLATES_DIR.glob("*_schema.json"):
            with open(schema_file, "r") as f:
                schema = json.load(f)
                schemas.append({
                    "name": schema.get("form_name", schema_file.stem),
                    "id": schema.get("form_id", schema_file.stem),
                    "path": str(schema_file),
                    "total_pages": schema.get("total_pages", 0),
                })
    return {"schemas": schemas}


@app.get("/api/extractions")
async def list_extractions(user_id: str = Depends(_require_user)):
    """List all extraction jobs from the database."""
    jobs = job_manager.list_jobs()
    return {
        "extractions": [
            {
                "job_id": j["id"],
                "status": j["status"],
                "total_pages": j.get("total_pages"),
                "created_at": j.get("created_at"),
                "completed_at": j.get("completed_at"),
            }
            for j in jobs
        ]
    }


# =============================================================================
# Patient Management
# =============================================================================

class CreatePatientRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    phone_primary: Optional[str] = None


@app.post("/api/patients")
async def create_patient(body: CreatePatientRequest, user_id: str = Depends(_require_user)):
    """Create a new patient record."""
    patient_id = job_manager.create_patient(
        first_name=body.first_name,
        last_name=body.last_name,
        date_of_birth=body.date_of_birth,
        phone_primary=body.phone_primary,
    )
    job_manager.write_audit_log(
        action="patient_created",
        resource_type="patient",
        resource_id=patient_id,
        user_id=user_id,
        details={"first_name": body.first_name, "last_name": body.last_name},
    )
    return {"patient_id": patient_id}


@app.get("/api/patients")
async def list_patients(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(_require_user),
):
    """List patients with document counts."""
    return job_manager.list_patients(search=search, limit=limit, offset=offset)


@app.get("/api/patients/{patient_id}")
async def get_patient_detail(patient_id: str, user_id: str = Depends(_require_user)):
    """Get full patient detail with documents and reports."""
    detail = job_manager.get_patient_detail(patient_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Patient not found")
    return detail


class CaseInfoRequest(BaseModel):
    claim_number: Optional[str] = None
    wcab_venue: Optional[str] = None
    case_number: Optional[str] = None
    injury_date: Optional[str] = None
    exam_date: Optional[str] = None
    interpreter_language: Optional[str] = None
    patient_sex: Optional[str] = None
    employer_name: Optional[str] = None
    occupation: Optional[str] = None
    patient_address: Optional[str] = None
    patient_city: Optional[str] = None
    patient_state: Optional[str] = None
    patient_zip: Optional[str] = None
    employer_address: Optional[str] = None
    employer_city: Optional[str] = None
    employer_state: Optional[str] = None
    employer_zip: Optional[str] = None
    claims_admin_name: Optional[str] = None
    claims_admin_address: Optional[str] = None
    claims_admin_city: Optional[str] = None
    claims_admin_state: Optional[str] = None
    claims_admin_zip: Optional[str] = None
    claims_admin_phone: Optional[str] = None


@app.post("/api/patients/{patient_id}/case-info")
async def save_case_info(
    patient_id: str,
    body: CaseInfoRequest,
    user_id: str = Depends(_require_user),
):
    """Upsert case/legal info into patient_medical_history for report generation."""
    sb = get_supabase()
    row = {k: v for k, v in body.model_dump().items() if v is not None}
    if not row:
        raise HTTPException(status_code=400, detail="No fields provided")
    row["patient_id"] = patient_id

    existing = sb.table("patient_medical_history").select("id").eq("patient_id", patient_id).limit(1).execute()
    if existing.data:
        sb.table("patient_medical_history").update(row).eq("id", existing.data[0]["id"]).execute()
    else:
        sb.table("patient_medical_history").insert(row).execute()

    job_manager.write_audit_log(
        action="case_info_saved",
        resource_type="patient",
        resource_id=patient_id,
        user_id=user_id,
        details={"fields_updated": list(row.keys())},
    )
    return {"status": "ok", "patient_id": patient_id}


# =============================================================================
# Document Management
# =============================================================================

@app.get("/api/documents")
async def list_documents(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(_require_user),
):
    """List all documents with patient info, job status, and report counts."""
    return job_manager.list_documents(search=search, status=status, limit=limit, offset=offset)


@app.get("/api/documents/{document_id}")
async def get_document_detail(document_id: str, user_id: str = Depends(_require_user)):
    """Get full document detail with jobs, results, reports, and audit log."""
    detail = job_manager.get_document_detail(document_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Document not found")
    return detail


@app.get("/api/documents/{document_id}/pages")
async def get_document_pages(document_id: str, user_id: str = Depends(_require_user)):
    """Get annotated page images for a document (signed URLs for re-opening in annotator)."""
    pages = job_manager.get_document_pages(document_id)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages found for this document")

    page_urls = []
    for p in pages:
        path = p.get("annotated_image_path") or p.get("original_image_path")
        signed_url = None
        if path:
            bucket = storage_manager.BUCKET_ANNOTATED if "annotated" in (path or "") else storage_manager.BUCKET_PAGES
            clean_path = path.replace(f"{bucket}/", "", 1) if path.startswith(bucket) else path
            # Remove leading bucket name prefix like "annotated/" if present
            for prefix in ("annotated/", "pages/", "originals/"):
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
                    break
            try:
                signed_url = storage_manager.get_signed_url(bucket, clean_path, expires_in=3600)
            except Exception as e:
                logger.warning("Failed to get signed URL for %s: %s", path, e)

        page_urls.append({
            "page_number": p["page_number"],
            "signed_url": signed_url,
            "annotated_image_path": p.get("annotated_image_path"),
            "original_image_path": p.get("original_image_path"),
        })

    return {"document_id": document_id, "pages": page_urls}


@app.post("/api/documents/{document_id}/reanalyze")
async def reanalyze_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_user),
):
    """Re-analyze an existing document by creating a new extraction job."""
    pages = job_manager.get_document_pages(document_id)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages found for this document")

    # Download annotated page images from storage
    tmp_dir = Path(tempfile.mkdtemp(prefix="di_reanalyze_"))
    image_paths = []
    page_info = []

    for p in pages:
        path = p.get("annotated_image_path") or p.get("original_image_path")
        if not path:
            continue

        bucket = storage_manager.BUCKET_ANNOTATED if "annotated" in path else storage_manager.BUCKET_PAGES
        clean_path = path
        for prefix in ("annotated/", "pages/", "originals/"):
            if clean_path.startswith(prefix):
                clean_path = clean_path[len(prefix):]
                break

        try:
            content = storage_manager.download_file(bucket, clean_path)
            filename = f"page_{p['page_number']:03d}.png"
            tmp_path = tmp_dir / filename
            tmp_path.write_bytes(content)
            image_paths.append(tmp_path)
            page_info.append(f"Page {p['page_number']}")
        except Exception as e:
            logger.warning("Failed to download page %d: %s", p["page_number"], e)

    if not image_paths:
        raise HTTPException(status_code=400, detail="Could not retrieve any page images for re-analysis")

    job_id = job_manager.create_job(document_id=document_id, total_pages=len(image_paths))
    job_manager.update_document(document_id, status="processing")

    job_manager.write_audit_log(
        action="reanalysis_started",
        resource_type="extraction_job",
        resource_id=job_id,
        user_id=user_id,
        details={"document_id": document_id, "pages": len(image_paths)},
    )

    background_tasks.add_task(
        run_extraction_images, job_id, document_id, image_paths,
        f"reanalysis_{document_id[:8]}", page_info,
        schema_path="templates/orofacial_exam_schema.json",
    )

    return {"job_id": job_id, "status": "pending", "message": f"Re-analysis started for {len(image_paths)} pages"}


# =============================================================================
# Report Persistence
# =============================================================================

@app.post("/api/reports")
async def save_report(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    report_type: str = Form("extraction_findings"),
    user_id: str = Depends(_require_user),
):
    """Upload a generated DOCX report to Supabase Storage and create a reports record."""
    logger.info("POST /api/reports — file=%s, job=%s", file.filename, job_id)

    content = await file.read()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    storage_path = f"reports/{timestamp}/{file.filename}"

    try:
        storage_manager.upload_file(
            storage_manager.BUCKET_REPORTS, storage_path, content,
            content_type=file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        logger.error("Failed to upload report to storage: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload report")

    if not document_id and job_id:
        job = job_manager.get_job(job_id)
        if job:
            document_id = job.get("document_id")

    patient_id = None
    if document_id:
        sb = get_supabase()
        doc = sb.table("documents").select("patient_id").eq("id", document_id).execute()
        if doc.data and doc.data[0].get("patient_id"):
            patient_id = doc.data[0]["patient_id"]

    report_id = job_manager.save_report(
        document_id=document_id,
        job_id=job_id,
        storage_path=storage_path,
        report_type=report_type,
        patient_id=patient_id,
        metadata={"original_filename": file.filename, "size_bytes": len(content)},
    )

    job_manager.write_audit_log(
        action="report_generated",
        resource_type="report",
        resource_id=report_id,
        user_id=user_id,
        details={"job_id": job_id, "document_id": document_id, "storage_path": storage_path},
    )

    return {"report_id": report_id, "storage_path": storage_path}


@app.get("/api/reports/{report_id}/download")
async def get_report_download_url(report_id: str, user_id: str = Depends(_require_user)):
    """Generate a signed download URL for a report."""
    sb = get_supabase()
    result = sb.table("reports").select("storage_path").eq("id", report_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    storage_path = result.data[0].get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="Report file not available")

    try:
        url = storage_manager.get_signed_url(storage_manager.BUCKET_REPORTS, storage_path, expires_in=3600)
        return {"report_id": report_id, "download_url": url}
    except Exception as e:
        logger.error("Failed to create signed URL for report %s: %s", report_id, e)
        raise HTTPException(status_code=500, detail="Failed to generate download URL")


# =============================================================================
# Clinical Report Generation
# =============================================================================

class ClinicalReportRequest(BaseModel):
    job_id: Optional[str] = None
    document_id: Optional[str] = None
    report_type: str = "clinical_report"


@app.post("/api/generate-clinical-report")
async def generate_clinical_report_endpoint(
    req: ClinicalReportRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_user),
):
    """Generate a clinical narrative DOCX from extraction results using learned rules."""
    from src.generators.clinical_report_generator import generate_clinical_report

    job_id = req.job_id
    document_id = req.document_id

    if not job_id and not document_id:
        raise HTTPException(status_code=400, detail="Either job_id or document_id is required")

    if not job_id and document_id:
        sb = get_supabase()
        jobs = (
            sb.table("extraction_jobs")
            .select("id")
            .eq("document_id", document_id)
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not jobs.data:
            raise HTTPException(status_code=404, detail="No completed extraction found for this document")
        job_id = jobs.data[0]["id"]

    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Extraction not completed — status: {job['status']}")

    pages = job_manager.get_extraction_results(job_id)
    if not pages:
        raise HTTPException(status_code=404, detail="No extraction results found")

    patient_info = job_manager.extract_patient_summary(pages)
    all_pages = [
        {
            "page_number": p["page_number"],
            "field_values": p.get("field_values", {}),
        }
        for p in pages
    ]

    extraction_data = {
        "patient_name": patient_info.get("patient_name"),
        "patient_dob": patient_info.get("patient_dob"),
        "form_date": patient_info.get("form_date"),
        "pages": all_pages,
    }

    if not document_id:
        document_id = job.get("document_id")

    patient_id = None
    patient_context = None
    if document_id:
        sb = get_supabase()
        doc = sb.table("documents").select("patient_id").eq("id", document_id).execute()
        if doc.data and doc.data[0].get("patient_id"):
            patient_id = doc.data[0]["patient_id"]
            try:
                pmh = sb.table("patient_medical_history").select("*").eq("patient_id", patient_id).limit(1).execute()
                if pmh.data:
                    row = pmh.data[0]
                    patient_context = {
                        k: str(v) for k, v in row.items()
                        if v is not None and k not in ("id", "patient_id", "created_at", "updated_at")
                    }
            except Exception as e:
                logger.debug("patient_medical_history fetch skipped: %s", e)

            try:
                pt = sb.table("patients").select("first_name, last_name, date_of_birth, phone_primary").eq("id", patient_id).limit(1).execute()
                if pt.data:
                    p = pt.data[0]
                    patient_context = patient_context or {}
                    if p.get("first_name"):
                        patient_context["patient_first_name"] = p["first_name"]
                    if p.get("last_name"):
                        patient_context["patient_last_name"] = p["last_name"]
                    if p.get("date_of_birth"):
                        patient_context["patient_dob"] = p["date_of_birth"]
                    if p.get("phone_primary"):
                        patient_context["patient_phone"] = p["phone_primary"]
            except Exception as e:
                logger.debug("patients table fetch skipped: %s", e)

    logger.info("Generating clinical report for job %s (%s) — %d pages",
                job_id, patient_info.get("patient_name"), len(all_pages))

    try:
        docx_bytes, low_confidence_fields, _gen_log = generate_clinical_report(
            extraction_data, patient_context=patient_context,
        )
    except Exception as e:
        logger.error("Clinical report generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    patient_name = (patient_info.get("patient_name") or "patient").replace(" ", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"clinical_report_{patient_name}_{timestamp}.docx"
    storage_path = f"reports/{timestamp}/{filename}"

    try:
        storage_manager.upload_file(
            storage_manager.BUCKET_REPORTS, storage_path, docx_bytes,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as e:
        logger.error("Failed to upload clinical report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to upload report")

    report_id = job_manager.save_report(
        document_id=document_id,
        job_id=job_id,
        storage_path=storage_path,
        report_type=req.report_type,
        patient_id=patient_id,
        metadata={"original_filename": filename, "size_bytes": len(docx_bytes), "generator": "clinical_rules_v1"},
    )

    job_manager.write_audit_log(
        action="clinical_report_generated",
        resource_type="report",
        resource_id=report_id,
        user_id=user_id,
        details={"job_id": job_id, "document_id": document_id, "storage_path": storage_path},
    )

    logger.info("Clinical report saved — report_id=%s, path=%s", report_id, storage_path)
    return {
        "report_id": report_id,
        "storage_path": storage_path,
        "filename": filename,
        "low_confidence_fields": low_confidence_fields,
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
