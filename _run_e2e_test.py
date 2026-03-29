"""
E2E Pipeline Comparison Test

Generates clinical reports from 3 real patient extractions using the full LLM
pipeline, then compares those reports against the actual doctor-written ground
truth reports using Claude for section-by-section analysis.

Run from: c:/Digital_Ink/form-extractor
Usage:    python _run_e2e_test.py
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH)

sys.path.insert(0, str(Path(__file__).parent))

spec = importlib.util.spec_from_file_location(
    "crg", str(Path(__file__).parent / "src" / "generators" / "clinical_report_generator.py")
)
crg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crg)

from report_learning.scanner.docx_parser import parse_docx  # noqa: E402

import anthropic  # noqa: E402

BASE = Path(__file__).parent
OUT = BASE / "report_learning" / "outputs" / "e2e_test"

PATIENTS = [
    {
        "name": "Ronald Anderson",
        "condensed": BASE / "report_learning" / "outputs" / "extractions_v2" / "condensed" / "RONALD ANDERSON INIT_condensed.json",
        "lawyer": BASE / "report_learning" / "outputs" / "extractions_lawyer" / "RONALD ANDERSON INIT_extraction.json",
        "ground_truth": BASE / "report_learning" / "outputs" / "scanned" / "anderson.ronald.011126.INI_scan.json",
        "slug": "anderson",
    },
    {
        "name": "Patricia Benton",
        "condensed": BASE / "report_learning" / "outputs" / "extractions_v2" / "condensed" / "PATRICIA BENTON INIT_condensed.json",
        "lawyer": BASE / "report_learning" / "outputs" / "extractions_lawyer" / "PATRICIA BENTON INIT_extraction.json",
        "ground_truth": BASE / "report_learning" / "outputs" / "scanned" / "benton.patricia.011126.INI_scan.json",
        "slug": "benton",
    },
    {
        "name": "Jenea Carraway",
        "condensed": BASE / "report_learning" / "outputs" / "extractions_v2" / "condensed" / "JENEA CARRAWAY INIT_condensed.json",
        "lawyer": BASE / "report_learning" / "outputs" / "extractions_lawyer" / "JENEA CARRAWAY INIT_extraction.json",
        "ground_truth": BASE / "report_learning" / "outputs" / "scanned" / "carraway.jenea.011126.INI_scan.json",
        "slug": "carraway",
    },
]

STAGE_DIRS = [
    "stage1_input",
    "stage2_normalized",
    "stage3_derived",
    "stage4_field_resolution",
    "stage5_generated_docx",
    "stage6_generated_scan",
    "stage7_ground_truth_scan",
    "stage8_comparison",
]


def _ensure_dirs():
    OUT.mkdir(parents=True, exist_ok=True)
    for d in STAGE_DIRS:
        (OUT / d).mkdir(exist_ok=True)


def _save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _print_stage(stage: int, title: str, patient: str):
    print(f"\n{'='*70}")
    print(f"  STAGE {stage}: {title}  —  {patient}")
    print(f"{'='*70}")


# ---------------------------------------------------------------------------
# Stage 1: Snapshot Inputs
# ---------------------------------------------------------------------------

def stage1_snapshot(patient: dict) -> dict:
    _print_stage(1, "SNAPSHOT INPUTS", patient["name"])
    out_dir = OUT / "stage1_input"

    condensed = _load_json(patient["condensed"])
    lawyer = _load_json(patient["lawyer"])

    slug = patient["slug"]
    _save_json(out_dir / f"{slug}_condensed.json", condensed)
    _save_json(out_dir / f"{slug}_lawyer.json", lawyer)

    total_cond_fields = sum(len(p.get("fields", {})) for p in condensed.get("pages", []))
    total_law_fields = sum(len(p.get("field_values", {})) for p in lawyer.get("pages", []))
    print(f"  Condensed: {len(condensed.get('pages', []))} pages, {total_cond_fields} fields")
    print(f"  Lawyer:    {len(lawyer.get('pages', []))} pages, {total_law_fields} fields")

    return {"condensed": condensed, "lawyer": lawyer}


# ---------------------------------------------------------------------------
# Stage 2: Normalize
# ---------------------------------------------------------------------------

def stage2_normalize(patient: dict, raw: dict) -> dict:
    _print_stage(2, "NORMALIZE EXTRACTION", patient["name"])
    out_dir = OUT / "stage2_normalized"

    exam_pages = [
        {"page_number": p["page_number"], "field_values": p.get("fields", {})}
        for p in raw["condensed"].get("pages", [])
    ]
    lawyer_pages = [
        {"page_number": p["page_number"], "field_values": p.get("field_values", {})}
        for p in raw["lawyer"].get("pages", [])
    ]

    all_pages = lawyer_pages + exam_pages
    all_fields = crg._flatten_all_fields(all_pages)

    snapshot = {"exam_pages": len(exam_pages), "lawyer_pages": len(lawyer_pages), "all_fields_count": len(all_fields)}
    _save_json(out_dir / f"{patient['slug']}_normalized.json", snapshot)

    print(f"  Flattened: {len(all_pages)} total pages, {len(all_fields)} fields")

    return {"all_fields": all_fields, "pages": all_pages}


# ---------------------------------------------------------------------------
# Stage 3: Derive Fields
# ---------------------------------------------------------------------------

def stage3_derive(patient: dict, normalized: dict) -> dict:
    _print_stage(3, "DERIVE FIELDS", patient["name"])
    out_dir = OUT / "stage3_derived"

    all_fields = normalized.get("all_fields", crg._flatten_all_fields(normalized.get("pages", [])))
    derived = crg._derive_fields(all_fields, crg._FIELD_MAP, patient["name"])
    _save_json(out_dir / f"{patient['slug']}_derived.json", derived)

    key_fields = [
        "patient_name", "patient_title", "his_her", "he_she",
        "pain_qualifier", "diagnosis_list", "case_number", "venue",
        "date_of_injury", "occupation", "exam_date",
    ]
    print("  Key derived values:")
    for k in key_fields:
        v = derived.get(k, "—")
        display = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
        print(f"    {k:30s} = {display}")

    return derived


# ---------------------------------------------------------------------------
# Stage 4: Field Resolution Audit
# ---------------------------------------------------------------------------

def stage4_field_audit(patient: dict, normalized: dict, derived: dict) -> dict:
    _print_stage(4, "FIELD RESOLUTION AUDIT", patient["name"])
    out_dir = OUT / "stage4_field_resolution"

    rules = crg._load_rules()
    all_field_ids = set()
    for sec in rules.get("sections", []):
        all_field_ids.update(sec.get("source_field_ids", []))

    all_fields = normalized.get("all_fields", crg._flatten_all_fields(normalized.get("pages", [])))
    resolution = {}
    for fid in sorted(all_field_ids):
        val = crg._resolve_field(fid, all_fields, derived, crg._FIELD_MAP)
        resolution[fid] = str(val) if val is not None else None

    _save_json(out_dir / f"{patient['slug']}_field_resolution.json", resolution)

    resolved = sum(1 for v in resolution.values() if v is not None)
    total = len(resolution)
    unresolved = [fid for fid, v in resolution.items() if v is None]

    print(f"  Resolved: {resolved}/{total} ({100*resolved/total:.0f}%)")
    if unresolved:
        print(f"  Unresolved ({len(unresolved)}):")
        for fid in unresolved[:15]:
            print(f"    - {fid}")
        if len(unresolved) > 15:
            print(f"    ... and {len(unresolved)-15} more")

    return {"resolved": resolved, "total": total, "unresolved": unresolved}


# ---------------------------------------------------------------------------
# Stage 5: Generate FULL DOCX (Real LLM Narratives)
# ---------------------------------------------------------------------------

def stage5_generate_docx(patient: dict, raw: dict) -> Path:
    _print_stage(5, "GENERATE FULL DOCX (LLM)", patient["name"])
    out_dir = OUT / "stage5_generated_docx"

    extraction_data = {
        "patient_name": patient["name"],
        "pages": [
            {"page_number": p["page_number"], "field_values": p.get("fields", {})}
            for p in raw["condensed"].get("pages", [])
        ],
    }
    _unused_lawyer_data = {
        "pages": [
            {"page_number": p["page_number"], "field_values": p.get("field_values", {})}
            for p in raw["lawyer"].get("pages", [])
        ],
    }

    print(f"  Calling generate_clinical_report() with real LLM...")
    print(f"  This will make ~30 LLM calls — expect 3-5 minutes...")
    t0 = time.time()
    docx_bytes, _low_conf = crg.generate_clinical_report(extraction_data)
    elapsed = time.time() - t0

    docx_path = out_dir / f"{patient['slug']}_report.docx"
    docx_path.write_bytes(docx_bytes)

    size_kb = len(docx_bytes) / 1024
    print(f"  Generated: {docx_path.name}  ({size_kb:.1f} KB, {elapsed:.1f}s)")
    return docx_path


# ---------------------------------------------------------------------------
# Stage 6: Parse Generated Report
# ---------------------------------------------------------------------------

def stage6_parse_generated(patient: dict, docx_path: Path) -> dict:
    _print_stage(6, "PARSE GENERATED REPORT", patient["name"])
    out_dir = OUT / "stage6_generated_scan"

    report = parse_docx(docx_path)
    scan_data = report.model_dump()
    _save_json(out_dir / f"{patient['slug']}_generated_scan.json", scan_data)

    narrative_sections = 0
    for sec in scan_data.get("sections", []):
        text = " ".join(e.get("text", "") for e in sec.get("elements", []))
        if len(text) > 100:
            narrative_sections += 1

    print(f"  Sections: {scan_data.get('total_sections', 0)}")
    print(f"  Sections with substantial text (>100 chars): {narrative_sections}")
    return scan_data


# ---------------------------------------------------------------------------
# Stage 7: Ground Truth Scans
# ---------------------------------------------------------------------------

def stage7_ground_truth(patient: dict) -> dict:
    _print_stage(7, "GROUND TRUTH SCAN", patient["name"])
    out_dir = OUT / "stage7_ground_truth_scan"

    gt_path = patient["ground_truth"]
    dest = out_dir / f"{patient['slug']}_ground_truth_scan.json"
    shutil.copy2(gt_path, dest)

    gt_data = _load_json(dest)
    print(f"  Copied pre-parsed scan: {gt_path.name}")
    print(f"  Sections: {gt_data.get('total_sections', 0)}")
    return gt_data


# ---------------------------------------------------------------------------
# Stage 8: Claude Comparison
# ---------------------------------------------------------------------------

def _extract_full_text(scan_data: dict) -> str:
    """Concatenate all section headings and element text into a single string."""
    parts = []
    for sec in scan_data.get("sections", []):
        heading = sec.get("heading", "")
        elements = sec.get("elements", [])
        section_text = heading
        for el in elements:
            txt = el.get("text", "").strip()
            if txt:
                section_text += "\n" + txt
        parts.append(section_text)
    return "\n\n".join(parts)


COMPARISON_PROMPT = """You are an expert clinical report analyst. You have two versions of an orofacial pain evaluation report for the same patient:

