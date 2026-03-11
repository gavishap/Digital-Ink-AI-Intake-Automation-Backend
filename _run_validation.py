"""Run Phase 5: Validate rules against known reports + suggest refinements."""
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(".env")

from report_learning.rules.rule_validator import validate_all

RULES_PATH = Path("report_learning/outputs/rules/report_rules.json")
SCANNED_DIR = Path("report_learning/outputs/scanned")
CONDENSED_DIR = Path("report_learning/outputs/extractions_v2/condensed")
OUTPUT_PATH = Path("report_learning/outputs/rules/validation_scores.json")

start = time.time()
print(f"Rules: {RULES_PATH}")
print(f"Reports: {SCANNED_DIR}")
print(f"Extractions: {CONDENSED_DIR}")
print(f"Output: {OUTPUT_PATH}")

results = validate_all(
    rules_path=RULES_PATH,
    reports_dir=SCANNED_DIR,
    extractions_dir=CONDENSED_DIR,
    output_path=OUTPUT_PATH,
    parallel=3,
)

elapsed = time.time() - start
print(f"\nDone in {elapsed/60:.1f} min")
print(f"  Validated: {len(results)} reports")
if results:
    avg = sum(r.overall_score for r in results) / len(results)
    print(f"  Avg score: {avg:.0%}")
