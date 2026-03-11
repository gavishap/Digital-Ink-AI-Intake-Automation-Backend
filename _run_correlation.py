"""Run full correlation pipeline: 31 pairs (parallel) + cross-report pattern analysis."""
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(".env")

from report_learning.correlator.field_mapper import correlate_all_pairs, CLAUDE_MODEL, MAX_PARALLEL
from report_learning.correlator.pattern_analyzer import analyse_patterns

SCANNED_DIR = Path("report_learning/outputs/scanned")
CONDENSED_DIR = Path("report_learning/outputs/extractions_v2/condensed")
LAWYER_DIR = Path("report_learning/outputs/extractions_v2/lawyer")
CORRELATIONS_DIR = Path("report_learning/outputs/correlations")

start = time.time()
print(f"Model: {CLAUDE_MODEL} | Parallel: {MAX_PARALLEL}")
print(f"Reports: {SCANNED_DIR} | Extractions: {CONDENSED_DIR}")
print(f"Output: {CORRELATIONS_DIR}")
sys.stdout.flush()

correlations = correlate_all_pairs(
    reports_dir=SCANNED_DIR,
    extractions_dir=CONDENSED_DIR,
    output_dir=CORRELATIONS_DIR,
    lawyer_dir=LAWYER_DIR,
    skip_existing=True,
    parallel=MAX_PARALLEL,
)

elapsed = time.time() - start
print(f"\n=== Per-pair done: {len(correlations)} pairs in {elapsed/60:.1f} min ===")
sys.stdout.flush()

if correlations:
    print("\nStarting cross-report pattern analysis...")
    sys.stdout.flush()
    patterns = analyse_patterns(correlations)
    patterns_path = CORRELATIONS_DIR / "cross_report_patterns.json"
    patterns_path.write_text(patterns.model_dump_json(indent=2), encoding="utf-8")

    total = time.time() - start
    print(f"\n=== COMPLETE: {len(correlations)} pairs + patterns in {total/60:.1f} min ===")
    print(f"  Sections: {len(patterns.section_patterns)}")
    print(f"  Universal: {len(patterns.universal_sections)}")
    print(f"  Conditional: {len(patterns.conditional_sections)}")
else:
    print("No correlations produced!")
