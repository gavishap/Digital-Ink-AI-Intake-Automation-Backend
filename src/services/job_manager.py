"""
Database-backed job tracking for extraction jobs.
Replaces the in-memory job_status dict with Supabase persistence.
"""

import logging
from datetime import datetime
from typing import Optional
from .supabase_client import get_supabase

logger = logging.getLogger(__name__)


def create_job(
    document_id: Optional[str] = None,
    total_pages: Optional[int] = None,
    initiated_by: Optional[str] = None,
) -> str:
    sb = get_supabase()
    row = {
        "status": "pending",
        "progress": 0,
        "percentage": 0,
        "current_stage": "Queued",
        "total_pages": total_pages,
    }
    if document_id:
        row["document_id"] = document_id
    if initiated_by:
        row["initiated_by"] = initiated_by

    result = sb.table("extraction_jobs").insert(row).execute()
    job_id = result.data[0]["id"]
    logger.info("Created extraction job %s (document=%s, pages=%s)", job_id, document_id, total_pages)
    return job_id


def update_job(job_id: str, **fields) -> None:
    sb = get_supabase()
    if "status" in fields and fields["status"] == "processing" and "started_at" not in fields:
        fields["started_at"] = datetime.utcnow().isoformat()
    if "status" in fields and fields["status"] in ("completed", "failed") and "completed_at" not in fields:
        fields["completed_at"] = datetime.utcnow().isoformat()

    sb.table("extraction_jobs").update(fields).eq("id", job_id).execute()

    if "status" in fields:
        logger.info("Job %s → %s", job_id[:8], fields["status"])
    elif "current_stage" in fields:
        logger.debug("Job %s stage: %s", job_id[:8], fields["current_stage"])


def get_job(job_id: str) -> Optional[dict]:
    sb = get_supabase()
    result = sb.table("extraction_jobs").select("*").eq("id", job_id).execute()
    return result.data[0] if result.data else None


def save_page_result(
    job_id: str,
    document_id: str,
    page_number: int,
    page_data: dict,
) -> str:
    sb = get_supabase()
    row = {
        "job_id": job_id,
        "document_id": document_id,
        "page_number": page_number,
        "field_values": page_data.get("field_values", {}),
        "visual_elements": page_data.get("visual_elements", []),
        "spatial_connections": page_data.get("spatial_connections", []),
        "annotation_groups": page_data.get("annotation_groups", []),
        "free_form_annotations": page_data.get("free_form_annotations", []),
        "circled_selections": page_data.get("circled_selections", []),
        "cross_page_references": page_data.get("cross_page_references", []),
        "unknown_marks": page_data.get("unknown_marks", []),
        "overall_confidence": page_data.get("overall_confidence", 0),
        "items_needing_review": page_data.get("items_needing_review", 0),
    }

    n_fields = len(page_data.get("field_values", {}))
    try:
        result = sb.table("extraction_results").insert(row).execute()
        result_id = result.data[0]["id"]
        logger.info(
            "Saved page %d results for job %s (%d fields, confidence=%.2f)",
            page_number, job_id[:8], n_fields, page_data.get("overall_confidence", 0),
        )
        return result_id
    except Exception as e:
        logger.error("FAILED saving page %d for job %s — %s", page_number, job_id[:8], e)
        raise


def create_document(
    file_name: str,
    file_type: str,
    storage_path: str,
    total_pages: Optional[int] = None,
    file_size_bytes: Optional[int] = None,
    document_type: Optional[str] = None,
    uploaded_by: Optional[str] = None,
) -> str:
    sb = get_supabase()
    row = {
        "file_name": file_name,
        "file_type": file_type,
        "storage_path": storage_path,
        "status": "uploaded",
    }
    if total_pages is not None:
        row["total_pages"] = total_pages
    if file_size_bytes is not None:
        row["file_size_bytes"] = file_size_bytes
    if document_type:
        row["document_type"] = document_type
    if uploaded_by:
        row["uploaded_by"] = uploaded_by

    result = sb.table("documents").insert(row).execute()
    doc_id = result.data[0]["id"]
    logger.info("Created document %s: %s (%s, %s bytes)", doc_id[:8], file_name, file_type, file_size_bytes)
    return doc_id


def update_document(document_id: str, **fields) -> None:
    sb = get_supabase()
    sb.table("documents").update(fields).eq("id", document_id).execute()
    if "status" in fields:
        logger.info("Document %s → %s", document_id[:8], fields["status"])


def save_document_page(
    document_id: str,
    page_number: int,
    original_image_path: Optional[str] = None,
    annotated_image_path: Optional[str] = None,
) -> str:
    sb = get_supabase()
    row = {
        "document_id": document_id,
        "page_number": page_number,
    }
    if original_image_path:
        row["original_image_path"] = original_image_path
    if annotated_image_path:
        row["annotated_image_path"] = annotated_image_path

    result = sb.table("document_pages").insert(row).execute()
    page_id = result.data[0]["id"]
    logger.debug("Saved document page %d for doc %s", page_number, document_id[:8])
    return page_id


