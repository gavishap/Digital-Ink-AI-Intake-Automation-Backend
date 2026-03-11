"""
Rule validation engine (LLM Calls 5 and 6).

Call 5: For each known case, simulates report generation with the rules
and compares against the original report section-by-section.

Call 6: For weak sections, asks the LLM to suggest rule refinements.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import anthropic
import instructor
from rich.console import Console
from rich.table import Table

from ..scanner.models import ScannedReport
from .models import (
    LLMRefinementResult,
    LLMValidationResult,
    ReportRules,
    RuleRefinement,
    SectionScore,
    ValidationResult,
)

console = Console()

CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_PARALLEL = 3


def _build_client() -> instructor.Instructor:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


def _simulate_section(rule, extraction: dict[str, Any]) -> str:
    """Produce a textual preview of what the rule would generate."""
    from .models import ContentType

    if rule.content_type == ContentType.STATIC_TEXT:
        return (rule.static_content or "(static)")[:200]

    if rule.content_type in (ContentType.DIRECT_FILL, ContentType.FORMATTED_FILL):
        if rule.template:
            text = rule.template
            for fid in rule.source_field_ids:
                val = _lookup_field(extraction, fid)
                text = text.replace(f"{{{fid}}}", str(val or "???"))
            return text
        vals = [str(_lookup_field(extraction, f) or "???") for f in rule.source_field_ids]
        return " ".join(vals)

    if rule.content_type == ContentType.NARRATIVE:
        fields_preview = {
            fid: str(_lookup_field(extraction, fid) or "")[:80]
            for fid in rule.source_field_ids
        }
        return f"[NARRATIVE from: {fields_preview}]"

    if rule.content_type == ContentType.LIST:
        val = _lookup_field(extraction, rule.list_field_id) if rule.list_field_id else None
        return f"[LIST: {val}]"

    if rule.content_type == ContentType.TABLE:
        return f"[TABLE: {len(rule.table_columns)} columns]"

    return f"[{rule.content_type.value}]"


def _lookup_field(extraction: dict[str, Any], field_id: str) -> Any:
    for page in extraction.get("pages", []):
        source = page.get("fields") or page.get("field_values") or {}
        fv = source.get(field_id)
        if fv is None:
            continue
        if isinstance(fv, dict):
            return fv.get("value") or fv.get("circled_options") or fv
        return fv
    return None


VALIDATION_PROMPT = """Compare simulated rule output against the original clinical report.

SIMULATED (from rules + extraction data):
{simulated_report}

ORIGINAL (ground truth):
{original_report}

Score each section:
- structure_match (0-1): Present and positioned correctly?
- data_accuracy (0-1): Correct values in correct places?
- narrative_quality (0-1): Style and content match for narrative sections?
- overall (0-1): Combined quality

List missing_sections, extra_sections, and critical_issues. Be strict."""


REFINEMENT_PROMPT = """Improve report generation rules for weak sections.

WEAK SECTIONS (avg < 0.7):
{weak_sections}

CURRENT RULES:
{current_rules}

EXAMPLES of correct output:
{examples}

