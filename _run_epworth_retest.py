"""Focused differential extraction of just the Epworth table using cropped images."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from src.models import FormSchema, PageSchema
from src.services.extraction_pipeline import ExtractionPipeline

console = Console()

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUT_DIR = Path(__file__).parent / "report_learning" / "outputs" / "page3_retest"

FILLED_CROP = OUT_DIR / "epworth_filled_crop.png"
BLANK_CROP  = OUT_DIR / "epworth_blank_crop.png"


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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(TEMPLATES_DIR / "orofacial_exam_schema.json", encoding="utf-8") as f:
        schema_data = json.load(f)
    _fix_enum_values(schema_data)
    form_schema = FormSchema(**schema_data)
    page11_schema: PageSchema = {ps.page_number: ps for ps in form_schema.pages}[11]

    # Keep only the Epworth section fields
    epworth_section = next(
        (s for s in page11_schema.sections if "epworth" in s.section_id.lower()),
        None,
    )
    if not epworth_section:
        console.print("[red]Epworth section not found in schema[/red]")
        return

    # Build a minimal page schema with just the Epworth section
    epworth_schema = page11_schema.model_copy(deep=True)
    epworth_schema.sections = [epworth_section]
    epworth_schema.standalone_fields = []
    epworth_schema.standalone_tables = []

    console.print("[bold cyan]Running focused Epworth differential extraction...[/bold cyan]")
    pipeline = ExtractionPipeline()

    result = pipeline.extract_page(
        image_path=FILLED_CROP,
        page_number=11,
        page_schema=epworth_schema,
        blank_image_path=BLANK_CROP,
        extraction_mode="differential",
    )

    console.print("\n[bold green]Results:[/bold green]")
    ground_truth = {"sitting_reading": 0, "watching_tv": 1, "sitting_inactive": 0,
                    "passenger_car": 0, "lying_down_afternoon": 3, "sitting_talking": 0,
                    "sitting_after_lunch": 0, "car_traffic": 0}

    correct = 0
    for fid, fv in result.field_values.items():
        val = fv.get("value") or (fv.get("circled_options") or [None])[0]
        short = fid.replace("p11_epworth_", "")
        actual = ground_truth.get(short, "?")
        match = "OK" if str(val) == str(actual) else "XX"
        console.print(f"  {match} {short:25s} got={val}  actual={actual}")
        if str(val) == str(actual):
            correct += 1

    console.print(f"\n[bold]Score: {correct}/8 correct[/bold]")

    with open(OUT_DIR / "epworth_raw.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(result.model_dump_json()), f, indent=2)


if __name__ == "__main__":
    main()
