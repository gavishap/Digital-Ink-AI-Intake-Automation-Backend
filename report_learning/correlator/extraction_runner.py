"""
V2 extraction runner: two-mode pipeline with Claude validation.

For each signed PDF:
  1. Convert to images at 250 DPI.
  2. Detect exam start via structural image comparison against blank_page_1.
  3. Extract lawyer cover pages in "full_page" mode (all printed + handwritten text).
  4. Extract exam pages:
       - Compare each page against current blank template.
       - If match: "differential" extraction using blank template comparison.
       - If no match: "single-image" extraction (no blank), don't advance template index.
  5. Run Claude on the first exam page for accuracy validation.
  6. Save exam extraction, lawyer extraction, and validation report.
"""

import json
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
from rich.console import Console
from scipy.ndimage import uniform_filter

console = Console()

EXAM_PAGE_COUNT = 20
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
SCHEMA_PATH = TEMPLATES_DIR / "orofacial_exam_schema.json"

EXAM_START_THRESHOLD = 0.6
TEMPLATE_MATCH_THRESHOLD = 0.35


# ---------------------------------------------------------------------------
# Image-based page matching (combined correlation + SSIM)
# ---------------------------------------------------------------------------

def _page_similarity(img_pil: Image.Image, blank_path: Path, size=(300, 390)) -> float:
    """Combined max(correlation, SSIM) for robust page matching.

    Correlation excels at highly-structured pages (page 1 with YES/NO grid).
    SSIM excels when handwriting or stamps shift overall brightness.
    Taking the max leverages each metric's strength.
    """
    with Image.open(blank_path) as blank:
        a = np.array(img_pil.resize(size).convert("L"), dtype=np.float64)
        b = np.array(blank.resize(size).convert("L"), dtype=np.float64)

    # Pearson correlation on heavily-blurred images
    a_blur = uniform_filter(a, size=15)
    b_blur = uniform_filter(b, size=15)
    af, bf = a_blur.flatten(), b_blur.flatten()
    am, bm = af.mean(), bf.mean()
    num_c = np.sum((af - am) * (bf - bm))
    den_c = np.sqrt(np.sum((af - am) ** 2) * np.sum((bf - bm) ** 2))
    corr = float(num_c / den_c) if den_c > 0 else 0.0

    # Windowed SSIM
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    win = 11
    mu_a = uniform_filter(a, size=win)
    mu_b = uniform_filter(b, size=win)
    sig_a2 = uniform_filter(a * a, size=win) - mu_a * mu_a
    sig_b2 = uniform_filter(b * b, size=win) - mu_b * mu_b
    sig_ab = uniform_filter(a * b, size=win) - mu_a * mu_b
    num_s = (2 * mu_a * mu_b + C1) * (2 * sig_ab + C2)
    den_s = (mu_a ** 2 + mu_b ** 2 + C1) * (sig_a2 + sig_b2 + C2)
    ssim_val = float(np.mean(num_s / den_s))

    return max(corr, ssim_val)


def _find_exam_start(page_images: list, blank1_path: Path) -> int:
    """Return the 0-based index of the first orofacial exam page."""
    for i, pg in enumerate(page_images):
        score = _page_similarity(pg, blank1_path)
        console.print(f"  Page {i+1} vs blank_1: {score:.3f}", end="")
        if score >= EXAM_START_THRESHOLD:
            console.print(" [green]← exam start[/green]")
            return i
        console.print(" [dim](lawyer)[/dim]")
    console.print("  [yellow]Could not detect exam start; defaulting to page 0[/yellow]")
    return 0


# ---------------------------------------------------------------------------
# Schema / template helpers
# ---------------------------------------------------------------------------

def _load_form_schema():
    import sys
    _fe_root = str(Path(__file__).resolve().parents[2])
    if _fe_root not in sys.path:
        sys.path.insert(0, _fe_root)
    from src.models import FormSchema
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema = FormSchema.model_validate(data)
    schema.build_field_index()
    return schema


