"""
Click CLI for the Report Learning Module.

Commands:
  scan             Parse all reports (slim output)
  diff             Cross-report diff to extract template
  extract          Run extraction pipeline on matching source forms
  correlate        Map extraction fields to report elements + analyse patterns
  generate-rules   Synthesise rules from correlations and patterns
  validate         Validate rules against known reports
  status           Show pipeline status
"""

import json
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

console = Console()

MODULE_ROOT = Path(__file__).parent
TRAINING_DATA = MODULE_ROOT / "training_data"
REPORTS_DIR = TRAINING_DATA / "reports"
FORMS_DIR = TRAINING_DATA / "source_forms"
OUTPUTS = MODULE_ROOT / "outputs"
SCANNED_DIR = OUTPUTS / "scanned"
CORRECTED_DIR = OUTPUTS / "corrected"
EXTRACTIONS_DIR = OUTPUTS / "extractions"
EXTRACTIONS_TRIMMED_DIR = OUTPUTS / "extractions_trimmed"
EXTRACTIONS_V2_DIR = OUTPUTS / "extractions_v2"
CONDENSED_DIR = OUTPUTS / "extractions_v2" / "condensed"
CORRELATIONS_DIR = OUTPUTS / "correlations"
RULES_DIR = OUTPUTS / "rules"


def _load_env():
    env_path = MODULE_ROOT.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@click.group()
def cli():
    """Report Learning Module -- learn report structure from examples."""
    _load_env()


# -- scan ------------------------------------------------------------------

@cli.command()
@click.option("--reports-dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Override reports directory")
def scan(reports_dir: Path | None):
    """Phase 1a: Parse all reports into slim section-grouped JSON."""
    from .scanner.docx_parser import parse_all_reports

    src = reports_dir or REPORTS_DIR
    console.print(Panel(f"[bold]Phase 1a: Slim Parse[/bold]\nSource: {src}", expand=False))

    reports = parse_all_reports(src)
    if not reports:
        return

    SCANNED_DIR.mkdir(parents=True, exist_ok=True)
    for report in reports:
        out_path = SCANNED_DIR / f"{report.report_id}_scan.json"
        out_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"  Saved [cyan]{out_path.name}[/cyan]")

    console.print(f"\n[green bold]Scanned {len(reports)} reports -> {SCANNED_DIR}[/green bold]")


# -- diff ------------------------------------------------------------------

@cli.command()
def diff():
    """Phase 1b: Cross-report diff to identify static vs dynamic content."""
    from .scanner.models import ScannedReport
    from .scanner.template_differ import diff_reports

    console.print(Panel("[bold]Phase 1b: Cross-Report Diff[/bold]", expand=False))

    scan_files = sorted(SCANNED_DIR.glob("*_scan.json"))
    if not scan_files:
        console.print(f"[red]No scan files in {SCANNED_DIR}. Run 'scan' first.[/red]")
        return

    reports: list[ScannedReport] = []
    for f in scan_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        reports.append(ScannedReport.model_validate(data))

    console.print(f"Loaded {len(reports)} scanned reports")

    template = diff_reports(reports)

    RULES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RULES_DIR / "template_definition.json"
    out_path.write_text(template.model_dump_json(indent=2), encoding="utf-8")

    console.print(f"\n[green bold]Template saved -> {out_path}[/green bold]")

    # Print summary
    console.print(f"\n[bold]Template Summary:[/bold]")
    for sec in template.sections:
        static_count = sum(1 for s in sec.slots if s.slot_type.value == "static")
        dynamic_count = len(sec.slots) - static_count
        required = "required" if sec.is_required else f"conditional ({sec.appears_in}/{sec.total_reports})"
        console.print(
            f"  {sec.heading[:60]:<60}  "
            f"{static_count:>2} static, {dynamic_count:>2} dynamic  [{required}]"
        )


# -- narratives ------------------------------------------------------------

@cli.command()
def narratives():
    """Phase 1c: LLM analysis of narrative sections (~$2)."""
    from .scanner.models import ReportTemplate, ScannedReport
    from .scanner.llm_content_analyzer import analyze_narrative_sections, save_narrative_analysis

    console.print(Panel("[bold]Phase 1c: Narrative Analysis (LLM)[/bold]", expand=False))

    template_path = RULES_DIR / "template_definition.json"
    if not template_path.exists():
        console.print(f"[red]Template not found. Run 'diff' first.[/red]")
        return

    template = ReportTemplate.model_validate_json(template_path.read_text(encoding="utf-8"))

    scan_files = sorted(SCANNED_DIR.glob("*_scan.json"))
    reports = [
        ScannedReport.model_validate_json(f.read_text(encoding="utf-8"))
        for f in scan_files
    ]

    patterns = analyze_narrative_sections(template, reports)

    out_path = RULES_DIR / "narrative_patterns.json"
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    save_narrative_analysis(patterns, out_path)

    console.print(f"\n[green bold]Analyzed {len(patterns)} narrative sections[/green bold]")


