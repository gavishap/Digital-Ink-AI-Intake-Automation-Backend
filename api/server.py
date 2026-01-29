"""
FastAPI server for the Form Extractor AI Engine.
Provides REST API endpoints for document analysis and report generation.
"""

import os
import sys
import uuid
import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

from src.services.pdf_processor import PDFProcessor
from src.services.extraction_pipeline import ExtractionPipeline
from src.generators.schema_generator import SchemaGenerator

# Initialize FastAPI app
app = FastAPI(
    title="Form Extractor API",
    description="AI-powered medical form extraction using Claude",
    version="1.0.0",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTIONS_DIR = BASE_DIR / "extractions"
UPLOADS_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"
ANNOTATED_FORMS_DIR = BASE_DIR / "annotated_forms"

# Ensure directories exist
EXTRACTIONS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
ANNOTATED_FORMS_DIR.mkdir(exist_ok=True)

# In-memory job status tracking
job_status: dict = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for analysis endpoint."""
    name: Optional[str] = None
    schema_path: Optional[str] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None


class AnalyzeResponse(BaseModel):
    """Response model for analysis endpoint."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: Optional[int] = None
    total_pages: Optional[int] = None
    percentage: Optional[float] = None
    current_stage: Optional[str] = None
    message: Optional[str] = None
    result_path: Optional[str] = None


class ExtractionResultSummary(BaseModel):
    """Summary of extraction results."""
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

def run_extraction(
    job_id: str,
    file_path: Path,
    name: str,
    schema_path: Optional[str] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
):
    """Run the extraction pipeline as a background task."""
    try:
        job_status[job_id]["status"] = "processing"
        job_status[job_id]["current_stage"] = "Initializing"
        
        # Initialize services
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        
        pdf_processor = PDFProcessor(dpi=150)
        pipeline = ExtractionPipeline(api_key=api_key)
        
        # Load schema if provided
        form_schema = None
        if schema_path and Path(schema_path).exists():
            schema_gen = SchemaGenerator(TEMPLATES_DIR)
            form_schema = schema_gen.load_form_schema(Path(schema_path))
        
        # Convert PDF to images
        job_status[job_id]["current_stage"] = "Converting PDF to images"
        
        if file_path.suffix.lower() == ".pdf":
            image_paths = pdf_processor.convert_pdf_to_images(
                file_path,
                prefix=name,
                start_page=start_page,
                end_page=end_page,
            )
        else:
            # Single image
            image_paths = [file_path]
        
        job_status[job_id]["total_pages"] = len(image_paths)
        
        # Run extraction
        job_status[job_id]["current_stage"] = "Running AI extraction"
        
        result = pipeline.extract_form(
            image_paths=image_paths,
            form_schema=form_schema,
            form_name=name,
        )
        
        # Save results
        job_status[job_id]["current_stage"] = "Saving results"
        
        output_dir = EXTRACTIONS_DIR / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Save complete extraction
        extraction_path = output_dir / f"{name}_extraction.json"
        with open(extraction_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        # Save per-page results
        for page in result.pages:
            page_path = output_dir / f"{name}_page_{page.page_number}.json"
            with open(page_path, "w") as f:
                json.dump(page.model_dump(), f, indent=2, default=str)
        
        # Save summary
        summary_path = output_dir / f"{name}_summary.txt"
        with open(summary_path, "w") as f:
            f.write(f"Extraction Summary: {name}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Patient Name: {result.patient_name or 'Not detected'}\n")
            f.write(f"Patient DOB: {result.patient_dob or 'Not detected'}\n")
            f.write(f"Form Date: {result.form_date or 'Not detected'}\n")
            f.write(f"Extracted: {result.extraction_timestamp}\n\n")
            f.write(f"Overall Confidence: {result.overall_confidence * 100:.1f}%\n")
            f.write(f"Items Needing Review: {result.total_items_needing_review}\n")
            f.write(f"Total Pages: {len(result.pages)}\n")
        
        # Update job status
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["result_path"] = str(output_dir)
        job_status[job_id]["message"] = "Extraction completed successfully"
        job_status[job_id]["current_stage"] = "Completed"
        
        # Clean up temp files
        pdf_processor.cleanup()
        
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = str(e)
        job_status[job_id]["current_stage"] = "Failed"


def run_extraction_images(
    job_id: str,
    image_paths: List[Path],
    name: str,
    schema_path: Optional[str] = None,
):
    """Run the extraction pipeline on a batch of images as a background task with parallel processing."""
    try:
        job_status[job_id]["status"] = "processing"
        job_status[job_id]["current_stage"] = "Initializing"
        job_status[job_id]["percentage"] = 0
        
        # Log page info if available
        page_info = job_status[job_id].get("page_info", [])
        if page_info:
            print(f"\n📄 Analyzing {len(page_info)} annotated pages:")
            for i, info in enumerate(page_info):
                print(f"   {i + 1}. {info}")
            print()
        
        # Initialize services
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        
        pipeline = ExtractionPipeline(api_key=api_key)
        
        # Load schema if provided
        form_schema = None
        if schema_path and Path(schema_path).exists():
            schema_gen = SchemaGenerator(TEMPLATES_DIR)
            form_schema = schema_gen.load_form_schema(Path(schema_path))
        
        job_status[job_id]["total_pages"] = len(image_paths)
        job_status[job_id]["progress"] = 0
        
        # Progress callback for real-time updates
        def progress_callback(completed: int, total: int, percentage: float):
            job_status[job_id]["progress"] = completed
            job_status[job_id]["percentage"] = percentage
            completed_info = page_info[completed - 1] if completed <= len(page_info) else f"Page {completed}"
            job_status[job_id]["current_stage"] = f"Analyzing: {completed_info} ({percentage}% complete)"
        
        # Run extraction with parallel processing
        job_status[job_id]["current_stage"] = "Running AI extraction (parallel)"
        
        result = pipeline.extract_form(
            image_paths=image_paths,
            form_schema=form_schema,
            form_name=name,
            max_workers=4,  # Process 4 pages concurrently
            progress_callback=progress_callback,
        )
        
        # Save results
        job_status[job_id]["current_stage"] = "Saving results"
        job_status[job_id]["percentage"] = 95
        
        output_dir = EXTRACTIONS_DIR / job_id
        output_dir.mkdir(exist_ok=True)
        
        # Save complete extraction
        extraction_path = output_dir / f"{name}_extraction.json"
        with open(extraction_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        # Save per-page results
        for page in result.pages:
            page_path = output_dir / f"{name}_page_{page.page_number}.json"
            with open(page_path, "w") as f:
                json.dump(page.model_dump(), f, indent=2, default=str)
        
        # Save summary with page details
        page_info = job_status[job_id].get("page_info", [])
        annotated_forms_path = job_status[job_id].get("annotated_forms_path", "")
        
        summary_path = output_dir / f"{name}_summary.txt"
        with open(summary_path, "w") as f:
            f.write(f"Extraction Summary: {name}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Patient Name: {result.patient_name or 'Not detected'}\n")
            f.write(f"Patient DOB: {result.patient_dob or 'Not detected'}\n")
            f.write(f"Form Date: {result.form_date or 'Not detected'}\n")
            f.write(f"Extracted: {result.extraction_timestamp}\n\n")
            f.write(f"Overall Confidence: {result.overall_confidence * 100:.1f}%\n")
            f.write(f"Items Needing Review: {result.total_items_needing_review}\n")
            f.write(f"Total Pages Analyzed: {len(result.pages)}\n\n")
            
            if page_info:
                f.write("Pages Analyzed (with original page numbers):\n")
                f.write("-" * 40 + "\n")
                for i, info in enumerate(page_info):
                    f.write(f"  {i + 1}. {info}\n")
                f.write("\n")
            
            if annotated_forms_path:
                f.write(f"Annotated Forms Saved: {annotated_forms_path}\n")
        
        # Update job status
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["result_path"] = str(output_dir)
        job_status[job_id]["message"] = "Extraction completed successfully"
        job_status[job_id]["current_stage"] = "Completed"
        job_status[job_id]["percentage"] = 100
        
        print(f"\n✅ Extraction complete!")
        print(f"   Results: {output_dir}")
        print(f"   Annotated forms: {annotated_forms_path}")
        
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = str(e)
        job_status[job_id]["current_stage"] = "Failed"
        job_status[job_id]["percentage"] = 0


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return {
        "status": "healthy",
        "api_key_configured": bool(api_key),
        "extractions_dir": str(EXTRACTIONS_DIR),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = None,
    schema_path: Optional[str] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
):
    """
    Upload and analyze a document.
    
    - Accepts PDF files or images
    - Runs the 6-stage extraction pipeline
    - Returns a job ID for tracking progress
    """
    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
        )
    
    # Generate job ID and name
    job_id = str(uuid.uuid4())[:8]
    if not name:
        name = Path(file.filename).stem.lower().replace(" ", "_")
    
    # Save uploaded file
    upload_path = UPLOADS_DIR / f"{job_id}_{file.filename}"
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Initialize job status
    job_status[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "total_pages": None,
        "current_stage": "Queued",
        "message": "Analysis queued",
        "result_path": None,
        "file_name": file.filename,
        "name": name,
    }
    
    # Start background extraction
    background_tasks.add_task(
        run_extraction,
        job_id,
        upload_path,
        name,
        schema_path,
        start_page,
        end_page,
    )
    
    return AnalyzeResponse(
        job_id=job_id,
        status="pending",
        message=f"Analysis started for {file.filename}",
    )


@app.post("/api/analyze-images", response_model=AnalyzeResponse)
async def analyze_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    name: Optional[str] = None,
    schema_path: Optional[str] = None,
    page_metadata: Optional[str] = None,  # JSON string with page info
):
    """
    Upload and analyze multiple page images as a batch.
    
    - Accepts multiple PNG/JPEG images (one per page)
    - Used when capturing annotated pages from the PDF annotator
    - Runs the 6-stage extraction pipeline on all images
    - Saves annotated forms permanently with proper naming
    - Returns a job ID for tracking progress
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    for f in files:
        file_ext = Path(f.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}",
            )
    
    # Parse page metadata if provided
    parsed_metadata = None
    if page_metadata:
        try:
            parsed_metadata = json.loads(page_metadata)
        except json.JSONDecodeError:
            pass
    
    # Generate job ID and name
    job_id = str(uuid.uuid4())[:8]
    if not name:
        name = f"batch_{job_id}"
    
    # Create directories for this job
    job_upload_dir = UPLOADS_DIR / job_id
    job_upload_dir.mkdir(exist_ok=True)
    
    # Create annotated forms directory for permanent storage
    job_annotated_dir = ANNOTATED_FORMS_DIR / job_id
    job_annotated_dir.mkdir(exist_ok=True)
    
    # Save all uploaded files with proper naming
    image_paths = []
    page_info = []  # Track page info for logging
    
    for i, file in enumerate(files):
        # Get metadata for this page
        meta = parsed_metadata[i] if parsed_metadata and i < len(parsed_metadata) else None
        
        if meta:
            doc_name = meta.get("documentName", "unknown").replace(" ", "_")
            orig_page = meta.get("originalPageNumber", i + 1)
            filename = f"{doc_name}_page_{orig_page:03d}.png"
            page_info.append(f"{meta.get('documentName', 'Unknown')} page {orig_page}")
        else:
            filename = f"page_{i + 1:03d}.png"
            page_info.append(f"Page {i + 1}")
        
        # Save to uploads (for processing)
        upload_path = job_upload_dir / filename
        content = await file.read()
        with open(upload_path, "wb") as f:
            f.write(content)
        image_paths.append(upload_path)
        
        # Also save to annotated_forms (permanent storage)
        annotated_path = job_annotated_dir / filename
        with open(annotated_path, "wb") as f:
            f.write(content)
    
    # Initialize job status with percentage and page metadata
    job_status[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "total_pages": len(files),
        "percentage": 0,
        "current_stage": "Queued",
        "message": f"Analysis queued for {len(files)} pages",
        "result_path": None,
        "annotated_forms_path": str(job_annotated_dir),
        "file_name": f"{len(files)} page images",
        "name": name,
        "page_metadata": parsed_metadata,
        "page_info": page_info,
    }
    
    # Start background extraction with parallel processing
    background_tasks.add_task(
        run_extraction_images,
        job_id,
        image_paths,
        name,
        schema_path,
    )
    
    # Build detailed message
    pages_detail = ", ".join(page_info[:3])
    if len(page_info) > 3:
        pages_detail += f" ...and {len(page_info) - 3} more"
    
    return AnalyzeResponse(
        job_id=job_id,
        status="pending",
        message=f"Analysis started for {len(files)} pages: {pages_detail}",
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an analysis job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**job_status[job_id])


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get the extraction results for a completed job."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_status[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}",
        )
    
    # Load and return results
    result_dir = Path(job["result_path"])
    name = job["name"]
    
    extraction_path = result_dir / f"{name}_extraction.json"
    if not extraction_path.exists():
        raise HTTPException(status_code=404, detail="Results file not found")
    
    with open(extraction_path, "r") as f:
        results = json.load(f)
    
    return results


@app.get("/api/results/{job_id}/summary")
async def get_results_summary(job_id: str):
    """Get a summary of the extraction results."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_status[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}",
        )
    
    # Load results and return summary
    result_dir = Path(job["result_path"])
    name = job["name"]
    
    extraction_path = result_dir / f"{name}_extraction.json"
    if not extraction_path.exists():
        raise HTTPException(status_code=404, detail="Results file not found")
    
    with open(extraction_path, "r") as f:
        results = json.load(f)
    
    return ExtractionResultSummary(
        job_id=job_id,
        patient_name=results.get("patient_name"),
        patient_dob=results.get("patient_dob"),
        form_date=results.get("form_date"),
        overall_confidence=results.get("overall_confidence", 0),
        total_pages=len(results.get("pages", [])),
        total_items_needing_review=results.get("total_items_needing_review", 0),
        extraction_timestamp=results.get("extraction_timestamp", ""),
    )


@app.get("/api/results/{job_id}/page/{page_number}")
async def get_page_results(job_id: str, page_number: int):
    """Get results for a specific page."""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_status[job_id]
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}",
        )
    
    result_dir = Path(job["result_path"])
    name = job["name"]
    
    page_path = result_dir / f"{name}_page_{page_number}.json"
    if not page_path.exists():
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found")
    
    with open(page_path, "r") as f:
        page_results = json.load(f)
    
    return page_results


@app.get("/api/schemas")
async def list_schemas():
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
async def list_extractions():
    """List all completed extractions."""
    extractions = []
    
    for job_id, job in job_status.items():
        if job["status"] == "completed":
            extractions.append({
                "job_id": job_id,
                "name": job.get("name"),
                "file_name": job.get("file_name"),
                "status": job["status"],
            })
    
    return {"extractions": extractions}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
