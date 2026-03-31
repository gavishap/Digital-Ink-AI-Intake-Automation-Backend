"""
Fix V2 Rules -> V3: Ground dead source_field_ids, fix broken conditions,
then LLM-improve prompts/few-shots based on comparison faults.

Run from: c:/Digital_Ink/form-extractor
Usage:    python _fix_rules_v3.py
"""
from __future__ import annotations
import json, os, re, sys, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from rich.console import Console
from rich.table import Table

console = Console(record=True)
BASE = Path(__file__).parent
RULES_PATH = BASE / "report_learning" / "outputs" / "rules" / "report_rules.json"
V1_PATH = BASE / "report_learning" / "outputs" / "rules" / "report_rules_v1.json"
SCHEMA_PATH = BASE / "templates" / "orofacial_exam_schema.json"
E2E_DIR = BASE / "report_learning" / "outputs" / "e2e_v2"
E2E_BACKUP = BASE / "report_learning" / "outputs" / "e2e_v2_backup"
OUT_DIR = BASE / "report_learning" / "outputs" / "fix_v3"
TEMPLATE_DEF_PATH = BASE / "report_learning" / "outputs" / "rules" / "template_definition.json"

TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
TOGETHER_BASE_URL = "https://api.together.xyz/v1"

# Programmatic mapping for dead fields -> correct schema field or None (remove)
FIELD_FIXES = {
    # Wrong page prefix / wrong name -> correct schema field
    "p9_hand_dominance": "p4_hand_dominance",
    "p17_r19_6_halitosis": "p17_g51_0_halitosis",
    "p7_tx_received_physical_therapy": "p8_tx_received",
    "p7_tx_received_chiropractic_manipulations": "p8_tx_received",
    "p7_tx_received_acupuncture": "p8_tx_received",
    "p14_mandible_deviation_opening": "p14_jaw_deviation_opening",
    "p14_mandible_deviation_closing": "p14_jaw_deviation_closing",
    "p14_right_condylar_head_vas": "p14_right_via_eam_vas",
    "p14_left_condylar_head_vas": "p14_left_via_eam_vas",
    "p14_sternocleidomastoid_right_y_n": "p14_multiple_tender_points",
    "p14_sternocleidomastoid_left_y_n": "p14_multiple_tender_points",
    "p16_max_newtons": "Diagnostic_Bite_Force_Analysis_Left",
    "p15_bleeding_gingiva": "p15_bleeding_gums",
    "p15_decay": "p15_visually_apparent_decayed_teeth",
    "p15_fractured_denture": "p15_fractured_dentures",
    "p15_fractured_tooth": "p15_fractured_teeth",
    "p15_mobile_tooth": "p15_teeth_mobility",
    "p15_openbite": "p15_open_bite",
    "p15_recession": "p15_gum_recession_teeth",
    "p15_sensitive_to_percussion": "p15_teeth_sensitive_percussion",
    "p15_tori": "p15_tori_location",
    "p15_unstable_bite": "p15_crossbite",
    "p15_midline_deviation_direction": "p15_midline_deviation",
    "p9_dentist_office_name": "p9_dentist_1_name",
    "p9_dentist_office_phone": "p9_dentist_1_phone",
    "p3_breathing_problems": "p1_breathing_problems",
    "p3_breathing_problems_types": "p1_breathing_problems_types",
    # Long epworth names -> canonical
    "epworth_sleepiness_scale_sitting_and_reading": "p11_epworth_sitting_reading",
    "epworth_sleepiness_scale_watching_tv": "p11_epworth_watching_tv",
    "epworth_sleepiness_scale_sitting_inactive_in_a_public_place": "p11_epworth_sitting_inactive",
    "epworth_sleepiness_scale_as_a_passenger_in_a_motor_vehicle_for_an_hour_or_more": "p11_epworth_passenger_car",
    "epworth_sleepiness_scale_lying_down_in_the_afternoon": "p11_epworth_lying_down_afternoon",
    "epworth_sleepiness_scale_sitting_and_talking_to_someone": "p11_epworth_sitting_talking",
    "epworth_sleepiness_scale_sitting_quietly_after_lunch_no_alcohol": "p11_epworth_sitting_after_lunch",
    "epworth_sleepiness_scale_stopped_for_a_few_minutes_in_traffic_while_driving": "p11_epworth_car_traffic",
    "epworth_sleepiness_scale_total_score": "p11_epworth_total_score",
    # Pain/interference fields -> closest schema
    "p10_face_pain_aggravating_factors": "p12_concentration_interference",
    "p10_face_pain_interfering_factors": "p12_social_activities_interference",
    "p10_oral_hygiene_impact": "p4_hand_dominance",
    "p11_weight_gain": "p10_weight_loss_lbs",
    "p12_industrial_medications": "p1_current_medications",
    "p8_pain_severity_ratings": "p10_left_face_pain_severity",
    "tmj_pain_frequency": "p10_left_tmj_pain_severity",
    "tmj_pain_intensity": "p10_right_tmj_pain_severity",
    # Condition field fixes
    "reviewed_medical_records": None,
    "review_of_records_available": None,
    "medical_records_review": None,
    "medications_taken_on_industrial_basis": "p1_current_medications",
    # Derived fields -> remove (auto-available via _derive_fields)
    "patient_last_name": None, "patient_title": None, "patient_first_name": None,
    "patient_gender": None, "patient_sex": None, "he_she": None, "his_her": None,
    "exam_date": None, "venue": None, "case_number": None,
    "patient_city": None, "patient_state": None, "patient_zip": None,
    "ann_claim_number": None,
    # Examiner fields -> remove (not form data)
    "examiner_name": None, "examiner_credentials": None,
    "examiner_license_number": None, "examiner_phone": None,
    "examiner_fax": None, "examiner_address": None,
    # Invented descriptive names -> remove
    "Patient_self_reported_clenching_behaviors": None,
    "Patient_stress_reports": None,
    "Periodontal_examination_findings": None,
    "Pre_existing_risk_factors": None,
    "Saliva_examination_findings": None,
    "Upper_extremity_injury_details": None,
    "Halitosis_complaints": None,
    "radiographic_findings": None,
    "sEMG_test_results": None,
    "industrial_injury_history": None,
    "treatments_received_due_to_industrial_injury": None,
    "p1_last_name": None, "p1_title": None,
    "p1_date_of_birth": None,
    "p5_computer_equipment_use": None, "p5_workstation_ergonomics": None,
    "p5_presently_working_at_different_company": None,
    "tenderness_masseter_left": None, "tenderness_masseter_right": None,
    "tenderness_temporalis_left": None, "tenderness_temporalis_right": None,
}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _extract_json(text: str):
    text = re.sub(r"^```json\s*", "", text.strip())
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