def _blank_template_paths() -> list[Optional[Path]]:
    paths: list[Optional[Path]] = []
    for i in range(1, EXAM_PAGE_COUNT + 1):
        p = TEMPLATES_DIR / f"orofacial_exam_blank_page_{i}.png"
        paths.append(p if p.exists() else None)
    return paths


# ---------------------------------------------------------------------------
# Field-value comparison (Claude validation)
# ---------------------------------------------------------------------------

def _compare_field_values(llama_fv: dict, claude_fv: dict) -> dict:
    all_keys = set(llama_fv) | set(claude_fv)
    if not all_keys:
        return {"total": 0, "match": 0, "pct": 100.0, "mismatches": []}
    matches, mismatches = 0, []
    for k in sorted(all_keys):
        lv, cv = llama_fv.get(k, {}), claude_fv.get(k, {})
        l_val = (lv.get("value") or "").strip().lower() if isinstance(lv, dict) else str(lv).strip().lower()
        c_val = (cv.get("value") or "").strip().lower() if isinstance(cv, dict) else str(cv).strip().lower()
        if l_val == c_val:
            matches += 1
        else:
            mismatches.append({"field": k, "llama": l_val, "claude": c_val})
    pct = round(matches / len(all_keys) * 100, 1)
    return {"total": len(all_keys), "match": matches, "pct": pct, "mismatches": mismatches}


# ---------------------------------------------------------------------------
# Single-form extraction
# ---------------------------------------------------------------------------