For each, suggest: prompt changes, example updates, template fixes, or field_id corrections. Prioritise high-impact fixes."""


def validate_single(
    rules: ReportRules,
    report: ScannedReport,
    extraction: dict[str, Any],
    client: Optional[instructor.Instructor] = None,
) -> ValidationResult:
    """Validate rules against a single known report+extraction pair."""
    if client is None:
        client = _build_client()

    simulated_lines: list[str] = []
    for sr in rules.sections:
        preview = _simulate_section(sr, extraction)
        simulated_lines.append(f"## {sr.title} ({sr.section_id})\n{preview}\n")
    simulated_text = "\n".join(simulated_lines)

    original_lines: list[str] = []
    for sec in report.sections:
        sec_text = "\n".join(el.text for el in sec.elements if el.text.strip())
        if sec_text.strip():
            original_lines.append(f"## {sec.heading} ({sec.id})\n{sec_text[:400]}\n")
    original_text = "\n".join(original_lines)

    llm_result: LLMValidationResult = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": VALIDATION_PROMPT.format(
                simulated_report=simulated_text,
                original_report=original_text,
            ),
        }],
        response_model=LLMValidationResult,
    )

    return ValidationResult(
        report_id=report.report_id,
        section_scores=llm_result.section_scores,
        overall_score=llm_result.overall_score,
        missing_sections=llm_result.missing_sections,
        extra_sections=llm_result.extra_sections,
        critical_issues=llm_result.critical_issues,
    )


def _validate_one(
    idx: int,
    total: int,
    rules: ReportRules,
    report: ScannedReport,
    extraction: dict[str, Any],
) -> ValidationResult | None:
    """Worker for parallel validation."""
    label = f"{idx+1}/{total} {report.report_id[:30]}"
    console.print(f"  [bold]{label}[/bold] ...")
    client = _build_client()
    try:
        vr = validate_single(rules, report, extraction, client=client)
        console.print(f"  [green]{label} -> {vr.overall_score:.0%}[/green]")
        return vr
    except Exception as e:
        console.print(f"  [red]{label} FAILED: {e}[/red]")
        return None


def suggest_refinements(
    rules: ReportRules,
    validation_results: list[ValidationResult],
    reports: list[ScannedReport],
    client: Optional[instructor.Instructor] = None,
) -> list[RuleRefinement]:
    """Suggest improvements for sections that scored poorly."""
    if client is None:
        client = _build_client()

    score_sums: dict[str, list[float]] = {}
    for vr in validation_results:
        for ss in vr.section_scores:
            score_sums.setdefault(ss.section_id, []).append(ss.overall)

    weak_sections: list[dict] = []
    rule_map = {sr.section_id: sr for sr in rules.sections}
    for sid, scores in score_sums.items():
        avg = sum(scores) / len(scores)
        if avg < 0.7:
            weak_sections.append({"section_id": sid, "avg_score": round(avg, 2)})

    if not weak_sections:
        console.print("[green]No weak sections found (all >= 0.7 avg)[/green]")
        return []

    console.print(f"[yellow]{len(weak_sections)} weak sections, generating refinements...[/yellow]")

    weak_rules_text = ""
    for ws in weak_sections:
        rule = rule_map.get(ws["section_id"])
        if rule:
            weak_rules_text += f"--- {ws['section_id']} (avg={ws['avg_score']}) ---\n"
            weak_rules_text += rule.model_dump_json(indent=2)[:1500] + "\n\n"

    examples_text = ""
    for ws in weak_sections:
        sid = ws["section_id"]
        for report in reports[:5]:
            for sec in report.sections:
                if sec.id == sid:
                    sec_text = "\n".join(el.text for el in sec.elements if el.text.strip())
                    examples_text += f"[{report.report_id}] {sid}: {sec_text[:250]}\n"

    result: LLMRefinementResult = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": REFINEMENT_PROMPT.format(
                weak_sections=json.dumps(weak_sections, indent=2),
                current_rules=weak_rules_text,
                examples=examples_text,
            ),
        }],
        response_model=LLMRefinementResult,
    )

    return result.refinements


def validate_all(
    rules_path: Path,
    reports_dir: Path,
    extractions_dir: Path,
    output_path: Path,
    parallel: int = MAX_PARALLEL,
) -> list[ValidationResult]:
    """Run validation across all known reports in parallel and save results."""
    rules = ReportRules.model_validate_json(
        rules_path.read_text(encoding="utf-8")
    )

    reports: list[ScannedReport] = []
    for f in sorted(reports_dir.glob("*.json")):
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            try:
                reports.append(ScannedReport.model_validate_json(text))
            except Exception:
                pass

    ext_patterns = ["*_condensed.json", "*_extraction.json"]
    extractions: list[dict[str, Any]] = []
    for pat in ext_patterns:
        for f in sorted(extractions_dir.glob(pat)):
            text = f.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                try:
                    extractions.append(json.loads(text))
                except Exception:
                    pass
        if extractions:
            break

    count = min(len(reports), len(extractions))
    console.print(
        f"[bold]Validating rules against {count} reports | parallel={parallel}[/bold]"
    )

    indexed_results: list[tuple[int, ValidationResult | None]] = []

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = {
            pool.submit(
                _validate_one, i, count, rules, reports[i], extractions[i]
            ): i
            for i in range(count)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                vr = future.result()
                indexed_results.append((idx, vr))
            except Exception as e:
                console.print(f"  [red]Report {idx+1} exception: {e}[/red]")
                indexed_results.append((idx, None))

    indexed_results.sort(key=lambda x: x[0])
    results = [vr for _, vr in indexed_results if vr is not None]

    if results:
        _print_summary(results)

    refinements = suggest_refinements(rules, results, reports)

    output_data = {
        "validation_results": [vr.model_dump() for vr in results],
        "refinements": [r.model_dump() for r in refinements],
        "summary": {
            "total_reports": count,
            "validated": len(results),
            "avg_score": round(
                sum(vr.overall_score for vr in results) / max(len(results), 1), 3
            ),
            "weak_section_count": len(refinements),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    console.print(f"\n[green]Saved validation results -> {output_path}[/green]")

    return results


def _print_summary(results: list[ValidationResult]):
    table = Table(title="Validation Summary")
    table.add_column("Report", style="cyan")
    table.add_column("Overall", justify="right")
    table.add_column("Missing", justify="right")
    table.add_column("Issues", justify="right")

    for vr in results:
        score_color = "green" if vr.overall_score >= 0.7 else "yellow" if vr.overall_score >= 0.5 else "red"
        table.add_row(
            vr.report_id,
            f"[{score_color}]{vr.overall_score:.0%}[/{score_color}]",
            str(len(vr.missing_sections)),
            str(len(vr.critical_issues)),
        )

    avg = sum(vr.overall_score for vr in results) / len(results)
    table.add_row("AVERAGE", f"[bold]{avg:.0%}[/bold]", "", "", style="bold")
    console.print(table)
