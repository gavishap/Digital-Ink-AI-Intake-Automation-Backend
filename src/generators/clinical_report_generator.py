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
    # --- Patient demographics (p1) ---
    "patient_name": "p1_patient_name",
    "Participant name": "p1_patient_name",
    "name": "p1_patient_name",
    "date": "p1_date",
    "date_of_birth": "p1_birth_date",
    "gender": "p1_gender",
    "address": "p1_address",
    "home_phone": "p1_home_phone",
    "cell_phone": "p1_cell_phone",
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

    # --- Halitosis / bad breath (p3) ---
    "bad_breath_before_injury": "p3_bad_breath_after",
    "bad_breath_percentage_after": "p3_bad_breath_percentage_after",
    "breath_intensity_after": "p3_breath_intensity_after",
    "embarrassment_after": "p3_embarrassment_after",
    "interfere_others_after": "p3_interfere_others_after",

    # --- Social history (p4) ---
    "do_you_smoke": "p4_do_you_smoke",
    "have_you_ever_smoked": "p4_have_you_ever_smoked",
    "do_you_drink_alcohol": "p4_do_you_drink_alcohol",
    "cigarettes_per_day": "p4_cigarettes_per_day",
    "years_smoker": "p4_years_smoker",
    "when_stop_smoking": "p4_when_stop_smoking_years",

    # --- Employment / injury (p5) ---
    "employer": "p5_employed_at",
    "Employer": "p5_employed_at",
    "job_title": "p5_job_title",
    "job_description": "p5_job_requirements_initial",
    "job_requirements": "p5_job_requirements_initial",
    "current_work_status": "p5_current_work_status",
    "years_employed": "p5_worked_days_per_week",
    "hours_per_day": "p5_worked_hours_per_day",
    "lifting_max": "p5_lifting_maximum_lbs",
    "carrying_max": "p5_carrying_maximum_lbs",
    "Date of injury": "p5_date_of_injury",
    "date_of_injury": "p5_date_of_injury",
    "presently_working_different_company": "p5_presently_working_at_different_company",

    # --- Injury history (p6) ---
    "history_of_industrial_injury": "p6_injury_description_1",
    "work_injury_body_parts": "p6_injury_body_parts",

    # --- Treatment / stressors (p7) ---
    "developed_stressors_in_response_to_industrial_orthopedic_injuries": "p7_developed_stressors_injury",
    "orthopedic_pain_causing_clenching_bracing_of_facial_muscles": "p7_orthopedic_pain_clenching",
    "treatments_received_due_to_industrial_injury_tx_received": "p7_treatments_received",
    "treatments_received_due_to_industrial_injury_surgery": "p7_surgery_body_parts",
    "treatments_received": "p7_tx_received",
    "treatments_received_due_to_industrial_injury": "p7_tx_received",
    "tx_received_acupuncture": "p7_tx_received_acupuncture",
    "tx_received_chiropractic": "p7_tx_received_chiropractic_manipulations",
    "tx_received_physical_therapy": "p7_tx_received_physical_therapy",

    # --- Past medical history (p8) ---
    "Past Medical History": "p8_past_medical_history",
    "Past Surgeries": "p8_past_surgeries",
    "History of Prior Industrial Injuries": "p8_history_prior_industrial_injuries",
    "History of Non-Industrial Injuries": "p8_history_non_industrial_injuries",
    "Any Injuries After the Date of Industrial Injury": "p8_any_injuries_after_industrial_date",
    "MVA Injuries": "p8_mva_injuries",

    # --- Dental history (p9) ---
    "last_time_seen_by_dentist": "p9_last_dentist_visit",
    "last_dental_checkup": "p9_last_dentist_visit",
    "last_teeth_cleaned": "p9_last_teeth_cleaned",
    "last_xray": "p9_last_xray",
    "dentist_name": "p9_dentist_1_name",

    # --- Headache / pain (p10) ---
    "headache_vas": "p10_headache_vas",
    "headache_location": "p10_headache_locations",
    "headache_frequency": "p10_headache_frequency",
    "headache_percent_time": "p10_headache_frequency",
    "left_face_pain_vas": "p10_left_face_pain_frequency",
    "right_face_pain_vas": "p10_right_face_pain_frequency",

    # --- Functional limitations (p13) ---
    "mastication": "p13_mastication_severity",
    "brushing_teeth": "p13_brushing_teeth_severity",
    "flossing_teeth": "p13_flossing_teeth_severity",
    "swallowing": "p13_swallowing_severity",
    "speak_for_extended_period_of_time": "p13_speak_extended_period_severity",
    "bruxism": "p13_bruxism_severity",

    # --- Clinical exam (p14) ---
    "Maximum Interincisal Opening": "p14_maximum_interincisal_opening_mm",
    "Left Lateral": "p14_left_lateral_mm",
    "Right Lateral": "p14_right_lateral_mm",
    "Protrusion": "p14_protrusion_mm",
    "Pain on Maximum Interincisal Opening": "p14_max_opening_vas",
    "Left Lateral Pole pain VAS": "p14_left_lateral_pole_vas",
    "Right Lateral Pole pain VAS": "p14_right_lateral_pole_vas",
    "Masseter tenderness score": "p14_masseter_right_vas",
    "Temporalis tenderness score": "p14_temporalis_right_vas",
    "Temporalis Right tenderness": "p14_temporalis_right_y_n",
    "Temporalis Left tenderness": "p14_temporalis_left_y_n",
    "Masseter Right tenderness": "p14_masseter_right_y_n",
    "Masseter Left tenderness": "p14_masseter_left_y_n",
    "temporalis_right_vas": "p14_temporalis_right_vas",
    "temporalis_left_vas": "p14_temporalis_left_vas",
    "masseter_right_vas": "p14_masseter_right_vas",
    "masseter_left_vas": "p14_masseter_left_vas",
    "Joint Noises Lateral": "p14_joint_noises_lateral",
    "Joint Noises Translational": "p14_joint_noises_translational",
    "tenderness_masseter_left": "p14_masseter_left_vas",
    "tenderness_masseter_right": "p14_masseter_right_vas",
    "tenderness_temporalis_left": "p14_temporalis_left_vas",
    "tenderness_temporalis_right": "p14_temporalis_right_vas",

    # --- Intraoral exam (p15) ---
    "Occlusion": "p15_class_selection",
    "classification": "p15_class_selection",
    "Occlusal Wear": "p15_occlusal_wear",
    "occlusal_wear": "p15_occlusal_wear",
    "missing_teeth": "p15_missing_teeth",
    "Missing Teeth": "p15_missing_teeth",
    "Buccal Mucosal Ridging": "p15_buccal_mucosal_ridging",
    "buccal_mucosal_ridging": "Buccal_Mucosal_Ridging",
    "Midline Deviation": "p15_midline_deviation",
    "midline_deviation": "p15_midline_deviation",
    "overbite_mm": "p15_overbite_mm",
    "overjet_mm": "p15_overjet_mm",
    "scalloping": "p15_scalloping",
    "Lateral Border of the Tongue Scalloping": "p15_scalloping",
    "inflamed_gingiva": "p15_inflamed_gingiva",
    "gingival_bleeding": "Gingival_Bleeding",

    # --- Diagnostic tests (p16) ---
    "adherence_of_tongue_depressor": "p16_adherence_tongue_depressor",
    "Tongue Blades adhering to inside of cheeks": "p16_adherence_tongue_depressor",
    "Tongue Depressor Adherence": "Adherence_of_Tongue_Depressor_on_inside_of_cheek",
    "amylase_test": "p16_amylase_test",
    "Amylase Test": "Amylase_Test",
    "amylase_test_result": "Amylase_Test",
    "quality_of_saliva": "p16_quality_of_saliva",
    "tissue_analysis_of_lips": "p16_tissue_analysis_lips",
    "tissue_analysis_of_tongue": "p16_tissue_analysis_tongue",
    "diagnostic_bite_force_left": "p16_left_newtons",
    "diagnostic_bite_force_right": "p16_right_newtons",
    "Bite Force Left": "Diagnostic_Bite_Force_Analysis_Left",
    "Bite Force Right": "Diagnostic_Bite_Force_Analysis_Right",
    "bite_force_left": "Diagnostic_Bite_Force_Analysis_Left",
    "bite_force_right": "Diagnostic_Bite_Force_Analysis_Right",
    "diagnostic_autonomic_nervous_system_before_o2": "p16_before_o2",
    "diagnostic_autonomic_nervous_system_before_pulse": "p16_before_pulse",
    "diagnostic_autonomic_nervous_system_after_o2": "p16_after_o2",
    "diagnostic_autonomic_nervous_system_after_pulse": "p16_after_pulse",
    "elevated_muscular_activity": "p16_elevated_muscular_activity",
    "incoordination_aberrant_function": "p16_incoordination_aberrant_function",
    "Salivary Flow Stimulated": "Salivary_Flow_Stimulated",
    "Salivary Flow Unstimulated": "Salivary_Flow_Unstimulated",
    "salivary_flow_stimulated": "Salivary_Flow_Stimulated",
    "salivary_flow_unstimulated": "Salivary_Flow_Unstimulated",
    "Blood Pressure": "Blood_Pressure",
    "blood_pressure": "Blood_Pressure",
    "No Clicking Auscultated": "p16_no_clicking_was_auscultated",
    "Damage Translation R": "p16_damage_translation_r",
    "Damage Translation L": "p16_damage_translation_l",
    "Damage Lateral R": "p16_damage_lateral_r",
    "Damage Lateral L": "p16_damage_lateral_l",

    # --- Diagnosis (p17) ---
    "diagnosis_bruxism": "p17_f45_8",
    "diagnosis_myalgia_of_facial_muscles": "p17_m79_1",
    "diagnosis_capsulitis_inflammation": "p17_m65_80",
    "diagnosis_trigeminal_nerve_neuropathic_pain": "p17_g50_0",
    "Halitosis diagnosis": "p17_g51_0_halitosis",
    "Gingival disease": "p17_k05_6",
    "Osteoarthritis": "p17_m26_69_osteoarthritis",

    # --- Intraoral photos (p19) ---
    "p19_occlusal_wear_photo": "p19_occlusal_wear",

    # --- Epworth (p3 canonical IDs from schema) ---
    "p3_epworth_sitting_reading": "epworth_sitting_reading",
    "p3_epworth_watching_tv": "epworth_watching_tv",
    "p3_epworth_sitting_inactive": "epworth_sitting_inactive",
    "p3_epworth_passenger_car": "epworth_passenger_car",
    "p3_epworth_lying_down_afternoon": "epworth_lying_down_afternoon",
    "p3_epworth_sitting_talking": "epworth_sitting_talking",
    "p3_epworth_sitting_after_lunch": "epworth_sitting_after_lunch",
    "p3_epworth_car_traffic": "epworth_car_traffic",
    "p3_epworth_total_score": "epworth_sleepiness_scale_total_score",
    "epworth_sleepiness_scale_responses": "epworth_activities",
    "total_score": "epworth_sleepiness_scale_total_score",

    # --- Lawyer page aliases ---
    "Injured worker first name": "patient_first_name",
    "Injured worker last name": "patient_last_name",
    "injured_worker_name": "p1_patient_name",
    "case_number": "ann_case_number",
    "EAMS case number": "ann_case_number",
    "Case location": "ann_venue",
    "case_location": "ann_venue",
    "applicant_attorney_name": "ann_applicant_attorney",
    "body_parts": "ann_body_parts",
    "injury_claim_number": "ann_claim_number",
    "injury_wcab_number": "ann_case_number",
    "injury_date_of_injury": "p5_date_of_injury",
    "injury_injured_body_parts": "ann_body_parts",
}