def _run_single_extraction_v2(
    pdf_path: Path,
    exam_output: Path,
    lawyer_output: Path,
    validation_output: Path,
    form_schema,
    blank_paths: list,
) -> dict:
    import sys
    _fe_root = str(Path(__file__).resolve().parents[2])
    if _fe_root not in sys.path:
        sys.path.insert(0, _fe_root)
    from src.services.pdf_processor import PDFProcessor
    from src.services.extraction_pipeline import ExtractionPipeline
    from src.models import PageExtractionResult

    name = pdf_path.stem
    console.print(f"\n{'='*60}")
    console.print(f"[bold cyan]{name}[/bold cyan]")
    console.print(f"{'='*60}")

    with tempfile.TemporaryDirectory() as tmpdir:
        processor = PDFProcessor(output_dir=Path(tmpdir))
        image_paths = processor.convert_pdf_to_images(pdf_path, prefix=name)
        if not image_paths:
            console.print(f"  [red]No pages from {name}[/red]")
            return {"name": name, "status": "no_pages"}

        total = len(image_paths)

        # ---- Detect exam start via image comparison ----
        console.print(f"  [bold]Detecting exam start ({total} pages)...[/bold]")
        pil_pages = [Image.open(p) for p in image_paths]
        blank1 = blank_paths[0]
        if not blank1:
            console.print("  [red]blank_page_1 missing![/red]")
            return {"name": name, "status": "missing_template"}

        exam_start = _find_exam_start(pil_pages, blank1)
        lawyer_count = exam_start
        console.print(f"  → {lawyer_count} lawyer page(s), exam from page {exam_start+1}")

        pipeline = ExtractionPipeline()

        # ---- Lawyer pages (full_page mode) ----
        lawyer_pages = []
        for i in range(lawyer_count):
            try:
                page = pipeline.extract_page(
                    image_paths[i], i + 1,
                    extraction_mode="full_page",
                )
                lawyer_pages.append(page)
            except Exception as e:
                console.print(f"  [red]Lawyer page {i+1} failed: {e}[/red]")
                lawyer_pages.append(PageExtractionResult(
                    page_number=i + 1, overall_confidence=0.0,
                    items_needing_review=1,
                    review_reasons=[f"Lawyer page {i+1} failed: {e}"],
                ))

        # ---- Exam pages (smart template matching) ----
        exam_image_paths = image_paths[exam_start:]
        exam_pil_pages = pil_pages[exam_start:]
        exam_page_count = len(exam_image_paths)

        # Build per-page extraction plan
        blank_idx = 0
        page_plans: list[dict] = []
        for j in range(exam_page_count):
            plan: dict = {"global_idx": exam_start + j, "local_idx": j}
            if blank_idx < EXAM_PAGE_COUNT and blank_paths[blank_idx]:
                score = _page_similarity(exam_pil_pages[j], blank_paths[blank_idx])
                plan["sim_score"] = round(score, 3)
                plan["tested_blank"] = blank_idx + 1
                if score >= TEMPLATE_MATCH_THRESHOLD:
                    plan["mode"] = "differential"
                    plan["blank_idx"] = blank_idx
                    plan["page_schema_idx"] = blank_idx
                    blank_idx += 1
                    console.print(
                        f"  Exam pg {j+1}: [green]MATCH blank_{plan['tested_blank']} "
                        f"({score:.3f})[/green] → differential"
                    )
                else:
                    plan["mode"] = "single"
                    plan["blank_idx"] = None
                    plan["page_schema_idx"] = None
                    console.print(
                        f"  Exam pg {j+1}: [yellow]NO MATCH blank_{plan['tested_blank']} "
                        f"({score:.3f})[/yellow] → single-image"
                    )
            else:
                plan["mode"] = "single"
                plan["blank_idx"] = None
                plan["page_schema_idx"] = None
                plan["sim_score"] = None
                plan["tested_blank"] = None
                console.print(f"  Exam pg {j+1}: [dim]templates exhausted → single-image[/dim]")
            page_plans.append(plan)

        matched = sum(1 for p in page_plans if p["mode"] == "differential")
        console.print(
            f"  [bold]Plan: {matched} differential, "
            f"{exam_page_count - matched} single-image[/bold]"
        )

        # Close PIL images (no longer needed)
        for img in pil_pages:
            img.close()

        # Execute extraction plan
        exam_pages_raw = [None] * exam_page_count

        def _extract_exam_page(plan: dict):
            j = plan["local_idx"]
            gi = plan["global_idx"]
            page_schema = None
            blank = None
            mode = plan["mode"]

            if mode == "differential":
                bi = plan["blank_idx"]
                blank = blank_paths[bi]
                if form_schema and bi < len(form_schema.pages):
                    page_schema = form_schema.pages[bi]
            else:
                mode = "differential"  # pipeline still runs 6 stages, just without blank

            try:
                return j, pipeline.extract_page(
                    image_paths[gi],
                    gi + 1,
                    page_schema=page_schema,
                    blank_image_path=blank,
                    extraction_mode=mode,
                )
            except Exception as e:
                console.print(f"  [red]Exam page {j+1} failed: {e}[/red]")
                return j, PageExtractionResult(
                    page_number=gi + 1, overall_confidence=0.0,
                    items_needing_review=1,
                    review_reasons=[f"Exam page {j+1} failed: {e}"],
                )

        workers = min(2, exam_page_count)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(_extract_exam_page, plan): plan for plan in page_plans}
            for fut in as_completed(futs):
                j, result = fut.result(timeout=900)
                exam_pages_raw[j] = result

        exam_pages = [p for p in exam_pages_raw if p is not None]
        for i, p in enumerate(exam_pages):
            p.page_number = i + 1

        # ---- Claude validation on first exam page ----
        validation: dict = {"skipped": True}
        first_diff = next((p for p in page_plans if p["mode"] == "differential"), None)
        if exam_pages and pipeline.claude_client and first_diff:
            gi = first_diff["global_idx"]
            bi = first_diff["blank_idx"]
            page_schema_0 = form_schema.pages[bi] if form_schema and bi < len(form_schema.pages) else None
            blank_0 = blank_paths[bi] if bi is not None else None
            try:
                console.print(f"  [cyan]Running Claude validation on exam page {first_diff['local_idx']+1}...[/cyan]")
                claude_page = pipeline.extract_page(
                    image_paths[gi], gi + 1,
                    page_schema=page_schema_0,
                    blank_image_path=blank_0,
                    extraction_mode="differential",
                    force_provider="claude",
                )
                li = first_diff["local_idx"]
                comparison = _compare_field_values(
                    exam_pages[li].field_values,
                    claude_page.field_values,
                )
                validation = {
                    "skipped": False,
                    "exam_page_idx": li + 1,
                    "match_pct": comparison["pct"],
                    "total_fields": comparison["total"],
                    "matched": comparison["match"],
                    "mismatches": comparison["mismatches"],
                    "claude_field_values": claude_page.field_values,
                }
                color = "green" if comparison["pct"] >= 85 else "yellow" if comparison["pct"] >= 70 else "red"
                console.print(
                    f"  [{color}]Validation: {comparison['pct']}% match "
                    f"({comparison['match']}/{comparison['total']})[/{color}]"
                )
            except Exception as e:
                console.print(f"  [red]Claude validation failed: {e}[/red]")
                validation = {"skipped": False, "error": str(e)}

        # ---- Build & save results ----
        def _build_form_result(pages, label, extra_meta=None):
            successful = [p for p in pages if p.overall_confidence > 0]
            avg_conf = sum(p.overall_confidence for p in successful) / len(successful) if successful else 0
            result = {
                "form_name": name,
                "source_file": pdf_path.name,
                "extraction_type": label,
                "total_pages": len(pages),
                "overall_confidence": round(avg_conf, 3),
                "pages": [p.model_dump(mode="json") for p in pages],
            }
            if extra_meta:
                result.update(extra_meta)
            return result

        plan_summary = [
            {
                "exam_page": p["local_idx"] + 1,
                "pdf_page": p["global_idx"] + 1,
                "mode": p["mode"],
                "blank_template": p.get("tested_blank"),
                "similarity": p.get("sim_score"),
            }
            for p in page_plans
        ]

        exam_result = _build_form_result(
            exam_pages, "smart_extraction",
            extra_meta={"page_plans": plan_summary},
        )
        lawyer_result = _build_form_result(lawyer_pages, "full_page") if lawyer_pages else None

        exam_output.write_text(json.dumps(exam_result, indent=2, default=str), encoding="utf-8")
        console.print(f"  [green]Exam saved ({len(exam_pages)} pages, {matched} differential)[/green]")

        if lawyer_result:
            lawyer_output.write_text(json.dumps(lawyer_result, indent=2, default=str), encoding="utf-8")
            console.print(f"  [green]Lawyer saved ({len(lawyer_pages)} pages)[/green]")

        val_report = {
            "form_name": name,
            "total_pdf_pages": total,
            "exam_start_page": exam_start + 1,
            "lawyer_pages": lawyer_count,
            "exam_pages": exam_page_count,
            "differential_pages": matched,
            "single_image_pages": exam_page_count - matched,
            "model_primary": pipeline.qwen_model,
            "model_validation": pipeline.claude_model,
            "validation": validation,
            "page_plans": plan_summary,
        }
        validation_output.write_text(json.dumps(val_report, indent=2, default=str), encoding="utf-8")

        return {
            "name": name,
            "status": "ok",
            "exam_pages": len(exam_pages),
            "lawyer_pages": len(lawyer_pages),
            "differential": matched,
            "single_image": exam_page_count - matched,
            "validation_pct": validation.get("match_pct", -1),
        }


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def run_all_extractions_v2(
    forms_dir: Path,
    output_dir: Path,
    skip_existing: bool = True,
    limit: int | None = None,
    parallel: int = 1,
) -> list[dict]:
    """Run smart two-mode extraction on all PDFs.

    Output structure:
        exam/        - per-form extraction JSONs (exam pages)
        lawyer/      - per-form extraction JSONs (cover pages)
        validation/  - per-form Claude comparison + page plan reports
    """
    pdf_files = sorted(forms_dir.rglob("*.pdf"))
    if limit:
        pdf_files = pdf_files[:limit]
    if not pdf_files:
        console.print(f"[red]No PDFs in {forms_dir}[/red]")
        return []

    exam_dir = output_dir / "exam"
    lawyer_dir = output_dir / "lawyer"
    val_dir = output_dir / "validation"
    for d in (exam_dir, lawyer_dir, val_dir):
        d.mkdir(parents=True, exist_ok=True)

    form_schema = _load_form_schema()
    blank_paths = _blank_template_paths()
    console.print(f"[bold]Schema: {form_schema.form_name} ({form_schema.total_pages} pages)[/bold]")
    console.print(f"[bold]Blank templates: {sum(1 for p in blank_paths if p)} available[/bold]")

    to_process: list[Path] = []
    results: list[dict] = []
    for pdf in pdf_files:
        exam_out = exam_dir / f"{pdf.stem}_extraction.json"
        if skip_existing and exam_out.exists():
            console.print(f"  [yellow]Skipping {pdf.name} (exists)[/yellow]")
            results.append({"name": pdf.stem, "status": "skipped"})
            continue
        to_process.append(pdf)

    total = len(to_process)
    console.print(f"\n[bold]Processing {total} PDFs ({len(results)} skipped)[/bold]")
    if not to_process:
        return results

    lock = threading.Lock()
    done = [0]

    def _process(pdf: Path) -> dict:
        exam_out = exam_dir / f"{pdf.stem}_extraction.json"
        lawyer_out = lawyer_dir / f"{pdf.stem}_lawyer.json"
        val_out = val_dir / f"{pdf.stem}_validation.json"
        try:
            r = _run_single_extraction_v2(
                pdf, exam_out, lawyer_out, val_out,
                form_schema, blank_paths,
            )
        except Exception as e:
            console.print(f"[red]FATAL {pdf.name}: {e}[/red]")
            import traceback
            traceback.print_exc()
            r = {"name": pdf.stem, "status": "fatal_error", "error": str(e)}
        with lock:
            done[0] += 1
            console.print(f"\n[bold green]Progress: {done[0]}/{total}[/bold green]")
        return r

    if parallel <= 1:
        for pdf in to_process:
            results.append(_process(pdf))
    else:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futs = {pool.submit(_process, pdf): pdf for pdf in to_process}
            for fut in as_completed(futs):
                results.append(fut.result())

    return results


