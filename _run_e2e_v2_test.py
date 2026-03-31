"""
E2E Pipeline Comparison Test V2

Starts from raw signed PDF exams, runs the full production-equivalent pipeline
locally (page trimming, 2-stage vision extraction with merged schemas for old-format
pages, first-page context parsing, report generation), then compares 3 generated
reports against the real doctor-written reports section-by-section using
Together/Fireworks LLMs.

Run from: c:/Digital_Ink/form-extractor
Usage:    python _run_e2e_v2_test.py              # full run (all stages)
          python _run_e2e_v2_test.py --stage 4    # re-run from report generation (skip extraction)
          python _run_e2e_v2_test.py --stage 6    # re-run comparison + final report only
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from rich.console import Console
from rich.table import Table

from src.models import PageSchema, FormSchema, PageExtractionResult, FormExtractionResult
from src.services.extraction_pipeline import ExtractionPipeline
from src.services.pdf_processor import PDFProcessor
from report_learning.scanner.docx_parser import parse_docx

spec = importlib.util.spec_from_file_location(
    "crg", str(Path(__file__).parent / "src" / "generators" / "clinical_report_generator.py")
)
crg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crg)

console = Console(record=True)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
PDF_DIR = BASE / "report_learning" / "training_data" / "source_forms" / "Matthew Signed Documents"
SCAN_DIR = BASE / "report_learning" / "outputs" / "scanned"
TEMPLATES_DIR = BASE / "templates"
OUT_DIR = BASE / "report_learning" / "outputs" / "e2e_v2"

PATIENTS = [
    {
        "name": "Isaac Lupercio",
        "pdf": PDF_DIR / "ISAAC LUPERCIO INIT.pdf",
        "scan": SCAN_DIR / "lupercio.isaac.011126.INI_scan.json",
        "slug": "lupercio",
        "skip_start": 2,
        "skip_end": 1,
    },
    {
        "name": "Jorge Rivera",
        "pdf": PDF_DIR / "JORGE RIVERA INIT.pdf",
        "scan": SCAN_DIR / "rivera.jorge.011126.INI_scan.json",
        "slug": "rivera",
        "skip_start": 1,
        "skip_end": 1,
    },
    {
        "name": "Margalit Bachar",
        "pdf": PDF_DIR / "MARGALIT BACHAR INIT.pdf",
        "scan": SCAN_DIR / "bachar.margalit.011126.INI_scan.json",
        "slug": "bachar",
        "skip_start": 1,
        "skip_end": 1,
    },
]

STAGE_DIRS = [
    "stage1_split",
    "stage2_context",
    "stage3_extraction",
    "stage4_report",
    "stage5_parsed",
    "stage6_comparison",
]

# LLM config for comparison (Together/Fireworks)
TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
TOGETHER_BASE_URL = "https://api.together.xyz/v1"
FIREWORKS_MODEL = "accounts/fireworks/models/deepseek-v3p1"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _banner(stage: int, title: str, patient: str = "") -> None:
    label = f"STAGE {stage}: {title}"
    if patient:
        label += f"  —  {patient}"
    console.print(f"\n{'='*70}")
    console.print(f"  {label}")
    console.print(f"{'='*70}")


def _merge_page_schemas(primary: PageSchema, donor: PageSchema) -> PageSchema:
    merged = primary.model_copy(deep=True)
    merged.sections.extend(donor.sections)
    merged.standalone_fields.extend(donor.standalone_fields)
    merged.standalone_tables.extend(donor.standalone_tables)
    return merged


def _build_comparison_client() -> tuple[OpenAI, str] | None:
    together_key = os.getenv("TOGETHER_API_KEY")
    if together_key:
        return OpenAI(api_key=together_key, base_url=TOGETHER_BASE_URL, timeout=120.0), TOGETHER_MODEL
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if fireworks_key:
        return OpenAI(api_key=fireworks_key, base_url=FIREWORKS_BASE_URL, timeout=120.0), FIREWORKS_MODEL
    return None


def _extract_section_text(section: dict) -> str:
    heading = section.get("heading", "")
    parts = [heading] if heading else []
    for el in section.get("elements", []):
        txt = el.get("text", "").strip()
        if txt:
            parts.append(txt)
    return "\n".join(parts)


def _extract_full_text(scan_data: dict) -> str:
    parts = []
    for sec in scan_data.get("sections", []):
        parts.append(_extract_section_text(sec))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Stage 0: Setup
# ---------------------------------------------------------------------------

def stage0_setup() -> None:
    _banner(0, "SETUP")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for d in STAGE_DIRS:
        (OUT_DIR / d).mkdir(exist_ok=True)

    for p in PATIENTS:
        assert p["pdf"].exists(), f"PDF not found: {p['pdf']}"
        assert p["scan"].exists(), f"Scan not found: {p['scan']}"
    console.print(f"  Output dir: {OUT_DIR}")
    console.print(f"  Patients: {', '.join(p['name'] for p in PATIENTS)}")
    console.print("  All input files verified.")


# ---------------------------------------------------------------------------
# Stage 1: PDF to images + page trimming + schema plan
# ---------------------------------------------------------------------------

def stage1_split(patient: dict) -> tuple[list[Path], list[dict]]:
    _banner(1, "PDF SPLIT + SCHEMA PLAN", patient["name"])
    slug = patient["slug"]
    img_dir = OUT_DIR / "stage1_split" / f"{slug}_page_images"
    img_dir.mkdir(parents=True, exist_ok=True)

    processor = PDFProcessor(dpi=250, output_dir=img_dir)
    all_images = processor.convert_pdf_to_images(patient["pdf"], prefix="page")
    console.print(f"  Total PDF pages: {len(all_images)}")

    skip_s = patient["skip_start"]
    skip_e = patient["skip_end"]
    exam_images = all_images[skip_s: len(all_images) - skip_e]
    console.print(f"  After trimming (skip_start={skip_s}, skip_end={skip_e}): {len(exam_images)} exam pages")

    _save_json(OUT_DIR / "stage1_split" / f"{slug}_page_trim.json", {
        "total_pdf_pages": len(all_images),
        "skip_start": skip_s,
        "skip_end": skip_e,
        "exam_page_count": len(exam_images),
    })

    schema_plan = []
    for i in range(1, 21):
        if i == 3:
            schema_plan.append({
                "exam_page": i, "mode": "merged_schema",
                "schema_pages": [3, 11],
                "note": "old format: has Epworth (p11 fields) + bad breath (p3 fields)",
            })
        elif i == 4:
            schema_plan.append({
                "exam_page": i, "mode": "merged_schema",
                "schema_pages": [4, 3],
                "note": "old format: has dry mouth at bottom (p3 fields)",
            })
        elif i == 8:
            schema_plan.append({
                "exam_page": i, "mode": "standard",
                "schema_pages": [8],
                "note": "old format: missing Tx Received at top, rest identical",
            })
        elif i == 11:
            schema_plan.append({
                "exam_page": i, "mode": "standard",
                "schema_pages": [11],
                "note": "old format: no Epworth at bottom (already on page 3)",
            })
        else:
            schema_plan.append({
                "exam_page": i, "mode": "standard",
                "schema_pages": [i], "note": "identical layout",
            })

    _save_json(OUT_DIR / "stage1_split" / f"{slug}_schema_plan.json", schema_plan)

    table = Table(title="Schema Plan")
    table.add_column("Page", style="cyan", width=6)
    table.add_column("Mode", style="green", width=15)
    table.add_column("Schema Pages", width=14)
    table.add_column("Note", width=50)
    for sp in schema_plan:
        mode_style = "bold yellow" if sp["mode"] == "merged_schema" else ""
        table.add_row(
            str(sp["exam_page"]),
            f"[{mode_style}]{sp['mode']}[/]" if mode_style else sp["mode"],
            str(sp["schema_pages"]),
            sp["note"],
        )
    console.print(table)

    return exam_images, schema_plan


# ---------------------------------------------------------------------------
# Stage 2: Parse ground-truth report cover into patient_context
# ---------------------------------------------------------------------------

def stage2_context(patient: dict) -> dict[str, str]:
    _banner(2, "PARSE PATIENT CONTEXT", patient["name"])
    slug = patient["slug"]
    scan_data = _load_json(patient["scan"])

    cover_elements = []
    for sec in scan_data.get("sections", []):
        if sec.get("id") == "and_request_for_authorization":
            cover_elements = sec.get("elements", [])
            break

    _save_json(OUT_DIR / "stage2_context" / f"{slug}_raw_cover_elements.json", cover_elements)

    ctx: dict[str, str] = {}
    field_map = {
        "DATE:": "exam_date",
        "CLAIM:": "claim_number",
        "WCAB:": "wcab_venue",
        "Case #:": "case_number",
        "Date of Injury:": "date_of_injury",
        "Date of current exam:": "exam_date",
        "Last Name:": "patient_last_name",
        "First Name:": "patient_first_name",
        "Sex:": "patient_sex",
        "Date of Birth:": "patient_dob",
        "Occupation:": "occupation",
        "Address:": None,
        "City:": None,
        "State:": None,
        "Zip:": None,
        "Phone No.:": "patient_phone",
        "Phone:": None,
        "Interpreter:": "interpreter",
    }

    current_section = "case"
    for el in cover_elements:
        text = el.get("text", "").strip()
        if not text:
            continue

        if el.get("bold") and text == "Patient":
            current_section = "patient"
            continue
        elif el.get("bold") and "Claims Administrator" in text:
            current_section = "claims_admin"
            continue
        elif el.get("bold") and text == "Employer":
            current_section = "employer"
            continue

        for label, key in field_map.items():
            if text.startswith(label) or text.replace("\t", " ").startswith(label):
                value = re.split(r":\s*\t*", text, maxsplit=1)[-1].strip()

                if key:
                    ctx[key] = value
                elif label == "Address:":
                    prefix = {"patient": "patient_", "claims_admin": "claims_admin_", "employer": "employer_"}.get(current_section, "")
                    ctx[f"{prefix}address"] = value
                elif label == "City:":
                    prefix = {"patient": "patient_", "claims_admin": "claims_admin_", "employer": "employer_"}.get(current_section, "")
                    ctx[f"{prefix}city"] = value
                elif label == "State:":
                    prefix = {"patient": "patient_", "claims_admin": "claims_admin_", "employer": "employer_"}.get(current_section, "")
                    ctx[f"{prefix}state"] = value
                elif label == "Zip:":
                    prefix = {"patient": "patient_", "claims_admin": "claims_admin_", "employer": "employer_"}.get(current_section, "")
                    ctx[f"{prefix}zip"] = value
                elif label == "Phone:":
                    prefix = {"claims_admin": "claims_admin_", "employer": "employer_"}.get(current_section, "")
                    ctx[f"{prefix}phone"] = value

                if label == "Name:" and current_section == "claims_admin":
                    ctx["claims_admin_name"] = value
                elif label == "Name:" and current_section == "employer":
                    ctx["employer_name"] = value
                break

        if text.startswith("Name:") or ("\tName:" in text):
            value = re.split(r"Name:\s*\t*", text, maxsplit=1)[-1].strip()
            if current_section == "claims_admin":
                ctx["claims_admin_name"] = value
            elif current_section == "employer":
                ctx["employer_name"] = value

    ctx.setdefault("venue", ctx.get("wcab_venue", ""))

    _save_json(OUT_DIR / "stage2_context" / f"{slug}_patient_context.json", ctx)

    table = Table(title="Patient Context")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    for k, v in sorted(ctx.items()):
        table.add_row(k, v)
    console.print(table)

    return ctx


# ---------------------------------------------------------------------------
# Stage 3: Run 2-stage extraction pipeline
# ---------------------------------------------------------------------------

def stage3_extraction(
    patient: dict,
    schema_plan: list[dict],
    exam_images: list[Path],
) -> dict[str, Any]:
    _banner(3, "EXTRACTION (2-STAGE VLM)", patient["name"])
    slug = patient["slug"]
    ext_dir = OUT_DIR / "stage3_extraction" / slug
    ext_dir.mkdir(parents=True, exist_ok=True)

    schema_data = _load_json(TEMPLATES_DIR / "orofacial_exam_schema.json")

    def _fix_enum_values(obj):
        """Fix non-standard enum values in the schema before Pydantic validation."""
        if isinstance(obj, dict):
            if obj.get("field_type") == "number":
                obj["field_type"] = "text_numeric"
            if obj.get("data_type") == "number":
                obj["data_type"] = "int"
            for v in obj.values():
                _fix_enum_values(v)
        elif isinstance(obj, list):
            for item in obj:
                _fix_enum_values(item)

    _fix_enum_values(schema_data)
    form_schema = FormSchema(**schema_data)
    schema_pages = {ps.page_number: ps for ps in form_schema.pages}

    blank_templates = {}
    for i in range(1, 21):
        bp = TEMPLATES_DIR / f"orofacial_exam_blank_page_{i}.png"
        if bp.exists():
            blank_templates[i] = bp

    pipeline = ExtractionPipeline()
    pages: list[PageExtractionResult] = []
    stats: list[dict] = []

    for idx, sp in enumerate(schema_plan):
        page_num = sp["exam_page"]
        mode = sp["mode"]
        image_path = exam_images[idx]

        if mode == "merged_schema":
            primary_num = sp["schema_pages"][0]
            donor_num = sp["schema_pages"][1]
            primary_schema = schema_pages[primary_num]
            donor_schema = schema_pages[donor_num]
            page_schema = _merge_page_schemas(primary_schema, donor_schema)
            blank_path = None
            _save_json(ext_dir / f"page_{page_num:02d}_merged_schema.json",
                       json.loads(page_schema.model_dump_json()))
        else:
            page_schema = schema_pages[page_num]
            blank_path = blank_templates.get(page_num)

        console.print(f"  Page {page_num:2d} [{mode:14s}] extracting...", end=" ")
        t0 = time.time()
        try:
            result = pipeline.extract_page(
                image_path=image_path,
                page_number=page_num,
                page_schema=page_schema,
                blank_image_path=blank_path,
                extraction_mode="differential" if blank_path else "standard",
            )
        except Exception as e:
            console.print(f"[red]FAILED: {e}[/red]")
            result = PageExtractionResult(
                page_number=page_num, overall_confidence=0.0,
                items_needing_review=1, review_reasons=[str(e)],
            )
        elapsed = time.time() - t0

        pages.append(result)
        result_dict = json.loads(result.model_dump_json())
        _save_json(ext_dir / f"page_{page_num:02d}_raw.json", result_dict)

        field_count = len(result.field_values) if result.field_values else 0
        conf = result.overall_confidence
        console.print(f"fields={field_count:3d}  conf={conf:.2f}  time={elapsed:.1f}s")

        summary_lines = [f"Page {page_num} | Mode: {mode} | Fields: {field_count} | Confidence: {conf:.2f}"]
        if result.field_values:
            for fid, fv in result.field_values.items():
                val = fv.get("value", "") if isinstance(fv, dict) else fv
                if val is None and isinstance(fv, dict):
                    checked = fv.get("is_checked")
                    if checked is not None:
                        val = "YES" if checked else "NO"
                c = fv.get("confidence", 1.0) if isinstance(fv, dict) else 1.0
                summary_lines.append(f"  {fid:50s} = {str(val)[:60]:60s}  conf={c:.2f}")
        (ext_dir / f"page_{page_num:02d}_fields_summary.txt").write_text(
            "\n".join(summary_lines), encoding="utf-8"
        )

        stats.append({
            "page": page_num, "mode": mode, "fields": field_count,
            "confidence": conf, "elapsed": round(elapsed, 1),
            "review_flags": len(result.review_reasons),
        })

    patient_name = patient_dob = form_date = None
    if pages and pages[0].field_values:
        for field_id, value in pages[0].field_values.items():
            if isinstance(value, dict):
                v = value.get("value")
            else:
                v = value
            if v is None:
                continue
            fid_lower = field_id.lower()
            if "name" in fid_lower and not patient_name:
                patient_name = str(v)
            if "dob" in fid_lower or "birth" in fid_lower:
                patient_dob = str(v)
            if "date" in fid_lower and "birth" not in fid_lower and not form_date:
                form_date = str(v)

    extraction_data = {
        "patient_name": patient_name or patient["name"],
        "patient_dob": patient_dob,
        "form_date": form_date,
        "pages": [
            {"page_number": p.page_number, "field_values": p.field_values or {}}
            for p in pages
        ],
    }

    _save_json(ext_dir / "extraction_combined.json", extraction_data)
    _save_json(ext_dir / "extraction_stats.json", stats)

    table = Table(title=f"Extraction Summary — {patient['name']}")
    table.add_column("Page", style="cyan", width=6)
    table.add_column("Mode", width=15)
    table.add_column("Fields", width=7)
    table.add_column("Confidence", width=11)
    table.add_column("Time (s)", width=9)
    for s in stats:
        table.add_row(str(s["page"]), s["mode"], str(s["fields"]),
                       f"{s['confidence']:.2f}", str(s["elapsed"]))
    console.print(table)

    total_fields = sum(s["fields"] for s in stats)
    avg_conf = sum(s["confidence"] for s in stats) / len(stats) if stats else 0
    console.print(f"  Total fields: {total_fields}  Avg confidence: {avg_conf:.2f}")

    return extraction_data


# ---------------------------------------------------------------------------
# Stage 4: Field resolution + derivation + report generation
# ---------------------------------------------------------------------------

def stage4_report(
    patient: dict,
    extraction_data: dict[str, Any],
    patient_context: dict[str, str],
) -> tuple[Path, dict]:
    _banner(4, "REPORT GENERATION", patient["name"])
    slug = patient["slug"]
    rpt_dir = OUT_DIR / "stage4_report" / slug
    rpt_dir.mkdir(parents=True, exist_ok=True)

    all_fields = crg._flatten_all_fields(extraction_data.get("pages", []))
    rules = crg._load_rules()
    all_field_ids = set()
    for sec in rules.get("sections", []):
        all_field_ids.update(sec.get("source_field_ids", []))

    resolution = {}
    for fid in sorted(all_field_ids):
        val = crg._resolve_field(fid, all_fields, {}, crg._FIELD_MAP)
        resolution[fid] = str(val) if val is not None else None

    _save_json(rpt_dir / "field_resolution.json", resolution)
    unresolved = [fid for fid, v in resolution.items() if v is None]
    _save_json(rpt_dir / "unresolved_fields.json", unresolved)

    resolved_count = sum(1 for v in resolution.values() if v is not None)
    console.print(f"  Field resolution (pre-derivation): {resolved_count}/{len(resolution)} "
                  f"({100*resolved_count/len(resolution):.0f}%)")
    if unresolved:
        console.print(f"  Unresolved ({len(unresolved)}): {', '.join(unresolved[:10])}{'...' if len(unresolved)>10 else ''}")

    derived = crg._derive_fields(
        all_fields, crg._FIELD_MAP,
        extraction_data.get("patient_name"),
        patient_context,
    )
    _save_json(rpt_dir / "derived_fields.json", derived)
    console.print(f"  Derived fields: {len(derived)}")

    console.print("  Generating DOCX (LLM narrative calls)...")
    t0 = time.time()
    docx_bytes, low_conf, gen_log = crg.generate_clinical_report(
        extraction_data, patient_context=patient_context,
    )
    elapsed = time.time() - t0

    docx_path = rpt_dir / "report.docx"
    docx_path.write_bytes(docx_bytes)
    _save_json(rpt_dir / "low_confidence_fields.json", low_conf)
    _save_json(rpt_dir / "generation_log.json", gen_log)
    _save_json(rpt_dir / "generation_meta.json", {
        "elapsed_seconds": round(elapsed, 1),
        "file_size_kb": round(len(docx_bytes) / 1024, 1),
    })

    console.print(f"  Generated: {docx_path.name} ({len(docx_bytes)/1024:.1f} KB, {elapsed:.1f}s)")
    console.print(f"  Low confidence fields: {len(low_conf)}")

    return docx_path, {"elapsed": elapsed, "resolved": resolved_count, "total_fields": len(resolution)}


# ---------------------------------------------------------------------------
# Stage 5: Parse both reports
# ---------------------------------------------------------------------------

def stage5_parse(patient: dict, docx_path: Path) -> tuple[dict, dict]:
    _banner(5, "PARSE REPORTS", patient["name"])
    slug = patient["slug"]
    parsed_dir = OUT_DIR / "stage5_parsed"

    gen_report = parse_docx(docx_path)
    gen_data = gen_report.model_dump()
    _save_json(parsed_dir / f"{slug}_generated_scan.json", gen_data)

    gt_data = _load_json(patient["scan"])
    _save_json(parsed_dir / f"{slug}_ground_truth_scan.json", gt_data)

    text_dir = parsed_dir / f"{slug}_text_by_section"
    text_dir.mkdir(parents=True, exist_ok=True)

    gen_sections = gen_data.get("sections", [])
    gt_sections = gt_data.get("sections", [])

    for i, sec in enumerate(gen_sections):
        sid = sec.get("id", f"unknown_{i}")
        text = _extract_section_text(sec)
        (text_dir / f"gen_{i:02d}_{sid}.txt").write_text(text, encoding="utf-8")

    for i, sec in enumerate(gt_sections):
        sid = sec.get("id", f"unknown_{i}")
        text = _extract_section_text(sec)
        (text_dir / f"gt_{i:02d}_{sid}.txt").write_text(text, encoding="utf-8")

    gen_inventory = [{"idx": i, "section_id": s.get("id", ""), "heading": s.get("heading", ""),
                      "element_count": len(s.get("elements", []))}
                     for i, s in enumerate(gen_sections)]
    gt_inventory = [{"idx": i, "section_id": s.get("id", ""), "heading": s.get("heading", ""),
                     "element_count": len(s.get("elements", []))}
                    for i, s in enumerate(gt_sections)]

    _save_json(parsed_dir / f"{slug}_section_inventory.json", {
        "generated_sections": gen_inventory,
        "ground_truth_sections": gt_inventory,
        "generated_count": len(gen_sections),
        "ground_truth_count": len(gt_sections),
    })

    console.print(f"  Generated sections: {len(gen_sections)}")
    console.print(f"  Ground truth sections: {len(gt_sections)}")

    return gen_data, gt_data


# ---------------------------------------------------------------------------
# Stage 6: Section-by-section LLM comparison
# ---------------------------------------------------------------------------

SECTION_COMPARISON_PROMPT = """You are comparing TWO versions of a specific section from an orofacial pain evaluation report.

