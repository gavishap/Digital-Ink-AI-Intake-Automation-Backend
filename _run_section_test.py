"""Test single section generation. Usage: python _run_section_test.py <section_id> [patient_slug]"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "crg", str(Path(__file__).parent / "src" / "generators" / "clinical_report_generator.py")
)
crg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crg)

BASE = Path(__file__).parent
OUT_DIR = BASE / "report_learning" / "outputs" / "section_tests"
E2E_DIR = BASE / "report_learning" / "outputs" / "e2e_v2"

def main():
    section_id = sys.argv[1] if len(sys.argv) > 1 else "conclusion"
    slug = sys.argv[2] if len(sys.argv) > 2 else "bachar"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ext_path = E2E_DIR / "stage3_extraction" / slug / "extraction_combined.json"
    ctx_path = E2E_DIR / "stage2_context" / f"{slug}_patient_context.json"
    extraction_data = json.loads(ext_path.read_text(encoding="utf-8"))
    patient_context = json.loads(ctx_path.read_text(encoding="utf-8"))

    rules = crg._load_rules()
    sec_rule = None
    for s in rules.get("sections", []):
        if s.get("section_id") == section_id:
            sec_rule = s
            break
    if not sec_rule:
        print(f"Section '{section_id}' not found in rules")
        return

    all_fields = crg._flatten_all_fields(extraction_data.get("pages", []))
    field_map = crg._FIELD_MAP
    patient_name = extraction_data.get("patient_name", "Patient")
    derived = crg._derive_fields(all_fields, field_map, patient_name, patient_context)
    llm_clients = crg._build_llm_clients()

    source_ids = sec_rule.get("source_field_ids", [])
    resolved = {}
    for fid in source_ids:
        val = crg._resolve_field(fid, all_fields, derived, field_map)
        if val is not None:
            resolved[fid] = str(val)

    print(f"Section: {section_id} | Patient: {slug}")
    print(f"Content type: {sec_rule.get('content_type')}")
    print(f"Source fields: {len(source_ids)} | Resolved: {len(resolved)}/{len(source_ids)}")
    print(f"Min required: {sec_rule.get('min_required_fields', 1)}")
    print(f"Has hybrid: {bool(sec_rule.get('hybrid_template'))}")
    print(f"Temperature: {sec_rule.get('temperature', 0.3)}")
    print(f"\nResolved fields:")
    for fid, val in resolved.items():
        print(f"  {fid} = {val[:80]}")
    print()

    slog = {}
    t0 = time.time()
    if sec_rule.get("hybrid_template"):
        text = crg._generate_hybrid(sec_rule, all_fields, derived, field_map, patient_name, llm_clients, _log=slog)
    else:
        text = crg._generate_narrative(sec_rule, all_fields, derived, field_map, patient_name, llm_clients, _log=slog)

    if text:
        hybrid_tmpl = sec_rule.get("hybrid_template") or ""
        is_pure_hybrid = hybrid_tmpl and "[BRIDGE:" not in hybrid_tmpl
        skip_verify = sec_rule.get("skip_verification", False)
        if is_pure_hybrid or skip_verify:
            verified_text = text
        else:
            relevant = {fid: str(v) for fid in source_ids
                        if (v := crg._resolve_field(fid, all_fields, derived, field_map)) is not None}
            verified_text = crg._verify_narrative(text, relevant, sec_rule.get("title", ""), llm_clients, _log=slog)
    else:
        verified_text = ""
    elapsed = time.time() - t0

    print(f"Generation log: {json.dumps(slog, indent=2)}")
    print(f"\n{'='*60}")
    print(f"GENERATED TEXT ({len(text)} chars):")
    print(f"{'='*60}")
    print(text or "[EMPTY]")
    print(f"\n{'='*60}")
    print(f"AFTER VERIFICATION ({len(verified_text)} chars):")
    print(f"{'='*60}")
    print(verified_text or "[EMPTY]")
    print(f"\nTime: {elapsed:.1f}s")

    result = {
        "section_id": section_id, "patient": slug,
        "generated_text": text, "verified_text": verified_text,
        "generation_log": slog, "resolved_fields": resolved,
        "elapsed": round(elapsed, 1),
    }
    out_path = OUT_DIR / f"{section_id}_{slug}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out_path}")

if __name__ == "__main__":
    main()