1. **GENERATED REPORT** — produced by our automated pipeline from extracted form data
2. **GROUND TRUTH REPORT** — the actual report written by Dr. Matthew (the doctor)

Compare them section-by-section and produce a structured analysis.

## Comparison Dimensions

### 1. Section Inventory
List which sections appear in both reports, which are only in the generated version, which are only in the ground truth.

### 2. Template-Fill Accuracy
For header sections (date, claim, venue, case number, patient name, DOB, occupation, phone), mandibular range of motion measurements, intraoral examination findings, and diagnosis codes — compare exact values. List matches and mismatches.

### 3. Narrative Content Comparison
For each narrative section present in both:
- Are the same clinical facts present?
- Is the patient name used correctly? (Mr./Ms. + correct last name)
- Are pronouns correct? (he/his for male, she/her for female)
- Is anything **hallucinated** (in generated but NOT in ground truth)?
- Is anything **missing** (in ground truth but NOT in generated)?
- Is the clinical tone appropriate?

### 4. Data Accuracy Spot-Check
Verify key facts match: dates, measurements, diagnosis codes, treatment history, social history details.

### 5. Overall Quality Score (0-100)
Provide a breakdown:
- Section coverage: X/Y sections present
- Data accuracy: correct facts / total verifiable facts
- Clinical tone: appropriate / needs improvement
- Hallucination count: number of fabricated details
- Missing data count: number of facts in ground truth but absent from generated

