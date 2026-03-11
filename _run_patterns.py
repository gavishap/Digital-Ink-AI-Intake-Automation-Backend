"""Run pattern analysis on completed correlations."""
import json
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(".env")

from report_learning.correlator.pattern_analyzer import analyse_from_files

CORRELATIONS_DIR = Path("report_learning/outputs/correlations")
PATTERNS_PATH = CORRELATIONS_DIR / "cross_report_patterns.json"

start = time.time()
print(f"Loading correlations from {CORRELATIONS_DIR}")
patterns = analyse_from_files(CORRELATIONS_DIR, PATTERNS_PATH)

elapsed = time.time() - start
print(f"\nDone in {elapsed/60:.1f} min")
print(f"Sections: {len(patterns.section_patterns)}")
print(f"Universal: {len(patterns.universal_sections)}")
print(f"Conditional: {len(patterns.conditional_sections)}")