GENERATED section (from automated pipeline):
{generated_text}

GROUND TRUTH section (doctor's original):
{ground_truth_text}

Section: "{section_title}"
{fairness_note}

Compare these two sections and respond with ONLY valid JSON (no markdown fences):
{{
  "data_accuracy_score": <0-100>,
  "language_match_score": <0-100>,
  "hallucinations": ["list of facts in generated but NOT in ground truth"],
  "missing_data": ["list of facts in ground truth but NOT in generated"],
  "key_differences": ["list of notable differences"],
  "overall_score": <0-100>,
  "notes": "brief assessment"
}}"""


def _extract_json_from_text(text: str) -> dict | None:
    """Try to extract a JSON object from text that may contain prose around it."""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _compare_section(
    client: OpenAI, model: str,
    gen_text: str, gt_text: str,
    section_title: str, fairness_note: str = "",
) -> dict:
    prompt = SECTION_COMPARISON_PROMPT.format(
        generated_text=gen_text[:8000],
        ground_truth_text=gt_text[:8000],
        section_title=section_title,
        fairness_note=fairness_note,
    )
    max_retries = 3
    last_raw = ""
    for attempt in range(max_retries):
        try:
            messages = [{"role": "user", "content": prompt}]
            if attempt > 0:
                messages.append({"role": "user", "content": "Your previous response was not valid JSON. Respond with ONLY a valid JSON object, no other text."})
            resp = client.chat.completions.create(
                model=model, max_tokens=2000, temperature=0.1,
                messages=messages,
            )
            last_raw = resp.choices[0].message.content.strip()
            parsed = _extract_json_from_text(last_raw)
            if parsed and "overall_score" in parsed:
                return parsed
        except Exception as e:
            last_raw = str(e)
    return {
        "data_accuracy_score": 0, "language_match_score": 0,
        "hallucinations": [], "missing_data": [],
        "key_differences": [f"Comparison failed after {max_retries} attempts"],
        "overall_score": 0, "notes": f"LLM returned non-JSON",
        "raw_llm_response": last_raw[:2000],
    }


# --- Fuzzy section ID alignment ---

_SECTION_ALIASES: dict[str, str] = {
    "surface_electromyography": "surface_electromyography_semg",
    "surface_electromyography_semg": "surface_electromyography",
    "objective_clinical_findings_confirming_bruxism_clenching": "objective_clinical_findings_confirming_bruxismclenching",
    "objective_clinical_findings_confirming_bruxismclenching": "objective_clinical_findings_confirming_bruxism_clenching",
    "treatment_received_for_the_industrial_injury": "treatment_received_for_industrial_injury",
    "treatment_received_for_industrial_injury": "treatment_received_for_the_industrial_injury",
    "diagnostic_direct_fluorescence_visulization_dfv": "diagnostic_direct_fluorescence_visualization_dfv",
    "diagnostic_direct_fluorescence_visualization_dfv": "diagnostic_direct_fluorescence_visulization_dfv",
    "epworth_scale": "epworth_sleepiness_scale",
    "epworth_sleepiness_scale": "epworth_scale",
}

_KNOWN_SUBSECTION_IDS = {
    "dental": "subjective_complaints",
    "headaches": "subjective_complaints",
    "facial_pain": "subjective_complaints",
    "temporomandibular_joint": "subjective_complaints",
    "sleep_disturbances": "subjective_complaints",
}

_OLD_FORMAT_PAGE_PREFIXES = ("p3_", "p4_", "p8_", "p11_")
_TX_RECEIVED_PREFIXES = ("p7_tx_received", "p8_tx_received")


def _normalize_section_id(sid: str) -> str:
    return re.sub(r"[^a-z0-9]", "", sid.lower())


def _build_fuzzy_alignment(
    gen_by_id: dict[str, list[dict]],
    gt_by_id: dict[str, list[dict]],
) -> list[tuple[str, str | None, str | None, str]]:
    """Build aligned section pairs. Returns list of (canonical_id, gen_id, gt_id, match_type)."""
    matched_gen = set()
    matched_gt = set()
    pairs: list[tuple[str, str | None, str | None, str]] = []

    gen_ids = set(gen_by_id.keys())
    gt_ids = set(gt_by_id.keys())

    for sid in sorted(gen_ids & gt_ids):
        pairs.append((sid, sid, sid, "exact"))
        matched_gen.add(sid)
        matched_gt.add(sid)

    unmatched_gen = gen_ids - matched_gen
    unmatched_gt = gt_ids - matched_gt

    for g_sid in sorted(unmatched_gen):
        alias = _SECTION_ALIASES.get(g_sid)
        if alias and alias in unmatched_gt:
            canonical = min(g_sid, alias)
            pairs.append((canonical, g_sid, alias, "alias"))
            matched_gen.add(g_sid)
            matched_gt.add(alias)
            unmatched_gt.discard(alias)
            console.print(f"  [dim]Fuzzy match (alias): {g_sid} <-> {alias}[/dim]")

    still_unmatched_gen = sorted(gen_ids - matched_gen)
    still_unmatched_gt = sorted(gt_ids - matched_gt)

    gen_norm = {_normalize_section_id(s): s for s in still_unmatched_gen}
    gt_norm = {_normalize_section_id(s): s for s in still_unmatched_gt}
    for norm_id, g_sid in gen_norm.items():
        if norm_id in gt_norm:
            gt_sid = gt_norm[norm_id]
            canonical = min(g_sid, gt_sid)
            pairs.append((canonical, g_sid, gt_sid, "normalized"))
            matched_gen.add(g_sid)
            matched_gt.add(gt_sid)
            console.print(f"  [dim]Fuzzy match (normalized): {g_sid} <-> {gt_sid}[/dim]")

    for g_sid in sorted(gen_ids - matched_gen):
        pairs.append((g_sid, g_sid, None, "gen_only"))
    for gt_sid in sorted(gt_ids - matched_gt):
        pairs.append((gt_sid, None, gt_sid, "gt_only"))

    return pairs


def _build_dynamic_fairness(section_rule: dict | None) -> str:
    if not section_rule:
        return ""
    source_ids = section_rule.get("source_field_ids", [])
    has_old_format = any(fid.startswith(p) for fid in source_ids for p in _OLD_FORMAT_PAGE_PREFIXES)
    has_tx = any(fid.startswith(p) for fid in source_ids for p in _TX_RECEIVED_PREFIXES)
    if has_tx:
        return ("NOTE: The Tx Received fields do NOT exist in the old exam format. "
                "Any missing data here is expected, not a pipeline bug.")
    if has_old_format:
        return ("NOTE: This section's data came from old-format exam pages (p3/p4/p8/p11) "
                "via merged schema extraction. Minor field mapping differences are expected.")
    return ""


# --- Content gap detection patterns ---

_RE_CITATION = re.compile(r"(Vol\.\s*\d|Journal\b|pp\.\s*\d|https?://|doi:|Shushma|Okeson|AAOP|American Academy)", re.IGNORECASE)
_RE_LEGAL = re.compile(r"(L\.C\.\s*\d|Labor\s+Code|460[4-9]|540[2-9]|4628|IMC|MTUS|ACOEM|ODG)", re.IGNORECASE)
_RE_PLACEHOLDER = re.compile(r"\[VERIFY:|\\[Signature\\]|\[Name\]|\[Credentials\]|\[Date\]|\[Address\]", re.IGNORECASE)
_RE_META_LEAK = re.compile(r"(^SECTION:|^GENERATED TEXT:|^Changes made:|^Since ['\"]?p\d+_|^becomes$|^is not needed|^the correct response is)", re.IGNORECASE | re.MULTILINE)


# --- LLM root cause analysis ---

_ROOT_CAUSE_PROMPT = """You are diagnosing WHY a generated clinical report section differs from the ground truth.

SECTION: "{section_title}"
OVERALL SCORE: {score}/100

GENERATED TEXT:
{gen_text}

GROUND TRUTH TEXT:
{gt_text}

RULE DEFINITION:
- content_type: {content_type}
- source_field_ids ({field_count} total): {source_field_ids}
- has generation_prompt: {has_prompt}
- has few_shot_examples: {has_few_shot}
- generation_prompt snippet: {prompt_snippet}

RESOLVED FIELD VALUES (data the generator had):
{resolved_fields}

UNRESOLVED FIELDS (data the generator did NOT have):
{unresolved_fields}

COMPARISON RESULT:
- Hallucinations found: {hallucinations}
- Missing data: {missing_data}

HARDCODED PRE-CHECKS:
{precheck_summary}

Analyze the root cause. For EACH issue you find, classify it into exactly one of these categories:
- "extraction_gap": data was never extracted from the form
- "rule_underspecified": the rule's source_field_ids or prompt doesn't cover what the GT section needs
- "rule_missing_few_shot": the rule has no few-shot examples so the LLM doesn't know the expected output style/density
- "generation_hallucination": the LLM fabricated facts not in the source data
- "generation_dropped_data": the LLM had the data but didn't include it in the output
- "generation_too_brief": the LLM produced much less detail than the GT
- "missing_citations": GT has academic/legal citations the generated text lacks
- "missing_legal_boilerplate": GT has statute references or legal language the generated text lacks
- "missing_provider_info": GT has doctor/practice details not available to the generator
- "verification_corrupted": the verification step damaged or shortened the text
- "meta_text_leaked": LLM reasoning or field IDs leaked into the clinical text
- "structural_mismatch": section ID alignment issue (subsection split, duplicate)
- "data_contradiction": generated text states a different value than what was extracted

Respond with ONLY valid JSON:
{{
  "primary_cause": "<most impactful category>",
  "secondary_causes": ["<other applicable categories>"],
  "explanation": "<2-3 sentence explanation of why the generated text differs from ground truth>",
  "actionable_fix": "<what specifically should be changed to fix this - e.g. add field X to source_field_ids, add few-shot example, fix extraction for field Y>"
}}"""


def _llm_root_cause_analysis(
    client: OpenAI, model: str,
    section_title: str, score: int,
    gen_text: str, gt_text: str,
    rule: dict,
    fields_resolved: dict, fields_unresolved: list,
    comparison_result: dict,
    precheck_summary: str,
) -> dict | None:
    """Use an LLM to diagnose root cause for low-scoring sections."""
    prompt = _ROOT_CAUSE_PROMPT.format(
        section_title=section_title,
        score=score,
        gen_text=gen_text[:4000],
        gt_text=gt_text[:4000],
        content_type=rule.get("content_type", "unknown"),
        field_count=len(rule.get("source_field_ids", [])),
        source_field_ids=json.dumps(rule.get("source_field_ids", [])[:20]),
        has_prompt="yes" if rule.get("generation_prompt") else "NO",
        has_few_shot="yes" if rule.get("few_shot_examples") else "NO",
        prompt_snippet=(rule.get("generation_prompt") or "")[:500],
        resolved_fields=json.dumps(fields_resolved, indent=1)[:2000],
        unresolved_fields=json.dumps(fields_unresolved)[:500],
        hallucinations=json.dumps(comparison_result.get("hallucinations", []))[:1000],
        missing_data=json.dumps(comparison_result.get("missing_data", []))[:1000],
        precheck_summary=precheck_summary,
    )
    try:
        resp = client.chat.completions.create(
            model=model, max_tokens=800, temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content.strip()
        parsed = _extract_json_from_text(raw)
        if parsed and "primary_cause" in parsed:
            return parsed
    except Exception as e:
        console.print(f"  [dim]LLM root cause failed: {e}[/dim]")
    return None


def _detect_content_gaps(gen_text: str, gt_text: str) -> dict:
    gt_has_citations = bool(_RE_CITATION.search(gt_text))
    gen_has_citations = bool(_RE_CITATION.search(gen_text))
    gt_has_legal = bool(_RE_LEGAL.search(gt_text))
    gen_has_legal = bool(_RE_LEGAL.search(gen_text))

    return {
        "missing_citations": gt_has_citations and not gen_has_citations,
        "missing_legal_text": gt_has_legal and not gen_has_legal,
        "placeholder_leakage": bool(_RE_PLACEHOLDER.search(gen_text)),
        "meta_text_leakage": bool(_RE_META_LEAK.search(gen_text)),
        "gt_citation_count": len(_RE_CITATION.findall(gt_text)),
        "gen_citation_count": len(_RE_CITATION.findall(gen_text)),
        "gt_legal_count": len(_RE_LEGAL.findall(gt_text)),
        "gen_legal_count": len(_RE_LEGAL.findall(gen_text)),
    }


def _build_deep_root_cause(
    section_id: str,
    gen_text: str,
    gt_text: str,
    match_type: str,
    comparison_result: dict,
    rules_by_id: dict[str, dict],
    field_resolution: dict[str, Any],
    unresolved_fields: list[str],
    low_confidence_fields: list[dict],
    generation_log: dict[str, dict],
    derived_fields: dict[str, str],
    llm_client: tuple[OpenAI, str] | None = None,
) -> dict:
    rule = rules_by_id.get(section_id, {})
    source_ids = rule.get("source_field_ids", [])
    content_type = rule.get("content_type", "unknown")
    glog = generation_log.get(section_id, {})

    fields_resolved = {}
    fields_unresolved = []
    for fid in source_ids:
        val = field_resolution.get(fid)
        if val is None:
            val = derived_fields.get(fid)
        if val is not None:
            fields_resolved[fid] = val
        else:
            fields_unresolved.append(fid)

    fields_low_conf = [lc for lc in low_confidence_fields if lc.get("field_id") in source_ids]
    gen_has_text = bool(gen_text.strip())
    gt_has_text = bool(gt_text.strip())
    halluc_count = len(comparison_result.get("hallucinations", []))
    score = comparison_result.get("overall_score", 0)

    # --- Layer 1: Rule ---
    if not rule:
        rule_status, rule_detail = "fail", "no rule defined for this section_id"
    elif content_type == "narrative" and len(source_ids) <= 2:
        rule_status, rule_detail = "warning", f"only {len(source_ids)} source_field_ids for a narrative section"
    elif content_type == "narrative" and not rule.get("generation_prompt"):
        rule_status, rule_detail = "warning", "narrative section has no generation_prompt"
    else:
        rule_status, rule_detail = "ok", ""
    layer_rule = {"status": rule_status, "detail": rule_detail,
                  "has_prompt": bool(rule.get("generation_prompt")),
                  "has_few_shot": bool(rule.get("few_shot_examples")),
                  "source_field_count": len(source_ids)}

    # --- Layer 2: Condition ---
    cond_result = glog.get("conditions_result", True)
    layer_condition = {"status": "ok" if cond_result else "blocked",
                       "detail": "" if cond_result else "section skipped by _check_conditions"}

    # --- Layer 3: Extraction ---
    total = len(source_ids) or 1
    coverage = len(fields_resolved) / total
    if coverage >= 0.7:
        ext_status = "ok"
    elif coverage >= 0.4:
        ext_status = "partial"
    else:
        ext_status = "fail"
    layer_extraction = {"status": ext_status, "coverage": round(coverage, 2),
                        "resolved": len(fields_resolved), "total": len(source_ids),
                        "detail": f"{len(fields_unresolved)} unresolved: {', '.join(fields_unresolved[:5])}" if fields_unresolved else ""}

    # --- Layer 4: Resolution ---
    layer_resolution = {"status": "ok", "detail": ""}

    # --- Layer 5: Min-fields gate ---
    gate_passed = glog.get("min_fields_passed", True)
    threshold = glog.get("min_fields_threshold", 0)
    resolved_count = glog.get("fields_resolved_count", len(fields_resolved))
    layer_gate = {"status": "passed" if gate_passed else "blocked",
                  "threshold": threshold, "resolved": resolved_count}

    # --- Layer 6: Generation ---
    narr_gen = glog.get("narrative_generated", gen_has_text)
    raw_len = glog.get("narrative_raw_length", 0)
    clean_len = glog.get("narrative_clean_length", 0)
    if not gen_has_text and content_type == "narrative":
        if not gate_passed:
            gen_status = "gate_blocked"
        elif not narr_gen:
            gen_status = "failed"
        else:
            gen_status = "empty"
    elif gen_has_text and raw_len > 0 and clean_len < raw_len * 0.5:
        gen_status = "heavily_cleaned"
    else:
        gen_status = "ok"
    layer_generation = {"status": gen_status, "raw_len": raw_len, "clean_len": clean_len,
                        "final_len": glog.get("final_text_length", len(gen_text))}

    # --- Layer 7: Verification ---
    was_verified = glog.get("verified", False)
    verified_len = glog.get("verified_length", 0)
    if was_verified and clean_len > 0 and verified_len < clean_len * 0.7:
        verif_status = "corrupted"
    elif _RE_META_LEAK.search(gen_text):
        verif_status = "leaked"
    else:
        verif_status = "ok"
    layer_verification = {"status": verif_status, "was_verified": was_verified,
                          "len_before": clean_len, "len_after": verified_len}

    # --- Layer 8: Content gaps ---
    layer_content = _detect_content_gaps(gen_text, gt_text)

    # --- Layer 9: Structure ---
    if section_id in _KNOWN_SUBSECTION_IDS:
        struct_status = "subsection_split"
        struct_detail = f"GT treats this as subsection of {_KNOWN_SUBSECTION_IDS[section_id]}"
    elif match_type == "gen_only" and content_type == "unknown":
        struct_status = "unmapped_section"
        struct_detail = "section exists in generated but has no matching rule"
    elif match_type in ("gen_only", "gt_only"):
        struct_status = match_type
        struct_detail = f"section only in {'generated' if match_type == 'gen_only' else 'ground truth'}"
    else:
        struct_status = "ok"
        struct_detail = ""
    layer_structure = {"status": struct_status, "detail": struct_detail}

    # --- Layer 10: Parser ---
    if section_id == "verified_text" or "VERIFIED TEXT" in (comparison_result.get("heading") or ""):
        parser_status, parser_detail = "artifact", "verification output leaked into DOCX"
    elif gen_has_text and len(gen_text.strip().split("\n")) == 1 and len(gen_text.strip()) < 80:
        parser_status, parser_detail = "orphan_heading", "generated text is only a heading with no body"
    else:
        parser_status, parser_detail = "ok", ""
    layer_parser = {"status": parser_status, "detail": parser_detail}

    # --- Determine primary + secondary causes from hardcoded checks ---
    hc_causes = []
    if parser_status != "ok":
        hc_causes.append(parser_status)
    if struct_status not in ("ok", "gen_only", "gt_only"):
        hc_causes.append(struct_status)
    if not cond_result:
        hc_causes.append("condition_blocked")
    if not gate_passed:
        hc_causes.append("min_fields_gate_blocked")
    if ext_status == "fail":
        hc_causes.append("extraction_gap")
    elif ext_status == "partial":
        hc_causes.append("extraction_partial")
    if gen_status in ("failed", "empty", "gate_blocked"):
        hc_causes.append("generation_failure")
    if gen_status == "heavily_cleaned":
        hc_causes.append("clean_narrative_stripped")
    if verif_status == "corrupted":
        hc_causes.append("verification_corrupted")
    if verif_status == "leaked":
        hc_causes.append("verification_leaked")
    if halluc_count > 0 and gen_has_text:
        hc_causes.append("generation_hallucination")
    if layer_content.get("missing_citations"):
        hc_causes.append("missing_citations")
    if layer_content.get("missing_legal_text"):
        hc_causes.append("missing_legal_text")
    if layer_content.get("placeholder_leakage"):
        hc_causes.append("placeholder_leakage")
    if layer_content.get("meta_text_leakage"):
        hc_causes.append("meta_text_leakage")
    if rule_status == "warning":
        hc_causes.append("rule_underspecified")

    # Clear-cut cases that don't need an LLM call
    clear_cut = {"artifact", "orphan_heading", "subsection_split", "condition_blocked",
                 "min_fields_gate_blocked", "parser_artifact"}
    is_clear_cut = bool(set(hc_causes) & clear_cut)

    # For ambiguous/low-scoring sections, use LLM to diagnose
    llm_diagnosis = None
    explanation = ""
    actionable_fix = ""
    if llm_client and not is_clear_cut and score < 70 and gen_has_text and gt_has_text:
        precheck_lines = []
        for name, layer in [("rule", layer_rule), ("extraction", layer_extraction),
                            ("generation", layer_generation), ("verification", layer_verification)]:
            if layer.get("status") != "ok":
                precheck_lines.append(f"{name}: {layer.get('status')} — {layer.get('detail', '')}")
        if layer_content.get("missing_citations"):
            precheck_lines.append("content: GT has citations, generated does not")
        if layer_content.get("missing_legal_text"):
            precheck_lines.append("content: GT has legal text, generated does not")

        llm_diagnosis = _llm_root_cause_analysis(
            llm_client[0], llm_client[1],
            comparison_result.get("heading", section_id), score,
            gen_text, gt_text, rule,
            fields_resolved, fields_unresolved,
            comparison_result,
            "\n".join(precheck_lines) if precheck_lines else "All hardcoded pre-checks passed",
        )

    if llm_diagnosis:
        primary = llm_diagnosis["primary_cause"]
        secondary = llm_diagnosis.get("secondary_causes", [])
        explanation = llm_diagnosis.get("explanation", "")
        actionable_fix = llm_diagnosis.get("actionable_fix", "")
    elif not hc_causes:
        primary = "ok" if score >= 70 else "generation_quality"
        secondary = []
    else:
        primary = hc_causes[0]
        secondary = hc_causes[1:] if len(hc_causes) > 1 else []

    return {
        "layers": {
            "rule": layer_rule,
            "condition": layer_condition,
            "extraction": layer_extraction,
            "resolution": layer_resolution,
            "min_fields_gate": layer_gate,
            "generation": layer_generation,
            "verification": layer_verification,
            "content_gaps": layer_content,
            "structure": layer_structure,
            "parser": layer_parser,
        },
        "primary_cause": primary,
        "secondary_causes": secondary,
        "explanation": explanation,
        "actionable_fix": actionable_fix,
        "diagnosed_by": "llm" if llm_diagnosis else "hardcoded",
        "source_field_ids": source_ids,
        "fields_resolved": fields_resolved,
        "fields_unresolved": fields_unresolved,
        "fields_low_confidence": fields_low_conf,
    }


def stage6_comparison(patient: dict, gen_data: dict, gt_data: dict) -> dict:
    _banner(6, "LLM COMPARISON", patient["name"])
    slug = patient["slug"]
    cmp_dir = OUT_DIR / "stage6_comparison" / slug
    sec_dir = cmp_dir / "per_section"
    sec_dir.mkdir(parents=True, exist_ok=True)

    llm = _build_comparison_client()
    if not llm:
        console.print("[red]  No Together/Fireworks API key found. Skipping LLM comparison.[/red]")
        return {"error": "no_api_key"}

    client, model = llm

    rules_path = BASE / "report_learning" / "outputs" / "rules" / "report_rules.json"
    rules_data = _load_json(rules_path) if rules_path.exists() else {}
    rules_by_id: dict[str, dict] = {}
    for sec in rules_data.get("sections", []):
        rules_by_id[sec.get("section_id", "")] = sec
        alias = _SECTION_ALIASES.get(sec.get("section_id", ""))
        if alias:
            rules_by_id.setdefault(alias, sec)

    rpt_dir = OUT_DIR / "stage4_report" / slug
    field_resolution = _load_json(rpt_dir / "field_resolution.json") if (rpt_dir / "field_resolution.json").exists() else {}
    unresolved_fields = _load_json(rpt_dir / "unresolved_fields.json") if (rpt_dir / "unresolved_fields.json").exists() else []
    low_confidence_fields = _load_json(rpt_dir / "low_confidence_fields.json") if (rpt_dir / "low_confidence_fields.json").exists() else []
    generation_log = _load_json(rpt_dir / "generation_log.json") if (rpt_dir / "generation_log.json").exists() else {}
    derived_fields = _load_json(rpt_dir / "derived_fields.json") if (rpt_dir / "derived_fields.json").exists() else {}

    gen_sections = gen_data.get("sections", [])
    gt_sections = gt_data.get("sections", [])

    gt_by_id: dict[str, list[dict]] = {}
    for sec in gt_sections:
        gt_by_id.setdefault(sec.get("id", ""), []).append(sec)

    gen_by_id: dict[str, list[dict]] = {}
    for sec in gen_sections:
        gen_by_id.setdefault(sec.get("id", ""), []).append(sec)

    aligned = _build_fuzzy_alignment(gen_by_id, gt_by_id)
    console.print(f"  Aligned pairs: {len(aligned)}  "
                  f"(exact={sum(1 for _,_,_,m in aligned if m=='exact')}, "
                  f"alias={sum(1 for _,_,_,m in aligned if m=='alias')}, "
                  f"normalized={sum(1 for _,_,_,m in aligned if m=='normalized')}, "
                  f"gen_only={sum(1 for _,_,_,m in aligned if m=='gen_only')}, "
                  f"gt_only={sum(1 for _,_,_,m in aligned if m=='gt_only')})")

    section_results = []
    root_cause_counts: dict[str, int] = Counter()

    for canonical_id, gen_id, gt_id, match_type in aligned:
        gen_list = gen_by_id.get(gen_id, []) if gen_id else []
        gt_list = gt_by_id.get(gt_id, []) if gt_id else []
        max_occ = max(len(gen_list), len(gt_list), 1)

        for occ in range(max_occ):
            gen_sec = gen_list[occ] if occ < len(gen_list) else None
            gt_sec = gt_list[occ] if occ < len(gt_list) else None

            gen_text = _extract_section_text(gen_sec) if gen_sec else ""
            gt_text = _extract_section_text(gt_sec) if gt_sec else ""
            title = (gen_sec or gt_sec or {}).get("heading", canonical_id)

            if not gen_text.strip() and not gt_text.strip():
                continue

            if not gen_text.strip():
                result = {
                    "data_accuracy_score": 0, "language_match_score": 0,
                    "hallucinations": [], "missing_data": ["Entire section missing from generated"],
                    "key_differences": ["Section exists in ground truth only"],
                    "overall_score": 0, "notes": "Missing from generated report",
                }
            elif not gt_text.strip():
                result = {
                    "data_accuracy_score": 50, "language_match_score": 50,
                    "hallucinations": ["Entire section exists only in generated"],
                    "missing_data": [],
                    "key_differences": ["Section exists in generated only"],
                    "overall_score": 50, "notes": "Extra section in generated report",
                }
            else:
                rule = rules_by_id.get(canonical_id) or rules_by_id.get(gen_id or "") or rules_by_id.get(gt_id or "")
                fairness = _build_dynamic_fairness(rule)
                result = _compare_section(client, model, gen_text, gt_text, title, fairness)

            result["section_id"] = canonical_id
            result["occurrence"] = occ
            result["heading"] = title
            result["match_type"] = match_type
            if gen_id and gt_id and gen_id != gt_id:
                result["gen_section_id"] = gen_id
                result["gt_section_id"] = gt_id
            result["generated_text"] = gen_text
            result["ground_truth_text"] = gt_text

            rca = _build_deep_root_cause(
                canonical_id, gen_text, gt_text, match_type, result,
                rules_by_id, field_resolution, unresolved_fields, low_confidence_fields,
                generation_log, derived_fields,
                llm_client=(client, model),
            )
            result["root_cause_analysis"] = rca
            root_cause_counts[rca["primary_cause"]] += 1

            section_results.append(result)
            _save_json(sec_dir / f"{canonical_id}_{occ}.json", result)

            score = result.get("overall_score", 0)
            cause = rca["primary_cause"]
            secondary = rca.get("secondary_causes", [])
            style = "green" if score >= 80 else "yellow" if score >= 50 else "red"
            sec_str = f" +{','.join(secondary[:2])}" if secondary else ""
            console.print(f"  [{style}]{canonical_id}:{occ} — score={score}  cause={cause}{sec_str}[/{style}]  "
                          f"halluc={len(result.get('hallucinations', []))} "
                          f"missing={len(result.get('missing_data', []))}")

    _save_json(cmp_dir / "comparison_summary.json", section_results)

    scores_table = Table(title=f"Section Scores — {patient['name']}")
    scores_table.add_column("Section", width=40)
    scores_table.add_column("Score", width=7)
    scores_table.add_column("Cause", width=22)
    scores_table.add_column("Halluc", width=7)
    scores_table.add_column("Missing", width=7)
    for r in sorted(section_results, key=lambda x: x.get("overall_score", 0)):
        s = r.get("overall_score", 0)
        style = "green" if s >= 80 else "yellow" if s >= 50 else "red"
        cause = r.get("root_cause_analysis", {}).get("primary_cause", "?")
        scores_table.add_row(
            f"{r['section_id']}:{r['occurrence']}",
            f"[{style}]{s}[/{style}]",
            cause,
            str(len(r.get("hallucinations", []))),
            str(len(r.get("missing_data", []))),
        )
    console.print(scores_table)

    # --- Enhanced comparison_full.md with layered diagnostics ---
    md_lines = [f"# Comparison: {patient['name']}\n"]
    md_lines.append(f"**Root Cause Breakdown:** {dict(root_cause_counts)}\n")
    for r in sorted(section_results, key=lambda x: x.get("overall_score", 0)):
        rca = r.get("root_cause_analysis", {})
        layers = rca.get("layers", {})
        md_lines.append(f"## {r['heading']} (occ {r['occurrence']}) — Score: {r.get('overall_score', 0)}")
        diagnosed_by = rca.get("diagnosed_by", "hardcoded")
        md_lines.append(f"- Primary cause: **{rca.get('primary_cause', '?')}** (diagnosed by: {diagnosed_by})")
        if rca.get("secondary_causes"):
            md_lines.append(f"- Secondary causes: {', '.join(rca['secondary_causes'])}")
        if rca.get("explanation"):
            md_lines.append(f"- Explanation: {rca['explanation']}")
        if rca.get("actionable_fix"):
            md_lines.append(f"- Fix: {rca['actionable_fix']}")
        md_lines.append(f"- Match type: {r.get('match_type', '?')}")
        if r.get("gen_section_id"):
            md_lines.append(f"- Fuzzy: gen=`{r['gen_section_id']}` gt=`{r.get('gt_section_id', '')}`")
        md_lines.append(f"- Data accuracy: {r.get('data_accuracy_score', 0)} | Language match: {r.get('language_match_score', 0)}")

        md_lines.append(f"\n**Diagnostic Layers:**")
        lr = layers.get("rule", {})
        md_lines.append(f"- Rule: `{lr.get('status', '?')}` — {lr.get('source_field_count', 0)} source fields, prompt={'yes' if lr.get('has_prompt') else 'NO'}, few-shot={'yes' if lr.get('has_few_shot') else 'NO'}{' — ' + lr['detail'] if lr.get('detail') else ''}")
        lc = layers.get("condition", {})
        if lc.get("status") != "ok":
            md_lines.append(f"- Condition: `{lc.get('status', '?')}` — {lc.get('detail', '')}")
        le = layers.get("extraction", {})
        md_lines.append(f"- Extraction: `{le.get('status', '?')}` — coverage {le.get('coverage', 0):.0%} ({le.get('resolved', 0)}/{le.get('total', 0)}){' — ' + le['detail'] if le.get('detail') else ''}")
        lg = layers.get("min_fields_gate", {})
        if lg.get("status") != "passed":
            md_lines.append(f"- Min-fields gate: `BLOCKED` — needed {lg.get('threshold', '?')}, had {lg.get('resolved', '?')}")
        lgen = layers.get("generation", {})
        if lgen.get("status") != "ok":
            md_lines.append(f"- Generation: `{lgen.get('status', '?')}` — raw={lgen.get('raw_len', 0)}, clean={lgen.get('clean_len', 0)}, final={lgen.get('final_len', 0)}")
        lv = layers.get("verification", {})
        if lv.get("status") != "ok":
            md_lines.append(f"- Verification: `{lv.get('status', '?')}` — before={lv.get('len_before', 0)}, after={lv.get('len_after', 0)}")
        lcg = layers.get("content_gaps", {})
        gaps = [k for k, v in lcg.items() if v is True]
        if gaps:
            md_lines.append(f"- Content gaps: {', '.join(gaps)}")
        ls = layers.get("structure", {})
        if ls.get("status") != "ok":
            md_lines.append(f"- Structure: `{ls.get('status', '?')}` — {ls.get('detail', '')}")
        lp = layers.get("parser", {})
        if lp.get("status") != "ok":
            md_lines.append(f"- Parser: `{lp.get('status', '?')}` — {lp.get('detail', '')}")

        if rca.get("fields_unresolved"):
            md_lines.append(f"- Unresolved fields: {', '.join(rca['fields_unresolved'])}")
        if r.get("hallucinations"):
            md_lines.append(f"- Hallucinations: {'; '.join(str(h) for h in r['hallucinations'])}")
        if r.get("missing_data"):
            md_lines.append(f"- Missing: {'; '.join(str(m) for m in r['missing_data'])}")
        if r.get("key_differences"):
            md_lines.append(f"- Differences: {'; '.join(str(d) for d in r['key_differences'])}")
        md_lines.append(f"- Notes: {r.get('notes', '')}")
        md_lines.append(f"\n### Generated Text\n```\n{r.get('generated_text', '[EMPTY]') or '[EMPTY]'}\n```")
        md_lines.append(f"\n### Ground Truth Text\n```\n{r.get('ground_truth_text', '[EMPTY]') or '[EMPTY]'}\n```\n")

    (cmp_dir / "comparison_full.md").write_text("\n".join(md_lines), encoding="utf-8")

    avg_score = (sum(r.get("overall_score", 0) for r in section_results) / len(section_results)
                 if section_results else 0)
    total_halluc = sum(len(r.get("hallucinations", [])) for r in section_results)
    total_missing = sum(len(r.get("missing_data", [])) for r in section_results)

    return {
        "avg_score": round(avg_score, 1),
        "total_hallucinations": total_halluc,
        "total_missing": total_missing,
        "sections_compared": len(section_results),
        "section_results": section_results,
        "root_cause_breakdown": dict(root_cause_counts),
    }


# ---------------------------------------------------------------------------
# Stage 7: Final consolidated report
# ---------------------------------------------------------------------------

def stage7_final(all_results: list[dict]) -> None:
    _banner(7, "FINAL REPORT")

    scores = [r["comparison"].get("avg_score", 0) for r in all_results]
    avg = sum(scores) / len(scores) if scores else 0

    total_root_causes: dict[str, int] = Counter()
    for r in all_results:
        for k, v in r["comparison"].get("root_cause_breakdown", {}).items():
            total_root_causes[k] += v

    summary = {
        "test_date": datetime.now().isoformat(),
        "patients": [{
            "name": r["name"],
            "avg_score": r["comparison"].get("avg_score", 0),
            "total_hallucinations": r["comparison"].get("total_hallucinations", 0),
            "total_missing": r["comparison"].get("total_missing", 0),
            "sections_compared": r["comparison"].get("sections_compared", 0),
            "root_cause_breakdown": r["comparison"].get("root_cause_breakdown", {}),
            "extraction_time": r.get("extraction_time", 0),
            "generation_time": r.get("generation_time", 0),
        } for r in all_results],
        "aggregate_score": round(avg, 1),
        "root_cause_breakdown": dict(total_root_causes),
    }
    _save_json(OUT_DIR / "summary.json", summary)

    all_section_results = []
    for r in all_results:
        for sr in r["comparison"].get("section_results", []):
            sr_copy = dict(sr)
            sr_copy["patient"] = r["name"]
            all_section_results.append(sr_copy)

    worst = sorted(all_section_results, key=lambda x: x.get("overall_score", 0))[:15]
    all_halluc = []
    all_missing = []
    for sr in all_section_results:
        for h in sr.get("hallucinations", []):
            all_halluc.append(f"[{sr.get('patient', '?')}] {sr['section_id']}: {h}")
        for m in sr.get("missing_data", []):
            all_missing.append(f"[{sr.get('patient', '?')}] {sr['section_id']}: {m}")

    md = ["# E2E V3 Pipeline Comparison — Final Report\n"]
    md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    md.append(f"**Aggregate Score:** {avg:.1f}/100\n")

    md.append("## Root Cause Breakdown (all patients)\n")
    md.append("| Cause | Count |")
    md.append("|-------|-------|")
    for cause, count in sorted(total_root_causes.items(), key=lambda x: -x[1]):
        md.append(f"| {cause} | {count} |")

    md.append("\n## Per-Patient Summary\n")
    md.append("| Patient | Avg Score | Hallucinations | Missing Data | Sections |")
    md.append("|---------|-----------|----------------|--------------|----------|")
    for r in all_results:
        c = r["comparison"]
        md.append(f"| {r['name']} | {c.get('avg_score', 0):.1f} | "
                  f"{c.get('total_hallucinations', 0)} | {c.get('total_missing', 0)} | "
                  f"{c.get('sections_compared', 0)} |")

    md.append("\n## Worst Sections (across all patients)\n")
    md.append("| Patient | Section | Score | Cause | Halluc | Missing |")
    md.append("|---------|---------|-------|-------|--------|---------|")
    for w in worst:
        cause = w.get("root_cause_analysis", {}).get("primary_cause", "?")
        md.append(f"| {w.get('patient', '?')} | {w['section_id']}:{w['occurrence']} | "
                  f"{w.get('overall_score', 0)} | {cause} | {len(w.get('hallucinations', []))} | "
                  f"{len(w.get('missing_data', []))} |")

    if all_halluc:
        md.append("\n## All Hallucinations\n")
        for h in all_halluc[:50]:
            md.append(f"- {h}")

    if all_missing:
        md.append("\n## All Missing Data\n")
        for m in all_missing[:50]:
            md.append(f"- {m}")

    (OUT_DIR / "final_report.md").write_text("\n".join(md), encoding="utf-8")

    _save_json(OUT_DIR / "run_meta.json", {
        "test_date": datetime.now().isoformat(),
        "patients": [p["name"] for p in PATIENTS],
        "aggregate_score": round(avg, 1),
        "root_cause_breakdown": dict(total_root_causes),
    })

    final_table = Table(title="FINAL RESULTS")
    final_table.add_column("Patient", width=20)
    final_table.add_column("Score", width=8)
    final_table.add_column("Halluc", width=8)
    final_table.add_column("Missing", width=8)
    final_table.add_column("Sections", width=10)
    for r in all_results:
        c = r["comparison"]
        s = c.get("avg_score", 0)
        style = "green" if s >= 70 else "yellow" if s >= 50 else "red"
        final_table.add_row(
            r["name"],
            f"[{style}]{s:.1f}[/{style}]",
            str(c.get("total_hallucinations", 0)),
            str(c.get("total_missing", 0)),
            str(c.get("sections_compared", 0)),
        )
    console.print(final_table)

    console.print(f"\n  Root Cause Breakdown:")
    for cause, count in sorted(total_root_causes.items(), key=lambda x: -x[1]):
        console.print(f"    {cause}: {count}")

    console.print(f"\n  Aggregate Score: {avg:.1f}/100")
    console.print(f"  Reports saved to: {OUT_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="E2E Pipeline Comparison Test V3")
    parser.add_argument("--stage", type=int, default=0,
                        help="Start from this stage (skips earlier stages). E.g. --stage 4 re-runs stages 4-7, --stage 6 re-runs stages 6-7.")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Override output directory (e.g. e2e_v3). Extraction data is still read from e2e_v2.")
    args = parser.parse_args()
    start_stage = args.stage

    global OUT_DIR
    E2E_SOURCE_DIR = OUT_DIR  # where to read stages 1-3 data from
    if args.output_dir:
        OUT_DIR = BASE / "report_learning" / "outputs" / args.output_dir
        E2E_SOURCE_DIR = BASE / "report_learning" / "outputs" / "e2e_v2"

    console.print(f"\n{'='*70}")
    console.print("  E2E PIPELINE COMPARISON TEST V3")
    console.print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if start_stage > 0:
        console.print(f"  Starting from stage {start_stage} (skipping stages 0-{start_stage - 1})")
    console.print(f"{'='*70}")

    total_start = time.time()

    if start_stage <= 0:
        stage0_setup()
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for d in STAGE_DIRS:
            (OUT_DIR / d).mkdir(exist_ok=True)

    all_results = []

    for patient in PATIENTS:
        console.print(f"\n{'#'*70}")
        console.print(f"  PATIENT: {patient['name']}")
        console.print(f"{'#'*70}")
        patient_start = time.time()
        slug = patient["slug"]
        extraction_time = 0.0
        generation_time = 0.0

        if start_stage <= 1:
            exam_images, schema_plan = stage1_split(patient)
        else:
            plan_path = E2E_SOURCE_DIR / "stage1_split" / f"{slug}_schema_plan.json"
            schema_plan = _load_json(plan_path)
            img_dir = E2E_SOURCE_DIR / "stage1_split" / f"{slug}_page_images"
            exam_images = sorted(img_dir.glob("page_*.png"))
            console.print(f"  [dim]Stage 1 skipped — loaded {len(exam_images)} images, {len(schema_plan)} schema entries[/dim]")

        if start_stage <= 2:
            patient_context = stage2_context(patient)
        else:
            ctx_path = E2E_SOURCE_DIR / "stage2_context" / f"{slug}_patient_context.json"
            patient_context = _load_json(ctx_path)
            console.print(f"  [dim]Stage 2 skipped — loaded patient_context ({len(patient_context)} keys)[/dim]")

        if start_stage <= 3:
            ext_start = time.time()
            extraction_data = stage3_extraction(patient, schema_plan, exam_images)
            extraction_time = time.time() - ext_start
        else:
            combined_path = E2E_SOURCE_DIR / "stage3_extraction" / slug / "extraction_combined.json"
            extraction_data = _load_json(combined_path)
            console.print(f"  [dim]Stage 3 skipped — loaded extraction_combined.json ({len(extraction_data.get('pages', []))} pages)[/dim]")

        if start_stage <= 4:
            gen_start = time.time()
            docx_path, report_meta = stage4_report(patient, extraction_data, patient_context)
            generation_time = time.time() - gen_start
        else:
            docx_path = OUT_DIR / "stage4_report" / slug / "report.docx"
            console.print(f"  [dim]Stage 4 skipped — using existing {docx_path.name}[/dim]")

        if start_stage <= 5:
            gen_data, gt_data = stage5_parse(patient, docx_path)
        else:
            gen_data = _load_json(OUT_DIR / "stage5_parsed" / f"{slug}_generated_scan.json")
            gt_data = _load_json(OUT_DIR / "stage5_parsed" / f"{slug}_ground_truth_scan.json")
            console.print(f"  [dim]Stage 5 skipped — loaded parsed scans[/dim]")

        comparison = stage6_comparison(patient, gen_data, gt_data)

        all_results.append({
            "name": patient["name"],
            "slug": patient["slug"],
            "comparison": comparison,
            "extraction_time": round(extraction_time, 1),
            "generation_time": round(generation_time, 1),
            "patient_time": round(time.time() - patient_start, 1),
        })

        console.print(f"\n  Patient {patient['name']} done in {time.time()-patient_start:.0f}s  "
                       f"Score: {comparison.get('avg_score', '?')}/100")

    stage7_final(all_results)

    total_elapsed = time.time() - total_start
    console.print(f"\n  Total time: {total_elapsed:.0f}s")

    log_path = OUT_DIR / "console_log.txt"
    log_path.write_text(console.export_text(), encoding="utf-8")
    console.print(f"  Console log saved: {log_path}")


if __name__ == "__main__":
    main()
