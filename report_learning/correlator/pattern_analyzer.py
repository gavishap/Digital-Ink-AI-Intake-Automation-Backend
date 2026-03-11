"""
Cross-report pattern analysis (LLM Call 3).

Sends all 20 pair correlations to the LLM to identify consistent patterns,
conditional sections, universal formatting rules, and canonical ordering.
"""

import json
import os
from pathlib import Path
from typing import Optional

import anthropic
import instructor
from rich.console import Console

from .models import CrossReportPatterns, PairCorrelation

console = Console()

CLAUDE_MODEL = "claude-sonnet-4-20250514"


def _build_client() -> instructor.Instructor:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


def _summarise_correlations(correlations: list[PairCorrelation]) -> str:
    """Compact summary of all correlations for the LLM prompt.

    Focuses on section-level patterns rather than per-element detail
    to keep the prompt under token limits.
    """
    parts: list[str] = []
    for corr in correlations:
        section_map: dict[str, list[dict]] = {}
        for m in corr.mappings:
            sec = m.report_section_id
            section_map.setdefault(sec, []).append({
                "fields": m.source_field_ids,
                "transform": m.transformation.value,
                "source": m.data_source.value,
                "rule": (m.transformation_notes or "")[:100],
            })

        lines = [f"--- {corr.report_id} ({corr.mapping_coverage:.0%} coverage, {len(corr.mappings)} mappings) ---"]
        for sec_id, mappings in section_map.items():
            all_fields = []
            transforms = set()
            sources = set()
            rules = []
            for mp in mappings:
                all_fields.extend(mp["fields"])
                transforms.add(mp["transform"])
                sources.add(mp["source"])
                if mp["rule"]:
                    rules.append(mp["rule"])
            lines.append(
                f"  {sec_id}: fields=[{','.join(all_fields[:8])}{'...' if len(all_fields)>8 else ''}] "
                f"types={','.join(transforms)} src={','.join(sources)}"
            )
            if rules:
                lines.append(f"    rules: {rules[0]}")
        lines.append(f"  unmapped_report: {len(corr.unmapped_report_elements)} elements")
        lines.append(f"  unmapped_extract: {len(corr.unmapped_extraction_fields)} fields")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


PATTERN_PROMPT = """You are analysing the correlation results from {count} clinical report+extraction pairs.

Each pair maps extraction field_ids to report elements showing how patient form data becomes a final clinical report.

IMPORTANT CONTEXT:
The extraction data was produced by an automated vision LLM and contains known inaccuracies in specific values (misread circles, wrong VAS numbers, false positive selections). However, the STRUCTURAL MAPPINGS — which fields connect to which report sections — are reliable. Your job is to find the RULES and PATTERNS for report generation, not to validate individual values.

Your task: Identify PATTERNS across all {count} pairs.

For each SECTION found across the reports, determine:
1. How many reports contain it (appears_in_count)
2. Whether it is required (present in ALL reports) or conditional
3. Its typical position in the document
4. The dominant transformation type used
5. Which extraction fields are ALWAYS used (consistent_fields) vs sometimes used (optional_fields)
6. If conditional, what TRIGGERS its inclusion — be specific about the rule:
   - e.g. "Section appears when q10_breathing_problems = YES"
   - e.g. "Section appears when any p6_orthopedic injury VAS > 0"
   - e.g. "Paragraph included when p4_have_you_ever_smoked = YES, text uses p4_when_stop_smoking_years"
7. For narrative sections, describe the consistent prose style and the FORMULA for assembling it

Also identify:
- The canonical section ordering (the order sections typically appear)
- Static text blocks that are identical across reports
- Overall field usage (which field_ids are used most/least)
- CONDITIONAL LOGIC RULES: For each conditional section or element, define the exact trigger condition(s) from the extraction data. These rules will drive automated report generation.
- Any interesting observations about how the report adapts to different patient data

CORRELATION DATA:
{correlations}

Analyse thoroughly. This is the foundation for automated report generation. The rules you identify here will be used to programmatically generate reports from new patient form data."""


def analyse_patterns(
    correlations: list[PairCorrelation],
    client: Optional[instructor.Instructor] = None,
) -> CrossReportPatterns:
    """Run cross-report pattern analysis on all correlations."""
    if client is None:
        client = _build_client()

    summary = _summarise_correlations(correlations)
    console.print(f"[dim]Analysing patterns across {len(correlations)} correlations...[/dim]")

    result: CrossReportPatterns = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": PATTERN_PROMPT.format(
                count=len(correlations),
                correlations=summary,
            ),
        }],
        response_model=CrossReportPatterns,
    )

    console.print(
        f"[green]Patterns found: {len(result.section_patterns)} sections, "
        f"{len(result.universal_sections)} universal, "
        f"{len(result.conditional_sections)} conditional[/green]"
    )
    return result


def analyse_from_files(
    correlations_dir: Path,
    output_path: Path,
) -> CrossReportPatterns:
    """Load correlation JSONs from disk, run analysis, save result."""
    files = sorted(correlations_dir.glob("correlation_*.json"))
    if not files:
        console.print(f"[red]No correlation files in {correlations_dir}[/red]")
        raise FileNotFoundError(f"No correlation_*.json in {correlations_dir}")

    correlations: list[PairCorrelation] = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        try:
            correlations.append(PairCorrelation.model_validate_json(text))
        except Exception as e:
            console.print(f"[yellow]Skipping {f.name}: {e}[/yellow]")
    console.print(f"[bold]Loaded {len(correlations)} correlations[/bold]")

    patterns = analyse_patterns(correlations)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(patterns.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[green]Saved patterns -> {output_path}[/green]")

    return patterns
