#!/usr/bin/env python3
"""
Medical Form Template Extraction System

CLI for scanning blank PDF forms and generating Pydantic model schemas
for use with the instructor package to extract filled-in form data.

Usage:
    # Scan a blank PDF and generate templates
    python main.py scan ./blank_form.pdf --name "workers_comp_dental" --output ./templates/
    
    # Scan a folder of page images
    python main.py scan ./pages/ --name "intake_form" --output ./templates/
    
    # Preview structure without saving
    python main.py scan ./form.pdf --preview
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn

from src.models import FormSchema, PageSchema, FieldLocation, FormExtractionResult
from src.services import FormAnalyzer, PDFProcessor, ExtractionPipeline
from src.generators import SchemaGenerator, PydanticModelGenerator

# Load environment variables
load_dotenv()

console = Console()


def create_form_id(name: str) -> str:
    """Convert form name to snake_case form_id."""
    return name.lower().replace(" ", "_").replace("-", "_")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Medical Form Template Extraction System
    
    Scan blank PDF forms and generate Pydantic schemas for data extraction.
    """
    pass


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--name", "-n",
    required=True,
    help="Name for this form (used in generated filenames)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./templates",
    help="Output directory for generated files"
)
@click.option(
    "--preview",
    is_flag=True,
    help="Preview structure without saving files"
)
@click.option(
    "--model",
    default="claude-sonnet-4-20250514",
    help="Claude model (sonnet-4 default, use opus for complex forms)"
)
@click.option(
    "--dpi",
    default=150,
    help="DPI for PDF conversion (150 is sufficient for forms)"
)
@click.option(
    "--max-tokens",
    default=16000,
    help="Max tokens for Claude response (16000 for complex pages)"
)
def scan(
    source: str,
    name: str,
    output: str,
    preview: bool,
    model: str,
    dpi: int,
    max_tokens: int,
):
    """
    Scan a blank form and generate templates.
    
    SOURCE can be a PDF file or a folder containing page images.
    
    Examples:
    
        python main.py scan ./form.pdf --name "dental_exam"
        
        python main.py scan ./pages/ --name "intake_form" --output ./out/
        
        python main.py scan ./form.pdf --name "test" --preview
    """
    source_path = Path(source)
    output_path = Path(output)
    form_id = create_form_id(name)
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]Medical Form Template Extraction[/bold cyan]\n"
        f"Form: {name}\n"
        f"Source: {source_path}\n"
        f"Output: {output_path if not preview else '[preview mode]'}",
        title="Form Extractor"
    ))
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        console.print("Set it with: export ANTHROPIC_API_KEY=your_key")
        sys.exit(1)
    
    # Initialize services
    pdf_processor = PDFProcessor(dpi=dpi)
    analyzer = FormAnalyzer(api_key=api_key, model=model, max_tokens=max_tokens)
    
    try:
        # Get page images
        console.print("\n[bold]Step 1: Preparing page images[/bold]")
        
        if source_path.is_file() and source_path.suffix.lower() == ".pdf":
            # Convert PDF to images
            image_paths = pdf_processor.convert_pdf_to_images(
                source_path,
                prefix=form_id
            )
        elif source_path.is_dir():
            # Load existing images from folder
            image_paths = pdf_processor.load_images_from_folder(source_path)
        else:
            console.print(f"[red]Error: Source must be a PDF file or folder of images[/red]")
            sys.exit(1)
        
        total_pages = len(image_paths)
        console.print(f"[green]Found {total_pages} pages to analyze[/green]\n")
        
        # Analyze each page
        console.print("[bold]Step 2: Analyzing pages with Claude[/bold]")
        
        pages: list[PageSchema] = []
        previous_context = ""
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing...", total=total_pages)
            
            for i, image_path in enumerate(image_paths, start=1):
                progress.update(task, description=f"Analyzing page {i}/{total_pages}")
                
                page_schema = analyzer.analyze_page(
                    image_path=image_path,
                    page_number=i,
                    form_name=name,
                    previous_context=previous_context if i > 1 else None,
                )
                pages.append(page_schema)
                
                # Update context for next page
                previous_context = analyzer.generate_context_summary(pages)
                
                progress.advance(task)
        
        # Build complete form schema
        console.print("\n[bold]Step 3: Building form schema[/bold]")
        
        form_schema = FormSchema(
            form_name=name,
            form_id=form_id,
            form_description=f"Schema for {name} form",
            total_pages=total_pages,
            pages=pages,
        )
        form_schema.build_field_index()
        
        # Print summary
        console.print(f"\n[bold green]Analysis Complete![/bold green]")
        console.print(f"  Total pages: {form_schema.total_pages}")
        console.print(f"  Total fields: {form_schema.total_fields}")
        console.print(f"  Total tables: {form_schema.total_tables}")
        console.print(f"  Fields indexed: {len(form_schema.field_index)}")
        
        # Per-page breakdown
        console.print("\n[bold]Page Breakdown:[/bold]")
        for page in form_schema.pages:
            complexity_color = "green" if page.complexity_score <= 3 else "yellow" if page.complexity_score <= 6 else "red"
            console.print(
                f"  Page {page.page_number}: "
                f"{page.total_fields} fields, "
                f"{page.total_tables} tables, "
                f"[{complexity_color}]complexity {page.complexity_score}/10[/{complexity_color}]"
            )
        
        if preview:
            console.print("\n[yellow]Preview mode - no files saved[/yellow]")
            
            # Show sample of schema
            console.print("\n[bold]Sample Field IDs:[/bold]")
            for field_id in list(form_schema.field_index.keys())[:10]:
                loc = form_schema.field_index[field_id]
                console.print(f"  - {field_id} (page {loc.page_number})")
            if len(form_schema.field_index) > 10:
                console.print(f"  ... and {len(form_schema.field_index) - 10} more")
        else:
            # Generate output files
            console.print("\n[bold]Step 4: Generating output files[/bold]")
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            # JSON schemas
            schema_gen = SchemaGenerator(output_path)
            
            # Save individual page schemas
            for page in form_schema.pages:
                schema_gen.save_page_schema(page, form_id)
            
            # Save complete form schema
            schema_gen.save_form_schema(form_schema)
            
            # Save summary
            summary = schema_gen.generate_summary(form_schema)
            summary_path = output_path / f"{form_id}_summary.txt"
            with open(summary_path, "w") as f:
                f.write(summary)
            console.print(f"  [dim]Saved: {form_id}_summary.txt[/dim]")
            
            # Pydantic models
            model_gen = PydanticModelGenerator(output_path)
            model_gen.generate_models_file(form_schema)
            model_gen.generate_extractor_stub(form_schema)
            
            console.print(f"\n[bold green]All files saved to: {output_path}[/bold green]")
            
            # List generated files
            console.print("\n[bold]Generated Files:[/bold]")
            for f in sorted(output_path.iterdir()):
                if f.is_file() and f.stem.startswith(form_id):
                    console.print(f"  - {f.name}")
    
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)
    
    finally:
        # Cleanup
        pdf_processor.cleanup()


