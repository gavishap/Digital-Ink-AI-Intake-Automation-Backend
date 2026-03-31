"""
Section-by-Section Relearning Engine

Iterates through all 39 report sections across 32 scanned training reports,
uses LLM calls to analyze what data each section needs, and outputs improved
report_rules_v2.json with better source_field_ids, generation_prompts,
few-shot examples, hybrid templates, min_required_fields, and temperature.

Run from: c:/Digital_Ink/form-extractor
Usage:    python _relearn_sections.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from rich.console import Console
from rich.table import Table

console = Console(record=True)

BASE = Path(__file__).parent
SCAN_DIR = BASE / "report_learning" / "outputs" / "scanned"
RULES_PATH = BASE / "report_learning" / "outputs" / "rules" / "report_rules.json"
TEMPLATE_DEF_PATH = BASE / "report_learning" / "outputs" / "rules" / "template_definition.json"
NARRATIVE_PAT_PATH = BASE / "report_learning" / "outputs" / "rules" / "narrative_patterns.json"
SCHEMA_PATH = BASE / "templates" / "orofacial_exam_schema.json"
E2E_DIR = BASE / "report_learning" / "outputs" / "e2e_v2"
OUT_DIR = BASE / "report_learning" / "outputs" / "relearn"

TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
TOGETHER_BASE_URL = "https://api.together.xyz/v1"

KNOWN_SUBSECTION_IDS = {
    "dental": "subjective_complaints",
    "headaches": "subjective_complaints",
    "facial_pain": "subjective_complaints",
    "temporomandibular_joint": "subjective_complaints",
    "sleep_disturbances": "subjective_complaints",
}

DATA_HEAVY_SECTIONS = {
    "clinical_examination_of_the_muscular_system",
    "clinical_examination_of_the_temporomandibular_joint",
    "diagnostic_bite_force_testing",
    "diagnostic_salivary_flow_and_buffering_tests",
    "diagnostic_autonomic_nervous_system_testing",
    "surface_electromyography",
    "ultrasonic_doppler_auscultation_analysis",
    "objective_clinical_findings_confirming_bruxism_clenching",
    "diagnostic_photographs",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def _extract_json_from_text(text: str) -> dict | None:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def _build_llm_client() -> tuple[OpenAI, str] | None:
    key = os.getenv("TOGETHER_API_KEY")
    if key:
        return OpenAI(api_key=key, base_url=TOGETHER_BASE_URL, timeout=120.0), TOGETHER_MODEL
    return None


def _extract_section_text(section: dict) -> str:
    parts = []
    for el in section.get("elements", []):
        txt = el.get("text", "").strip()
        if txt:
            parts.append(txt)
    return "\n".join(parts)


_SECTION_ALIASES: dict[str, str] = {
    "surface_electromyography": "surface_electromyography_semg",
    "surface_electromyography_semg": "surface_electromyography",
    "objective_clinical_findings_confirming_bruxism_clenching": "objective_clinical_findings_confirming_bruxismclenching",
    "objective_clinical_findings_confirming_bruxismclenching": "objective_clinical_findings_confirming_bruxism_clenching",
    "treatment_received_for_the_industrial_injury": "treatment_received_for_industrial_injury",
    "treatment_received_for_industrial_injury": "treatment_received_for_the_industrial_injury",
    "diagnostic_direct_fluorescence_visulization_dfv": "diagnostic_direct_fluorescence_visualization_dfv",
    "diagnostic_direct_fluorescence_visualization_dfv": "diagnostic_direct_fluorescence_visulization_dfv",
    "epworth_scale": "epworth_sleepiness_scale",
    "epworth_sleepiness_scale": "epworth_scale",
}


def _normalize_sid(sid: str) -> str:
    return re.sub(r"[^a-z0-9]", "", sid.lower())


def _section_id_matches(scan_id: str, target_id: str) -> bool:
    if scan_id == target_id:
        return True
    if _SECTION_ALIASES.get(target_id) == scan_id:
        return True
    if _normalize_sid(scan_id) == _normalize_sid(target_id):
        return True
    return False


def _collect_section_texts(scan_files: list[Path], section_id: str) -> list[dict]:
    """Collect full text of a section from all scan files where it appears."""
    results = []
    for scan_path in scan_files:
        data = _load_json(scan_path)
        patient = scan_path.stem.replace("_scan", "")
        for sec in data.get("sections", []):
            if _section_id_matches(sec.get("id", ""), section_id):
                text = _extract_section_text(sec)
                if text.strip():
                    results.append({"patient": patient, "text": text, "element_count": len(sec.get("elements", []))})
    return results


def _build_schema_field_summary(schema_data: dict) -> str:
    """Build a compact field inventory from the schema."""
    lines = []
    for page in schema_data.get("pages", []):
        page_num = page.get("page_number", "?")
        fields = []
        for section in page.get("sections", []):
            for field in section.get("fields", []):
                fid = field.get("field_id", "")
                label = field.get("field_label", "")
                ftype = field.get("field_type", "")
                fields.append(f"{fid} ({label}, {ftype})")
        for field in page.get("standalone_fields", []):
            fid = field.get("field_id", "")
            label = field.get("field_label", "")
            ftype = field.get("field_type", "")
            fields.append(f"{fid} ({label}, {ftype})")
        if fields:
            lines.append(f"Page {page_num}: {', '.join(fields[:30])}")
    return "\n".join(lines)


def _collect_comparison_data(section_id: str) -> list[dict]:
    """Collect comparison results for this section across 3 patients."""
    results = []
    for slug in ["bachar", "lupercio", "rivera"]:
        cmp_dir = E2E_DIR / "stage6_comparison" / slug
        summary_path = cmp_dir / "comparison_summary.json"
        if not summary_path.exists():
            continue
        data = _load_json(summary_path)
        for sec in data:
            if sec.get("section_id") == section_id:
                results.append({
                    "patient": slug,
                    "score": sec.get("overall_score", 0),
                    "hallucinations": sec.get("hallucinations", []),
                    "missing_data": sec.get("missing_data", []),
                    "root_cause": sec.get("root_cause_analysis", {}).get("primary_cause", "?"),
                    "explanation": sec.get("root_cause_analysis", {}).get("explanation", ""),
                })
    return results


def _collect_generation_log_data(section_id: str) -> list[dict]:
    """Collect generation log data for this section across 3 patients."""
    results = []
    for slug in ["bachar", "lupercio", "rivera"]:
        log_path = E2E_DIR / "stage4_report" / slug / "generation_log.json"
        if not log_path.exists():
            continue
        data = _load_json(log_path)
        entry = data.get(section_id, {})
        if entry:
            entry["patient"] = slug
            results.append(entry)
    return results


def _collect_field_resolution(section_id: str, source_field_ids: list[str]) -> dict:
    """Check which source fields resolved across all 3 patients."""
    field_status: dict[str, dict] = {}
    for fid in source_field_ids:
        field_status[fid] = {"resolved_in": [], "values": []}

    for slug in ["bachar", "lupercio", "rivera"]:
        fr_path = E2E_DIR / "stage4_report" / slug / "field_resolution.json"
        if not fr_path.exists():
            continue
        fr = _load_json(fr_path)
        for fid in source_field_ids:
            val = fr.get(fid)
            if val is not None:
                field_status[fid]["resolved_in"].append(slug)
                field_status[fid]["values"].append(str(val)[:100])

    return field_status


def _validate_conditions(conditions: list[dict]) -> list[dict]:
    """Check if condition field_ids actually resolve in extraction."""
    issues = []
    for cond in conditions:
        fid = cond.get("field_id", "")
        resolved_anywhere = False
        for slug in ["bachar", "lupercio", "rivera"]:
            fr_path = E2E_DIR / "stage4_report" / slug / "field_resolution.json"
            if not fr_path.exists():
                continue
            fr = _load_json(fr_path)
            if fr.get(fid) is not None:
                resolved_anywhere = True
                break
        if not resolved_anywhere:
            issues.append({"field_id": fid, "issue": "never resolves in any patient extraction"})
    return issues


ANALYSIS_PROMPT = """You are analyzing a specific section of a clinical orofacial pain evaluation report to improve its generation rules.

