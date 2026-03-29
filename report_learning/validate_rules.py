"""
Validate report_rules.json against training reports.

Scans training .doc files (preferring cached JSON when available),
cross-references section definitions, checks field correlations,
and performs static boilerplate parity analysis.

Usage:
    python -m report_learning.validate_rules [--force-rescan] [--min-length 80] [--threshold 1.0]
"""

import json
import re
import sys
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(highlight=False)

MODULE_ROOT = Path(__file__).parent
TRAINING_DIR = MODULE_ROOT / "training_data" / "reports"
SCANNED_DIR = MODULE_ROOT / "outputs" / "scanned"
E2E_SCAN_DIR = MODULE_ROOT / "outputs" / "e2e_test" / "stage7_ground_truth_scan"
RULES_PATH = MODULE_ROOT / "outputs" / "rules" / "report_rules.json"

GENERATOR_PATH = (
    MODULE_ROOT.parent / "src" / "generators" / "clinical_report_generator.py"
)

_COVER_SECTION_IDS = frozenset({
    "initial_report_in_the_field_of",
    "and_request_for_authorization",
})


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def _load_rules() -> dict[str, Any]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _load_scanned_json(stem: str) -> dict | None:
    """Try to load a cached scan JSON for a given report stem."""
    for directory in (SCANNED_DIR, E2E_SCAN_DIR):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.suffix == ".json" and stem in path.stem:
                return json.loads(path.read_text(encoding="utf-8"))
    return None


def _scan_doc_file(doc_path: Path) -> dict | None:
    """Scan a .doc file using docx_parser and return as dict."""
    try:
        from report_learning.scanner.docx_parser import parse_docx
    except ImportError:
        from scanner.docx_parser import parse_docx

    try:
        report = parse_docx(doc_path)
        return json.loads(report.model_dump_json())
    except Exception as e:
        console.print(f"  [red]Failed to scan {doc_path.name}: {e}[/red]")
        return None


def _load_or_scan(doc_path: Path, force_rescan: bool = False) -> dict | None:
    """Load cached scan or scan the doc file."""
    stem = doc_path.stem
    if not force_rescan:
        cached = _load_scanned_json(stem)
        if cached:
            return cached
    return _scan_doc_file(doc_path)


def _collect_training_docs() -> list[Path]:
    """Gather all .doc/.docx training files."""
    docs = []
    for ext in ("*.doc", "*.docx"):
        docs.extend(TRAINING_DIR.rglob(ext))
    return sorted(p for p in docs if not p.name.startswith("~$"))


def _normalize(text: str) -> str:
    """Collapse whitespace, normalize smart quotes, and lowercase for comparison."""
    t = text.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", t.strip()).lower()


