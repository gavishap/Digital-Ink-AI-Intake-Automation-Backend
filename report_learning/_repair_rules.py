"""
Comprehensive repair script for report_rules.json.

Phase A (deterministic, no LLM):
  - Add 12 missing sections with hand-crafted rules
  - Sanitize patient names from all few_shot_examples
  - Set per-section max_tokens
  - Reorder sections by template_definition
  - Cross-reference source_field_ids against condensed extractions
  - Output coverage report

Usage:
  python -m report_learning._repair_rules                # Full repair
  python -m report_learning._repair_rules --coverage-only # Just report coverage
  python -m report_learning._repair_rules --dry-run       # Show changes without saving
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()

MODULE_ROOT = Path(__file__).parent
OUTPUTS = MODULE_ROOT / "outputs"
RULES_DIR = OUTPUTS / "rules"
SCANNED_DIR = OUTPUTS / "scanned"
CONDENSED_DIR = OUTPUTS / "extractions_v2" / "condensed"

RULES_PATH = RULES_DIR / "report_rules.json"
TEMPLATE_PATH = RULES_DIR / "template_definition.json"
NARRATIVE_PATH = RULES_DIR / "narrative_patterns.json"
VALIDATION_PATH = RULES_DIR / "validation_scores.json"

# ── Patient names to sanitize ────────────────────────────────────────────────

PATIENT_NAMES = [
    ("Anderson", "Ronald"), ("Bachar", "Margalit"), ("Benton", "Patricia"),
    ("Boricean", "Maria"), ("Canseco Gutierrez", "Amador"),
    ("Witt", "Amber"), ("Vasquez", "Aubrie"), ("Higuera", "Aurora"),
    ("Celis Rochon", "Cesar"), ("Paprock", "Dara"), ("Lazo", "Erasmo"),
    ("Castro Laynez", "Fabian"), ("Dominguez", "Fernando"),
    ("Truong", "Hung Thai"), ("Lupercio", "Isaac"),
    ("Carraway", "Jenea"), ("Wahoff", "Jennifer"),
    ("Lambaren", "Jimmy"), ("Rivera", "Jorge"),
    ("Davila Rangel", "Jose"), ("Coreas Torres", "Juan"),
    ("Washington", "Lemeka"), ("Jimenez Rodriguez", "Manuel"),
    ("Rosales", "Rosa M."), ("Garcia", "Rosa"), ("Garcia", "Sergio"),
    ("Pina", "Tomas"), ("Sanchez", "Maridelia"),
    ("Picazo de Mayorga", "Martha"), ("Duran Saldivar", "Miguel"),
    ("Mooney", "Norvel"), ("Hernandez Aguilar", "Raquel"),
]

# ── Max tokens per section ───────────────────────────────────────────────────

MAX_TOKENS_MAP = {
    "discussion": 3000,
    "treatment_plan": 2500,
    "history_of_industrial_injury": 1000,
    "subjective_complaints": 1000,
    "conclusion": 1000,
    "temporal_connection_between_industrial_exposure_and": 1000,
    "credibility": 800,
    "diagnostic_photographs": 800,
    "diagnostic_salivary_flow_and_buffering_tests": 800,
    "diagnostic_bite_force_testing": 800,
    "diagnostic_autonomic_nervous_system_testing": 800,
    "review_of_records": 800,
    "disclosure_notice": 800,
}

# ── Missing section definitions ──────────────────────────────────────────────

def _build_missing_sections(template_sections: list[dict], narrative_map: dict[str, dict]) -> list[dict]:
    """Build SectionRule dicts for the 12 missing sections."""
    missing = []

    # Category A: Static headings
    missing.append({
        "section_id": "initial_report_in_the_field_of",
        "title": "Initial Report in the Field of Dentistry",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "static_text",
        "static_content": "INITIAL REPORT IN THE FIELD OF DENTISTRY",
        "source_field_ids": [],
        "template": None,
        "format_pattern": None,
        "generation_prompt": None,
        "few_shot_examples": [],
        "max_tokens": 100,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": {"font_name": "Arial", "font_size": 11.0, "bold": True, "italic": False, "underline": True, "alignment": "center", "color": None, "all_caps": True},
        "content_formatting": None,
        "notes": "Static heading only, no content elements in scanned reports.",
    })

    missing.append({
        "section_id": "diagnostic_testing",
        "title": "Diagnostic Testing",
        "ordering": 0,
        "page_break_before": True,
        "is_required": True,
        "content_type": "static_text",
        "static_content": "DIAGNOSTIC TESTING",
        "source_field_ids": [],
        "template": None,
        "format_pattern": None,
        "generation_prompt": None,
        "few_shot_examples": [],
        "max_tokens": 100,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": {"font_name": "Arial", "font_size": 11.0, "bold": True, "italic": False, "underline": True, "alignment": None, "color": None, "all_caps": True},
        "content_formatting": None,
        "notes": "Parent heading for diagnostic subsections. No content, just the heading.",
    })

    # Disclosure notice -- nearly static legal boilerplate
    missing.append({
        "section_id": "disclosure_notice",
        "title": "Disclosure Notice",
        "ordering": 0,
        "page_break_before": True,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the legal disclosure notice for a workers' compensation dental report. "
            "This section has a highly standardized structure:\n\n"
            "Paragraph 1: 'In accordance with Labor Code Section 4628, I solely performed the interview with "
            "{patient_title} {patient_last_name}. I solely performed the physical examination and I solely took "
            "the patient's history of injury and medical history. I performed the examination in its entirety at "
            "my office. I reviewed the medical records and personally reviewed and signed this report.'\n\n"
            "Paragraph 2: 'To the best of my knowledge, the evaluation and the time performing it were in "
            "accordance with the guidelines of the Industrial Medical Council of Administrative Director to the "
            "extent that those guidelines exist.'\n\n"
            "Paragraph 3: 'I did not bill for any other medical-legal evaluations or diagnostic procedures or "
            "diagnostic services performed by independent contractors.'\n\n"
            "Paragraph 4: The perjury declaration starting with '\"The undersigned declares under penalty of perjury...\"'\n\n"
            "Then the doctor signature block with name, credentials, license number, location, and contact info.\n\n"
            "Use {patient_title} {patient_last_name} for the patient reference. Use Mr./Ms. based on gender."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "In accordance with Labor Code Section 4628, I solely performed the interview with "
                    "Mr. {patient_last_name}. I solely performed the physical examination and I solely took the "
                    "patient's history of injury and medical history. I performed the examination in its entirety "
                    "at my office. I reviewed the medical records and personally reviewed and signed this report.\n"
                    "To the best of my knowledge, the evaluation and the time performing it were in accordance with "
                    "the guidelines of the Industrial Medical Council of Administrative Director to the extent that "
                    "those guidelines exist.\n"
                    "I did not bill for any other medical-legal evaluations or diagnostic procedures or diagnostic "
                    "services performed by independent contractors.\n"
                    "\"The undersigned declares under penalty of perjury that to the best of my knowledge I am not "
                    "in violation of L.C. 5703 or L.C. 139.3. I declare under penalty of perjury that the information "
                    "contained in this report and its attachments, if any, is true and correct to the best of my "
                    "knowledge and belief, except as to information that I have indicated that I received from others. "
                    "As to that information, I declare under penalty of perjury that the information accurately "
                    "describes the information provided to me and, except as noted herein, that I believe it to be true.\""
                ),
            }
        ],
        "max_tokens": 800,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Nearly identical across all 32 reports. Only patient name and doctor name/credentials vary.",
    })

    # Differential diagnosis -- nearly static with patient name
    missing.append({
        "section_id": "differential_diagnosis",
        "title": "Differential Diagnosis",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the differential diagnosis statement. This is a short, nearly static section. "
            "Structure:\n"
            "Paragraph 1: 'An examining doctor\\'s opinion for causation must be based on a reliable differential "
            "diagnosis formed after taking a history, physical examination, diagnostic tests and, if available, a "
            "review of prior medical records. I have considered this for {patient_title} {patient_last_name}.'\n"
            "Paragraph 2: 'The reader must remember: Treatment is not apportioned!'\n\n"
            "Use Mr./Ms. based on gender. This section is identical across all patients except for the name."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "An examining doctor's opinion for causation must be based on a reliable differential "
                    "diagnosis formed after taking a history, physical examination, diagnostic tests and, if "
                    "available, a review of prior medical records. I have considered this for Mr. {patient_last_name}.\n"
                    "The reader must remember: Treatment is not apportioned!"
                ),
            }
        ],
        "max_tokens": 500,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Nearly 100% static across all 32 reports. Only the patient name varies.",
    })

    # Credibility -- templated narrative with pronoun variations
    np = narrative_map.get("credibility", {})
    missing.append({
        "section_id": "credibility",
        "title": "Credibility",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the patient credibility assessment. This section follows a strict template:\n\n"
            "'I observed {patient_title} {patient_last_name} during the course of this evaluation. A comfortable "
            "doctor-patient relationship was established which enabled {patient_title} {patient_last_name} to "
            "candidly confide the difficulties {he_she} experienced as a result of {his_her} industrial injuries. "
            "I found {patient_title} {patient_last_name} to be a candid and sincere individual. I believe "
            "{patient_title} {patient_last_name} has done {his_her} best to provide an accurate account of "
            "{his_her} conditions. {patient_title} {patient_last_name}\\'s subjective complaints matched "
            "{the_my} objective findings in my evaluation of {him_her}. In summation, I find no basis for "
            "questioning {patient_title} {patient_last_name}\\'s credibility. It is evident {he_she} has "
            "suffered dental related injuries as a result of {his_her} industrial injuries.'\n\n"
            "Use Mr./Ms. based on gender. Use he/she, his/her, him/her accordingly. "
            "Some reports also include: '{patient_title} {patient_last_name}\\'s history of industrial injury "
            "and the symptoms {he_she} developed have been consistent throughout the medical records provided "
            "for my review.' -- include this if review_of_records section is present."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "I observed Mr. {patient_last_name} during the course of this evaluation. A comfortable "
                    "doctor-patient relationship was established which enabled Mr. {patient_last_name} to candidly "
                    "confide the difficulties he experienced as a result of his industrial injuries. I found "
                    "Mr. {patient_last_name} to be a candid and sincere individual. I believe Mr. {patient_last_name} "
                    "has done his best to provide an accurate account of his conditions. Mr. {patient_last_name}'s "
                    "subjective complaints matched my objective findings in my evaluation of him. In summation, I find "
                    "no basis for questioning Mr. {patient_last_name}'s credibility. It is evident he has suffered "
                    "dental related injuries as a result of his industrial injuries."
                ),
            }
        ],
        "max_tokens": 800,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Highly templated. Only varies by patient name, pronouns, and optional records-review sentence.",
    })

    # Temporal connection -- templated with pronoun/medication variations
    np = narrative_map.get("temporal_connection_between_industrial_exposure_and", {})
    missing.append({
        "section_id": "temporal_connection_between_industrial_exposure_and",
        "title": "Temporal Connection Between Industrial Exposure and Dental Conditions",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the temporal connection section. This follows a structured 3-paragraph template:\n\n"
            "Paragraph 1: 'In my discussion section above, I discussed how, with reasonable medical probability, "
            "the industrial exposure and its resultant orthopedic pain and emotional stressors, have developed "
            "consequential and derivative injuries for {patient_title} {patient_last_name} in the area of Dentistry.'\n\n"
            "Paragraph 2: 'As explained above, even if the medical records reveal {patient_title} {patient_last_name} "
            "had these dental problems prior to the industrial exposure, it is with reasonable medical probability that "
            "{his_her} dental problems were contributed to and aggravated on an industrial basis by at least 1% in "
            "response to {his_her} industrial pain, any resultant stress, and the side effect of medication taken on "
            "an industrial related basis.'\n\n"
            "Paragraph 3: 'While I understand that one of the arguments a person may bring up is latency of when "
            "these dental problems started to occur, one has to understand that latency is individual and depends "
            "on the intensity of exposure and predilection of the individual.'\n\n"
            "Use Mr./Ms. and he/she/his/her based on gender. If specific medications are known from the patient's "
            "history, mention them by name in paragraph 2 (e.g., 'side effect of the Norco medication')."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "In my discussion section above, I discussed how, with reasonable medical probability, the "
                    "industrial exposure and its resultant orthopedic pain and emotional stressors, have developed "
                    "consequential and derivative injuries for Mr. {patient_last_name} in the area of Dentistry.\n"
                    "As explained above, even if the medical records reveal Mr. {patient_last_name} had these dental "
                    "problems prior to the industrial exposure, it is with reasonable medical probability that his "
                    "dental problems were contributed to and aggravated on an industrial basis by at least 1% in "
                    "response to his industrial pain, any resultant stress, and the side effect of medication taken "
                    "on an industrial related basis.\n"
                    "While I understand that one of the arguments a person may bring up is latency of when these "
                    "dental problems started to occur, one has to understand that latency is individual and depends "
                    "on the intensity of exposure and predilection of the individual."
                ),
            }
        ],
        "max_tokens": 1000,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Highly templated. Varies by name, pronouns, and optional medication names.",
    })

    # Radiographic results -- short narrative, often pending
    missing.append({
        "section_id": "radiographic_results",
        "title": "Radiographic Results",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the radiographic results section. This is typically a short 1-2 sentence section.\n\n"
            "Default (most common): 'To be determined when {patient_title} {patient_last_name} returns to our "
            "Hawthorne, Reseda, and/or Anaheim offices for x-rays or presents us with x-rays taken at another "
            "dental office.'\n\n"
            "If X-ray findings are available, describe them: 'X-rays taken at [location], on [date], revealed "
            "[findings such as bone loss, missing teeth, etc.]'\n\n"
            "Use Mr./Ms. based on gender."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "To be determined when Mr. {patient_last_name} returns to our Hawthorne, Reseda, "
                    "and/or Anaheim offices for x-rays or presents us with x-rays taken at another dental office."
                ),
            },
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "FEMALE"},
                "output_text": (
                    "X-rays taken at another dental office, unidentified, on 7/16/25, revealed severe "
                    "bone loss around the teeth"
                ),
            },
        ],
        "max_tokens": 500,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Usually pending. When available, describes panoramic X-ray findings.",
    })

    # Diagnostic photographs -- semi-templated narrative
    np = narrative_map.get("diagnostic_photographs", {})
    missing.append({
        "section_id": "diagnostic_photographs",
        "title": "Diagnostic Photographs",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": [
            "p1_patient_name", "p1_gender",
            "Lateral Border of the Tongue Scalloping",
            "Buccal_Mucosal_Ridging", "Occlusal_Wear",
            "Adherence_of_Tongue_Depressor_on_inside_of_cheek",
            "Inflamed_Gingiva", "Gingival_Bleeding",
        ],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the diagnostic photographs findings section. This describes clinical findings "
            "documented in intraoral/extraoral photographs. Structure as a single flowing paragraph.\n\n"
            "Common findings to include (if present in data):\n"
            "- 'Diagnostic photographs document scalloping on the lateral borders of the tongue.'\n"
            "- 'The photographs document bite mark lines on the inside of the cheeks.'\n"
            "- 'The photographs document wear on the surfaces of the teeth.' (or 'anterior teeth')\n"
            "- 'The photographs document the Xerostomia / Anti-Cholinergic side effect where, due to "
            "qualitative changes of the saliva, a tongue depressor sticks to the inside of the cheek "
            "- even when not held by hand.'\n"
            "- Gum findings: 'receding gum tissues', 'swelling gum tissues', 'swollen and bleeding gum tissues'\n"
            "- Always end with: 'objectively-disclosed bacterial biofilm deposits on {patient_title} "
            "{patient_last_name}\\'s teeth and around {his_her} gum tissues.'\n\n"
            "Use Mr./Ms. and his/her based on gender."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "Diagnostic photographs document scalloping on the lateral borders of the tongue. "
                    "The photographs document bite mark lines on the inside of the cheeks. The photographs "
                    "document wear on the surfaces of the teeth. The photographs document the Xerostomia / "
                    "Anti-Cholinergic side effect where, due to qualitative changes of the saliva, a tongue "
                    "depressor sticks to the inside of the cheek - even when not held by hand. The photographs "
                    "document receding gum tissues as well as objectively-disclosed bacterial biofilm deposits "
                    "on Mr. {patient_last_name}'s teeth and around his gum tissues."
                ),
            }
        ],
        "max_tokens": 800,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Semi-templated. Core phrases are consistent; specific findings vary per patient.",
    })

    # Review of records -- conditional (7/32 reports)
    missing.append({
        "section_id": "review_of_records",
        "title": "Review of Records",
        "ordering": 0,
        "page_break_before": False,
        "is_required": False,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the review of records section. Only include this section when prior medical records "
            "have been provided for review.\n\n"
            "Always begin with the static disclaimer: 'Of the medical records provided for review, only the "
            "material immediately following was sufficiently significant to be quoted/paraphrased. The remainder "
            "of the material reviewed was either irrelevant to the decisions required today, or was redundant "
            "to the information presented in this section.'\n\n"
            "Then summarize the key records reviewed, including:\n"
            "- Source of records (doctor name, facility)\n"
            "- Date of records\n"
            "- Key findings, diagnoses, and complaints\n"
            "- Treatment recommendations from reviewed records\n\n"
            "Use {patient_title} {patient_last_name} for patient references."
        ),
        "few_shot_examples": [],
        "max_tokens": 800,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [
            {"field_id": "review_of_records_available", "operator": "exists", "value": None, "combine": "and"}
        ],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Conditional section, only present in 7/32 reports.",
    })

    # Conclusion -- templated with medication-specific content
    np = narrative_map.get("conclusion", {})
    missing.append({
        "section_id": "conclusion",
        "title": "Conclusion",
        "ordering": 0,
        "page_break_before": False,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the conclusion section. This follows a structured 2-paragraph template:\n\n"
            "Paragraph 1: 'Based on the methodology used by dental physicians in the field of Dentistry, "
            "I have: 1) Shown data to support generic causation; 2) Ruled out other well-accepted risk factors "
            "in the patient; and 3) Shown a clear temporal relationship between the industrial exposure and "
            "trauma, resultant emotional stressors, [optional: side effect(s) of the {medication_names} "
            "medication taken on an industrial basis,] and the diagnoses presented regarding {patient_title} "
            "{patient_last_name}.'\n\n"
            "Paragraph 2: 'Based on the available data, the history provided to me by {patient_title} "
            "{patient_last_name}, my objective findings, the scientific literature, and my expertise in the "
            "field, it is my opinion that, with reasonable medical probability, {patient_title} "
            "{patient_last_name}\\'s presenting complaints and clinical symptoms in my area of expertise were "
            "caused or aggravated on an industrial basis.'\n\n"
            "If medications are documented in the patient's history, list them specifically in paragraph 1. "
            "If no medications, omit that clause. Use Mr./Ms. based on gender."
        ),
        "few_shot_examples": [
            {
                "input_fields": {"patient_name": "{patient_name}", "p1_gender": "MALE"},
                "output_text": (
                    "Based on the methodology used by dental physicians in the field of Dentistry, I have: "
                    "1) Shown data to support generic causation; 2) Ruled out other well-accepted risk factors "
                    "in the patient; and 3) Shown a clear temporal relationship between the industrial exposure "
                    "and trauma, resultant emotional stressors, and the diagnoses presented regarding "
                    "Mr. {patient_last_name}.\n"
                    "Based on the available data, the history provided to me by Mr. {patient_last_name}, my "
                    "objective findings, the scientific literature, and my expertise in the field, it is my "
                    "opinion that, with reasonable medical probability, Mr. {patient_last_name}'s presenting "
                    "complaints and clinical symptoms in my area of expertise were caused or aggravated on an "
                    "industrial basis."
                ),
            }
        ],
        "max_tokens": 1000,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Templated. Key variation: medication names in paragraph 1.",
    })

    # Discussion -- longest section, complex medical-legal analysis
    np = narrative_map.get("discussion", {})
    writing_pattern = np.get("writing_pattern", "")
    static_phrases = np.get("static_phrases", [])
    data_points = np.get("data_points_used", [])

    dp_text = ""
    if data_points:
        dp_lines = [f"- {dp['data_point']} ({'REQUIRED' if dp.get('required') else 'optional'}): {dp.get('how_used', '')}" for dp in data_points[:15]]
        dp_text = "\n\nData points to incorporate:\n" + "\n".join(dp_lines)

    sp_text = ""
    if static_phrases:
        sp_text = "\n\nStatic phrases that should appear verbatim:\n" + "\n".join(f"- \"{p}\"" for p in static_phrases[:15])

    missing.append({
        "section_id": "discussion",
        "title": "Discussion",
        "ordering": 0,
        "page_break_before": True,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": [
            "p1_patient_name", "p1_gender",
            "Diagnostic_Bite_Force_Analysis_Left", "Diagnostic_Bite_Force_Analysis_Right",
            "tenderness_masseter_left", "tenderness_masseter_right",
            "tenderness_temporalis_left", "tenderness_temporalis_right",
            "Salivary_Flow_Stimulated", "Salivary_Flow_Unstimulated",
            "Amylase_Test", "Blood_Pressure",
        ],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the Discussion section -- the longest and most complex section of the report. "
            "This is a detailed medical-legal analysis connecting the patient's industrial exposure to their "
            "dental conditions.\n\n"
            f"Writing pattern: {writing_pattern[:600]}\n"
            f"{dp_text}{sp_text}\n\n"
            "The discussion typically follows this structure:\n"
            "1. Opening: Objective clinical findings of bruxism (scalloping, bite marks, wear)\n"
            "2. Muscle examination findings (painful palpation, taut bands)\n"
            "3. Diagnostic test results (Doppler, sEMG, bite force, ANS testing, salivary flow)\n"
            "4. Medical literature citations linking industrial stress to bruxism\n"
            "5. Causation analysis connecting orthopedic pain -> emotional stress -> bruxism -> dental damage\n"
            "6. Medication side effects (xerostomia from industrial medications)\n"
            "7. Summary of industrial causation opinion\n\n"
            "Use formal medical-legal language. Reference specific test values from the data. "
            "Use {patient_title} {patient_last_name} throughout."
        ),
        "few_shot_examples": [],
        "max_tokens": 3000,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Longest section (~6600 chars avg). Requires diagnostic test data and clinical findings.",
    })

    # Treatment plan -- second longest section
    np = narrative_map.get("treatment_plan", {})
    writing_pattern = np.get("writing_pattern", "")
    static_phrases = np.get("static_phrases", [])
    data_points = np.get("data_points_used", [])

    dp_text = ""
    if data_points:
        dp_lines = [f"- {dp['data_point']} ({'REQUIRED' if dp.get('required') else 'optional'}): {dp.get('how_used', '')}" for dp in data_points[:15]]
        dp_text = "\n\nData points to incorporate:\n" + "\n".join(dp_lines)

    sp_text = ""
    if static_phrases:
        sp_text = "\n\nStatic phrases that should appear verbatim:\n" + "\n".join(f"- \"{p}\"" for p in static_phrases[:15])

    missing.append({
        "section_id": "treatment_plan",
        "title": "Treatment Plan",
        "ordering": 0,
        "page_break_before": True,
        "is_required": True,
        "content_type": "narrative",
        "static_content": None,
        "source_field_ids": ["p1_patient_name", "p1_gender"],
        "template": None,
        "format_pattern": None,
        "generation_prompt": (
            "Generate the Treatment Plan section -- the second longest section of the report. "
            "This details recommended treatments with legal citations.\n\n"
            f"Writing pattern: {writing_pattern[:600]}\n"
            f"{dp_text}{sp_text}\n\n"
            "The treatment plan typically includes:\n"
            "1. Legal citation: 'Please Note: I researched the ACOEM guidelines, the MTUS guidelines, "
            "and the ODG guidelines...' followed by Labor Code Section 4604.5(d)\n"
            "2. ADA standard of care citation\n"
            "3. Specific treatment recommendations:\n"
            "   - Orofacial Pain Occlusal Orthotic Device (with CPT codes)\n"
            "   - Nocturnal Orthopedic Repositioning Device (if nighttime bruxism present)\n"
            "   - Physical medicine modalities / orthotic training\n"
            "   - Referrals (ENT, internal medicine, psychological as indicated)\n"
            "   - Follow-up schedule\n"
            "4. RFA (Request for Authorization) specifics\n\n"
            "Use formal medical-legal language. Include CPT codes where applicable."
        ),
        "few_shot_examples": [],
        "max_tokens": 2500,
        "list_field_id": None,
        "list_bullet_style": "bullet",
        "table_columns": [],
        "table_row_source_field": None,
        "conditions": [],
        "child_sections": [],
        "title_formatting": None,
        "content_formatting": None,
        "notes": "Second longest section (~7500 chars avg). Heavy legal citations and CPT codes.",
    })

    return missing


# ── Sanitization ─────────────────────────────────────────────────────────────

def _build_name_patterns() -> list[tuple[re.Pattern, str]]:
    """Build regex patterns for all known patient names."""
    patterns = []
    for last, first in PATIENT_NAMES:
        first_parts = first.split()
        first_name = first_parts[0]

        for title in ["Mr.", "Ms.", "Mrs."]:
            patterns.append(
                (re.compile(re.escape(f"{title} {last}"), re.IGNORECASE),
                 f"{{patient_title}} {{patient_last_name}}")
            )

        patterns.append(
            (re.compile(re.escape(f"{last}, {first}"), re.IGNORECASE),
             "{patient_name}")
        )
        patterns.append(
            (re.compile(re.escape(f"{first} {last}"), re.IGNORECASE),
             "{patient_first_name} {patient_last_name}")
        )
        if first_name != first:
            patterns.append(
                (re.compile(re.escape(f"{first_name} {last}"), re.IGNORECASE),
                 "{patient_first_name} {patient_last_name}")
            )

        patterns.append(
            (re.compile(rf"(?<!\w){re.escape(last)}(?:'s|'s)?(?!\w)", re.IGNORECASE),
             "{patient_last_name}")
        )

    return patterns


def _sanitize_text(text: str, patterns: list[tuple[re.Pattern, str]]) -> str:
    """Replace patient names in text with placeholders."""
    for pat, replacement in patterns:
        text = pat.sub(replacement, text)
    return text


def sanitize_rules(rules: list[dict], patterns: list[tuple[re.Pattern, str]]) -> int:
    """Strip patient names from all few_shot_examples. Returns count of changes."""
    changes = 0
    for rule in rules:
        for ex in rule.get("few_shot_examples", []):
            original = ex.get("output_text", "")
            sanitized = _sanitize_text(original, patterns)
            if sanitized != original:
                ex["output_text"] = sanitized
                changes += 1

            inp = ex.get("input_fields", {})
            if "patient_name" in inp:
                for last, first in PATIENT_NAMES:
                    val = inp["patient_name"]
                    if last.lower() in val.lower() or first.lower() in val.lower():
                        inp["patient_name"] = "{patient_name}"
                        changes += 1
                        break
    return changes


# ── Coverage check ───────────────────────────────────────────────────────────

def run_coverage_check(
    rules: list[dict],
    template_sections: list[dict],
    condensed_dir: Path,
) -> dict[str, Any]:
    """Check rule coverage against template and field resolution against extractions."""
    rule_ids = {r["section_id"] for r in rules}
    template_ids = {s["id"] for s in template_sections}

    missing_from_rules = template_ids - rule_ids
    extra_in_rules = rule_ids - template_ids

    # Field resolution check
    all_extraction_fields: set[str] = set()
    ext_files = sorted(condensed_dir.glob("*_condensed.json")) if condensed_dir.exists() else []
    for f in ext_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for page in data.get("pages", []):
                all_extraction_fields.update(page.get("fields", {}).keys())
        except Exception:
            pass

    field_results: dict[str, dict] = {}
    total_fields = 0
    resolved_fields = 0
    for rule in rules:
        sid = rule["section_id"]
        src_fields = rule.get("source_field_ids", [])
        resolved = [f for f in src_fields if f in all_extraction_fields]
        unresolved = [f for f in src_fields if f not in all_extraction_fields]
        total_fields += len(src_fields)
        resolved_fields += len(resolved)
        if unresolved:
            field_results[sid] = {"resolved": resolved, "unresolved": unresolved}

    section_coverage = 1.0 - len(missing_from_rules) / max(len(template_ids), 1)
    field_resolution = resolved_fields / max(total_fields, 1)

    return {
        "section_coverage": section_coverage,
        "template_sections": len(template_ids),
        "rule_sections": len(rule_ids),
        "missing_from_rules": sorted(missing_from_rules),
        "extra_in_rules": sorted(extra_in_rules),
        "field_resolution": field_resolution,
        "total_source_fields": total_fields,
        "resolved_source_fields": resolved_fields,
        "unresolved_by_section": field_results,
        "extraction_field_count": len(all_extraction_fields),
    }


def print_coverage(cov: dict[str, Any]):
    """Pretty-print coverage results."""
    console.print(f"\n[bold]Section Coverage: {cov['section_coverage']:.0%}[/bold] "
                  f"({cov['rule_sections']}/{cov['template_sections']} template sections have rules)")

    if cov["missing_from_rules"]:
        console.print(f"  [red]Missing ({len(cov['missing_from_rules'])}): {cov['missing_from_rules']}[/red]")
    else:
        console.print("  [green]All template sections covered![/green]")

    if cov["extra_in_rules"]:
        console.print(f"  [yellow]Extra: {cov['extra_in_rules']}[/yellow]")

    console.print(f"\n[bold]Field Resolution: {cov['field_resolution']:.0%}[/bold] "
                  f"({cov['resolved_source_fields']}/{cov['total_source_fields']} field IDs resolve in extractions)")

    if cov["unresolved_by_section"]:
        table = Table(title="Unresolved Fields by Section")
        table.add_column("Section", style="cyan", max_width=45)
        table.add_column("Unresolved", style="red")
        for sid, data in sorted(cov["unresolved_by_section"].items()):
            table.add_row(sid, ", ".join(data["unresolved"][:5]))
        console.print(table)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Repair report_rules.json")
    parser.add_argument("--coverage-only", action="store_true", help="Just report coverage, don't modify")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without saving")
    args = parser.parse_args()

    # Load source data
    console.print("[bold]Loading source data...[/bold]")

    rules_data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    rules = rules_data.get("sections", [])
    console.print(f"  Rules: {len(rules)} sections")

    template_data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    template_sections = template_data.get("sections", [])
    template_order = template_data.get("section_order", [])
    console.print(f"  Template: {len(template_sections)} sections")

    narrative_map: dict[str, dict] = {}
    if NARRATIVE_PATH.exists():
        np_data = json.loads(NARRATIVE_PATH.read_text(encoding="utf-8"))
        for p in np_data.get("patterns", []):
            narrative_map[p["section_id"]] = p
        console.print(f"  Narrative patterns: {len(narrative_map)}")

    # Coverage check (before repair)
    if args.coverage_only:
        cov = run_coverage_check(rules, template_sections, CONDENSED_DIR)
        print_coverage(cov)
        return

    # ── Step 1: Add missing sections ─────────────────────────────────────
    console.print("\n[bold]Step 1: Adding missing sections[/bold]")
    existing_ids = {r["section_id"] for r in rules}
    new_sections = _build_missing_sections(template_sections, narrative_map)

    added = 0
    for ns in new_sections:
        if ns["section_id"] not in existing_ids:
            rules.append(ns)
            existing_ids.add(ns["section_id"])
            added += 1
            console.print(f"  [green]+ {ns['section_id']}[/green] ({ns['content_type']})")
        else:
            console.print(f"  [dim]  {ns['section_id']} already exists[/dim]")
    console.print(f"  Added {added} new sections")

    # ── Step 2: Sanitize patient names ───────────────────────────────────
    console.print("\n[bold]Step 2: Sanitizing patient names[/bold]")
    name_patterns = _build_name_patterns()
    sanitize_count = sanitize_rules(rules, name_patterns)
    console.print(f"  Sanitized {sanitize_count} example fields")

    # ── Step 3: Set max_tokens ───────────────────────────────────────────
    console.print("\n[bold]Step 3: Setting per-section max_tokens[/bold]")
    tokens_changed = 0
    for rule in rules:
        sid = rule["section_id"]
        if sid in MAX_TOKENS_MAP:
            old = rule.get("max_tokens", 500)
            new = MAX_TOKENS_MAP[sid]
            if old != new:
                rule["max_tokens"] = new
                tokens_changed += 1
                console.print(f"  {sid}: {old} -> {new}")
    console.print(f"  Updated {tokens_changed} sections")

    # ── Step 4: Reorder by template_definition ───────────────────────────
    console.print("\n[bold]Step 4: Reordering sections by template[/bold]")
    order_map = {sid: idx for idx, sid in enumerate(template_order)}
    rules.sort(key=lambda r: order_map.get(r["section_id"], 999))
    for i, rule in enumerate(rules):
        rule["ordering"] = i
    console.print(f"  Reordered {len(rules)} sections")

    # ── Step 5: Coverage check (after repair) ────────────────────────────
    console.print("\n[bold]Step 5: Coverage check[/bold]")
    cov = run_coverage_check(rules, template_sections, CONDENSED_DIR)
    print_coverage(cov)

    # ── Save ─────────────────────────────────────────────────────────────
    if args.dry_run:
        console.print("\n[yellow]Dry run -- no files modified[/yellow]")
        return

    rules_data["sections"] = rules
    RULES_PATH.write_text(
        json.dumps(rules_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.print(f"\n[green bold]Saved {len(rules)} sections -> {RULES_PATH}[/green bold]")


if __name__ == "__main__":
    main()