def build_valid_universe():
    schema = _load_json(SCHEMA_PATH)
    schema_fields = set()
    for page in schema.get("pages", []):
        for sec in page.get("sections", []):
            for f in sec.get("fields", []):
                schema_fields.add(f["field_id"])
        for f in page.get("standalone_fields", []):
            schema_fields.add(f["field_id"])
    resolves = set()
    for slug in ["bachar", "lupercio", "rivera"]:
        fr_path = E2E_DIR / "stage4_report" / slug / "field_resolution.json"
        if fr_path.exists():
            fr = _load_json(fr_path)
            for k, v in fr.items():
                if v is not None:
                    resolves.add(k)
    return schema_fields | resolves


def get_section_frequency():
    freqs = {}
    if TEMPLATE_DEF_PATH.exists():
        td = _load_json(TEMPLATE_DEF_PATH)
        total = td.get("total_reports_analyzed", 32)
        for s in td.get("sections", []):
            pct = min(100, round(s.get("appears_in", total) / max(total, 1) * 100))
            freqs[s["id"]] = pct
    return freqs


def collect_comparison_faults(section_id):
    faults = []
    for base_dir in [E2E_DIR, E2E_BACKUP]:
        for slug in ["bachar", "lupercio", "rivera"]:
            cmp_path = base_dir / "stage6_comparison" / slug / "comparison_summary.json"
            if not cmp_path.exists():
                continue
            label = "v2" if base_dir == E2E_DIR else "v1"
            for sec in _load_json(cmp_path):
                if sec.get("section_id") == section_id:
                    faults.append({
                        "patient": slug, "run": label,
                        "score": sec.get("overall_score", 0),
                        "hallucinations": sec.get("hallucinations", []),
                        "missing_data": sec.get("missing_data", []),
                        "generated_text": sec.get("generated_text", "")[:2000],
                        "ground_truth_text": sec.get("ground_truth_text", "")[:2000],
                        "root_cause": sec.get("root_cause_analysis", {}).get("primary_cause", ""),
                        "explanation": sec.get("root_cause_analysis", {}).get("explanation", ""),
                    })
    return faults


