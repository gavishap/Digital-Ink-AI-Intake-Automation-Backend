
"""
Extraction Script for: consents_2026

This is a stub script for Phase 2 extraction.
It demonstrates how to use the generated models with instructor
to extract data from filled-in forms.

Usage:
    python consents_2026_extractor.py path/to/filled_form.pdf --output results.json
"""

import os
import json
import base64
from pathlib import Path
from datetime import datetime

import click
import instructor
import anthropic
from rich.console import Console

from consents_2026_models import Consents2026Extraction

console = Console()

# Load API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")


EXTRACTION_PROMPT = """You are a medical form data extractor. Analyze this filled-in form page and extract all handwritten and marked data.

For EACH field:
1. Find the printed label
2. Identify any marks (handwriting, circles, checkmarks, X marks)
3. Extract the value, normalizing where appropriate
4. Note confidence level
5. Flag anything that needs human review

Watch for:
- Circled options vs checked boxes
- Crossed-out and changed answers
- "See attached" references
- Unclear handwriting
- Both YES and NO marked (flag for review)

Return complete structured data matching the schema."""


def extract_from_image(client, image_path: Path, page_number: int) -> dict:
    """Extract data from a single page image."""

    # Load image
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    suffix = image_path.suffix.lower()
    media_type = {"png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(suffix, "image/png")

    # This is a simplified extraction - in production you'd want to
    # use the full Consents2026Extraction model
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=8192,
        system=EXTRACTION_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Extract all data from page {page_number}."
                    }
                ]
            }
        ],
        response_model=Consents2026Extraction,
    )

    return response.model_dump()


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
def main(pdf_path: str, output: str):
    """Extract data from a filled form PDF."""

    console.print(f"[cyan]Extracting data from: {pdf_path}[/cyan]")

    # Initialize client
    client = instructor.from_anthropic(
        anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    )

    # TODO: Convert PDF to images and process each page
    # This stub shows the structure - implement full pipeline

    console.print("[yellow]Note: This is a stub script. Implement full extraction pipeline.[/yellow]")

    # Example output structure
    result = {
        "form_id": "consents_2026",
        "extracted_at": datetime.now().isoformat(),
        "pages": [],
        "needs_review": False,
    }

    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        console.print(f"[green]Saved to: {output}[/green]")
    else:
        console.print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