@cli.command()
@click.argument("schema_file", type=click.Path(exists=True))
def info(schema_file: str):
    """
    Display information about a generated schema.
    
    SCHEMA_FILE should be a *_schema.json file.
    """
    schema_path = Path(schema_file)
    
    schema_gen = SchemaGenerator(schema_path.parent)
    form_schema = schema_gen.load_form_schema(schema_path)
    
    summary = schema_gen.generate_summary(form_schema)
    console.print(summary)


@cli.command()
def check():
    """
    Check system requirements.
    
    Verifies that all dependencies are installed and configured.
    """
    console.print("[bold]System Check[/bold]\n")
    
    all_ok = True
    
    # Check Python version
    py_version = sys.version_info
    if py_version >= (3, 10):
        console.print(f"[green]OK[/green] Python {py_version.major}.{py_version.minor}")
    else:
        console.print(f"[red]FAIL[/red] Python {py_version.major}.{py_version.minor} (need 3.10+)")
        all_ok = False
    
    # Check required packages
    packages = [
        ("instructor", "instructor"),
        ("anthropic", "anthropic"),
        ("pydantic", "pydantic"),
        ("pdf2image", "pdf2image"),
        ("PIL", "Pillow"),
        ("click", "click"),
        ("dotenv", "python-dotenv"),
        ("rich", "rich"),
    ]
    
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            console.print(f"[green]OK[/green] {package_name}")
        except ImportError:
            console.print(f"[red]FAIL[/red] {package_name} not installed")
            all_ok = False
    
    # Check poppler
    try:
        from pdf2image import pdfinfo_from_path
        # Try to call pdfinfo (will fail if poppler not installed)
        console.print("[green]OK[/green] poppler (for PDF conversion)")
    except Exception:
        console.print("[yellow]?[/yellow] poppler - install separately:")
        console.print("    macOS: brew install poppler")
        console.print("    Ubuntu: sudo apt-get install poppler-utils")
        console.print("    Windows: Download from github.com/oschwartz10612/poppler-windows")
    
    # Check API key
    if os.getenv("ANTHROPIC_API_KEY"):
        console.print("[green]OK[/green] ANTHROPIC_API_KEY is set")
    else:
        console.print("[red]FAIL[/red] ANTHROPIC_API_KEY not set")
        all_ok = False
    
    console.print()
    if all_ok:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        console.print("[bold red]Some checks failed. Please install missing dependencies.[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--name", "-n",
    required=True,
    help="Name for the extraction output"
)
@click.option(
    "--schema", "-s",
    type=click.Path(exists=True),
    default=None,
    help="Path to form schema JSON (from 'scan' command)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./extractions",
    help="Output directory for extraction results"
)
@click.option(
    "--model",
    default="claude-sonnet-4-20250514",
    help="Claude model (sonnet-4 default, use opus for complex forms)"
)
@click.option(
    "--start-page",
    type=int,
    default=1,
    help="Start page number (1-indexed, default: 1)"
)
@click.option(
    "--end-page",
    type=int,
    default=None,
    help="End page number (1-indexed, default: last page)"
)
def extract(
    source: str,
    name: str,
    schema: Optional[str],
    output: str,
    model: str,
    start_page: int,
    end_page: Optional[int],
):
    """
    Extract data from a FILLED form using multi-stage pipeline.
    
    This command processes filled-in forms and extracts:
    - Standard field values
    - Handwritten annotations
    - Brackets, lines, and spatial connections
    - Grouped items with their meanings
    - Cross-page references
    
    SOURCE can be a PDF file or a folder containing page images.
    
    Examples:
    
        # Extract from filled PDF (no schema)
        python main.py extract ./filled_form.pdf --name "patient_smith"
        
        # Extract with schema for better field mapping
        python main.py extract ./filled_form.pdf --name "patient_smith" --schema ./templates/exam_schema.json
        
        # Extract from folder of images
        python main.py extract ./scanned_pages/ --name "patient_doe"
    """
    source_path = Path(source)
    output_path = Path(output)
    
    # Page range info
    page_range_str = f"Pages {start_page}-{end_page}" if end_page else f"Pages {start_page}-end"
    if start_page == 1 and end_page is None:
        page_range_str = "All pages"
    
    # Header
    console.print(Panel.fit(
        f"[bold cyan]Multi-Stage Form Extraction Pipeline[/bold cyan]\n"
        f"Form: {name}\n"
        f"Source: {source_path}\n"
        f"Page Range: {page_range_str}\n"
        f"Model: {model}\n"
        f"Schema: {schema or 'None (will extract without field mapping)'}",
        title="Form Extractor - Phase 2"
    ))
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        sys.exit(1)
    
    # Initialize services
    pdf_processor = PDFProcessor(dpi=150)  # Lower DPI for cost efficiency
    
    try:
        # Load schema if provided
        form_schema = None
        if schema:
            schema_gen = SchemaGenerator(Path(schema).parent)
            form_schema = schema_gen.load_form_schema(Path(schema))
            console.print(f"[green]Loaded schema: {form_schema.form_name}[/green]")
        
        # Get page images
        console.print("\n[bold]Step 1: Preparing page images[/bold]")
        
        if source_path.is_file() and source_path.suffix.lower() == ".pdf":
            image_paths = pdf_processor.convert_pdf_to_images(
                source_path,
                prefix=name.lower().replace(" ", "_"),
                start_page=start_page,
                end_page=end_page,
            )
        elif source_path.is_dir():
            image_paths = pdf_processor.load_images_from_folder(source_path)
            # Apply page range to folder images
            if start_page > 1 or end_page is not None:
                actual_end = end_page if end_page else len(image_paths)
                image_paths = image_paths[start_page - 1:actual_end]
        else:
            console.print(f"[red]Error: Source must be a PDF file or folder of images[/red]")
            sys.exit(1)
        
        console.print(f"[green]Found {len(image_paths)} pages to process[/green]")
        
        # Initialize extraction pipeline
        console.print("\n[bold]Step 2: Running Multi-Stage Extraction Pipeline[/bold]")
        console.print("[dim]6 stages per page: Visual Detection > OCR > Spatial Analysis > Field Mapping > Semantic Understanding > Validation[/dim]\n")
        
        pipeline = ExtractionPipeline(api_key=api_key, model=model)
        
        # Extract form
        result = pipeline.extract_form(
            image_paths=image_paths,
            form_schema=form_schema,
            form_name=name,
        )
        
        # Save results
        console.print("\n[bold]Step 3: Saving extraction results[/bold]")
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save complete result as JSON
        result_file = output_path / f"{result.form_id}_extraction.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        console.print(f"  [green]Saved: {result_file.name}[/green]")
        
        # Save per-page results
        for page in result.pages:
            page_file = output_path / f"{result.form_id}_page_{page.page_number}.json"
            with open(page_file, "w", encoding="utf-8") as f:
                json.dump(page.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
            console.print(f"  [dim]Saved: {page_file.name}[/dim]")
        
        # Save human-readable summary
        summary_file = output_path / f"{result.form_id}_summary.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"Extraction Summary: {result.form_name}\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(f"Patient Name: {result.patient_name or 'Not extracted'}\n")
            f.write(f"Patient DOB: {result.patient_dob or 'Not extracted'}\n")
            f.write(f"Form Date: {result.form_date or 'Not extracted'}\n")
            f.write(f"Extracted: {result.extraction_timestamp}\n\n")
            f.write(f"Overall Confidence: {result.overall_confidence:.1%}\n")
            f.write(f"Items Needing Review: {result.total_items_needing_review}\n\n")
            
            for page in result.pages:
                f.write(f"\nPage {page.page_number}:\n")
                f.write(f"  Fields extracted: {len(page.field_values)}\n")
                f.write(f"  Annotation groups: {len(page.annotation_groups)}\n")
                f.write(f"  Free-form annotations: {len(page.free_form_annotations)}\n")
                f.write(f"  Spatial connections: {len(page.spatial_connections)}\n")
                f.write(f"  Cross-page references: {len(page.cross_page_references)}\n")
                f.write(f"  Confidence: {page.overall_confidence:.1%}\n")
                
                if page.annotation_groups:
                    f.write(f"\n  Annotation Groups:\n")
                    for group in page.annotation_groups:
                        f.write(f"    - {group.interpretation}\n")
                        if group.annotation_text:
                            f.write(f"      Note: \"{group.annotation_text}\"\n")
                
                if page.review_reasons:
                    f.write(f"\n  [!] Items for review:\n")
                    for reason in page.review_reasons:
                        f.write(f"    - {reason}\n")
        
        console.print(f"  [green]Saved: {summary_file.name}[/green]")
        
        # Print summary
        console.print(f"\n[bold green]Extraction Complete![/bold green]")
        console.print(f"\n[bold]Results Summary:[/bold]")
        console.print(f"  Patient: {result.patient_name or 'N/A'}")
        console.print(f"  Overall Confidence: {result.overall_confidence:.1%}")
        console.print(f"  Items for Review: {result.total_items_needing_review}")
        
        if result.all_review_reasons:
            console.print(f"\n[yellow]WARNING - Review Required:[/yellow]")
            for reason in result.all_review_reasons[:5]:
                console.print(f"  - {reason}")
            if len(result.all_review_reasons) > 5:
                console.print(f"  ... and {len(result.all_review_reasons) - 5} more")
        
        console.print(f"\n[bold]Output saved to: {output_path}[/bold]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)
    
    finally:
        pdf_processor.cleanup()


if __name__ == "__main__":
    cli()
