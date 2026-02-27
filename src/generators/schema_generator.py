"""
JSON schema generator - outputs form schemas as JSON files.
"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console

from ..models import FormSchema, PageSchema

console = Console()


class SchemaGenerator:
    """
    Generates JSON schema files from analyzed form structures.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to write schema files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_page_schema(
        self,
        page: PageSchema,
        form_id: str,
    ) -> Path:
        """
        Save a single page schema to JSON.
        
        Args:
            page: The page schema to save
            form_id: Form identifier for filename
            
        Returns:
            Path to the saved file
        """
        filename = f"{form_id}_page_{page.page_number}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                page.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        console.print(f"  [dim]Saved: {filename}[/dim]")
        return filepath
    
    def save_form_schema(
        self,
        form: FormSchema,
    ) -> Path:
        """
        Save the complete form schema to JSON.
        
        Args:
            form: The complete form schema
            
        Returns:
            Path to the saved file
        """
        filename = f"{form.form_id}_schema.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                form.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        console.print(f"[green]Saved complete schema: {filename}[/green]")
        return filepath
    
    def load_form_schema(self, filepath: Path) -> FormSchema:
        """
        Load a form schema from JSON.
        
        Args:
            filepath: Path to the JSON schema file
            
        Returns:
            FormSchema instance
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return FormSchema.model_validate(data)
    
    def generate_summary(self, form: FormSchema) -> str:
        """
        Generate a human-readable summary of the form schema.
        
        Args:
            form: The form schema
            
        Returns:
            Summary string
        """
        lines = [
            f"Form Schema Summary: {form.form_name}",
            f"{'=' * 50}",
            f"Form ID: {form.form_id}",
            f"Total Pages: {form.total_pages}",
            f"Total Fields: {form.total_fields}",
            f"Total Tables: {form.total_tables}",
            "",
        ]
        
        for page in form.pages:
            lines.append(f"Page {page.page_number}: {page.page_title or 'Untitled'}")
            lines.append(f"  Fields: {page.total_fields}")
            lines.append(f"  Tables: {page.total_tables}")
            lines.append(f"  Sections: {len(page.sections)}")
            lines.append(f"  Complexity: {page.complexity_score}/10")
            
            if page.sections:
                for section in page.sections:
                    lines.append(f"    - {section.section_title}: {len(section.fields)} fields")
            
            lines.append("")
        
        if form.cross_page_references:
            lines.append("Cross-Page References:")
            for ref in form.cross_page_references:
                lines.append(f"  - {ref}")
            lines.append("")
        
        return "\n".join(lines)