FAULT_FIX_PROMPT = """You are improving a clinical report section rule based on comparison failures.

SECTION: "{section_id}" ({content_type})

CURRENT GENERATION PROMPT:
{generation_prompt}

CURRENT FEW-SHOT EXAMPLES ({few_shot_count}):
{few_shot_summary}

{hybrid_section}

COMPARISON FAULTS (what went wrong across multiple patients and runs):
{faults_json}

Based on these faults, improve the rule. Focus on:
1. Fix the generation_prompt to prevent the specific hallucinations and missing data patterns seen above
2. Add explicit instructions for what NOT to invent (e.g. if faults show invented pulse rates, add "do not invent specific values")
3. Add explicit instructions for what MUST be included (e.g. if faults show missing citations, specify which citations)
4. Improve few_shot_examples to show 2-3 correct outputs that match the ground truth patterns
5. If hybrid_template exists, fix it based on the faults

Respond with ONLY valid JSON:
{{
    "generation_prompt": "<improved prompt text>",
    "few_shot_examples": [<2-3 improved examples with input_fields and output_text>],
    "hybrid_template": "<improved or null if not applicable>",
    "changes_made": ["list of specific changes and why"]
}}"""


def phase1_programmatic(rules):
    """Fix dead fields, broken conditions, cap min_required_fields."""
    valid = build_valid_universe()
    freqs = get_section_frequency()
    v1 = _load_json(V1_PATH) if V1_PATH.exists() else {"sections": []}
    v1_map = {s["section_id"]: s for s in v1["sections"]}

    stats = {"fields_fixed": 0, "fields_removed": 0, "conditions_fixed": 0, "min_capped": 0}

    for sec in rules["sections"]:
        sid = sec["section_id"]
        freq = freqs.get(sid, 100)
        is_universal = freq >= 80

        # Fix source_field_ids
        new_ids = []
        for fid in sec.get("source_field_ids", []):
            if fid in valid:
                new_ids.append(fid)
            elif fid in FIELD_FIXES:
                replacement = FIELD_FIXES[fid]
                if replacement and replacement not in new_ids:
                    new_ids.append(replacement)
                    stats["fields_fixed"] += 1
                else:
                    stats["fields_removed"] += 1
            else:
                stats["fields_removed"] += 1
        sec["source_field_ids"] = list(dict.fromkeys(new_ids))

        # Fix conditions
        v1_conds = v1_map.get(sid, {}).get("conditions", [])
        if is_universal and not v1_conds and sec.get("conditions"):
            console.print(f"  [yellow]{sid}: stripping {len(sec['conditions'])} invented conditions (universal)[/yellow]")
            sec["conditions"] = []
            stats["conditions_fixed"] += len(sec.get("conditions", []))

        valid_conds = []
        for c in sec.get("conditions", []):
            fid = c.get("field_id", "")
            if fid in FIELD_FIXES:
                replacement = FIELD_FIXES[fid]
                if replacement:
                    c["field_id"] = replacement
                    valid_conds.append(c)
                    stats["conditions_fixed"] += 1
                else:
                    stats["conditions_fixed"] += 1
            elif fid in valid:
                valid_conds.append(c)
            elif is_universal:
                stats["conditions_fixed"] += 1
            else:
                valid_conds.append(c)
        sec["conditions"] = valid_conds

        # Cap min_required_fields
        resolved_counts = []
        for slug in ["bachar", "lupercio", "rivera"]:
            fr_path = E2E_DIR / "stage4_report" / slug / "field_resolution.json"
            if not fr_path.exists():
                continue
            fr = _load_json(fr_path)
            count = sum(1 for fid in sec["source_field_ids"] if fr.get(fid) is not None)
            resolved_counts.append(count)
        if resolved_counts:
            min_res = min(resolved_counts)
            cur_min = sec.get("min_required_fields", 1)
            if cur_min > min_res and min_res > 0:
                sec["min_required_fields"] = max(1, min_res)
                stats["min_capped"] += 1

    return stats


