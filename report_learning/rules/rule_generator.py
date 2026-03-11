"""
Rule generation engine (LLM Call 4).

Takes cross-report patterns + all per-pair correlations + scanned report
sections + extraction data and synthesises a complete SectionRule for
every report section.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

import anthropic
import instructor
from rich.console import Console

from ..correlator.models import CrossReportPatterns, PairCorrelation
from ..scanner.models import ScannedReport
from .models import (
    FormattingRule,
    LLMReportRulesResult,
    ReportRules,
    SectionRule,
)

console = Console()

CLAUDE_MODEL = "claude-sonnet-4-20250514"


def _build_client() -> instructor.Instructor:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


def _collect_section_examples(
    section_id: str,
    reports: list[ScannedReport],
    correlations: list[PairCorrelation],
    extractions: list[dict[str, Any]],
) -> str:
    """Gather diverse examples of a section across reports for the prompt."""
    examples: list[str] = []

    corr_map = {c.report_id: c for c in correlations}
    ext_map = {e.get("form_id", ""): e for e in extractions}

    for report in reports:
        matching_section = None
        for sec in report.sections:
            if sec.id == section_id:
                matching_section = sec
                break
        if not matching_section:
            continue

        section_text = "\n".join(
            el.text for el in matching_section.elements if el.text.strip()
        )
        if not section_text.strip():
            continue

        corr = corr_map.get(report.report_id)
        relevant_fields: dict[str, str] = {}
        if corr:
            for m in corr.mappings:
                if m.report_section_id == section_id:
                    ext = ext_map.get(corr.extraction_id, {})
                    for fid in m.source_field_ids:
                        val = _lookup_field(ext, fid)
                        if val is not None:
                            relevant_fields[fid] = str(val)[:150]

        ex_block = f"--- Example (report={report.report_id}) ---\n"
        if relevant_fields:
            ex_block += "Input fields:\n"
            for fid, val in list(relevant_fields.items())[:15]:
                ex_block += f"  {fid} = {val}\n"
        ex_block += f"Output text:\n  {section_text[:400]}\n"
        examples.append(ex_block)

    return "\n".join(examples[:5])


def _lookup_field(extraction: dict[str, Any], field_id: str) -> Any:
    """Find a field value in an extraction result across all pages.

    Supports both raw format (field_values) and condensed format (fields).
    """
    for page in extraction.get("pages", []):
        source = page.get("fields") or page.get("field_values") or {}
        fv = source.get(field_id)
        if fv is None:
            continue
        if isinstance(fv, dict):
            return fv.get("value") or fv.get("circled_options") or fv
        return fv
    return None


RULE_GENERATION_PROMPT = """Generate rules for automated clinical report generation.

CROSS-REPORT PATTERNS (what's consistent across {n_reports} reports):
{patterns_summary}

SECTION EXAMPLES (real input/output for each section):
{section_examples}

For EVERY section, produce a rule:
- content_type: static_text | direct_fill | formatted_fill | narrative | list | table | conditional_block
- static_text: exact boilerplate
- direct_fill/formatted_fill: source_field_ids + template with {{field_id}} placeholders
- narrative: detailed generation_prompt (clinical tone, structure, missing-data handling) + 2-3 few_shot_examples
- list: list_field_id
- table: columns + row source
- conditional_block: conditions (field_id, operator, value)

Keep generation_prompt concise but specific about clinical style and sentence patterns.
Include field_id_glossary mapping every used field_id to a human description."""


def _summarise_patterns_for_prompt(patterns: CrossReportPatterns) -> str:
    """Compact summary of patterns to save tokens."""
    lines: list[str] = []
    lines.append(f"report_ordering: {patterns.report_ordering}")
    lines.append(f"universal: {patterns.universal_sections}")
    lines.append(f"conditional: {patterns.conditional_sections}")
    for sp in patterns.section_patterns:
        parts = [
            f"  {sp.section_id} ({sp.title}): pos={sp.typical_position}",
            f"required={sp.is_required}",
            f"transform={sp.dominant_transformation.value}",
            f"src={sp.primary_data_source.value}",
            f"fields={sp.consistent_fields}",
        ]
        if sp.optional_fields:
            parts.append(f"optional={sp.optional_fields}")
        if sp.conditional_trigger:
            parts.append(f"trigger={sp.conditional_trigger}")
        if sp.generation_rule:
            parts.append(f"rule={sp.generation_rule[:120]}")
        if sp.narrative_style_notes:
            parts.append(f"style={sp.narrative_style_notes[:120]}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def generate_rules(
    patterns: CrossReportPatterns,
    reports: list[ScannedReport],
    correlations: list[PairCorrelation],
    extractions: list[dict[str, Any]],
    client: Optional[instructor.Instructor] = None,
) -> ReportRules:
    """Generate complete report rules from patterns and examples."""
    if client is None:
        client = _build_client()

    all_examples: list[str] = []
    for sp in patterns.section_patterns:
        examples = _collect_section_examples(
            sp.section_id, reports, correlations, extractions
        )
        if examples:
            all_examples.append(f"\n=== {sp.section_id} ({sp.title}) ===\n{examples}")

    patterns_text = _summarise_patterns_for_prompt(patterns)

    console.print(f"[dim]Generating rules for {len(patterns.section_patterns)} sections...[/dim]")

    llm_result: LLMReportRulesResult = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": RULE_GENERATION_PROMPT.format(
                n_reports=patterns.total_reports_analysed,
                patterns_summary=patterns_text,
                section_examples="\n".join(all_examples),
            ),
        }],
        response_model=LLMReportRulesResult,
    )

    sections = [
        SectionRule(**sr.model_dump()) for sr in llm_result.sections
    ]

    rules = ReportRules(
        report_name=llm_result.report_name,
        sections=sections,
        field_id_glossary=llm_result.field_id_glossary,
        generation_notes=llm_result.generation_notes,
        total_estimated_pages=patterns.total_reports_analysed,
    )

    console.print(
        f"[green]Generated {len(rules.sections)} section rules, "
        f"{len(rules.field_id_glossary)} glossary entries[/green]"
    )
    return rules


def generate_from_files(
    patterns_path: Path,
    reports_dir: Path,
    correlations_dir: Path,
    extractions_dir: Path,
    output_path: Path,
) -> ReportRules:
    """Load all inputs from disk, generate rules, save result."""
    patterns = CrossReportPatterns.model_validate_json(
        patterns_path.read_text(encoding="utf-8")
    )

    reports: list[ScannedReport] = []
    for f in sorted(reports_dir.glob("*.json")):
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            try:
                reports.append(ScannedReport.model_validate_json(text))
            except Exception:
                pass

    correlations: list[PairCorrelation] = []
    for f in sorted(correlations_dir.glob("correlation_*.json")):
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            try:
                correlations.append(PairCorrelation.model_validate_json(text))
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

    console.print(
        f"[bold]Loaded {len(reports)} reports, {len(correlations)} correlations, "
        f"{len(extractions)} extractions[/bold]"
    )

    rules = generate_rules(patterns, reports, correlations, extractions)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rules.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[green]Saved rules -> {output_path}[/green]")

    return rules