def _text_hash(text: str) -> str:
    return sha256(_normalize(text).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Generator constant extraction
# ---------------------------------------------------------------------------

def _extract_generator_constants() -> dict[str, str]:
    """Read clinical_report_generator.py and extract _LEGAL_* / _PREAMBLE_* constants."""
    constants: dict[str, str] = {}
    if not GENERATOR_PATH.exists():
        return constants

    try:
        src = GENERATOR_PATH.read_text(encoding="utf-8")
    except Exception:
        return constants

    pattern = re.compile(
        r'^(_(?:LEGAL|PREAMBLE)_\w+)\s*=\s*\(\s*((?:"[^"]*"\s*)+)\)',
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(src):
        name = m.group(1)
        raw_parts = re.findall(r'"([^"]*)"', m.group(2))
        value = "".join(raw_parts)
        constants[name] = value

    return constants


def _strip_template_placeholders(text: str) -> list[str]:
    """Split a constant around {placeholders}, returning the literal segments."""
    segments = re.split(r"\{[^}]+\}", text)
    return [s for s in segments if len(s.strip()) > 20]


# ---------------------------------------------------------------------------
# Rules helpers
# ---------------------------------------------------------------------------

def _collect_rules_static_text(rules: dict) -> dict[str, list[str]]:
    """Collect all static text from rules, keyed by section_id."""
    result: dict[str, list[str]] = {}
    for sec in rules.get("sections", []):
        sid = sec.get("section_id", "")
        texts = []
        sc = sec.get("static_content")
        if sc and isinstance(sc, str) and len(sc.strip()) > 30:
            texts.append(sc.strip())
        tmpl = sec.get("template")
        if tmpl and isinstance(tmpl, str):
            for line in tmpl.split("\n"):
                clean = re.sub(r"\{[^}]+\}", "", line).strip()
                if len(clean) > 60:
                    texts.append(clean)
        for child in sec.get("child_sections", []):
            child_sc = child.get("static_content")
            if child_sc and isinstance(child_sc, str) and len(child_sc.strip()) > 30:
                texts.append(child_sc.strip())
        if texts:
            result[sid] = texts
    return result


# ---------------------------------------------------------------------------
# Pass 1: Section alignment
# ---------------------------------------------------------------------------

def _validate_section_alignment(
    scanned_reports: list[dict],
    rules: dict,
) -> list[dict]:
    """Cross-reference sections between training reports and rules."""
    findings: list[dict] = []
    rules_sections = {s["section_id"]: s for s in rules.get("sections", [])}
    rules_ids = set(rules_sections.keys())

    all_seen_ids: set[str] = set()

    for report in scanned_reports:
        filename = report.get("filename", "?")
        occurrence_count: dict[str, int] = {}

        for section in report.get("sections", []):
            sid = section.get("id", "")
            idx = occurrence_count.get(sid, 0)
            occurrence_count[sid] = idx + 1
            all_seen_ids.add(sid)

            rule = rules_sections.get(sid)
            if not rule:
                findings.append({
                    "type": "section_not_in_rules",
                    "file": filename,
                    "section_id": sid,
                    "heading": section.get("heading", ""),
                    "occurrence": idx,
                })
                continue

            _validate_occurrence(findings, rule, section, filename, idx)
            _validate_content_type(findings, rule, section, filename)

        for sid in occurrence_count:
            if sid in _COVER_SECTION_IDS and occurrence_count[sid] < 2:
                findings.append({
                    "type": "missing_preamble_occurrence",
                    "file": filename,
                    "section_id": sid,
                    "occurrences_found": occurrence_count[sid],
                    "expected": 2,
                })

    for sid in rules_ids - all_seen_ids:
        findings.append({
            "type": "rule_not_in_training",
            "section_id": sid,
            "title": rules_sections[sid].get("title", ""),
        })

    return findings


def _validate_occurrence(
    findings: list[dict],
    rule: dict,
    section: dict,
    filename: str,
    occurrence: int,
) -> None:
    """Validate a specific section occurrence (cover vs preamble for duplicate IDs)."""
    sid = section.get("id", "")
    if sid not in _COVER_SECTION_IDS:
        return

    elements_text = " ".join(
        el.get("text", "") for el in section.get("elements", [])
    )
    norm_text = _normalize(elements_text)

    if occurrence == 1:
        disclaimer_norm = _normalize(
            "THIS IS AN EXAMINATION REPORT. THIS REPORT WILL BE INCORPORATED"
        )
        if disclaimer_norm not in norm_text and len(norm_text) > 50:
            findings.append({
                "type": "preamble_missing_disclaimer",
                "file": filename,
                "section_id": sid,
                "occurrence": occurrence,
                "hint": "Second occurrence should contain the preamble disclaimer text",
            })


def _validate_content_type(
    findings: list[dict],
    rule: dict,
    section: dict,
    filename: str,
) -> None:
    """Check if rule content_type matches what appears in the training section."""
    content_type = rule.get("content_type", "")
    elements = section.get("elements", [])
    if not elements:
        return

    texts = [el.get("text", "") for el in elements if el.get("text", "").strip()]
    if not texts:
        return

    unique_texts = set(_normalize(t) for t in texts)

    if content_type == "narrative" and len(unique_texts) == 1 and len(texts) > 0:
        single = texts[0]
        if len(single) > 80:
            findings.append({
                "type": "possible_misclassified_static",
                "file": filename,
                "section_id": rule.get("section_id", ""),
                "content_type": content_type,
                "hint": "Section has identical long text across elements; may be static_text",
            })


# ---------------------------------------------------------------------------
# Pass 2: Source field correlation
# ---------------------------------------------------------------------------

def _validate_source_fields(
    scanned_reports: list[dict],
    rules: dict,
) -> list[dict]:
    """Check if source_field_ids correlate with section content."""
    findings: list[dict] = []

    for sec_rule in rules.get("sections", []):
        source_ids = sec_rule.get("source_field_ids", [])
        if not source_ids:
            continue

        sid = sec_rule.get("section_id", "")
        content_type = sec_rule.get("content_type", "")

        if content_type in ("static_text",):
            if source_ids:
                findings.append({
                    "type": "static_with_source_fields",
                    "section_id": sid,
                    "source_field_ids": source_ids,
                    "hint": "Static sections should not reference source_field_ids",
                })

    return findings


# ---------------------------------------------------------------------------
# Pass 3: Static boilerplate parity
# ---------------------------------------------------------------------------

def _extract_paragraphs_by_section(
    report: dict,
    min_length: int = 80,
) -> dict[tuple[str, int], list[str]]:
    """Extract long paragraphs keyed by (section_id, occurrence_index)."""
    result: dict[tuple[str, int], list[str]] = defaultdict(list)
    occurrence_count: dict[str, int] = {}

    for section in report.get("sections", []):
        sid = section.get("id", "")
        idx = occurrence_count.get(sid, 0)
        occurrence_count[sid] = idx + 1

        for el in section.get("elements", []):
            text = el.get("text", "").strip()
            if len(text) >= min_length:
                result[(sid, idx)].append(text)

    return dict(result)


def _run_boilerplate_parity(
    scanned_reports: list[dict],
    rules: dict,
    generator_constants: dict[str, str],
    min_length: int = 80,
    threshold: float = 1.0,
) -> list[dict]:
    """Fingerprint static paragraphs and compare to rules + generator constants."""
    findings: list[dict] = []
    n_reports = len(scanned_reports)
    if n_reports == 0:
        return findings

    min_count = max(1, int(n_reports * threshold))

    paragraph_registry: dict[str, dict] = {}

    for report in scanned_reports:
        filename = report.get("filename", "?")
        paragraphs_by_section = _extract_paragraphs_by_section(report, min_length)

        seen_hashes: set[str] = set()
        for (sid, occ_idx), texts in paragraphs_by_section.items():
            for text in texts:
                h = _text_hash(text)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)

                if h not in paragraph_registry:
                    paragraph_registry[h] = {
                        "text_preview": text[:120],
                        "full_text": text,
                        "normalized": _normalize(text),
                        "section_id": sid,
                        "occurrence_index": occ_idx,
                        "files": set(),
                    }
                paragraph_registry[h]["files"].add(filename)

    rules_static = _collect_rules_static_text(rules)
    all_rules_text_norm = []
    for texts in rules_static.values():
        for t in texts:
            all_rules_text_norm.append(_normalize(t))

    all_gen_text_norm = {
        name: _normalize(val) for name, val in generator_constants.items()
    }

    static_candidates = {
        h: info for h, info in paragraph_registry.items()
        if len(info["files"]) >= min_count
    }

    for h, info in static_candidates.items():
        norm = info["normalized"]
        sid = info["section_id"]
        occ = info["occurrence_index"]

        found_in_rules = any(
            norm in rt or rt in norm for rt in all_rules_text_norm
        )
        found_in_generator = any(
            norm in gn or gn in norm for gn in all_gen_text_norm.values()
        )

        if not found_in_rules and not found_in_generator:
            if sid in _COVER_SECTION_IDS and occ == 0:
                continue

            findings.append({
                "type": "orphan_boilerplate",
                "section_id": sid,
                "occurrence_index": occ,
                "file_count": len(info["files"]),
                "text_preview": info["text_preview"],
                "hint": "Static text in training but not in rules or generator constants",
            })

    for name, val in generator_constants.items():
        if name == "_LEGAL_DEMAND_BOX":
            continue

        segments = _strip_template_placeholders(val)
        gen_norm = _normalize(val)
        found = False

        for info in paragraph_registry.values():
            pnorm = info["normalized"]
            if gen_norm in pnorm or pnorm in gen_norm:
                found = True
                break
            if segments and all(_normalize(seg) in pnorm for seg in segments):
                found = True
                break

        if not found:
            findings.append({
                "type": "dead_constant",
                "constant_name": name,
                "text_preview": val[:120],
                "hint": "Generator constant never appears in any training report scan "
                        "(may be correct if in text box not visible to scanner)",
            })

    findings.append({
        "type": "known_limitation",
        "message": (
            "Cover-page legal demand text box is not visible to docx_parser. "
            "_LEGAL_DEMAND_BOX content must be verified manually against training "
            "report images or by opening in Word."
        ),
    })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_validation(
    force_rescan: bool = False,
    min_length: int = 80,
    threshold: float = 1.0,
) -> dict[str, Any]:
    """Run all validation passes and return structured results."""
    console.print(Panel("[bold]Report Rules Validation[/bold]", expand=False))

    rules = _load_rules()
    console.print(f"  Loaded {len(rules.get('sections', []))} rule sections")

    training_docs = _collect_training_docs()
    console.print(f"  Found {len(training_docs)} training documents")

    scanned_reports: list[dict] = []
    for doc_path in training_docs:
        console.print(f"  Loading [cyan]{doc_path.name}[/cyan]...")
        report = _load_or_scan(doc_path, force_rescan)
        if report:
            scanned_reports.append(report)

    console.print(f"  Successfully loaded {len(scanned_reports)} reports\n")

    # Pass 1: Section alignment
    console.print("[bold]Pass 1: Section Alignment[/bold]")
    alignment_findings = _validate_section_alignment(scanned_reports, rules)
    console.print(f"  {len(alignment_findings)} findings\n")

    # Pass 2: Source field correlation
    console.print("[bold]Pass 2: Source Field Correlation[/bold]")
    field_findings = _validate_source_fields(scanned_reports, rules)
    console.print(f"  {len(field_findings)} findings\n")

    # Pass 3: Static boilerplate parity
    console.print("[bold]Pass 3: Static Boilerplate Parity[/bold]")
    generator_constants = _extract_generator_constants()
    console.print(f"  Found {len(generator_constants)} generator constants")
    boilerplate_findings = _run_boilerplate_parity(
        scanned_reports, rules, generator_constants, min_length, threshold,
    )
    console.print(f"  {len(boilerplate_findings)} findings\n")

    all_findings = alignment_findings + field_findings + boilerplate_findings

    results = {
        "total_training_reports": len(scanned_reports),
        "total_rule_sections": len(rules.get("sections", [])),
        "total_findings": len(all_findings),
        "findings_by_type": _group_by_type(all_findings),
        "findings": all_findings,
    }

    _print_summary(results)
    return results


def _group_by_type(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for f in findings:
        counts[f.get("type", "unknown")] += 1
    return dict(counts)


def _print_summary(results: dict) -> None:
    console.print(Panel("[bold]Validation Summary[/bold]", expand=False))

    table = Table(title="Findings by Type")
    table.add_column("Type", style="cyan")
    table.add_column("Count", justify="right", style="bold")
    for ftype, count in sorted(results["findings_by_type"].items()):
        table.add_row(ftype, str(count))
    console.print(table)

    for finding in results["findings"]:
        ftype = finding.get("type", "")
        if ftype == "known_limitation":
            console.print(f"  [yellow]KNOWN LIMITATION:[/yellow] {finding['message']}")
        elif ftype == "orphan_boilerplate":
            console.print(
                f"  [red]ORPHAN:[/red] [{finding['section_id']} occ {finding['occurrence_index']}] "
                f"({finding['file_count']} files) {finding['text_preview'][:80]}..."
            )
        elif ftype == "dead_constant":
            console.print(
                f"  [yellow]DEAD?:[/yellow] {finding['constant_name']} -- "
                f"{finding['text_preview'][:80]}..."
            )
        elif ftype == "section_not_in_rules":
            console.print(
                f"  [red]NO RULE:[/red] {finding['file']} >> "
                f"{finding['section_id']} (occ {finding['occurrence']}) "
                f"'{finding['heading']}'"
            )
        elif ftype == "rule_not_in_training":
            console.print(
                f"  [yellow]UNUSED RULE:[/yellow] {finding['section_id']} -- "
                f"{finding['title']}"
            )
        elif ftype == "preamble_missing_disclaimer":
            console.print(
                f"  [red]PREAMBLE:[/red] {finding['file']} → "
                f"{finding['section_id']} occ {finding['occurrence']} "
                f"missing disclaimer text"
            )
        elif ftype == "static_with_source_fields":
            console.print(
                f"  [yellow]STATIC+FIELDS:[/yellow] {finding['section_id']} has "
                f"source_field_ids but is content_type=static_text"
            )
        elif ftype in ("possible_misclassified_static", "missing_preamble_occurrence"):
            console.print(f"  [yellow]{ftype.upper()}:[/yellow] {json.dumps(finding, default=str)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate report_rules.json against training data")
    parser.add_argument("--force-rescan", action="store_true", help="Re-scan .doc files even if cached JSON exists")
    parser.add_argument("--min-length", type=int, default=80, help="Minimum paragraph length for boilerplate detection")
    parser.add_argument("--threshold", type=float, default=1.0, help="Fraction of reports a paragraph must appear in (0.0-1.0)")
    parser.add_argument("--output", type=str, default=None, help="Write JSON results to this path")
    args = parser.parse_args()

    results = run_validation(
        force_rescan=args.force_rescan,
        min_length=args.min_length,
        threshold=args.threshold,
    )

    if args.output:
        out_path = Path(args.output)
        serializable = json.loads(json.dumps(results, default=lambda o: list(o) if isinstance(o, set) else str(o)))
        out_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        console.print(f"\n[green]Results written to {out_path}[/green]")


if __name__ == "__main__":
    main()