SECTION: "{section_id}" ({content_type})
Title: "{title}"

FULL TEXT FROM {num_reports} TRAINING REPORTS (this is what the section should look like):
{section_texts}

NARRATIVE PATTERN (learned writing style):
{narrative_pattern}

CURRENT RULE:
- source_field_ids: {current_source_fields}
- generation_prompt length: {prompt_len} chars
- few_shot_examples: {few_shot_count}
- conditions: {conditions}
- min_required_fields: {min_required}

SCHEMA FIELD INVENTORY (all available extraction fields):
{schema_summary}

E2E COMPARISON RESULTS (how well the current rule performed):
{comparison_data}

GENERATION LOG (what happened during generation):
{generation_log_data}

FIELD RESOLUTION STATUS (which source fields actually resolved):
{field_resolution}

CONDITION VALIDATION ISSUES:
{condition_issues}

IS DATA-HEAVY SECTION: {is_data_heavy}
SECTION FREQUENCY: Appears in {appears_in} of {total_reports} reports ({frequency_pct}%). {frequency_note}

Analyze this section thoroughly and respond with ONLY valid JSON:
{{
    "required_field_ids": ["list of field_ids that MUST be in source_field_ids"],
    "optional_field_ids": ["field_ids useful but not required"],
    "min_required_fields": <integer: minimum fields needed to generate this section>,
    "recommended_temperature": <float: 0.0 for data-heavy, 0.1 for formulaic, 0.2-0.3 for prose>,
    "use_hybrid_template": <boolean: true if section has rigid data-driven structure>,
    "static_phrases": ["exact phrases that appear verbatim across all reports"],
    "data_usage_rules": [
        {{"field_id": "xxx", "usage": "how this field value should be used in the text", "required": true}}
    ],
    "section_variants": [
        {{"condition": "when X", "structure": "how the section changes"}}
    ],
    "verification_shrinkage_issue": "<if verifier cut >40% of text, explain why and what to fix>",
    "condition_fixes": ["list of fixes needed for broken condition field_ids"],
    "issues_found": ["list of problems with current rule"],
    "recommended_max_tokens": <integer based on actual section length in training reports>,
    "section_frequency": "<universal if appears in >80% of reports, conditional if <80%>",
    "trigger_field": "<for conditional sections: the single most important field_id that determines if this section should exist. null for universal sections>"
}}"""


RULE_GENERATION_PROMPT = """Based on the analysis below, generate an improved rule for this report section.

