"""
Clinical report generator using learned rules.

Loads report_rules.json, processes extraction data through each section rule,
calls Together AI / Fireworks for narrative generation, and assembles a DOCX.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches
from openai import OpenAI

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).parent.parent.parent / "report_learning" / "outputs" / "rules" / "report_rules.json"

# Maps production extraction field names -> rule field IDs.
# The rules were trained with p1_/p5_/p8_ prefixed IDs; the production pipeline
# uses descriptive names. This bridge lets both systems work together.
FIELD_NAME_MAP: dict[str, str] = {
    "patient_name": "p1_patient_name",
    "Participant name": "p1_patient_name",
    "name": "p1_patient_name",
    "date": "p1_date",
    "date_of_birth": "p1_birth_date",
    "gender": "p1_gender",
    "address": "p1_address",
    "home_phone": "p1_home_phone",
    "Date of injury": "date_of_injury",
    "date_of_injury": "date_of_injury",
    "EAMS case number": "case_number",
    "Case location": "venue",
    "employer": "p5_employed_at",
    "Employer": "p5_employed_at",
    "job_title": "p5_job_title",
    "job_description": "p5_job_requirements_initial",
    "job_requirements": "p5_job_requirements_initial",
    "current_work_status": "p5_current_work_status",
    "years_employed": "p5_worked_days_per_week",
    "heart_problems": "p1_heart_problems",
    "high_blood_pressure": "p1_high_blood_pressure",
    "diabetes": "p1_diabetes",
    "stomach_acids": "p1_stomach_acids",
    "thyroid_problem": "p1_thyroid_problem",
    "breathing_problems": "p1_breathing_problems",
    "blood_thinners": "p1_blood_thinners",
    "kidney_problems": "p1_kidney_problems",
    "liver_problems": "p1_liver_problems",
    "numbness_or_tingling": "p1_numbness_pins_needles",
    "Past Medical History": "p8_past_medical_history",
    "Past Surgeries": "p8_past_surgeries",
    "History of Prior Industrial Injuries": "p8_history_prior_industrial_injuries",
    "History of Non-Industrial Injuries": "p8_history_non_industrial_injuries",
    "Any Injuries After the Date of Industrial Injury": "p8_any_injuries_after_industrial_date",
    "MVA Injuries": "p8_mva_injuries",
    "history_of_industrial_injury": "p6_injury_description_1",
    "developed_stressors_in_response_to_industrial_orthopedic_injuries": "p7_developed_stressors_injury",
    "orthopedic_pain_causing_clenching_bracing_of_facial_muscles": "p7_orthopedic_pain_clenching",
    "treatments_received_due_to_industrial_injury_tx_received": "p7_treatments_received",
    "treatments_received_due_to_industrial_injury_surgery": "p7_surgery_body_parts",
    "work_injury_body_parts": "p6_injury_body_parts",
    "do_you_smoke": "p4_do_you_smoke",
    "have_you_ever_smoked": "p4_have_you_ever_smoked",
    "do_you_drink_alcohol": "p4_do_you_drink_alcohol",
    "headache_vas": "p10_headache_vas",
    "headache_location": "p10_headache_locations",
    "left_face_pain_vas": "p10_left_face_pain_frequency",
    "right_face_pain_vas": "p10_right_face_pain_frequency",
    "mastication": "p13_mastication_severity",
    "brushing_teeth": "p13_brushing_teeth_severity",
    "flossing_teeth": "p13_flossing_teeth_severity",
    "swallowing": "p13_swallowing_severity",
    "speak_for_extended_period_of_time": "p13_speak_extended_period_severity",
    "bruxism": "p13_bruxism_severity",
    "Maximum Interincisal Opening": "p14_maximum_interincisal_opening_mm",
    "Left Lateral": "p14_left_lateral_mm",
    "Right Lateral": "p14_right_lateral_mm",
    "Protrusion": "p14_protrusion_mm",
    "Pain on Maximum Interincisal Opening": "p14_max_opening_vas",
    "Left Lateral Pole pain VAS": "p14_left_lateral_pole_vas",
    "Right Lateral Pole pain VAS": "p14_right_lateral_pole_vas",
    "Masseter tenderness score": "p14_masseter_right_vas",
    "Temporalis tenderness score": "p14_temporalis_right_vas",
    "Occlusion": "p15_class_selection",
    "classification": "p15_class_selection",
    "Occlusal Wear": "p15_occlusal_wear",
    "occlusal_wear": "p15_occlusal_wear",
    "missing_teeth": "p15_missing_teeth",
    "Missing Teeth": "p15_missing_teeth",
    "Buccal Mucosal Ridging": "p15_buccal_mucosal_ridging",
    "scalloping": "p15_scalloping",
    "Lateral Border of the Tongue Scalloping": "p15_scalloping",
    "inflamed_gingiva": "p15_inflamed_gingiva",
    "adherence_of_tongue_depressor": "p16_adherence_tongue_depressor",
    "Tongue Blades adhering to inside of cheeks": "p16_adherence_tongue_depressor",
    "amylase_test": "p16_amylase_test",
    "quality_of_saliva": "p16_quality_of_saliva",
    "tissue_analysis_of_lips": "p16_tissue_analysis_lips",
    "tissue_analysis_of_tongue": "p16_tissue_analysis_tongue",
    "diagnostic_bite_force_left": "p16_left_newtons",
    "diagnostic_bite_force_right": "p16_right_newtons",
    "diagnostic_autonomic_nervous_system_before_o2": "p16_before_o2",
    "diagnostic_autonomic_nervous_system_before_pulse": "p16_before_pulse",
    "diagnostic_autonomic_nervous_system_after_o2": "p16_after_o2",
    "diagnostic_autonomic_nervous_system_after_pulse": "p16_after_pulse",
    "elevated_muscular_activity": "p16_elevated_muscular_activity",
    "incoordination_aberrant_function": "p16_incoordination_aberrant_function",
    "last_time_seen_by_dentist": "p9_last_dentist_visit",
    "last_dental_checkup": "p9_last_dentist_visit",
    "epworth_sleepiness_scale_responses": "epworth_activities",
    "total_score": "epworth_sleepiness_scale_total_score",
    "bad_breath_before_injury": "p3_bad_breath_after",
    "diagnosis_bruxism": "p17_f45_8",
    "diagnosis_myalgia_of_facial_muscles": "p17_m79_1",
    "diagnosis_capsulitis_inflammation": "p17_m65_80",
    "diagnosis_trigeminal_nerve_neuropathic_pain": "p17_g50_0",
    "Injured worker first name": "patient_first_name",
    "Injured worker last name": "patient_last_name",
}

TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
TOGETHER_BASE_URL = "https://api.together.xyz/v1"
FIREWORKS_MODEL = "accounts/fireworks/models/deepseek-v3p1"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"


def _build_llm_clients() -> list[tuple[OpenAI, str]]:
    """Build LLM clients in priority order for automatic fallback."""
    clients = []
    together_key = os.getenv("TOGETHER_API_KEY")
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    if together_key:
        clients.append((OpenAI(api_key=together_key, base_url=TOGETHER_BASE_URL, timeout=120.0), TOGETHER_MODEL))
    if fireworks_key:
        clients.append((OpenAI(api_key=fireworks_key, base_url=FIREWORKS_BASE_URL, timeout=120.0), FIREWORKS_MODEL))
    return clients


def _load_rules(rules_path: Path | None = None) -> dict[str, Any]:
    path = rules_path or RULES_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def _build_reverse_map() -> dict[str, str]:
    """Build reverse lookup: rule_field_id -> production_field_name."""
    rev: dict[str, str] = {}
    for prod_name, rule_id in FIELD_NAME_MAP.items():
        rev.setdefault(rule_id, prod_name)
    return rev


_REVERSE_MAP: dict[str, str] = _build_reverse_map()


def _lookup_field(pages: list[dict[str, Any]], field_id: str) -> Any:
    """Find a field value across all pages of an extraction.

    Tries the exact field_id first, then checks the production-name alias.
    """
    aliases = [field_id]
    if field_id in _REVERSE_MAP:
        aliases.append(_REVERSE_MAP[field_id])
    mapped = FIELD_NAME_MAP.get(field_id)
    if mapped and mapped not in aliases:
        aliases.append(mapped)

    for page in pages:
        source = page.get("fields") or page.get("field_values") or {}
        fv = None
        for alias in aliases:
            fv = source.get(alias)
            if fv is not None:
                break
        if fv is None:
            continue
        if isinstance(fv, dict):
            val = fv.get("value")
            if val is not None and str(val).strip():
                return val
            checked = fv.get("is_checked")
            if checked is not None:
                return "Yes" if checked else "No"
            opts = fv.get("circled_options")
            if opts:
                return ", ".join(str(o) for o in opts) if isinstance(opts, list) else str(opts)
            return val
        return fv
    return None


def _check_conditions(conditions: list[dict], pages: list[dict]) -> bool:
    """Evaluate section conditions against extraction data."""
    if not conditions:
        return True

    results = []
    for cond in conditions:
        fid = cond.get("field_id", "")
        op = cond.get("operator", "exists")
        expected = cond.get("value")
        val = _lookup_field(pages, fid)

        if op == "exists":
            results.append(val is not None)
        elif op == "not_empty":
            results.append(val is not None and str(val).strip() != "")
        elif op == "equals":
            results.append(str(val).lower().strip() == str(expected).lower().strip() if val else False)
        elif op == "not_equals":
            results.append(str(val).lower().strip() != str(expected).lower().strip() if val else True)
        elif op == "contains":
            results.append(str(expected).lower() in str(val).lower() if val else False)
        elif op == "greater_than":
            try:
                results.append(float(val) > float(expected) if val else False)
            except (ValueError, TypeError):
                results.append(False)
        else:
            results.append(True)

    combine = conditions[0].get("combine", "and") if conditions else "and"
    if combine == "or":
        return any(results)
    return all(results)


def _derive_fields(pages: list[dict], patient_name: str | None = None) -> dict[str, str]:
    """Build derived/alias fields that the rules template expects but extraction doesn't have directly."""
    derived = {}

    full_name = patient_name or _lookup_field(pages, "p1_patient_name") or ""
    if full_name:
        parts = str(full_name).strip().split()
        derived["patient_first_name"] = parts[0] if parts else ""
        derived["patient_last_name"] = parts[-1] if len(parts) > 1 else ""

    aliases = {
        "patient_dob": ["p1_birth_date", "p1_dob"],
        "patient_sex": ["p1_gender", "p1_sex"],
        "patient_phone": ["p1_cell_phone", "p1_home_phone"],
        "patient_address": ["p1_address"],
        "occupation": ["p5_job_title"],
        "exam_date": ["p1_date"],
    }
    for target, sources in aliases.items():
        for src in sources:
            val = _lookup_field(pages, src)
            if val is not None and str(val).strip():
                derived[target] = str(val)
                break

    addr = derived.get("patient_address", "")
    if addr and "patient_city" not in derived:
        addr_parts = addr.split()
        if len(addr_parts) >= 3:
            derived.setdefault("patient_zip", addr_parts[-1] if addr_parts[-1].isdigit() else "")
            derived.setdefault("patient_state", addr_parts[-2] if len(addr_parts[-2]) == 2 else "")

    return derived


