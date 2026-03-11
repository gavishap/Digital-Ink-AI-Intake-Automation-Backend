"""
LLM-powered field-to-report mapping (LLM Call 2).

For each scanned-report + extraction pair, the LLM identifies which
extraction field_ids contributed to each report element and how
the data was transformed.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import anthropic
import instructor
from rich.console import Console

from ..scanner.models import ScannedReport
from .models import (
    DataSource,
    ElementMapping,
    LLMPairCorrelationResult,
    PairCorrelation,
)

console = Console()

CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 16000
MAX_PARALLEL = 3


def _build_client() -> instructor.Instructor:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


def _summarise_report_for_prompt(report: ScannedReport) -> str:
    """Build a concise representation of report elements for the LLM.

    Includes all elements (the LLM determines which are static template
    text vs dynamic patient content based on the extraction data).
    """
    lines: list[str] = []
    for el in report.flat_elements:
        content = el.text[:300] if el.text else "(empty)"
        if not content.strip():
            continue
        section = el.section_id or "no_section"
        el_type = el.type
        if el.table_cells:
            rows_preview = " | ".join(
                "/".join(cell[:40] for cell in row)
                for row in el.table_cells[:5]
            )
            content = f"TABLE: {rows_preview}"
        lines.append(f"[{el.element_id}] section={section} type={el_type}: {content}")
    return "\n".join(lines)


def _summarise_extraction_for_prompt(extraction: dict[str, Any]) -> str:
    """Build a concise representation of extracted field values.

    Supports both raw extraction format (field_values with nested dicts)
    and condensed format (flat fields dict).  For condensed dicts, produces
    richer output including is_checked, circled_options, and annotations so
    the correlation LLM can understand what each field represents.
    """
    lines: list[str] = []
    for page in extraction.get("pages", []):
        pnum = page.get("page_number", "?")
        fv_source = page.get("fields") or page.get("field_values") or {}
        for field_id, fv in fv_source.items():
            if isinstance(fv, str):
                lines.append(f"[page {pnum}] {field_id} = {fv[:200]}")
                continue
            if isinstance(fv, bool):
                lines.append(f"[page {pnum}] {field_id} = {fv}")
                continue
            if not isinstance(fv, dict):
                lines.append(f"[page {pnum}] {field_id} = {str(fv)[:200]}")
                continue

            parts: list[str] = []
            if "value" in fv and fv["value"] is not None:
                parts.append(str(fv["value"])[:200])
            if fv.get("is_checked") is True:
                parts.append("CHECKED=YES")
            elif fv.get("is_checked") is False:
                parts.append("CHECKED=NO")
            if fv.get("circled_options"):
                opts = fv["circled_options"]
                if isinstance(opts, list):
                    parts.append(f"circled=[{', '.join(str(o) for o in opts)}]")
                else:
                    parts.append(f"circled={opts}")
            if fv.get("annotation"):
                parts.append(f"note: {str(fv['annotation'])[:120]}")
            if fv.get("annotation_note"):
                parts.append(f"note: {str(fv['annotation_note'])[:120]}")

            lines.append(f"[page {pnum}] {field_id} = {' | '.join(parts) if parts else '(empty)'}")
    return "\n".join(lines)


def load_condensed_extraction(form_name: str, condensed_dir: Path) -> dict[str, Any] | None:
    """Load a condensed extraction JSON by form name stem."""
    stem = form_name.replace("_extraction", "").replace("_condensed", "")
    candidates = [
        condensed_dir / f"{stem}_condensed.json",
        condensed_dir / f"{stem}.json",
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


MAPPING_PROMPT = """Map extraction fields to report elements. Focus on STRUCTURAL RULES, not value accuracy.

Extraction values may be inaccurate (misread circles, OCR errors). Map the structural connection anyway.
Fields prefixed "sc_"/"ann_" come from spatial/annotation recovery.

data_source: "exam" (orofacial form), "lawyer_cover" (attorney pages), "both" (combined).
transformation: direct|formatted|narrative|list_assembly|table_population|conditional|aggregated|static.
transformation_notes: Write the RULE, e.g. "If q10_breathing=YES, include paragraph" or "Combine job requirements into list". Keep brief.

REPORT ELEMENTS:
{report_elements}