## Output Format

Use markdown with clear headers for each dimension. End with a JSON block:

```json
{
  "section_coverage": "X/Y",
  "data_accuracy_pct": 85,
  "clinical_tone": "appropriate",
  "hallucination_count": 2,
  "missing_data_count": 5,
  "overall_score": 78,
  "top_issues": ["issue1", "issue2", "issue3"]
}
```
"""


def stage8_comparison(patient: dict, generated_scan: dict, gt_scan: dict) -> dict:
    _print_stage(8, "CLAUDE COMPARISON", patient["name"])
    out_dir = OUT / "stage8_comparison"

    gen_text = _extract_full_text(generated_scan)
    gt_text = _extract_full_text(gt_scan)

    print(f"  Generated text: {len(gen_text)} chars")
    print(f"  Ground truth text: {len(gt_text)} chars")
    print(f"  Sending to Claude for comparison...")

    user_msg = (
        f"## Patient: {patient['name']}\n\n"
        f"---\n## GENERATED REPORT\n\n{gen_text}\n\n"
        f"---\n## GROUND TRUTH REPORT (Doctor's Original)\n\n{gt_text}"
    )

    client = anthropic.Anthropic()
    t0 = time.time()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=COMPARISON_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    elapsed = time.time() - t0

    comparison_text = response.content[0].text
    md_path = out_dir / f"{patient['slug']}_comparison.md"
    md_path.write_text(comparison_text, encoding="utf-8")

    print(f"  Claude response: {len(comparison_text)} chars ({elapsed:.1f}s)")
    print(f"  Saved: {md_path.name}")

    scores = _parse_scores(comparison_text)
    return scores


def _parse_scores(text: str) -> dict:
    """Extract the JSON score block from Claude's response."""
    import re
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {
        "section_coverage": "unknown",
        "data_accuracy_pct": 0,
        "clinical_tone": "unknown",
        "hallucination_count": -1,
        "missing_data_count": -1,
        "overall_score": 0,
        "top_issues": ["Could not parse scores from Claude response"],
    }