def _fill_template(template: str, pages: list[dict], derived: dict[str, str] | None = None) -> str:
    """Replace {field_id} placeholders in a template with extraction values."""
    extra = derived or {}

    def replacer(match):
        token = match.group(1)
        parts = token.split(":")
        fid = parts[0]
        default = parts[1] if len(parts) > 1 else ""
        val = extra.get(fid) or _lookup_field(pages, fid)
        return str(val) if val is not None else default

    return re.sub(r"\{([^}]+)\}", replacer, template)


def _generate_narrative(
    section_rule: dict,
    pages: list[dict],
    patient_name: str,
    llm_clients: list[tuple[OpenAI, str]],
) -> str:
    """Generate narrative text for a section, trying each LLM client in order."""
    prompt = section_rule.get("generation_prompt", "")
    field_ids = section_rule.get("source_field_ids", [])
    examples = section_rule.get("few_shot_examples", [])

    field_values = {}
    for fid in field_ids:
        val = _lookup_field(pages, fid)
        if val is not None:
            field_values[fid] = str(val)

    if not field_values:
        return ""

    messages: list[dict] = [
        {"role": "system", "content": f"You are a clinical report writer. {prompt}\nPatient name: {patient_name}. Write in third person using Mr./Ms./Mrs. Be concise and professional."},
    ]

    for ex in examples[:3]:
        inp = ex.get("input_fields", {})
        out = ex.get("output_text", "")
        if inp and out:
            messages.append({"role": "user", "content": f"Generate section from: {json.dumps(inp)}"})
            messages.append({"role": "assistant", "content": out})

    messages.append({
        "role": "user",
        "content": f"Generate section from: {json.dumps(field_values)}",
    })

    if not llm_clients:
        return f"[Narrative placeholder — LLM not configured]\nFields: {json.dumps(field_values, indent=2)}"

    last_error = None
    for client, model in llm_clients:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=section_rule.get("max_tokens", 500),
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            logger.warning("LLM call failed for %s with %s: %s — trying next provider",
                           section_rule.get("section_id"), model, e)

    logger.error("All LLM providers failed for %s: %s", section_rule.get("section_id"), last_error)
    return f"[Generation failed: {last_error}]\nFields: {json.dumps(field_values)}"