EXAM EXTRACTION:
{extraction_data}

LAWYER COVER:
{lawyer_data}

Map every report element to source field_ids. Put unmapped element_ids in unmapped_report_elements, unused field_ids in unmapped_extraction_fields."""


def correlate_pair(
    report: ScannedReport,
    extraction: dict[str, Any],
    lawyer_extraction: dict[str, Any] | None = None,
    client: Optional[instructor.Instructor] = None,
) -> PairCorrelation:
    """Correlate a single report+extraction pair using the LLM."""
    if client is None:
        client = _build_client()

    report_text = _summarise_report_for_prompt(report)
    extraction_text = _summarise_extraction_for_prompt(extraction)
    lawyer_text = (
        _summarise_extraction_for_prompt(lawyer_extraction)
        if lawyer_extraction and lawyer_extraction.get("pages")
        else "(none)"
    )

    prompt_content = MAPPING_PROMPT.format(
        report_elements=report_text,
        extraction_data=extraction_text,
        lawyer_data=lawyer_text,
    )

    llm_result: LLMPairCorrelationResult = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt_content}],
        response_model=LLMPairCorrelationResult,
    )

    element_map = {el.element_id: el for el in report.flat_elements}
    mappings: list[ElementMapping] = []
    for lm in llm_result.mappings:
        el = element_map.get(lm.report_element_id)
        mappings.append(ElementMapping(
            report_element_id=lm.report_element_id,
            report_section_id=(el.section_id or "unknown") if el else "unknown",
            report_text=(el.text[:300]) if el else "",
            data_source=lm.data_source,
            source_field_ids=lm.source_field_ids,
            transformation=lm.transformation,
            transformation_notes=lm.transformation_notes,
            format_pattern=lm.format_pattern,
            confidence=lm.confidence,
        ))

    total_elements = sum(1 for el in report.flat_elements if el.text.strip())
    coverage = len(mappings) / max(total_elements, 1)

    return PairCorrelation(
        report_id=report.report_id,
        extraction_id=extraction.get("form_id", report.report_id),
        patient_name=report.detected_patient_name,
        mappings=mappings,
        unmapped_report_elements=llm_result.unmapped_report_elements,
        unmapped_extraction_fields=llm_result.unmapped_extraction_fields,
        mapping_coverage=round(coverage, 3),
    )


_NAME_PREFIXES = {"de", "del", "la", "los", "las", "van", "von", "di"}

def _normalise_name(filename_stem: str) -> str:
    """Normalise a filename stem into a comparable name key.

    Handles both formats:
      Report:     'anderson.ronald.011126.INI_scan' -> 'anderson ronald'
      Extraction: 'RONALD ANDERSON INIT_condensed'  -> 'anderson ronald'
    """
    s = filename_stem.lower()
    for suffix in ("_scan", "_condensed", "_extraction", "_lawyer"):
        s = s.replace(suffix, "")
    s = s.replace(".", " ").replace("_", " ")
    parts = s.split()
    name_parts: list[str] = []
    for p in parts:
        if p.isdigit() or (len(p) == 6 and p.isdigit()):
            continue
        if p in ("ini", "init", "m"):
            continue
        if p in _NAME_PREFIXES:
            continue
        # Split compound prefixed names: "demayorga" -> "mayorga"
        for prefix in _NAME_PREFIXES:
            if p.startswith(prefix) and len(p) > len(prefix) + 2:
                p = p[len(prefix):]
                break
        name_parts.append(p)
    return " ".join(sorted(name_parts))


def _match_pairs(
    report_files: list[Path],
    extraction_files: list[Path],
) -> list[tuple[Path, Path]]:
    """Match report files to extraction files by normalised patient name."""
    ext_lookup: dict[str, Path] = {}
    for ef in extraction_files:
        key = _normalise_name(ef.stem)
        ext_lookup[key] = ef

    pairs: list[tuple[Path, Path]] = []
    unmatched_reports: list[str] = []

    for rf in report_files:
        rkey = _normalise_name(rf.stem)
        if rkey in ext_lookup:
            pairs.append((rf, ext_lookup[rkey]))
        else:
            best_match = None
            best_overlap = 0
            rset = set(rkey.split())
            for ekey, ef in ext_lookup.items():
                eset = set(ekey.split())
                overlap = len(rset & eset)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_match = ef
            if best_match and best_overlap >= 2:
                pairs.append((rf, best_match))
            else:
                unmatched_reports.append(rf.name)

    return pairs


def _find_lawyer(ext_name_key: str, lawyer_lookup: dict[str, Path]) -> dict[str, Any] | None:
    """Find matching lawyer data by name key."""
    lf = lawyer_lookup.get(ext_name_key)
    if not lf:
        eset = set(ext_name_key.split())
        for lkey, candidate in lawyer_lookup.items():
            if len(set(lkey.split()) & eset) >= 2:
                lf = candidate
                break
    if lf:
        return json.loads(lf.read_text(encoding="utf-8"))
    return None


def _process_one_pair(
    idx: int,
    total: int,
    report_path: Path,
    extraction_path: Path,
    lawyer_lookup: dict[str, Path],
    output_dir: Path,
    skip_existing: bool,
) -> PairCorrelation | None:
    """Correlate a single pair — designed for parallel execution."""
    out_path = output_dir / f"correlation_{idx + 1:02d}.json"
    if skip_existing and out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8", errors="replace"))
            console.print(f"  [dim]Skip (exists): pair {idx+1} {report_path.stem}[/dim]")
            return PairCorrelation.model_validate(data)
        except Exception:
            pass

    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    report = ScannedReport.model_validate(report_data)
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    lawyer_data = _find_lawyer(_normalise_name(extraction_path.stem), lawyer_lookup)

    label = f"Pair {idx+1}/{total}: {report_path.stem[:30]}"
    console.print(f"  [bold]{label}[/bold] ...")

    client = _build_client()
    try:
        correlation = correlate_pair(report, extraction, lawyer_data, client)
        out_path.write_text(correlation.model_dump_json(indent=2), encoding="utf-8")
        console.print(
            f"  [green]{label} -> {len(correlation.mappings)} mappings, "
            f"{correlation.mapping_coverage:.0%} cov[/green]"
        )
        return correlation
    except Exception as e:
        console.print(f"  [red]{label} FAILED: {e}[/red]")
        return None


def correlate_all_pairs(
    reports_dir: Path,
    extractions_dir: Path,
    output_dir: Path,
    lawyer_dir: Path | None = None,
    skip_existing: bool = True,
    parallel: int = MAX_PARALLEL,
) -> list[PairCorrelation]:
    """Correlate all report+extraction pairs in parallel.

    Args:
        reports_dir: Directory with scanned report JSONs.
        extractions_dir: Directory with exam extraction (or condensed) JSONs.
        output_dir: Where to write correlation results.
        lawyer_dir: Optional directory with lawyer cover page extractions.
        skip_existing: Skip pairs whose output file already exists.
        parallel: Max concurrent LLM calls.
    """
    report_files = sorted(reports_dir.glob("*.json"))
    extraction_files = sorted(extractions_dir.glob("*.json"))

    if not report_files:
        console.print(f"[red]No report JSONs in {reports_dir}[/red]")
        return []
    if not extraction_files:
        console.print(f"[red]No extraction JSONs in {extractions_dir}[/red]")
        return []

    pairs = _match_pairs(report_files, extraction_files)
    if not pairs:
        console.print("[red]No matching report-extraction pairs found[/red]")
        return []

    lawyer_lookup: dict[str, Path] = {}
    if lawyer_dir and lawyer_dir.exists():
        for lf in lawyer_dir.glob("*.json"):
            lawyer_lookup[_normalise_name(lf.stem)] = lf

    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        f"[bold]Correlating {len(pairs)} pairs | model={CLAUDE_MODEL} | "
        f"parallel={parallel} | skip_existing={skip_existing}[/bold]"
    )

    results: list[tuple[int, PairCorrelation | None]] = []

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = {
            pool.submit(
                _process_one_pair,
                i, len(pairs), rp, ep, lawyer_lookup, output_dir, skip_existing,
            ): i
            for i, (rp, ep) in enumerate(pairs)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                results.append((idx, result))
            except Exception as e:
                console.print(f"  [red]Pair {idx+1} exception: {e}[/red]")
                results.append((idx, None))

    results.sort(key=lambda x: x[0])
    return [r for _, r in results if r is not None]