# ---------------------------------------------------------------------------
# Legacy API (backward compat for old CLI command)
# ---------------------------------------------------------------------------

def run_all_extractions(
    forms_dir: Path,
    output_dir: Path,
    form_schema=None,
    skip_existing: bool = True,
    limit: int | None = None,
    parallel: int = 1,
) -> list[Path]:
    import sys
    _fe_root = str(Path(__file__).resolve().parents[2])
    if _fe_root not in sys.path:
        sys.path.insert(0, _fe_root)
    from src.services.pdf_processor import PDFProcessor
    from src.services.extraction_pipeline import ExtractionPipeline

    pdf_files = sorted(forms_dir.rglob("*.pdf"))
    if limit:
        pdf_files = pdf_files[:limit]
    if not pdf_files:
        console.print(f"[red]No PDF files found in {forms_dir}[/red]")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    for pdf_path in pdf_files:
        out_file = output_dir / f"{pdf_path.stem}_extraction.json"
        if skip_existing and out_file.exists():
            console.print(f"  [yellow]Skipping {pdf_path.name}[/yellow]")
            output_paths.append(out_file)
            continue

        console.print(f"\n[bold cyan]{pdf_path.name}[/bold cyan]")
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = PDFProcessor(output_dir=Path(tmpdir))
            image_paths = processor.convert_pdf_to_images(pdf_path, prefix=pdf_path.stem)
            if not image_paths:
                continue
            pipeline = ExtractionPipeline()
            result = pipeline.extract_form(
                image_paths=image_paths, form_schema=form_schema,
                form_name=pdf_path.stem, max_workers=2,
            )
            out_file.write_text(
                json.dumps(result.model_dump(mode="json"), indent=2, default=str),
                encoding="utf-8",
            )
            output_paths.append(out_file)

    return output_paths
