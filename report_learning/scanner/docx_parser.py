"""
Slim Word document parser.

Supports .doc (converted via Word COM) and .docx (native).
Extracts text content and structure, groups elements into sections by headings.
No per-character formatting -- just text, type, bold flag, alignment.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from rich.console import Console

from .models import ReportElement, ReportSection, ScannedReport

console = Console()

ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
}

SUPPORTED_EXTENSIONS = {".doc", ".docx"}


# ---------------------------------------------------------------------------
# .doc -> .docx conversion (unchanged from before)
# ---------------------------------------------------------------------------

def _convert_doc_to_docx(doc_path: Path, output_dir: Path) -> Path:
    """Convert .doc to .docx via Word COM, fallback to LibreOffice."""
    docx_path = output_dir / (doc_path.stem + ".docx")
    tmp_src = output_dir / doc_path.name
    shutil.copy2(doc_path, tmp_src)

    try:
        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            doc = word.Documents.Open(str(tmp_src.resolve()))
            doc.SaveAs2(str(docx_path.resolve()), FileFormat=16)
            doc.Close(False)
            word.Quit()
        finally:
            pythoncom.CoUninitialize()

        console.print(f"    [dim]Converted .doc -> .docx[/dim]")
        return docx_path

    except ImportError:
        pass
    except Exception as e:
        console.print(f"    [yellow]Word COM failed ({e}), trying LibreOffice[/yellow]")

    import subprocess
    for lo_path in [
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]:
        try:
            subprocess.run(
                [lo_path, "--headless", "--convert-to", "docx",
                 "--outdir", str(output_dir), str(doc_path)],
                capture_output=True, timeout=60, check=True,
            )
            if docx_path.exists():
                return docx_path
        except (FileNotFoundError, subprocess.SubprocessError):
            continue

    raise RuntimeError(f"Cannot convert {doc_path.name}: need Word or LibreOffice")


def _ensure_docx(filepath: Path) -> tuple[Path, Optional[Path]]:
    if filepath.suffix.lower() == ".docx":
        return filepath, None
    tmp_dir = Path(tempfile.mkdtemp(prefix="rle_conv_"))
    try:
        return _convert_doc_to_docx(filepath, tmp_dir), tmp_dir
    except Exception:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


# ---------------------------------------------------------------------------
# Slim parse helpers
# ---------------------------------------------------------------------------

def _is_bold(paragraph) -> bool:
    """True if the dominant formatting of the paragraph is bold."""
    bold_chars = 0
    total_chars = 0
    for run in paragraph.runs:
        n = len(run.text)
        total_chars += n
        if run.bold:
            bold_chars += n
    return bold_chars > total_chars / 2 if total_chars else False


def _detect_heading(paragraph) -> Optional[int]:
    style_name = paragraph.style.name if paragraph.style else ""
    if style_name.startswith("Heading"):
        try:
            return int(style_name.split()[-1])
        except (ValueError, IndexError):
            return 1

    text = paragraph.text.strip()
    if not text or len(text) > 120:
        return None

    # Lines with tabs are label:value pairs or table headers, not headings
    if "\t" in text:
        return None

    # Lines with colons followed by content are label:value, not headings
    if ":" in text and not text.endswith(":"):
        return None

    # Must have at least one real word (4+ alpha chars) to be a heading
    words = text.split()
    has_real_word = any(len(w) >= 4 and w.isalpha() for w in words)
    if not has_real_word:
        return None

    if text == text.upper() and any(c.isalpha() for c in text):
        has_bold = any(run.bold for run in paragraph.runs if run.text and run.text.strip())
        if has_bold or len(text) < 80:
            return 2
    return None


def _get_alignment(paragraph) -> str:
    if paragraph.alignment is not None:
        return ALIGNMENT_MAP.get(paragraph.alignment, "left")
    return "left"


def _parse_table_cells(table: DocxTable) -> list[list[str]]:
    """Extract table as a simple 2D text grid."""
    rows: list[list[str]] = []
    for row in table.rows:
        rows.append([cell.text.strip() for cell in row.cells])
    return rows


# ---------------------------------------------------------------------------
# Main parse
# ---------------------------------------------------------------------------

def parse_docx(filepath: Path) -> ScannedReport:
    """Parse a single Word file into a section-grouped ScannedReport."""
    original_name = filepath.name
    docx_path, tmp_dir = _ensure_docx(filepath)

    try:
        report = _parse_docx_core(docx_path, original_name)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    return report


def _make_section_id(heading_text: str) -> str:
    """Turn heading text into a snake_case section id."""
    cleaned = heading_text.lower().strip()
    cleaned = "".join(c if c.isalnum() or c == " " else "" for c in cleaned)
    parts = cleaned.split()
    return "_".join(parts[:6])


def _parse_docx_core(filepath: Path, original_name: str) -> ScannedReport:
    doc = Document(str(filepath))

    preamble: list[ReportElement] = []
    sections: list[ReportSection] = []
    current_section: Optional[ReportSection] = None
    order = 0

    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

        if tag == "p":
            from docx.text.paragraph import Paragraph
            para = Paragraph(block, doc)
            text = para.text.strip()

            if not text:
                continue

            heading_level = _detect_heading(para)

            if heading_level:
                current_section = ReportSection(
                    id=_make_section_id(text),
                    heading=text,
                    heading_level=heading_level,
                )
                sections.append(current_section)
                order += 1
                continue

            element = ReportElement(
                id=f"e{order:04d}",
                type="paragraph",
                text=text,
                bold=_is_bold(para),
                alignment=_get_alignment(para),
            )
            order += 1

            if current_section:
                current_section.elements.append(element)
            else:
                preamble.append(element)

        elif tag == "tbl":
            table = DocxTable(block, doc)
            cells = _parse_table_cells(table)
            flat_text = "\n".join(" | ".join(row) for row in cells)

            element = ReportElement(
                id=f"e{order:04d}",
                type="table",
                text=flat_text,
                table_cells=cells,
            )
            order += 1

            if current_section:
                current_section.elements.append(element)
            else:
                preamble.append(element)

    total_elements = sum(len(s.elements) for s in sections) + len(preamble)

    metadata = {}
    props = doc.core_properties
    if props.author:
        metadata["author"] = props.author
    if props.title:
        metadata["title"] = props.title

    return ScannedReport(
        report_id=Path(original_name).stem,
        filename=original_name,
        total_sections=len(sections),
        total_elements=total_elements,
        sections=sections,
        preamble=preamble,
        metadata=metadata,
    )


def parse_all_reports(reports_dir: Path) -> list[ScannedReport]:
    """Parse all Word files in a directory."""
    all_files: list[Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        all_files.extend(reports_dir.glob(f"*{ext}"))
    all_files = sorted(set(all_files))

    if not all_files:
        console.print(f"[red]No .doc/.docx files found in {reports_dir}[/red]")
        return []

    console.print(f"[bold]Found {len(all_files)} Word files[/bold]")
    results: list[ScannedReport] = []

    for filepath in all_files:
        console.print(f"  Parsing [cyan]{filepath.name}[/cyan]...")
        try:
            report = parse_docx(filepath)
            results.append(report)
            console.print(
                f"    [green]{report.total_sections} sections, "
                f"{report.total_elements} elements[/green]"
            )
        except Exception as e:
            console.print(f"    [red]Failed: {e}[/red]")

    return results