_VAS_FIELD_HINTS = frozenset({"vas", "intensity", "interfere", "embarrass", "stress", "percent_of_time"})


def _is_vas_field(field_id: str) -> bool:
    fid_lower = field_id.lower()
    return any(hint in fid_lower for hint in _VAS_FIELD_HINTS)


def _normalize_extraction(pages: list[dict]) -> list[dict]:
    """Normalize raw production extraction data to match the training condensed format.

    Handles:
      - Flattening nested field_values dicts
      - Recovering YES/NO from spatial_connections
      - VAS normalization (e.g. "67" -> "6-7")
      - Merging free_form_annotations into fields
    """
    normalized = []
    for page in pages:
        fields: dict[str, Any] = {}

        for fid, fv in page.get("field_values", {}).items():
            if isinstance(fv, dict):
                val = fv.get("value")
                if val is not None and str(val).strip():
                    fields[fid] = val
                elif fv.get("is_checked") is not None:
                    fields[fid] = "Yes" if fv["is_checked"] else "No"
                elif fv.get("circled_options"):
                    opts = fv["circled_options"]
                    fields[fid] = ", ".join(str(o) for o in opts) if isinstance(opts, list) else str(opts)
                elif val is not None:
                    fields[fid] = val
            else:
                fields[fid] = fv

        for conn in page.get("spatial_connections", []):
            if conn.get("relationship_meaning") != "Selection":
                continue
            cid = conn.get("connector_element_id", "")
            for suffix in ("_yes", "_no"):
                if cid.endswith(suffix):
                    field_key = cid[: -len(suffix)]
                    answer = suffix.lstrip("_").upper()
                    sc_key = f"sc_{field_key}"
                    if sc_key not in fields and field_key not in fields:
                        fields[sc_key] = answer
                    break

        for ann in page.get("free_form_annotations", []):
            raw_text = ann.get("raw_text", "")
            normalized_text = ann.get("normalized_text", "")
            related = ann.get("relates_to_field_ids") or []
            if not raw_text and not normalized_text:
                continue
            for rel_fid in related:
                matched = None
                rel_key = rel_fid.lower().replace(" ", "_")
                for fid in fields:
                    if rel_key in fid.lower():
                        matched = fid
                        break
                if matched:
                    existing = fields[matched]
                    if not existing or (isinstance(existing, str) and not existing.strip()):
                        fields[matched] = raw_text
                else:
                    ann_key = f"ann_{rel_key}"
                    if ann_key not in fields:
                        fields[ann_key] = raw_text

        for fid in list(fields):
            val = fields[fid]
            raw = str(val).strip() if val is not None else ""
            if _is_vas_field(fid) and re.fullmatch(r"\d{2}", raw):
                a, b = int(raw[0]), int(raw[1])
                if b > a and a <= 10 and b <= 10:
                    fields[fid] = f"{raw[0]}-{raw[1]}"

        normalized.append({
            "page_number": page.get("page_number"),
            "fields": fields,
            "field_values": fields,
        })
    return normalized


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


