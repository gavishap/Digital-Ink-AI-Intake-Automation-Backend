"""
LLM analysis of narrative sections only.

Phase 1c: For sections the diff classified as dynamic_narrative, sends
5 examples of each section to Claude to understand the writing pattern
and identify what patient data drives the narrative content.
"""

import json
import os
from pathlib import Path

import anthropic
import instructor
from pydantic import BaseModel, Field
from rich.console import Console

from .models import ReportTemplate, ScannedReport

console = Console()

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Sections to skip from narrative analysis (admin/legal, not true narratives)
SKIP_SECTIONS = {
    "and_request_for_authorization",
    "disclosure_notice",
}

MAX_EXAMPLES = 5


# ---------------------------------------------------------------------------
# LLM response models
# ---------------------------------------------------------------------------

class DataReference(BaseModel):
    """A piece of patient data referenced in the narrative."""
    data_point: str = Field(description="What data is being used (e.g. 'injury mechanism', 'patient occupation', 'date of injury')")
    how_used: str = Field(description="How it appears in the text (e.g. 'stated as direct quote', 'woven into sentence', 'listed as finding')")
    required: bool = Field(description="True if this data point appears in ALL examples")


class NarrativePattern(BaseModel):
    """LLM analysis of one narrative section's writing pattern."""
    section_id: str
    section_heading: str
    purpose: str = Field(description="What this section communicates (1-2 sentences)")
    writing_pattern: str = Field(description="How the doctor structures this section -- paragraph flow, sentence patterns, common phrases")
    data_points_used: list[DataReference] = Field(description="All patient data points referenced in this section")
    static_phrases: list[str] = Field(
        default_factory=list,
        description="Common phrases/sentence starters that appear in most examples verbatim",
    )
    variation_notes: str = Field(
        default="",
        description="What varies most between patients and why",
    )
    example_count: int = 0


class NarrativeAnalysisResult(BaseModel):
    """Full LLM response for analyzing narrative sections."""
    patterns: list[NarrativePattern]


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT = """You are analyzing a specific section from clinical dental/orofacial pain reports.
I'm showing you {n_examples} examples of the "{section_heading}" section from {n_examples} different patient reports.

Your job is to understand:
1. What is the PURPOSE of this section?
2. What WRITING PATTERN does the doctor follow? (paragraph structure, sentence flow, common phrases)
3. What PATIENT DATA POINTS drive the content? (what info from the patient's intake/exam gets used here)
4. What STATIC PHRASES appear across most/all examples verbatim?
5. What VARIES most between patients and why?

EXAMPLES:
{examples_text}

Analyze this section thoroughly. Identify every distinct data point the doctor references."""


def _build_client() -> instructor.Instructor:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


def _gather_section_examples(
    section_id: str,
    reports: list[ScannedReport],
    max_examples: int = MAX_EXAMPLES,
) -> list[tuple[str, str]]:
    """Collect (report_id, section_text) pairs for a given section."""
    examples: list[tuple[str, str]] = []
    for report in reports:
        for section in report.sections:
            if section.id == section_id:
                texts = [el.text for el in section.elements if el.text.strip()]
                if texts:
                    full_text = "\n".join(texts)
                    examples.append((report.report_id, full_text))
                    if len(examples) >= max_examples:
                        return examples
    return examples


def analyze_narrative_sections(
    template: ReportTemplate,
    reports: list[ScannedReport],
) -> list[NarrativePattern]:
    """Run LLM analysis on all narrative sections.

    Returns a NarrativePattern for each section analyzed.
    """
    client = _build_client()

    narrative_sections = [
        s for s in template.sections
        if s.classification == "dynamic_narrative"
        and s.id not in SKIP_SECTIONS
        and s.appears_in >= 10
    ]

    console.print(
        f"[bold]Analyzing {len(narrative_sections)} narrative sections via LLM...[/bold]"
    )

    results: list[NarrativePattern] = []

    for i, sec in enumerate(narrative_sections):
        console.print(
            f"  [{i + 1}/{len(narrative_sections)}] {sec.heading[:60]}..."
        )

        examples = _gather_section_examples(sec.id, reports)
        if not examples:
            console.print(f"    [yellow]No examples found, skipping[/yellow]")
            continue

        examples_text = ""
        for j, (rid, text) in enumerate(examples):
            examples_text += f"\n--- Example {j + 1} (Patient: {rid}) ---\n{text}\n"

        prompt = ANALYSIS_PROMPT.format(
            n_examples=len(examples),
            section_heading=sec.heading,
            examples_text=examples_text,
        )

        try:
            pattern: NarrativePattern = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                response_model=NarrativePattern,
            )
            pattern.section_id = sec.id
            pattern.section_heading = sec.heading
            pattern.example_count = len(examples)
            results.append(pattern)

            n_data = len(pattern.data_points_used)
            n_static = len(pattern.static_phrases)
            console.print(
                f"    [green]{n_data} data points, {n_static} static phrases[/green]"
            )
        except Exception as e:
            console.print(f"    [red]Failed: {e}[/red]")

    return results


def save_narrative_analysis(
    patterns: list[NarrativePattern],
    output_path: Path,
):
    result = NarrativeAnalysisResult(patterns=patterns)
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[green]Saved -> {output_path}[/green]")