# -- extract ---------------------------------------------------------------

@cli.command()
@click.option("--forms-dir", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--no-skip", is_flag=True, help="Re-extract even if output exists")
@click.option("--limit", type=int, default=None, help="Process only the first N forms")
@click.option("--parallel", type=int, default=3, help="Number of forms to process concurrently")
def extract(forms_dir: Path | None, no_skip: bool, limit: int | None, parallel: int):
    """Phase 2: Run extraction pipeline on matching source forms."""
    from .correlator.extraction_runner import run_all_extractions

    src = forms_dir or FORMS_DIR
    label = f"Source: {src}"
    if limit:
        label += f" (limit: {limit})"
    label += f" | parallel={parallel}"
    console.print(Panel(f"[bold]Phase 2: Extract Source Forms[/bold]\n{label}", expand=False))

    results = run_all_extractions(
        forms_dir=src,
        output_dir=EXTRACTIONS_DIR,
        skip_existing=not no_skip,
        limit=limit,
        parallel=parallel,
    )
    console.print(f"\n[green bold]Extracted {len(results)} forms -> {EXTRACTIONS_DIR}[/green bold]")


# -- extract-v2 ------------------------------------------------------------

@cli.command("extract-v2")
@click.option("--forms-dir", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--no-skip", is_flag=True, help="Re-extract even if output exists")
@click.option("--limit", type=int, default=None, help="Process only the first N forms")
@click.option("--parallel", type=int, default=1, help="Forms to process concurrently (keep 1 for stability)")
def extract_v2(forms_dir: Path | None, no_skip: bool, limit: int | None, parallel: int):
    """Phase 2 v2: Two-mode extraction (Llama 4 Maverick + Claude validation)."""
    from .correlator.extraction_runner import run_all_extractions_v2

    src = forms_dir or FORMS_DIR
    label = f"Source: {src}"
    if limit:
        label += f" (limit: {limit})"
    console.print(Panel(f"[bold]Phase 2 v2: Smart Extraction[/bold]\n{label}", expand=False))

    results = run_all_extractions_v2(
        forms_dir=src,
        output_dir=EXTRACTIONS_V2_DIR,
        skip_existing=not no_skip,
        limit=limit,
        parallel=parallel,
    )

    ok = sum(1 for r in results if r.get("status") == "ok")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    failed = len(results) - ok - skipped
    console.print(f"\n[green bold]Done: {ok} extracted, {skipped} skipped, {failed} failed[/green bold]")
    console.print(f"[bold]Output: {EXTRACTIONS_V2_DIR}[/bold]")

    val_pcts = [r["validation_pct"] for r in results if r.get("validation_pct", -1) >= 0]
    if val_pcts:
        avg = sum(val_pcts) / len(val_pcts)
        console.print(f"[bold]Claude validation avg: {avg:.1f}% across {len(val_pcts)} forms[/bold]")


# -- condense --------------------------------------------------------------

@cli.command()
@click.option("--input-dir", type=click.Path(exists=True, path_type=Path), default=None,
              help="Override extraction input directory")
@click.option("--no-skip", is_flag=True, help="Re-condense even if output exists")
@click.option("--ai-verify", is_flag=True, help="Run AI verification on flagged pages")
def condense(input_dir: Path | None, no_skip: bool, ai_verify: bool):
    """Phase 2c: Condense extraction JSONs into clean field summaries."""
    from .correlator.condenser import condense_all, verify_all

    src = input_dir or (EXTRACTIONS_V2_DIR / "exam")
    console.print(Panel(f"[bold]Phase 2c: Condense Extractions[/bold]\nSource: {src}", expand=False))

    results = condense_all(
        input_dir=src,
        output_dir=CONDENSED_DIR,
        skip_existing=not no_skip,
    )

    total_fields = sum(sum(len(p.get("fields", {})) for p in r["pages"]) for r in results)
    total_flags = sum(sum(len(p.get("review_flags", [])) for p in r["pages"]) for r in results)
    console.print(
        f"\n[green bold]Condensed {len(results)} forms -> {CONDENSED_DIR}[/green bold]"
        f"\n  Total fields: {total_fields} | Review flags: {total_flags}"
    )

    if ai_verify:
        console.print("\n[bold]Running AI verification on flagged pages...[/bold]")
        verified = verify_all(CONDENSED_DIR)
        console.print(f"[green bold]AI verified {verified} pages total[/green bold]")


# -- trim ------------------------------------------------------------------

@cli.command()
def trim():
    """Phase 2b: Split extractions into exam pages + lawyer cover pages."""
    from .correlator.trim_extractions import trim_all_extractions

    console.print(Panel("[bold]Phase 2b: Split Exam / Lawyer Pages[/bold]", expand=False))

    if not EXTRACTIONS_DIR.exists() or not list(EXTRACTIONS_DIR.glob("*.json")):
        console.print(f"[red]No extractions in {EXTRACTIONS_DIR}. Run 'extract' first.[/red]")
        return

    results = trim_all_extractions(
        input_dir=EXTRACTIONS_DIR,
        output_dir=EXTRACTIONS_TRIMMED_DIR,
        lawyer_dir=OUTPUTS / "extractions_lawyer",
    )
    console.print(f"\n[green bold]{len(results)} exam files -> {EXTRACTIONS_TRIMMED_DIR.name}/[/green bold]")
    console.print(f"[green bold]Lawyer covers -> extractions_lawyer/[/green bold]")


# -- correlate -------------------------------------------------------------

@cli.command()
@click.option("--use-condensed/--no-condensed", default=True,
              help="Use condensed extraction JSONs from Phase 2c (default: True)")
@click.option("--limit", type=int, default=None, help="Process only the first N pairs")
@click.option("--skip-patterns", is_flag=True, help="Skip cross-report pattern analysis")
def correlate(use_condensed: bool, limit: int | None, skip_patterns: bool):
    """Phase 3: Map extraction fields to report elements and find patterns."""
    from .correlator.field_mapper import correlate_all_pairs
    from .correlator.pattern_analyzer import analyse_patterns

    console.print(Panel("[bold]Phase 3: Correlate & Analyse Patterns[/bold]", expand=False))

    reports_dir = SCANNED_DIR
    if not list(reports_dir.glob("*.json")):
        console.print(f"[red]No scanned reports in {reports_dir}. Run 'scan' first.[/red]")
        return

    if use_condensed and CONDENSED_DIR.exists() and list(CONDENSED_DIR.glob("*_condensed.json")):
        ext_dir = CONDENSED_DIR
        console.print("[bold]Using condensed extractions[/bold]")
    else:
        ext_dir = EXTRACTIONS_TRIMMED_DIR if EXTRACTIONS_TRIMMED_DIR.exists() else EXTRACTIONS_DIR

    if not list(ext_dir.glob("*.json")):
        console.print(f"[red]No extractions in {ext_dir}[/red]")
        return

    lawyer_dir = EXTRACTIONS_V2_DIR / "lawyer"
    if not lawyer_dir.exists() or not list(lawyer_dir.glob("*.json")):
        lawyer_dir = OUTPUTS / "extractions_lawyer"
    has_lawyer = lawyer_dir.exists() and list(lawyer_dir.glob("*.json"))

    console.print(f"  Reports:          {reports_dir.name}/ ({len(list(reports_dir.glob('*.json')))} files)")
    console.print(f"  Exam extractions: {ext_dir.name}/ ({len(list(ext_dir.glob('*.json')))} files)")
    if has_lawyer:
        console.print(f"  Lawyer covers:    {lawyer_dir.name}/ ({len(list(lawyer_dir.glob('*.json')))} files)")
    if limit:
        console.print(f"  Limit: first {limit} pairs")

    console.print("\n[bold]Step 3a: Per-pair field mapping[/bold]")
    correlations = correlate_all_pairs(
        reports_dir=reports_dir,
        extractions_dir=ext_dir,
        output_dir=CORRELATIONS_DIR,
        lawyer_dir=lawyer_dir if has_lawyer else None,
    )

    if limit:
        correlations = correlations[:limit]

    if not correlations:
        console.print("[red]No correlations produced.[/red]")
        return

    if not skip_patterns:
        console.print("\n[bold]Step 3b: Cross-report pattern analysis[/bold]")
        patterns = analyse_patterns(correlations)

        patterns_path = CORRELATIONS_DIR / "cross_report_patterns.json"
        patterns_path.write_text(patterns.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[green]Patterns saved -> {patterns_path.name}[/green]")

    console.print(f"\n[green bold]Correlation complete. {len(correlations)} pairs analysed.[/green bold]")


# -- generate-rules --------------------------------------------------------

@cli.command("generate-rules")
def generate_rules():
    """Phase 4: Generate report assembly rules from correlations."""
    from .rules.rule_generator import generate_from_files

    console.print(Panel("[bold]Phase 4: Generate Report Rules[/bold]", expand=False))

    patterns_path = CORRELATIONS_DIR / "cross_report_patterns.json"
    if not patterns_path.exists():
        console.print(f"[red]Patterns file not found: {patterns_path}[/red]")
        return

    ext_dir = EXTRACTIONS_TRIMMED_DIR if EXTRACTIONS_TRIMMED_DIR.exists() else EXTRACTIONS_DIR
    rules_path = RULES_DIR / "report_rules.json"
    generate_from_files(
        patterns_path=patterns_path,
        reports_dir=SCANNED_DIR,
        correlations_dir=CORRELATIONS_DIR,
        extractions_dir=ext_dir,
        output_path=rules_path,
    )
    console.print(f"\n[green bold]Rules generated -> {rules_path}[/green bold]")


# -- validate --------------------------------------------------------------

@cli.command()
@click.option("--full", is_flag=True,
              help="Generate actual narrative text via LLM before validation (~$5-10 for 31 reports)")
def validate(full: bool):
    """Phase 5: Validate rules against known reports."""
    from .rules.rule_validator import validate_all

    mode = "FULL (LLM generation)" if full else "placeholder"
    console.print(Panel(f"[bold]Phase 5: Validate Rules[/bold]\nMode: {mode}", expand=False))

    rules_path = RULES_DIR / "report_rules.json"
    if not rules_path.exists():
        console.print(f"[red]Rules file not found: {rules_path}[/red]")
        return

    ext_dir = CONDENSED_DIR if CONDENSED_DIR.exists() and list(CONDENSED_DIR.glob("*_condensed.json")) else (
        EXTRACTIONS_TRIMMED_DIR if EXTRACTIONS_TRIMMED_DIR.exists() else EXTRACTIONS_DIR
    )
    console.print(f"  Extractions: {ext_dir}")
    scores_path = RULES_DIR / "validation_scores.json"
    validate_all(
        rules_path=rules_path,
        reports_dir=SCANNED_DIR,
        extractions_dir=ext_dir,
        output_path=scores_path,
        full_mode=full,
    )
    console.print(f"\n[green bold]Validation complete -> {scores_path}[/green bold]")


# -- status ----------------------------------------------------------------

@cli.command()
def status():
    """Show current pipeline status."""
    console.print(Panel("[bold]Report Learning Module -- Status[/bold]", expand=False))

    checks = [
        ("Training reports (.doc)", REPORTS_DIR, "*.doc"),
        ("Training reports (.docx)", REPORTS_DIR, "*.docx"),
        ("Source forms", FORMS_DIR, "*.pdf"),
        ("Scanned reports", SCANNED_DIR, "*.json"),
        ("Template definition", RULES_DIR, "template_definition.json"),
        ("Extractions (raw)", EXTRACTIONS_DIR, "*.json"),
        ("Extractions (exam)", EXTRACTIONS_TRIMMED_DIR, "*.json"),
        ("Extractions (lawyer)", OUTPUTS / "extractions_lawyer", "*.json"),
        ("Extractions v2 (exam)", EXTRACTIONS_V2_DIR / "exam", "*.json"),
        ("Extractions v2 (lawyer)", EXTRACTIONS_V2_DIR / "lawyer", "*.json"),
        ("Extractions v2 (validation)", EXTRACTIONS_V2_DIR / "validation", "*.json"),
        ("Extractions v2 (condensed)", CONDENSED_DIR, "*_condensed.json"),
        ("Correlations", CORRELATIONS_DIR, "correlation_*.json"),
        ("Report rules", RULES_DIR, "report_rules.json"),
        ("Validation", RULES_DIR, "validation_scores.json"),
    ]

    for label, directory, pattern in checks:
        files = list(directory.glob(pattern)) if directory.exists() else []
        count = len(files)
        if count > 0:
            console.print(f"  [green][+][/green] {label}: {count} file(s)")
        else:
            console.print(f"  [dim][ ][/dim] {label}: none")
