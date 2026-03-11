"""
Split extraction JSONs into exam pages and lawyer cover pages.

The signed PDF forms have 1-6 lawyer pages (case demographic sheets,
top sheets) prepended before the actual orofacial pain examination.
This module detects the split point and produces:
  - extractions_trimmed/  : exam pages only (used for 6-stage correlation)
  - extractions_lawyer/   : lawyer cover pages only (correlated separately
                            to identify report fields sourced from case info)

Detection tiers:
  1. First page with both a name-like AND nurse-like field key.
  2. First page with a name-like field AND a demographics field (date/birth).
  3. First page with medical content fields after leading empty/lawyer pages.
  4. Page 0 (assume no cover pages).
"""

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

MEDICAL_KEYWORDS = frozenset({
    "pain", "injury", "smoke", "alcohol", "medication", "vas",
    "halitosis", "diabetes", "blood_pressure", "thyroid",
    "hand_dominance", "breathing", "kidney", "headache", "allergy",
    "heart", "sleep", "before_", "after_", "presently_", "swallowing",
    "hoarseness", "saliva", "dry_mouth", "apnea", "cpap",
    "toothbrush", "floss", "bruxism", "numbness",
})

LAWYER_KEYWORDS = frozenset({
    "employer_address", "header_date", "header_page", "signature_title",
    "claim_no", "wcab", "adjuster", "attorney", "carrier",
})


def _keys_lower(field_values: dict) -> set[str]:
    return {k.lower().strip() for k in field_values}


def _has_name_field(keys: set[str]) -> bool:
    return any("name" in k for k in keys)


def _has_nurse_field(keys: set[str]) -> bool:
    return any("nurse" in k for k in keys)


def _has_demographics(keys: set[str]) -> bool:
    has_date = any(k in ("date", "p1_date") or k == "date" for k in keys)
    has_birth = any("birth" in k for k in keys)
    return has_date and has_birth


def _medical_score(keys: set[str]) -> int:
    score = 0
    for k in keys:
        if any(med in k for med in MEDICAL_KEYWORDS):
            score += 1
    return score


def _is_lawyer_page(keys: set[str]) -> bool:
    if not keys:
        return True
    return any(any(lk in k for lk in LAWYER_KEYWORDS) for k in keys)


def detect_form_start(pages: list[dict]) -> int:
    """Return the 0-based index of the first real examination page."""
    for idx, page in enumerate(pages):
        keys = _keys_lower(page.get("field_values", {}))
        if _has_name_field(keys) and _has_nurse_field(keys):
            return idx

    for idx, page in enumerate(pages):
        keys = _keys_lower(page.get("field_values", {}))
        if _has_name_field(keys) and _has_demographics(keys):
            return idx

    for idx, page in enumerate(pages):
        keys = _keys_lower(page.get("field_values", {}))
        if _is_lawyer_page(keys):
            continue
        if _medical_score(keys) >= 3:
            return idx

    return 0


def _renumber(pages: list[dict]) -> list[dict]:
    for i, p in enumerate(pages, start=1):
        p["page_number"] = i
    return pages


def split_single(data: dict) -> tuple[dict, dict, int]:
    """Split one extraction into exam + lawyer dicts.

    Returns (exam_data, lawyer_data, split_index).
    """
    pages = data.get("pages", [])
    split_idx = detect_form_start(pages)

    lawyer_pages = _renumber(list(pages[:split_idx]))
    exam_pages = _renumber(list(pages[split_idx:]))

    base = {k: v for k, v in data.items() if k != "pages"}

    exam = dict(base)
    exam["pages"] = exam_pages
    exam["_trim_info"] = {
        "source": "exam",
        "original_total_pages": len(pages),
        "pages_removed": split_idx,
        "original_start_page": split_idx + 1,
    }

    lawyer = dict(base)
    lawyer["pages"] = lawyer_pages
    lawyer["_trim_info"] = {
        "source": "lawyer_cover",
        "original_total_pages": len(pages),
        "lawyer_page_count": split_idx,
    }

    return exam, lawyer, split_idx


def _write_json(data: dict, path: Path):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def trim_all_extractions(
    input_dir: Path,
    output_dir: Path,
    lawyer_dir: Path | None = None,
) -> list[Path]:
    """Split all extraction JSONs into exam + lawyer outputs.

    Args:
        input_dir:  Directory with raw *_extraction.json files.
        output_dir: Directory for exam-only JSONs.
        lawyer_dir: Directory for lawyer-cover JSONs (optional; if None,
                    uses output_dir's sibling ``extractions_lawyer``).

    Returns list of exam output paths.
    """
    files = sorted(input_dir.glob("*_extraction.json"))
    if not files:
        console.print(f"[red]No extraction JSONs in {input_dir}[/red]")
        return []

    if lawyer_dir is None:
        lawyer_dir = output_dir.parent / "extractions_lawyer"

    output_dir.mkdir(parents=True, exist_ok=True)
    lawyer_dir.mkdir(parents=True, exist_ok=True)

    table = Table(title="Extraction Split Results")
    table.add_column("Form", style="cyan", min_width=35)
    table.add_column("Total", justify="right")
    table.add_column("Lawyer Pg", justify="right")
    table.add_column("Exam Pg", justify="right")

    exam_paths: list[Path] = []
    total_lawyer = 0
    forms_with_lawyer = 0

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        exam, lawyer, split_idx = split_single(data)

        exam_path = output_dir / f.name
        _write_json(exam, exam_path)
        exam_paths.append(exam_path)

        if split_idx > 0:
            lawyer_path = lawyer_dir / f.name
            _write_json(lawyer, lawyer_path)
            forms_with_lawyer += 1
        total_lawyer += split_idx

        orig = len(data.get("pages", []))
        table.add_row(
            data.get("form_name", f.stem),
            str(orig),
            str(split_idx) if split_idx > 0 else "-",
            str(len(exam["pages"])),
            style="green" if split_idx > 0 else "dim",
        )

    console.print(table)
    console.print(
        f"\n[bold]Split {len(files)} files: "
        f"{total_lawyer} lawyer pages from {forms_with_lawyer} forms -> {lawyer_dir.name}/[/bold]"
    )
    return exam_paths