SECTION: "{section_id}" ({content_type})
Title: "{title}"

ANALYSIS RESULTS:
{analysis_json}

FULL TEXT FROM TRAINING REPORTS (use these to write few-shot examples):
{section_texts_for_examples}

CURRENT RULE (preserve section_id, title, ordering, content_type, page_break_before, is_required):
{current_rule}

{hybrid_instruction}

Generate the improved rule as ONLY valid JSON. The output must include ALL fields from the current rule (preserving structural fields) with improved values for:
- source_field_ids (expanded based on analysis)
- min_required_fields (from analysis)
- temperature (from analysis)
- generation_prompt (rewritten with specific data usage rules, static phrases, paragraph structure, what NOT to invent)
- few_shot_examples (2-3 diverse examples from the training report texts, using {{patient_name}}, {{patient_title}}, {{patient_last_name}}, {{he_she}}, {{his_her}} placeholders)
- max_tokens (from analysis)
- conditions (with fixed field_ids if needed)
{hybrid_template_field}

IMPORTANT: The "conditions" field must be an array of objects with EXACTLY this format:
{{"field_id": "<actual_schema_field_id>", "operator": "<op>", "value": "<expected_value_or_null>", "combine": "<and_or_or>"}}
Valid operators: "exists", "not_empty", "equals", "not_equals", "contains", "greater_than"
Valid combine: "and" (ALL must pass) or "or" (ANY must pass)
Do NOT invent condition formats. Do NOT add conditions to sections that had none in the current rule unless the analysis specifically recommends it. If the current rule has no conditions, output "conditions": [].
All source_field_ids MUST be actual extraction field IDs from the schema (format: p<number>_<name>, e.g. p5_current_work_status). Do NOT invent descriptive field names.