_MIXED_CASE_TO_CANONICAL: dict[str, str] = {
    "Diagnostic_Bite_Force_Analysis_Left": "p16_left_newtons",
    "Diagnostic_Bite_Force_Analysis_Right": "p16_right_newtons",
    "Salivary_Flow_Stimulated": "p16_salivary_flow_stimulated",
    "Salivary_Flow_Unstimulated": "p16_salivary_flow_unstimulated",
    "Amylase_Test": "p16_amylase_test",
    "Blood_Pressure": "p16_blood_pressure",
    "Adherence_of_Tongue_Depressor_on_inside_of_cheek": "p16_adherence_tongue_depressor",
    "Buccal_Mucosal_Ridging": "p15_buccal_mucosal_ridging",
    "Gingival_Bleeding": "p16_gingival_bleeding",
    "Inflamed_Gingiva": "p15_inflamed_gingiva",
    "Occlusal_Wear": "p15_occlusal_wear",
    "Lateral Border of the Tongue Scalloping": "p15_scalloping",
    # p14 muscle palpation: rules use per-muscle names, condensed uses table aggregates
    "p14_masseter_right_vas": "p14_muscle_palpation_table_right_vas",
    "p14_masseter_left_vas": "p14_muscle_palpation_table_left_vas",
    "p14_temporalis_right_vas": "p14_muscle_palpation_table_right_vas",
    "p14_temporalis_left_vas": "p14_muscle_palpation_table_left_vas",
    "tenderness_masseter_left": "p14_muscle_palpation_table_left_vas",
    "tenderness_masseter_right": "p14_muscle_palpation_table_right_vas",
    "tenderness_temporalis_left": "p14_muscle_palpation_table_left_vas",
    "tenderness_temporalis_right": "p14_muscle_palpation_table_right_vas",
    # p17 diagnosis naming discrepancy (rule uses -itis, condensed uses -osis)
    "p17_m26_69_osteoarthritis": "p17_m26_69_osteoarthrosis",
    # p10 headache/face pain frequency aliases
    "p10_headache_frequency": "p10_headache_percent_time",
    "p10_headache_locations": "p10_headache_quality",
    "p10_left_face_pain_frequency": "p10_left_face_pain_percent_time",
    "p10_right_face_pain_frequency": "p10_right_face_pain_percent_time",
    # p9 dental history
    "p9_last_dentist_visit": "p9_last_teeth_cleaned",
    # p19 occlusal wear from intraoral photos
    "p19_occlusal_wear": "p19_biofilm_on_teeth",
    # Epworth total score (mixed-case in condensed data)
    "Epworth_Sleepiness_Scale_Total_Score": "epworth_sleepiness_scale_total_score",
}


