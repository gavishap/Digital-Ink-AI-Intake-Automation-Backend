"""Quick re-extraction of Bachar page 1 to validate YES/NO fixes."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console

from src.models import FormSchema, PageSchema
from src.services.extraction_pipeline import ExtractionPipeline

console = Console()

TEMPLATES_DIR = Path(__file__).parent / "templates"
EXAM_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 1
PDF_IMAGE_NUM = EXAM_PAGE + 1  # PDF page 1 is cover, so exam page N = pdf page N+1

IMAGE_PATH = Path(__file__).parent / "report_learning" / "outputs" / "e2e_v2" / "stage1_split" / "bachar_page_images" / f"page_{PDF_IMAGE_NUM:03d}.png"
BLANK_PATH = TEMPLATES_DIR / f"orofacial_exam_blank_page_{EXAM_PAGE}.png"
OUT_DIR = Path(__file__).parent / "report_learning" / "outputs" / f"page{EXAM_PAGE}_retest"


SCHEMA_PLAN_PATH = Path(__file__).parent / "report_learning" / "outputs" / "e2e_v2" / "stage1_split" / "bachar_schema_plan.json"


def _fix_enum_values(obj):
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


def _merge_page_schemas(primary: PageSchema, donor: PageSchema) -> PageSchema:
    merged = primary.model_copy(deep=True)
    merged.sections.extend(donor.sections)
    merged.standalone_fields.extend(donor.standalone_fields)
    merged.standalone_tables.extend(donor.standalone_tables)
    return merged


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    console.print("[bold cyan]Loading schema...[/bold cyan]")
    with open(TEMPLATES_DIR / "orofacial_exam_schema.json", encoding="utf-8") as f:
        schema_data = json.load(f)
    _fix_enum_values(schema_data)
    form_schema = FormSchema(**schema_data)
    schema_pages = {ps.page_number: ps for ps in form_schema.pages}

    with open(SCHEMA_PLAN_PATH, encoding="utf-8") as f:
        schema_plan = json.load(f)
    plan_entry = next((e for e in schema_plan if e["exam_page"] == EXAM_PAGE), None)

    if plan_entry and plan_entry["mode"] == "merged_schema":
        primary_num, donor_num = plan_entry["schema_pages"][0], plan_entry["schema_pages"][1]
        page_schema = _merge_page_schemas(schema_pages[primary_num], schema_pages[donor_num])
        BLANK_PATH_RESOLVED = BLANK_PATH  # no blank for merged pages
        mode = "standard"
        console.print(f"[bold cyan]Exam page: {EXAM_PAGE} | Mode: merged_schema (pages {primary_num}+{donor_num}) | Image: page_{PDF_IMAGE_NUM:03d}.png[/bold cyan]")
    else:
        page_schema = schema_pages[EXAM_PAGE]
        BLANK_PATH_RESOLVED = BLANK_PATH
        mode = "differential" if BLANK_PATH.exists() else "standard"
        console.print(f"[bold cyan]Exam page: {EXAM_PAGE} | Mode: {mode} | Image: page_{PDF_IMAGE_NUM:03d}.png[/bold cyan]")

    pipeline = ExtractionPipeline()

    provider = sys.argv[1] if len(sys.argv) > 1 else None
    console.print(f"\n[bold green]Extracting ({mode}, provider={provider or 'default'})...[/bold green]")
    t0 = time.time()
    result = pipeline.extract_page(
        image_path=IMAGE_PATH,
        page_number=EXAM_PAGE,
        page_schema=page_schema,
        blank_image_path=BLANK_PATH_RESOLVED if (mode == "differential" and BLANK_PATH_RESOLVED.exists()) else None,
        extraction_mode=mode,
        force_provider=provider,
    )
    elapsed = time.time() - t0

    result_dict = json.loads(result.model_dump_json())
    with open(OUT_DIR / "page_raw.json", "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    field_count = len(result.field_values) if result.field_values else 0
    conf = result.overall_confidence

    summary_lines = [f"Page {EXAM_PAGE} | Mode: {mode} | Fields: {field_count} | Confidence: {conf:.2f} | Time: {elapsed:.1f}s"]
    if result.field_values:
        for fid, fv in result.field_values.items():
            val = fv.get("value", "") if isinstance(fv, dict) else fv
            if val is None and isinstance(fv, dict):
                checked = fv.get("is_checked")
                if checked is not None:
                    val = "YES" if checked else "NO"
            c = fv.get("confidence", 1.0) if isinstance(fv, dict) else 1.0
            summary_lines.append(f"  {fid:50s} = {str(val)[:60]:60s}  conf={c:.2f}")

    summary_text = "\n".join(summary_lines)
    (OUT_DIR / "fields_summary.txt").write_text(summary_text, encoding="utf-8")

    console.print(f"\n[bold green]Done in {elapsed:.1f}s — {field_count} fields, confidence {conf:.2f}[/bold green]")
    console.print(f"[bold]Output: {OUT_DIR}[/bold]\n")
    console.print(summary_text)


if __name__ == "__main__":
    main()
