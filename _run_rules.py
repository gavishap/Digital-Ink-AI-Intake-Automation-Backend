"""Run Phase 4: Rule generation from correlations + patterns."""
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(".env")

from report_learning.rules.rule_generator import generate_from_files

SCANNED_DIR = Path("report_learning/outputs/scanned")
CORRELATIONS_DIR = Path("report_learning/outputs/correlations")
CONDENSED_DIR = Path("report_learning/outputs/extractions_v2/condensed")
PATTERNS_PATH = CORRELATIONS_DIR / "cross_report_patterns.json"
OUTPUT_PATH = Path("report_learning/outputs/rules/report_rules.json")

start = time.time()
print(f"Patterns: {PATTERNS_PATH}")
print(f"Reports: {SCANNED_DIR}")
print(f"Correlations: {CORRELATIONS_DIR}")
print(f"Extractions: {CONDENSED_DIR}")
print(f"Output: {OUTPUT_PATH}")

rules = generate_from_files(
    patterns_path=PATTERNS_PATH,
    reports_dir=SCANNED_DIR,
    correlations_dir=CORRELATIONS_DIR,
    extractions_dir=CONDENSED_DIR,
    output_path=OUTPUT_PATH,
)

elapsed = time.time() - start
print(f"\nDone in {elapsed:.0f}s")
print(f"  Sections: {len(rules.sections)}")
print(f"  Glossary: {len(rules.field_id_glossary)} entries")
print(f"  Notes: {rules.generation_notes[:200] if rules.generation_notes else 'none'}")