def _lookup_field(pages: list[dict[str, Any]], field_id: str) -> Any:
    """Find a field value across all pages of an extraction.

    Resolution order: exact match -> FIELD_NAME_MAP alias -> REVERSE_MAP alias
    -> mixed-case canonical mapping -> annotation fallback (ann_ prefix).
    """
    aliases = [field_id]
    if field_id in _REVERSE_MAP:
        aliases.append(_REVERSE_MAP[field_id])
    mapped = FIELD_NAME_MAP.get(field_id)
    if mapped and mapped not in aliases:
        aliases.append(mapped)
    canonical = _MIXED_CASE_TO_CANONICAL.get(field_id)
    if canonical and canonical not in aliases:
        aliases.append(canonical)

    for page in pages:
        source = page.get("fields") or page.get("field_values") or {}
        fv = None
        for alias in aliases:
            fv = source.get(alias)
            if fv is not None:
                break
        if fv is None:
            fid_lower = field_id.lower()
            for key in source:
                if key.lower() == fid_lower:
                    fv = source[key]
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
    derived: dict[str, str] = {}

    full_name = patient_name or _lookup_field(pages, "p1_patient_name") or ""
    if full_name:
        parts = str(full_name).strip().split()
        derived["patient_first_name"] = parts[0] if parts else ""
        derived["patient_last_name"] = parts[-1] if len(parts) > 1 else ""
        derived["patient_name"] = str(full_name).strip()

    # --- Simple aliases ---
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

    # --- Gender-based derived fields ---
    gender = _lookup_field(pages, "p1_gender") or ""
    gender_lower = str(gender).strip().lower()
    if gender_lower in ("male", "m"):
        derived["patient_title"] = "Mr."
        derived["his_her"] = "his"
        derived["he_she"] = "he"
    elif gender_lower in ("female", "f"):
        derived["patient_title"] = "Ms."
        derived["his_her"] = "her"
        derived["he_she"] = "she"
    else:
        derived["patient_title"] = "Mr./Ms."
        derived["his_her"] = "his/her"
        derived["he_she"] = "he/she"

    # --- Pain qualifier (from mandibular range of motion VAS) ---
    vas_raw = _lookup_field(pages, "p14_max_opening_vas")
    if vas_raw is not None:
        try:
            vas_val = float(str(vas_raw).split("-")[0])
            if vas_val == 0:
                derived["pain_qualifier"] = "painless"
            elif vas_val <= 3:
                derived["pain_qualifier"] = "mildly painful"
            elif vas_val <= 6:
                derived["pain_qualifier"] = "moderately painful"
            else:
                derived["pain_qualifier"] = "severely painful"
        except (ValueError, TypeError):
            derived["pain_qualifier"] = "painful"
    else:
        derived["pain_qualifier"] = "painless"

    # --- Midline text ---
    midline = _lookup_field(pages, "p15_midline_deviation")
    if midline and str(midline).strip().lower() not in ("none", "no", "centered", "0", ""):
        derived["midline_text"] = f"deviated to the {midline}"
    else:
        derived["midline_text"] = "centered"

    # --- Diagnosis list (from p17 ICD-10 checkboxes) ---
    dx_codes = {
        "p17_f45_8": ("F45.8", "Bruxism"),
        "p17_m79_1": ("M79.1", "Myalgia of Facial Muscles"),
        "p17_m65_80": ("M65.80", "Capsulitis/Inflammation of the TMJ"),
        "p17_g50_0": ("G50.0", "Trigeminal Nerve Neuropathic Pain"),
        "p17_m26_69_osteoarthritis": ("M26.69", "Osteoarthritis of the TMJ"),
        "p17_g51_0_halitosis": ("G51.0", "Halitosis"),
        "p17_k05_6": ("K05.6", "Gingival/Periodontal Disease"),
    }
    dx_items = []
    for fid, (code, desc) in dx_codes.items():
        val = _lookup_field(pages, fid)
        if val and str(val).strip().lower() not in ("no", "false", "none", ""):
            dx_items.append(f"{code} — {desc}")
    if dx_items:
        derived["diagnosis_list"] = "\n".join(f"{i+1}. {dx}" for i, dx in enumerate(dx_items))

    # --- Epworth activities list (try p3_ canonical IDs first, then legacy) ---
    epworth_fields = [
        ("Sitting and reading", "p3_epworth_sitting_reading", "epworth_sitting_reading"),
        ("Watching TV", "p3_epworth_watching_tv", "epworth_watching_tv"),
        ("Sitting inactive in a public place", "p3_epworth_sitting_inactive", "epworth_sitting_inactive"),
        ("Passenger in a car for 1 hour", "p3_epworth_passenger_car", "epworth_passenger_car"),
        ("Lying down in the afternoon", "p3_epworth_lying_down_afternoon", "epworth_lying_down_afternoon"),
        ("Sitting and talking to someone", "p3_epworth_sitting_talking", "epworth_sitting_talking"),
        ("Sitting quietly after lunch", "p3_epworth_sitting_after_lunch", "epworth_sitting_after_lunch"),
        ("In a car, stopped in traffic", "p3_epworth_car_traffic", "epworth_car_traffic"),
    ]
    epworth_items = []
    epworth_total = 0
    for label, canonical_fid, legacy_fid in epworth_fields:
        val = _lookup_field(pages, canonical_fid) or _lookup_field(pages, legacy_fid)
        if val is not None:
            try:
                score = int(str(val).strip())
                epworth_items.append(f"{label}: {score}")
                epworth_total += score
            except ValueError:
                pass
    if epworth_items:
        derived["epworth_activities"] = "\n".join(epworth_items)
        derived["epworth_sleepiness_scale_total_score"] = str(epworth_total)
    elif not epworth_items:
        raw_total = _lookup_field(pages, "p3_epworth_total_score") or _lookup_field(pages, "Epworth_Sleepiness_Scale_Total_Score")
        if raw_total is not None:
            derived["epworth_sleepiness_scale_total_score"] = str(raw_total).strip()

    # --- Lawyer-sourced case demographic fields ---
    for target, sources in {
        "case_number": ["ann_case_number", "injury_wcab_number", "case_number"],
        "claim_number": ["ann_claim_number", "injury_claim_number", "claim_number"],
        "venue": ["ann_venue", "venue", "case_location"],
        "date_of_injury": ["p5_date_of_injury", "injury_date_of_injury", "date_of_injury"],
        "interpreter": ["p1_interpreter", "interpreter"],
    }.items():
        for src in sources:
            val = _lookup_field(pages, src)
            if val is not None and str(val).strip():
                derived[target] = str(val)
                break

    # --- Date formatting (MM/DD/YYYY -> Month Day, Year) ---
    for date_key in ("exam_date", "patient_dob", "date_of_injury"):
        raw = derived.get(date_key, "")
        m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
        if m:
            from datetime import datetime as _dt
            try:
                dt = _dt(int(m.group(3)), int(m.group(1)), int(m.group(2)))
                derived[f"{date_key}_formatted"] = dt.strftime("%B %d, %Y")
            except ValueError:
                pass

    # --- Address parsing ---
    addr = derived.get("patient_address", "")
    if addr:
        parts = [p.strip() for p in str(addr).split(",")]
        if len(parts) >= 3:
            derived.setdefault("patient_city", parts[-2].strip())
            last = parts[-1].strip().split()
            if len(last) >= 2:
                derived.setdefault("patient_state", last[0])
                derived.setdefault("patient_zip", last[1])
        elif len(parts) == 2:
            last = parts[-1].strip().split()
            if len(last) >= 2:
                derived.setdefault("patient_state", last[0])
                derived.setdefault("patient_zip", last[1])
        else:
            addr_parts = addr.split()
            if len(addr_parts) >= 3:
                derived.setdefault("patient_zip", addr_parts[-1] if addr_parts[-1].isdigit() else "")
                derived.setdefault("patient_state", addr_parts[-2] if len(addr_parts[-2]) == 2 else "")

    # --- Tenderness Y/N derived from VAS values ---
    for muscle, vas_field in [
        ("p14_masseter_right_y_n", "p14_masseter_right_vas"),
        ("p14_masseter_left_y_n", "p14_masseter_left_vas"),
        ("p14_temporalis_right_y_n", "p14_temporalis_right_vas"),
        ("p14_temporalis_left_y_n", "p14_temporalis_left_vas"),
    ]:
        vas = _lookup_field(pages, vas_field)
        if vas is not None:
            try:
                derived[muscle] = "Yes" if float(str(vas).split("-")[0]) > 0 else "No"
            except (ValueError, TypeError):
                derived[muscle] = "Yes" if str(vas).strip() else "No"

    # --- Default for conditional fields ---
    derived.setdefault("additional_findings", "")

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