CRITICAL: Output ONLY the JSON object for this section rule. No explanations."""


def _run_llm_call(client: OpenAI, model: str, prompt: str, max_tokens: int = 4000) -> dict | None:
    """Run an LLM call and parse JSON response with retries."""
    for attempt in range(3):
        try:
            messages = [{"role": "user", "content": prompt}]
            if attempt > 0:
                messages.append({"role": "user", "content": "Respond with ONLY valid JSON."})
            resp = client.chat.completions.create(
                model=model, max_tokens=max_tokens, temperature=0.1,
                messages=messages,
            )
            raw = resp.choices[0].message.content.strip()
            parsed = _extract_json_from_text(raw)
            if parsed:
                return parsed
        except Exception as e:
            console.print(f"  [dim]LLM call attempt {attempt+1} failed: {e}[/dim]")
    return None


def process_section(
    section_rule: dict,
    scan_files: list[Path],
    narrative_patterns: dict[str, dict],
    schema_summary: str,
    client: OpenAI,
    model: str,
    template_def_sections: dict[str, dict] | None = None,
    total_reports: int = 32,
) -> tuple[dict, dict]:
    """Process one section: LLM Call 1 (analysis) + Call 2 (improved rule)."""
    section_id = section_rule.get("section_id", "")
    content_type = section_rule.get("content_type", "")
    title = section_rule.get("title", "")

    console.print(f"\n  [bold cyan]Processing: {section_id}[/bold cyan] ({content_type})")

    if content_type == "static_text":
        console.print(f"  [dim]Static section — skipping LLM analysis[/dim]")
        return section_rule, {"section_id": section_id, "skipped": True, "reason": "static_text"}

    section_texts = _collect_section_texts(scan_files, section_id)
    console.print(f"  Found in {len(section_texts)}/{len(scan_files)} reports")

    if not section_texts and section_id in KNOWN_SUBSECTION_IDS:
        parent_id = KNOWN_SUBSECTION_IDS[section_id]
        parent_texts = _collect_section_texts(scan_files, parent_id)
        heading_label = title.upper()
        for pt in parent_texts:
            if heading_label in pt["text"].upper():
                section_texts.append({
                    "patient": pt["patient"],
                    "text": f"[Extracted from parent section '{parent_id}']\n{pt['text']}",
                    "element_count": pt["element_count"],
                })
        console.print(f"  [dim]Subsection of {parent_id} — extracted {len(section_texts)} instances from parent text[/dim]")

    narr_pat = narrative_patterns.get(section_id, {})
    comparison_data = _collect_comparison_data(section_id)
    gen_log_data = _collect_generation_log_data(section_id)
    field_resolution = _collect_field_resolution(section_id, section_rule.get("source_field_ids", []))
    condition_issues = _validate_conditions(section_rule.get("conditions", []))
    is_data_heavy = section_id in DATA_HEAVY_SECTIONS

    td_sec = (template_def_sections or {}).get(section_id, {})
    appears_in = td_sec.get("appears_in", total_reports)
    frequency_pct = min(100, round(appears_in / max(total_reports, 1) * 100))
    is_universal = frequency_pct >= 80
    frequency_note = (
        "UNIVERSAL: This section appears in almost every report. Set min_required_fields=1 — just need ANY data."
        if is_universal else
        f"CONDITIONAL: This section only appears in {frequency_pct}% of reports. Identify the ONE trigger field that determines if this section should exist."
    )

    texts_for_prompt = "\n\n---\n\n".join(
        f"Report {i+1} ({t['patient']}):\n{t['text'][:4000]}"
        for i, t in enumerate(section_texts[:20])
    ) or "[No training examples found for this section]"

    avg_score = sum(c.get("score", 0) for c in comparison_data) / max(len(comparison_data), 1)
    console.print(f"  Avg comparison score: {avg_score:.0f}/100  |  Data-heavy: {is_data_heavy}")

    # --- LLM Call 1: Analysis ---
    analysis_prompt = ANALYSIS_PROMPT.format(
        section_id=section_id,
        content_type=content_type,
        title=title,
        num_reports=len(section_texts),
        section_texts=texts_for_prompt[:40000],
        narrative_pattern=json.dumps(narr_pat, indent=2)[:3000] if narr_pat else "[No narrative pattern available]",
        current_source_fields=json.dumps(section_rule.get("source_field_ids", [])),
        prompt_len=len(section_rule.get("generation_prompt", "") or ""),
        few_shot_count=len(section_rule.get("few_shot_examples", [])),
        conditions=json.dumps(section_rule.get("conditions", [])),
        min_required=section_rule.get("min_required_fields", 1),
        schema_summary=schema_summary[:6000],
        comparison_data=json.dumps(comparison_data, indent=2)[:3000],
        generation_log_data=json.dumps(gen_log_data, indent=2)[:2000],
        field_resolution=json.dumps(field_resolution, indent=2)[:2000],
        condition_issues=json.dumps(condition_issues) if condition_issues else "None",
        is_data_heavy=is_data_heavy,
        appears_in=appears_in,
        total_reports=total_reports,
        frequency_pct=frequency_pct,
        frequency_note=frequency_note,
    )

    console.print(f"  Running LLM Call 1 (analysis)...")
    analysis = _run_llm_call(client, model, analysis_prompt, max_tokens=3000)

    if not analysis:
        console.print(f"  [red]Analysis failed — keeping original rule[/red]")
        return section_rule, {"section_id": section_id, "error": "analysis_failed"}

    console.print(f"  Analysis: {len(analysis.get('required_field_ids', []))} required fields, "
                  f"min={analysis.get('min_required_fields', '?')}, "
                  f"hybrid={analysis.get('use_hybrid_template', False)}, "
                  f"temp={analysis.get('recommended_temperature', '?')}")

    # --- LLM Call 2: Rule Generation ---
    use_hybrid = analysis.get("use_hybrid_template", False) and content_type == "narrative"

    hybrid_instruction = ""
    hybrid_template_field = ""
    if use_hybrid:
        hybrid_instruction = (
            "This section should use a HYBRID TEMPLATE approach. Generate a 'hybrid_template' field "
            "that contains the section text with {field_id} placeholders for deterministic data insertion "
            "and [BRIDGE: instruction] markers where the LLM should generate short connecting prose. "
            "The LLM will ONLY generate text at [BRIDGE] points — all data values are pre-inserted by code."
        )
        hybrid_template_field = '- hybrid_template (new field with {field} placeholders + [BRIDGE: ...] markers)'

    texts_for_examples = "\n\n---\n\n".join(
        f"Report {i+1} ({t['patient']}):\n{t['text'][:4000]}"
        for i, t in enumerate(section_texts[:8])
    ) or "[No examples]"

    rule_prompt = RULE_GENERATION_PROMPT.format(
        section_id=section_id,
        content_type=content_type,
        title=title,
        analysis_json=json.dumps(analysis, indent=2)[:4000],
        section_texts_for_examples=texts_for_examples[:20000],
        current_rule=json.dumps(section_rule, indent=2)[:5000],
        hybrid_instruction=hybrid_instruction,
        hybrid_template_field=hybrid_template_field,
    )

    console.print(f"  Running LLM Call 2 (rule generation)...")
    new_rule = _run_llm_call(client, model, rule_prompt, max_tokens=6000)

    if not new_rule:
        console.print(f"  [red]Rule generation failed — keeping original with analysis updates[/red]")
        updated = dict(section_rule)
        updated["source_field_ids"] = analysis.get("required_field_ids", []) + analysis.get("optional_field_ids", [])
        updated["min_required_fields"] = analysis.get("min_required_fields", 1)
        updated["temperature"] = analysis.get("recommended_temperature", 0.3)
        return updated, {"section_id": section_id, "analysis": analysis, "rule_gen": "failed_used_analysis"}

    for key in ("section_id", "title", "ordering", "content_type", "page_break_before", "is_required"):
        new_rule[key] = section_rule.get(key, new_rule.get(key))

    if "min_required_fields" not in new_rule:
        new_rule["min_required_fields"] = analysis.get("min_required_fields", 1)
    if "temperature" not in new_rule:
        new_rule["temperature"] = analysis.get("recommended_temperature", 0.3)

    # --- Validate conditions: strip malformed + prevent new conditions on universal sections ---
    original_conditions = section_rule.get("conditions", [])
    valid_ops = {"exists", "not_empty", "equals", "not_equals", "contains", "greater_than"}
    valid_conditions = []
    for c in new_rule.get("conditions", []):
        if isinstance(c, dict) and "field_id" in c and c.get("operator") in valid_ops:
            c.setdefault("value", None)
            c.setdefault("combine", "and")
            valid_conditions.append(c)
    stripped_count = len(new_rule.get("conditions", [])) - len(valid_conditions)
    if stripped_count > 0:
        console.print(f"  [yellow]Stripped {stripped_count} malformed conditions[/yellow]")

    if is_universal and not original_conditions and valid_conditions:
        console.print(f"  [yellow]Universal section had no conditions in V1 — stripping {len(valid_conditions)} LLM-invented conditions[/yellow]")
        valid_conditions = []
    new_rule["conditions"] = valid_conditions

    # --- Set min_required_fields based on section frequency ---
    if is_universal:
        new_rule["min_required_fields"] = 1
        if analysis.get("min_required_fields", 1) > 1:
            console.print(f"  [yellow]Universal section: forcing min_required_fields=1 (was {analysis.get('min_required_fields')})[/yellow]")
    else:
        fr_data = _collect_field_resolution(section_id, new_rule.get("source_field_ids", []))
        resolved_counts = []
        for slug in ["bachar", "lupercio", "rivera"]:
            count = sum(1 for fid, info in fr_data.items() if slug in info.get("resolved_in", []))
            resolved_counts.append(count)
        min_resolved = min(resolved_counts) if resolved_counts else 0
        current_min = new_rule.get("min_required_fields", 1)
        if current_min > min_resolved and min_resolved > 0:
            console.print(f"  [yellow]Conditional section: capping min_required_fields {current_min} -> {max(1, min_resolved)}[/yellow]")
            new_rule["min_required_fields"] = max(1, min_resolved)
        elif min_resolved == 0:
            new_rule["min_required_fields"] = 1

    # --- Validate critical fields present ---
    if content_type == "narrative" and not new_rule.get("source_field_ids"):
        console.print(f"  [yellow]Warning: LLM produced empty source_field_ids — using analysis fields[/yellow]")
        new_rule["source_field_ids"] = analysis.get("required_field_ids", []) + analysis.get("optional_field_ids", [])
    if content_type == "narrative" and not new_rule.get("generation_prompt") and not new_rule.get("hybrid_template"):
        console.print(f"  [yellow]Warning: LLM dropped generation_prompt — keeping original[/yellow]")
        new_rule["generation_prompt"] = section_rule.get("generation_prompt", "")
    if content_type == "formatted_fill" and not new_rule.get("template"):
        console.print(f"  [yellow]Warning: LLM dropped template — keeping original[/yellow]")
        new_rule["template"] = section_rule.get("template", "")

    console.print(f"  [green]Done: {len(new_rule.get('source_field_ids', []))} source fields, "
                  f"min={new_rule.get('min_required_fields')}, "
                  f"temp={new_rule.get('temperature')}, "
                  f"hybrid={'yes' if new_rule.get('hybrid_template') else 'no'}, "
                  f"few_shot={len(new_rule.get('few_shot_examples', []))}[/green]")

    return new_rule, {"section_id": section_id, "analysis": analysis, "rule_gen": "success"}


def main():
    console.print(f"\n{'='*70}")
    console.print("  SECTION RELEARNING ENGINE")
    console.print(f"{'='*70}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    llm = _build_llm_client()
    if not llm:
        console.print("[red]No TOGETHER_API_KEY found. Cannot run relearning.[/red]")
        return
    client, model = llm

    scan_files = sorted(SCAN_DIR.glob("*_scan.json"))
    console.print(f"  Scan files: {len(scan_files)}")

    rules_data = _load_json(RULES_PATH)
    sections = rules_data.get("sections", [])
    console.print(f"  Current rules: {len(sections)} sections")

    narrative_patterns = {}
    if NARRATIVE_PAT_PATH.exists():
        np_data = _load_json(NARRATIVE_PAT_PATH)
        for p in np_data.get("patterns", []):
            narrative_patterns[p.get("section_id", "")] = p
    console.print(f"  Narrative patterns: {len(narrative_patterns)}")

    template_def_sections: dict[str, dict] = {}
    total_reports = 32
    if TEMPLATE_DEF_PATH.exists():
        td_data = _load_json(TEMPLATE_DEF_PATH)
        total_reports = td_data.get("total_reports_analyzed", 32)
        for s in td_data.get("sections", []):
            template_def_sections[s.get("id", "")] = s
    console.print(f"  Template definition: {len(template_def_sections)} sections, {total_reports} reports analyzed")

    schema_data = _load_json(SCHEMA_PATH)
    schema_summary = _build_schema_field_summary(schema_data)
    console.print(f"  Schema fields summary: {len(schema_summary)} chars")

    total_start = time.time()
    new_sections = []
    all_analyses = []

    for sec_rule in sections:
        section_id = sec_rule.get("section_id", "")
        t0 = time.time()

        new_rule, analysis_log = process_section(
            sec_rule, scan_files, narrative_patterns, schema_summary, client, model,
            template_def_sections=template_def_sections, total_reports=total_reports,
        )
        elapsed = time.time() - t0

        new_sections.append(new_rule)
        analysis_log["elapsed_seconds"] = round(elapsed, 1)
        all_analyses.append(analysis_log)

        _save_json(OUT_DIR / f"{section_id}_analysis.json", analysis_log)
        console.print(f"  Time: {elapsed:.1f}s")

    new_rules_data = dict(rules_data)
    new_rules_data["sections"] = new_sections
    new_rules_data["version"] = "2.0"

    v2_path = BASE / "report_learning" / "outputs" / "rules" / "report_rules_v2.json"
    _save_json(v2_path, new_rules_data)
    console.print(f"\n  [bold green]Saved: {v2_path}[/bold green]")

    _save_json(OUT_DIR / "relearn_log.json", {
        "total_sections": len(sections),
        "processed": sum(1 for a in all_analyses if not a.get("skipped")),
        "skipped": sum(1 for a in all_analyses if a.get("skipped")),
        "failed": sum(1 for a in all_analyses if "error" in a),
        "total_time": round(time.time() - total_start, 1),
        "analyses": all_analyses,
    })

    summary_table = Table(title="Relearning Summary")
    summary_table.add_column("Section", width=45)
    summary_table.add_column("Fields", width=7)
    summary_table.add_column("Min", width=5)
    summary_table.add_column("Temp", width=5)
    summary_table.add_column("Hybrid", width=7)
    summary_table.add_column("FewShot", width=8)
    for sec in new_sections:
        ct = sec.get("content_type", "")
        if ct == "static_text":
            continue
        summary_table.add_row(
            sec.get("section_id", ""),
            str(len(sec.get("source_field_ids", []))),
            str(sec.get("min_required_fields", 1)),
            f"{sec.get('temperature', 0.3):.1f}",
            "yes" if sec.get("hybrid_template") else "no",
            str(len(sec.get("few_shot_examples", []))),
        )
    console.print(summary_table)

    total_elapsed = time.time() - total_start
    console.print(f"\n  Total time: {total_elapsed:.0f}s")
    console.print(f"  Output: {v2_path}")

    log_path = OUT_DIR / "console_log.txt"
    log_path.write_text(console.export_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