def get_extraction_results(job_id: str) -> list[dict]:
    sb = get_supabase()
    result = (
        sb.table("extraction_results")
        .select("*")
        .eq("job_id", job_id)
        .order("page_number")
        .execute()
    )
    logger.info("Fetched %d extraction results for job %s", len(result.data), job_id[:8])
    return result.data


def list_jobs(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    sb = get_supabase()
    query = sb.table("extraction_jobs").select("*").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    return query.execute().data


# =============================================================================
# Patient extraction from results
# =============================================================================

_PATIENT_NAME_KEYS = {"patient_name", "name", "patient", "full_name", "patient_full_name"}
_DOB_KEYS = {"date_of_birth", "dob", "patient_dob", "birth_date", "birthdate"}
_DATE_KEYS = {"date", "form_date", "report_date", "exam_date", "visit_date", "signature_date"}
_GENDER_KEYS = {"gender", "sex", "patient_gender"}
_PHONE_KEYS = {"phone", "phone_number", "phone_primary", "patient_phone", "telephone"}
_EMAIL_KEYS = {"email", "patient_email", "email_address"}


def _find_field(field_values: dict, key_set: set[str]) -> Optional[str]:
    """Find the first matching field value from a set of possible keys."""
    for key in key_set:
        fv = field_values.get(key)
        if fv and isinstance(fv, dict) and fv.get("value"):
            return fv["value"]
    return None


def _split_name(full_name: str) -> tuple[str, str]:
    """Split a full name into (first_name, last_name)."""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("Unknown", "Unknown")
    if len(parts) == 1:
        return (parts[0], "Unknown")
    return (parts[0], " ".join(parts[1:]))


def extract_patient_from_results(pages: list[dict], document_id: Optional[str] = None) -> Optional[str]:
    """
    Scan extraction results for patient-identifying fields and upsert a patient record.
    Returns the patient_id if created/found, or None.
    """
    all_fields: dict = {}
    for page in pages:
        fv = page.get("field_values", {})
        if isinstance(fv, dict):
            all_fields.update(fv)

    patient_name = _find_field(all_fields, _PATIENT_NAME_KEYS)
    if not patient_name:
        logger.info("No patient name found in extraction results — skipping patient creation")
        return None

    first_name, last_name = _split_name(patient_name)

    row: dict = {"first_name": first_name, "last_name": last_name}

    dob = _find_field(all_fields, _DOB_KEYS)
    if dob:
        row["date_of_birth"] = dob

    gender = _find_field(all_fields, _GENDER_KEYS)
    if gender:
        row["gender"] = gender

    phone = _find_field(all_fields, _PHONE_KEYS)
    if phone:
        row["phone_primary"] = phone

    email = _find_field(all_fields, _EMAIL_KEYS)
    if email:
        row["email"] = email

    sb = get_supabase()
    try:
        result = sb.table("patients").insert(row).execute()
        patient_id = result.data[0]["id"]
        logger.info("Created patient %s: %s %s", patient_id[:8], first_name, last_name)

        if document_id:
            sb.table("documents").update({"patient_id": patient_id}).eq("id", document_id).execute()
            logger.info("Linked document %s → patient %s", document_id[:8], patient_id[:8])

        return patient_id
    except Exception as e:
        logger.error("Failed to create patient: %s", e)
        return None


def extract_patient_summary(pages: list[dict]) -> dict:
    """Extract patient_name, patient_dob, and form_date from extraction results."""
    all_fields: dict = {}
    for page in pages:
        fv = page.get("field_values", {})
        if isinstance(fv, dict):
            all_fields.update(fv)

    return {
        "patient_name": _find_field(all_fields, _PATIENT_NAME_KEYS),
        "patient_dob": _find_field(all_fields, _DOB_KEYS),
        "form_date": _find_field(all_fields, _DATE_KEYS),
    }


# =============================================================================
# Report persistence
# =============================================================================

def save_report(
    document_id: Optional[str],
    job_id: Optional[str],
    storage_path: str,
    report_type: str = "extraction_findings",
    patient_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> str:
    """Create a report record linking to a stored DOCX in Supabase Storage."""
    sb = get_supabase()
    row: dict = {
        "report_type": report_type,
        "status": "final",
        "storage_path": storage_path,
        "metadata": metadata or {},
    }
    if patient_id:
        row["patient_id"] = patient_id
    if job_id:
        row["source_extraction_ids"] = [job_id]
    if document_id:
        row["source_document_ids"] = [document_id]

    result = sb.table("reports").insert(row).execute()
    report_id = result.data[0]["id"]
    logger.info("Created report %s (type=%s, path=%s)", report_id[:8], report_type, storage_path)
    return report_id


# =============================================================================
# Audit logging
# =============================================================================

def write_audit_log(
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Write an entry to the audit_log table."""
    sb = get_supabase()
    row: dict = {"action": action}
    if resource_type:
        row["resource_type"] = resource_type
    if resource_id:
        row["resource_id"] = resource_id
    if user_id:
        row["user_id"] = user_id
    if details:
        row["details"] = details

    try:
        sb.table("audit_log").insert(row).execute()
        logger.debug("Audit: %s %s/%s", action, resource_type, resource_id and resource_id[:8])
    except Exception as e:
        logger.warning("Failed to write audit log: %s", e)