_PREAMBLE_PATTERNS = re.compile(
    r"^(here is|here's|based on|i will|i'll|the following|below is|let me|"
    r"sure,|certainly|of course|this section|the .* section)",
    re.IGNORECASE,
)


def _clean_narrative(text: str) -> str:
    """Strip LLM artifacts from generated narrative text."""
    lines = text.strip().split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if _PREAMBLE_PATTERNS.match(stripped):
            continue
        if stripped.startswith("#"):
            line = stripped.lstrip("#").strip()
        line = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", line)
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    if result.startswith('"') and result.endswith('"'):
        result = result[1:-1]
    return result


def _generate_narrative(
    section_rule: dict,
    pages: list[dict],
    patient_name: str,
    llm_clients: list[tuple[OpenAI, str]],
    derived: dict[str, str] | None = None,
) -> str:
    """Generate narrative text for a section, trying each LLM client in order."""
    prompt = section_rule.get("generation_prompt", "")
    field_ids = section_rule.get("source_field_ids", [])
    examples = section_rule.get("few_shot_examples", [])
    d = derived or {}

    field_values = {}
    for fid in field_ids:
        val = d.get(fid) or _lookup_field(pages, fid)
        if val is not None:
            field_values[fid] = str(val)

    if not field_values:
        return ""

    patient_last = d.get("patient_last_name", patient_name.split()[-1] if patient_name else "")
    title = d.get("patient_title", "Mr./Ms.")
    pronoun_he = d.get("he_she", "he/she")
    pronoun_his = d.get("his_her", "his/her")

    system_content = (
        f"You are an expert clinical report writer generating a section of an orofacial pain evaluation report.\n\n"
        f"SECTION: {section_rule.get('title', '')}\n"
        f"PATIENT: {patient_name}\n\n"
        f"INSTRUCTIONS:\n"
        f"- {prompt}\n"
        f"- Write ONLY the section content. Do NOT include any preamble, introduction, or meta-commentary.\n"
        f"- Do NOT start with phrases like 'Here is', 'Based on', 'I will', 'The following'.\n"
        f"- Use ONLY the patient name '{patient_name}' — never use names from examples.\n"
        f"- Write in third person using {title} {patient_last}.\n"
        f"- Use pronouns '{pronoun_he}' and '{pronoun_his}'.\n"
        f"- If a field value is missing or empty, omit that detail rather than inventing data.\n"
        f"- Be concise, professional, and use clinical terminology appropriate for a medical-legal report.\n"
    )

    messages: list[dict] = [{"role": "system", "content": system_content}]

    for ex in examples[:3]:
        inp = ex.get("input_fields", {})
        out = ex.get("output_text", "")
        if inp and out:
            out = out.replace("{patient_name}", patient_name)
            out = out.replace("{patient_last_name}", patient_last)
            out = out.replace("{patient_title}", title)
            out = out.replace("{his_her}", pronoun_his)
            out = out.replace("{he_she}", pronoun_he)
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
            raw = response.choices[0].message.content.strip()
            return _clean_narrative(raw)
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

    pages = _normalize_extraction(extraction_data.get("pages", []))
    if lawyer_data and lawyer_data.get("pages"):
        lawyer_pages = _normalize_extraction(lawyer_data["pages"])
        pages = lawyer_pages + pages

    patient_name = (
        extraction_data.get("patient_name")
        or _lookup_field(pages, "p1_patient_name")
        or "Patient"
    )

    if lawyer_data and lawyer_data.get("pages"):
        for lf in ("injured_worker_name", "p1_patient_name", "patient_name", "Participant name"):
            lawyer_name = _lookup_field(pages, lf)
            if lawyer_name and str(lawyer_name).strip():
                patient_name = str(lawyer_name).strip()
                break

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
            text = _generate_narrative(sec_rule, pages, patient_name, llm_clients, derived)
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