def _build_list_content(section_rule: dict, pages: list[dict]) -> str:
    """Build list content from extraction data."""
    fid = section_rule.get("list_field_id")
    if not fid:
        return ""
    val = _lookup_field(pages, fid)
    if isinstance(val, list):
        return "\n".join(f"• {item}" for item in val)
    return f"• {val}" if val else ""


def generate_clinical_report(
    extraction_data: dict[str, Any],
    lawyer_data: dict[str, Any] | None = None,
    rules_path: Path | None = None,
) -> bytes:
    """Generate a clinical DOCX report from extraction data using learned rules.

    Args:
        extraction_data: Extraction result with pages[].field_values
        lawyer_data: Optional lawyer cover extraction
        rules_path: Override path to report_rules.json

    Returns:
        DOCX file as bytes
    """
    rules = _load_rules(rules_path)
    sections = rules.get("sections", [])
    global_fmt = rules.get("global_formatting", {})

    pages = extraction_data.get("pages", [])
    if lawyer_data and lawyer_data.get("pages"):
        pages = lawyer_data["pages"] + pages

    patient_name = (
        extraction_data.get("patient_name")
        or _lookup_field(pages, "p1_patient_name")
        or "Patient"
    )

    derived = _derive_fields(pages, patient_name)
    llm_clients = _build_llm_clients()

    if llm_clients:
        logger.info("LLM providers configured: %s", [m for _, m in llm_clients])
    else:
        logger.warning("No LLM clients available — narrative sections will use placeholders")

    doc = DocxDocument()

    style = doc.styles["Normal"]
    font = style.font
    font.name = global_fmt.get("font_name", "Arial")
    font.size = Pt(global_fmt.get("font_size", 11))

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    for sec_rule in sections:
        content_type = sec_rule.get("content_type", "")
        conditions = sec_rule.get("conditions", [])

        if conditions and not _check_conditions(conditions, pages):
            continue

        title = sec_rule.get("title", "")
        if title and content_type != "static_text":
            heading = doc.add_heading(title, level=2)
            for run in heading.runs:
                run.font.name = "Arial"
                run.font.size = Pt(12)
                run.bold = True

        if content_type == "static_text":
            text = sec_rule.get("static_content", "")
            if text:
                if title:
                    heading = doc.add_heading(title, level=2)
                    for run in heading.runs:
                        run.font.name = "Arial"
                        run.font.size = Pt(12)
                        run.bold = True
                for line in text.split("\n"):
                    p = doc.add_paragraph(line)
                    p.style.font.name = "Arial"
                    p.style.font.size = Pt(11)

        elif content_type in ("direct_fill", "formatted_fill"):
            template = sec_rule.get("template", "")
            if template:
                filled = _fill_template(template, pages, derived)
                for line in filled.split("\n"):
                    p = doc.add_paragraph(line)
                    p.paragraph_format.space_after = Pt(2)

        elif content_type == "narrative":
            text = _generate_narrative(sec_rule, pages, patient_name, llm_clients)
            if text:
                for para in text.split("\n"):
                    if para.strip():
                        p = doc.add_paragraph(para.strip())
                        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        elif content_type == "list":
            text = _build_list_content(sec_rule, pages)
            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line, style="List Bullet")

        elif content_type == "table":
            columns = sec_rule.get("table_columns", [])
            if columns:
                table = doc.add_table(rows=1, cols=len(columns))
                table.style = "Table Grid"
                for i, col in enumerate(columns):
                    table.rows[0].cells[i].text = col.get("header", "")

        elif content_type == "conditional_block":
            child_sections = sec_rule.get("child_sections", [])
            for child in child_sections:
                child_conds = child.get("conditions", [])
                if child_conds and not _check_conditions(child_conds, pages):
                    continue
                child_text = child.get("static_content") or ""
                if child_text:
                    doc.add_paragraph(child_text)

    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