# ---------------------------------------------------------------------------
# Final Summary
# ---------------------------------------------------------------------------

def build_summary(results: list[dict]) -> dict:
    scores = [r.get("overall_score", 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    all_issues = []
    for r in results:
        all_issues.extend(r.get("top_issues", []))

    from collections import Counter
    issue_counts = Counter(all_issues)
    top_issues = [issue for issue, _ in issue_counts.most_common(10)]

    summary = {
        "test_date": datetime.now().isoformat(),
        "patients": results,
        "aggregate_score": round(avg_score, 1),
        "top_issues": top_issues,
    }
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 70)
    print("  E2E PIPELINE COMPARISON TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Patients: {', '.join(p['name'] for p in PATIENTS)}")
    print("=" * 70)

    _ensure_dirs()

    all_results = []
    total_start = time.time()

    for patient in PATIENTS:
        patient_start = time.time()
        print(f"\n{'#'*70}")
        print(f"  PATIENT: {patient['name']}")
        print(f"{'#'*70}")

        raw = stage1_snapshot(patient)
        normalized = stage2_normalize(patient, raw)
        derived = stage3_derive(patient, normalized)
        audit = stage4_field_audit(patient, normalized, derived)
        docx_path = stage5_generate_docx(patient, raw)
        generated_scan = stage6_parse_generated(patient, docx_path)
        gt_scan = stage7_ground_truth(patient)
        scores = stage8_comparison(patient, generated_scan, gt_scan)

        patient_result = {
            "name": patient["name"],
            "fields_resolved": f"{audit['resolved']}/{audit['total']}",
            "sections_generated": generated_scan.get("total_sections", 0),
            "sections_in_ground_truth": gt_scan.get("total_sections", 0),
            "elapsed_seconds": round(time.time() - patient_start, 1),
            **scores,
        }
        all_results.append(patient_result)

        print(f"\n  Patient {patient['name']} done in {patient_result['elapsed_seconds']}s")
        print(f"  Score: {scores.get('overall_score', '?')}/100")

    summary = build_summary(all_results)
    _save_json(OUT / "summary.json", summary)

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print("  FINAL SUMMARY")
    print("=" * 70)
    for r in all_results:
        print(f"  {r['name']:25s}  Score: {r.get('overall_score', '?'):>3}/100  "
              f"Fields: {r['fields_resolved']}  "
              f"Sections: {r['sections_generated']}/{r['sections_in_ground_truth']}")
    print(f"\n  Aggregate Score: {summary['aggregate_score']}/100")
    print(f"  Total Time: {total_elapsed:.0f}s")

    if summary["top_issues"]:
        print(f"\n  Top Issues:")
        for i, issue in enumerate(summary["top_issues"][:5], 1):
            print(f"    {i}. {issue}")

    print(f"\n  All outputs saved to: {OUT}")
    print(f"  Summary: {OUT / 'summary.json'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