def phase2_llm_fixes(rules, client, model):
    """LLM-improve prompts/few-shots for low-scoring sections."""
    fixed = 0
    for sec in rules["sections"]:
        sid = sec["section_id"]
        ct = sec.get("content_type", "")
        if ct in ("static_text", "table"):
            continue

        faults = collect_comparison_faults(sid)
        if not faults:
            continue

        v2_scores = [f["score"] for f in faults if f["run"] == "v2"]
        avg_score = sum(v2_scores) / max(len(v2_scores), 1)
        if avg_score >= 80:
            continue

        console.print(f"  [cyan]{sid}[/cyan] avg={avg_score:.0f} — running LLM fix...")

        hybrid_section = ""
        if sec.get("hybrid_template"):
            hybrid_section = f"CURRENT HYBRID TEMPLATE:\n{sec['hybrid_template'][:2000]}"

        few_shot_summary = json.dumps(sec.get("few_shot_examples", []), indent=1)[:2000]

        prompt = FAULT_FIX_PROMPT.format(
            section_id=sid, content_type=ct,
            generation_prompt=(sec.get("generation_prompt") or "")[:3000],
            few_shot_count=len(sec.get("few_shot_examples", [])),
            few_shot_summary=few_shot_summary,
            hybrid_section=hybrid_section,
            faults_json=json.dumps(faults, indent=1)[:8000],
        )

        for attempt in range(3):
            try:
                msgs = [{"role": "user", "content": prompt}]
                if attempt > 0:
                    msgs.append({"role": "user", "content": "Respond with ONLY valid JSON."})
                resp = client.chat.completions.create(
                    model=model, max_tokens=6000, temperature=0.1, messages=msgs,
                )
                raw = resp.choices[0].message.content.strip()
                parsed = _extract_json(raw)
                if parsed and "generation_prompt" in parsed:
                    if parsed.get("generation_prompt"):
                        sec["generation_prompt"] = parsed["generation_prompt"]
                    if parsed.get("few_shot_examples"):
                        sec["few_shot_examples"] = parsed["few_shot_examples"]
                    if parsed.get("hybrid_template") and sec.get("hybrid_template"):
                        sec["hybrid_template"] = parsed["hybrid_template"]
                    changes = parsed.get("changes_made", [])
                    console.print(f"    [green]Fixed: {len(changes)} changes[/green]")
                    _save_json(OUT_DIR / "per_section" / f"{sid}.json", {
                        "section_id": sid, "avg_score": avg_score,
                        "changes": changes, "faults_count": len(faults),
                    })
                    fixed += 1
                    break
            except Exception as e:
                console.print(f"    [dim]Attempt {attempt+1} failed: {e}[/dim]")

    return fixed


def main():
    console.print(f"\n{'='*60}")
    console.print("  FIX V2 RULES -> V3")
    console.print(f"{'='*60}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "per_section").mkdir(exist_ok=True)

    rules = _load_json(RULES_PATH)
    console.print(f"  Loaded V2 rules: {len(rules['sections'])} sections")

    # Phase 1
    console.print(f"\n--- PHASE 1: Programmatic Fixes ---")
    t0 = time.time()
    stats = phase1_programmatic(rules)
    console.print(f"  Fields fixed: {stats['fields_fixed']}")
    console.print(f"  Fields removed: {stats['fields_removed']}")
    console.print(f"  Conditions fixed: {stats['conditions_fixed']}")
    console.print(f"  Min capped: {stats['min_capped']}")
    console.print(f"  Phase 1 time: {time.time()-t0:.1f}s")

    # Phase 2
    console.print(f"\n--- PHASE 2: LLM Fault Corrections ---")
    key = os.getenv("TOGETHER_API_KEY")
    if not key:
        console.print("[red]No TOGETHER_API_KEY — skipping Phase 2[/red]")
        llm_fixed = 0
    else:
        client = OpenAI(api_key=key, base_url=TOGETHER_BASE_URL, timeout=120.0)
        t0 = time.time()
        llm_fixed = phase2_llm_fixes(rules, client, TOGETHER_MODEL)
        console.print(f"  LLM fixed: {llm_fixed} sections")
        console.print(f"  Phase 2 time: {time.time()-t0:.1f}s")

    # Save
    rules["version"] = "3.0"
    v3_path = BASE / "report_learning" / "outputs" / "rules" / "report_rules_v3.json"
    _save_json(v3_path, rules)
    console.print(f"\n  Saved: {v3_path}")

    _save_json(OUT_DIR / "fix_log.json", {
        "phase1": stats, "phase2_sections_fixed": llm_fixed,
    })

    # Summary table
    table = Table(title="V3 Rules Summary")
    table.add_column("Section", width=45)
    table.add_column("Fields", width=7)
    table.add_column("Min", width=5)
    table.add_column("Conds", width=6)
    for sec in rules["sections"]:
        if sec.get("content_type") == "static_text":
            continue
        table.add_row(
            sec["section_id"],
            str(len(sec.get("source_field_ids", []))),
            str(sec.get("min_required_fields", 1)),
            str(len(sec.get("conditions", []))),
        )
    console.print(table)

    log_path = OUT_DIR / "console_log.txt"
    log_path.write_text(console.export_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
