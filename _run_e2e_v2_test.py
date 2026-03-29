"""
E2E Pipeline Comparison Test V2

Starts from raw signed PDF exams, runs the full production-equivalent pipeline
locally (page trimming, 2-stage vision extraction with merged schemas for old-format
pages, first-page context parsing, report generation), then compares 3 generated
reports against the real doctor-written reports section-by-section using
Together/Fireworks LLMs.

Run from: c:/Digital_Ink/form-extractor
Usage:    python _run_e2e_v2_test.py
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
    docx_bytes, low_conf = crg.generate_clinical_report(
        extraction_data, patient_context=patient_context,
    )
    elapsed = time.time() - t0

    docx_path = rpt_dir / "report.docx"
    docx_path.write_bytes(docx_bytes)
    _save_json(rpt_dir / "low_confidence_fields.json", low_conf)
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


def _compare_section(
    client: OpenAI, model: str,
    gen_text: str, gt_text: str,
    section_title: str, fairness_note: str = "",
) -> dict:
    prompt = SECTION_COMPARISON_PROMPT.format(
        generated_text=gen_text[:3000],
        ground_truth_text=gt_text[:3000],
        section_title=section_title,
        fairness_note=fairness_note,
    )
    try:
        resp = client.chat.completions.create(
            model=model, max_tokens=2000, temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        return {
            "data_accuracy_score": 0, "language_match_score": 0,
            "hallucinations": [], "missing_data": [],
            "key_differences": [f"Comparison failed: {e}"],
            "overall_score": 0, "notes": f"Error: {e}",
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
    gen_sections = gen_data.get("sections", [])
    gt_sections = gt_data.get("sections", [])

    gt_by_id: dict[str, list[dict]] = {}
    for sec in gt_sections:
        sid = sec.get("id", "")
        gt_by_id.setdefault(sid, []).append(sec)

    gen_by_id: dict[str, list[dict]] = {}
    for sec in gen_sections:
        sid = sec.get("id", "")
        gen_by_id.setdefault(sid, []).append(sec)

    old_format_sections = {
        "epworth_sleepiness_scale", "p11_epworth", "sleep_disturbances",
        "p3_mouth_symptoms", "bad_breath", "taste_changes",
    }
    tx_received_sections = {"tx_received"}

    all_section_ids = sorted(set(list(gen_by_id.keys()) + list(gt_by_id.keys())))
    section_results = []

    for sid in all_section_ids:
        gen_list = gen_by_id.get(sid, [])
        gt_list = gt_by_id.get(sid, [])
        max_occ = max(len(gen_list), len(gt_list))

        for occ in range(max_occ):
            gen_sec = gen_list[occ] if occ < len(gen_list) else None
            gt_sec = gt_list[occ] if occ < len(gt_list) else None

            gen_text = _extract_section_text(gen_sec) if gen_sec else ""
            gt_text = _extract_section_text(gt_sec) if gt_sec else ""
            title = (gen_sec or gt_sec or {}).get("heading", sid)

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
                fairness = ""
                if sid in old_format_sections:
                    fairness = ("NOTE: This section's data came from an old-format exam page "
                                "via merged schema extraction. Minor field mapping differences are expected.")
                elif sid in tx_received_sections:
                    fairness = ("NOTE: The Tx Received section does NOT exist in the old exam format. "
                                "Any missing data here is expected, not a pipeline bug.")
                result = _compare_section(client, model, gen_text, gt_text, title, fairness)

            result["section_id"] = sid
            result["occurrence"] = occ
            result["heading"] = title
            section_results.append(result)

            _save_json(sec_dir / f"{sid}_{occ}.json", result)

            score = result.get("overall_score", 0)
            style = "green" if score >= 80 else "yellow" if score >= 50 else "red"
            console.print(f"  [{style}]{sid}:{occ} — score={score}[/{style}]  "
                          f"halluc={len(result.get('hallucinations', []))} "
                          f"missing={len(result.get('missing_data', []))}")

    _save_json(cmp_dir / "comparison_summary.json", section_results)

    scores_table = Table(title=f"Section Scores — {patient['name']}")
    scores_table.add_column("Section", width=40)
    scores_table.add_column("Score", width=7)
    scores_table.add_column("Halluc", width=7)
    scores_table.add_column("Missing", width=7)
    for r in sorted(section_results, key=lambda x: x.get("overall_score", 0)):
        s = r.get("overall_score", 0)
        style = "green" if s >= 80 else "yellow" if s >= 50 else "red"
        scores_table.add_row(
            f"{r['section_id']}:{r['occurrence']}",
            f"[{style}]{s}[/{style}]",
            str(len(r.get("hallucinations", []))),
            str(len(r.get("missing_data", []))),
        )
    console.print(scores_table)

    md_lines = [f"# Comparison: {patient['name']}\n"]
    for r in sorted(section_results, key=lambda x: x.get("overall_score", 0)):
        md_lines.append(f"## {r['heading']} (occ {r['occurrence']}) — Score: {r.get('overall_score', 0)}")
        md_lines.append(f"- Data accuracy: {r.get('data_accuracy_score', 0)}")
        md_lines.append(f"- Language match: {r.get('language_match_score', 0)}")
        if r.get("hallucinations"):
            md_lines.append(f"- Hallucinations: {'; '.join(r['hallucinations'])}")
        if r.get("missing_data"):
            md_lines.append(f"- Missing: {'; '.join(r['missing_data'])}")
        if r.get("key_differences"):
            md_lines.append(f"- Differences: {'; '.join(r['key_differences'])}")
        md_lines.append(f"- Notes: {r.get('notes', '')}\n")

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
    }


# ---------------------------------------------------------------------------
# Stage 7: Final consolidated report
# ---------------------------------------------------------------------------

def stage7_final(all_results: list[dict]) -> None:
    _banner(7, "FINAL REPORT")

    scores = [r["comparison"].get("avg_score", 0) for r in all_results]
    avg = sum(scores) / len(scores) if scores else 0

    summary = {
        "test_date": datetime.now().isoformat(),
        "patients": [{
            "name": r["name"],
            "avg_score": r["comparison"].get("avg_score", 0),
            "total_hallucinations": r["comparison"].get("total_hallucinations", 0),
            "total_missing": r["comparison"].get("total_missing", 0),
            "sections_compared": r["comparison"].get("sections_compared", 0),
            "extraction_time": r.get("extraction_time", 0),
            "generation_time": r.get("generation_time", 0),
        } for r in all_results],
        "aggregate_score": round(avg, 1),
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

    md = ["# E2E V2 Pipeline Comparison — Final Report\n"]
    md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    md.append(f"**Aggregate Score:** {avg:.1f}/100\n")

    md.append("## Per-Patient Summary\n")
    md.append("| Patient | Avg Score | Hallucinations | Missing Data | Sections |")
    md.append("|---------|-----------|----------------|--------------|----------|")
    for r in all_results:
        c = r["comparison"]
        md.append(f"| {r['name']} | {c.get('avg_score', 0):.1f} | "
                  f"{c.get('total_hallucinations', 0)} | {c.get('total_missing', 0)} | "
                  f"{c.get('sections_compared', 0)} |")

    md.append("\n## Worst Sections (across all patients)\n")
    md.append("| Patient | Section | Score | Halluc | Missing |")
    md.append("|---------|---------|-------|--------|---------|")
    for w in worst:
        md.append(f"| {w.get('patient', '?')} | {w['section_id']}:{w['occurrence']} | "
                  f"{w.get('overall_score', 0)} | {len(w.get('hallucinations', []))} | "
                  f"{len(w.get('missing_data', []))} |")

    if all_halluc:
        md.append("\n## All Hallucinations\n")
        for h in all_halluc[:30]:
            md.append(f"- {h}")

    if all_missing:
        md.append("\n## All Missing Data\n")
        for m in all_missing[:30]:
            md.append(f"- {m}")

    md.append("\n## Weakest Stage Analysis\n")
    extraction_issues = sum(1 for sr in all_section_results
                            if any("extraction" in str(d).lower() or "field" in str(d).lower()
                                   for d in sr.get("key_differences", [])))
    generation_issues = sum(1 for sr in all_section_results
                            if any("narrative" in str(d).lower() or "language" in str(d).lower() or "tone" in str(d).lower()
                                   for d in sr.get("key_differences", [])))
    data_issues = sum(1 for sr in all_section_results
                      if any("data" in str(d).lower() or "value" in str(d).lower() or "missing" in str(d).lower()
                             for d in sr.get("key_differences", [])))
    md.append(f"- Extraction-related issues: {extraction_issues}")
    md.append(f"- Generation/narrative issues: {generation_issues}")
    md.append(f"- Data accuracy issues: {data_issues}")

    (OUT_DIR / "final_report.md").write_text("\n".join(md), encoding="utf-8")

    _save_json(OUT_DIR / "run_meta.json", {
        "test_date": datetime.now().isoformat(),
        "patients": [p["name"] for p in PATIENTS],
        "aggregate_score": round(avg, 1),
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
    console.print(f"\n  Aggregate Score: {avg:.1f}/100")
    console.print(f"  Reports saved to: {OUT_DIR}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    console.print(f"\n{'='*70}")
    console.print("  E2E PIPELINE COMPARISON TEST V2")
    console.print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"{'='*70}")

    total_start = time.time()
    stage0_setup()

    all_results = []

    for patient in PATIENTS:
        console.print(f"\n{'#'*70}")
        console.print(f"  PATIENT: {patient['name']}")
        console.print(f"{'#'*70}")
        patient_start = time.time()

        exam_images, schema_plan = stage1_split(patient)
        patient_context = stage2_context(patient)

        ext_start = time.time()
        extraction_data = stage3_extraction(patient, schema_plan, exam_images)
        extraction_time = time.time() - ext_start

        gen_start = time.time()
        docx_path, report_meta = stage4_report(patient, extraction_data, patient_context)
        generation_time = time.time() - gen_start

        gen_data, gt_data = stage5_parse(patient, docx_path)
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
