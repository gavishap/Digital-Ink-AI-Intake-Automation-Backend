"""
Pydantic model generator - creates Python files with Pydantic models
ready for use with instructor in Phase 2 extraction.
"""

from pathlib import Path
from datetime import datetime
from textwrap import dedent

from rich.console import Console

from ..models import (
    FormSchema,
    PageSchema,
    SectionSchema,
    FormFieldSchema,
    TableSchema,
    FieldType,
    DataType,
)

console = Console()


class PydanticModelGenerator:
    """
    Generates Python files containing Pydantic models from form schemas.
    The generated models are ready to use with instructor for extraction.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to write Python files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _field_type_to_python(self, field: FormFieldSchema) -> str:
        """Convert field data type to Python type annotation."""
        type_map = {
            DataType.STRING: "str",
            DataType.INTEGER: "int",
            DataType.FLOAT: "float",
            DataType.BOOLEAN: "bool",
            DataType.DATE: "date",
            DataType.DATETIME: "datetime",
            DataType.LIST: "list",
            DataType.DICT: "dict",
            DataType.OPTIONAL_STRING: "Optional[str]",
            DataType.OPTIONAL_INT: "Optional[int]",
            DataType.OPTIONAL_FLOAT: "Optional[float]",
            DataType.OPTIONAL_BOOL: "Optional[bool]",
            DataType.OPTIONAL_DATE: "Optional[date]",
            DataType.LIST_STRING: "list[str]",
            DataType.LIST_DICT: "list[dict]",
        }
        
        base_type = type_map.get(field.data_type, "str")
        
        # Make optional if not required
        if not field.is_required and not base_type.startswith("Optional"):
            if base_type in ("str", "int", "float", "bool", "date", "datetime"):
                return f"Optional[{base_type}]"
        
        return base_type
    
    def _generate_field_line(self, field: FormFieldSchema, indent: int = 4) -> str:
        """Generate a single field definition line."""
        spaces = " " * indent
        python_type = self._field_type_to_python(field)
        
        # Build Field() arguments
        field_args = []
        
        # Default value
        if not field.is_required:
            field_args.append("default=None")
        
        # Description
        desc = field.field_label
        if field.expected_format:
            desc += f" (Format: {field.expected_format})"
        if field.helper_text:
            desc += f" - {field.helper_text}"
        field_args.append(f'description="{self._escape_string(desc)}"')
        
        # For scales, add constraints
        if field.scale_min is not None:
            field_args.append(f"ge={field.scale_min}")
        if field.scale_max is not None:
            field_args.append(f"le={field.scale_max}")
        
        field_def = f"{spaces}{field.field_id}: {python_type} = Field({', '.join(field_args)})"
        
        # Add comment for options
        if field.options:
            options_str = ", ".join(field.options[:5])
            if len(field.options) > 5:
                options_str += "..."
            field_def += f"  # Options: {options_str}"
        
        return field_def
    
    def _escape_string(self, s: str) -> str:
        """Escape a string for use in Python code."""
        return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    
    def _generate_section_class(
        self,
        section: SectionSchema,
        prefix: str = "",
    ) -> str:
        """Generate a Pydantic class for a section."""
        class_name = self._to_class_name(f"{prefix}{section.section_id}")
        
        lines = [
            f"class {class_name}(BaseModel):",
            f'    """',
            f"    {section.section_title}",
        ]
        
        if section.instructions:
            lines.append(f"    {section.instructions}")
        
        lines.append(f'    """')
        lines.append("")
        
        if not section.fields and not section.tables:
            lines.append("    pass")
        else:
            for field in section.fields:
                lines.append(self._generate_field_line(field))
            
            # Add table fields as nested lists
            for table in section.tables:
                table_class = self._to_class_name(table.table_id)
                lines.append(
                    f"    {table.table_id}: list[{table_class}Row] = Field("
                    f"default_factory=list, "
                    f'description="{table.table_title or table.table_id}")'
                )
        
        lines.append("")
        return "\n".join(lines)
    
    def _generate_table_row_class(self, table: TableSchema) -> str:
        """Generate a Pydantic class for table rows."""
        class_name = self._to_class_name(f"{table.table_id}_row")
        
        lines = [
            f"class {class_name}(BaseModel):",
            f'    """Row data for {table.table_title or table.table_id}."""',
            "",
        ]
        
        for col in table.columns:
            col_type = self._data_type_to_python(col.data_type)
            lines.append(
                f'    {col.column_id}: {col_type} = Field(default=None, description="{col.header}")'
            )
        
        # Add row label field if applicable
        if table.row_labels:
            lines.append(
                '    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")'
            )
        
        lines.append("")
        return "\n".join(lines)
    
    def _data_type_to_python(self, data_type: DataType) -> str:
        """Convert DataType enum to Python type string."""
        type_map = {
            DataType.STRING: "Optional[str]",
            DataType.INTEGER: "Optional[int]",
            DataType.FLOAT: "Optional[float]",
            DataType.BOOLEAN: "Optional[bool]",
            DataType.DATE: "Optional[date]",
            DataType.DATETIME: "Optional[datetime]",
            DataType.LIST: "Optional[list]",
            DataType.DICT: "Optional[dict]",
        }
        return type_map.get(data_type, "Optional[str]")
    
    def _to_class_name(self, snake_case: str) -> str:
        """Convert snake_case to PascalCase class name."""
        parts = snake_case.replace("-", "_").split("_")
        return "".join(word.capitalize() for word in parts if word)
    
    def generate_models_file(self, form: FormSchema) -> Path:
        """
        Generate a Python file with all Pydantic models for the form.
        
        Args:
            form: The complete form schema
            
        Returns:
            Path to the generated file
        """
        filename = f"{form.form_id}_models.py"
        filepath = self.output_dir / filename
        
        # Collect all tables for row classes
        all_tables: list[TableSchema] = []
        for page in form.pages:
            all_tables.extend(page.standalone_tables)
            for section in page.sections:
                all_tables.extend(section.tables)
        
        # Build file content
        content = self._generate_file_header(form)
        content += self._generate_imports()
        content += self._generate_enums_section(form)
        content += self._generate_evidence_models()
        
        # Generate table row classes first
        for table in all_tables:
            content += self._generate_table_row_class(table)
        
        # Generate section classes
        for page in form.pages:
            for section in page.sections:
                content += self._generate_section_class(
                    section, 
                    prefix=f"p{page.page_number}_"
                )
        
        # Generate page classes
        for page in form.pages:
            content += self._generate_page_class(page)
        
        # Generate main form extraction model
        content += self._generate_form_extraction_model(form)
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        console.print(f"[green]Generated models: {filename}[/green]")
        return filepath
    
    def _generate_file_header(self, form: FormSchema) -> str:
        """Generate file header with documentation."""
        return dedent(f'''
            """
            Pydantic Models for: {form.form_name}
            Form ID: {form.form_id}
            
            Generated on: {datetime.now().isoformat()}
            Total Pages: {form.total_pages}
            Total Fields: {form.total_fields}
            
            These models are designed for use with the `instructor` package
            to extract data from filled-in versions of this form.
            
            Usage:
                import instructor
                import anthropic
                from {form.form_id}_models import {self._to_class_name(form.form_id)}Extraction
                
                client = instructor.from_anthropic(anthropic.Anthropic())
                
                result = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=8192,
                    messages=[...],
                    response_model={self._to_class_name(form.form_id)}Extraction,
                )
            """
            
        ''')
    
    def _generate_imports(self) -> str:
        """Generate import statements."""
        return dedent('''
            from datetime import date, datetime
            from enum import Enum
            from typing import Optional, Any
            from pydantic import BaseModel, Field
            
            
        ''')
    
    def _generate_enums_section(self, form: FormSchema) -> str:
        """Generate enum classes for fields with options."""
        enums = []
        seen_enums = set()
        
        def collect_enums(fields: list[FormFieldSchema]):
            for field in fields:
                if field.options and len(field.options) > 1:
                    enum_name = self._to_class_name(f"{field.field_id}_options")
                    if enum_name not in seen_enums:
                        seen_enums.add(enum_name)
                        enum_values = [
                            f'    {self._to_enum_value(opt)} = "{opt}"'
                            for opt in field.options
                        ]
                        enums.append(
                            f"class {enum_name}(str, Enum):\n" +
                            "\n".join(enum_values) + "\n\n"
                        )
        
        for page in form.pages:
            collect_enums(page.standalone_fields)
            for section in page.sections:
                collect_enums(section.fields)
        
        if enums:
            return "# Field Options Enums\n" + "".join(enums) + "\n"
        return ""
    
    def _to_enum_value(self, value: str) -> str:
        """Convert a string value to valid enum member name."""
        # Replace spaces and special chars with underscore
        clean = "".join(c if c.isalnum() else "_" for c in value)
        # Ensure it starts with a letter
        if clean and clean[0].isdigit():
            clean = "VALUE_" + clean
        return clean.upper() or "UNKNOWN"
    
    def _generate_evidence_models(self) -> str:
        """Generate the SourceEvidence and ExtractedFieldValue models."""
        return dedent('''
            # =============================================================================
            # EXTRACTION EVIDENCE MODELS
            # =============================================================================
            
            class MarkType(str, Enum):
                """Types of marks found on forms."""
                HANDWRITING = "handwriting"
                CIRCLE = "circle"
                CHECKMARK = "checkmark"
                X_MARK = "x_mark"
                CROSSED_OUT = "crossed_out"
                ARROW = "arrow"
                UNDERLINE = "underline"
                FILL_IN_BLANK = "fill_in_blank"
            
            
            class SourceEvidence(BaseModel):
                """
                Tracks where extracted data came from on the form.
                Include this for audit trail and review flagging.
                """
                page_number: int = Field(description="Page number where value was found")
                anchor_text: str = Field(description="The printed label near the value")
                mark_type: MarkType = Field(description="Type of mark (handwriting, circle, etc.)")
                raw_handwriting: Optional[str] = Field(default=None, description="Exactly what is written")
                confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
                pertains_to: str = Field(description="What this value means")
                needs_review: bool = Field(default=False, description="Flag for human review")
                review_reason: Optional[str] = Field(default=None, description="Why review is needed")
            
            
            class ExtractedFieldValue(BaseModel):
                """Generic extracted field value with evidence."""
                field_id: str = Field(description="The field this value corresponds to")
                raw_value: Optional[str] = Field(default=None, description="Raw extracted value")
                normalized_value: Any = Field(default=None, description="Cleaned/standardized value")
                is_empty: bool = Field(default=False, description="True if field was blank")
                evidence: Optional[SourceEvidence] = Field(default=None, description="Extraction evidence")
                both_options_marked: bool = Field(default=False, description="Both yes/no marked")
                crossed_out_values: list[str] = Field(default_factory=list, description="Changed answers")
                see_attached_reference: Optional[str] = Field(default=None, description="Reference to attachment")
            
            
        ''')
    
    def _generate_page_class(self, page: PageSchema) -> str:
        """Generate a Pydantic class for a page."""
        class_name = f"Page{page.page_number}Data"
        
        lines = [
            f"class {class_name}(BaseModel):",
            f'    """',
            f"    Page {page.page_number}: {page.page_title or 'Untitled'}",
            f"    Complexity: {page.complexity_score}/10",
            f'    """',
            "",
        ]
        
        # Add section references
        for section in page.sections:
            section_class = self._to_class_name(f"p{page.page_number}_{section.section_id}")
            lines.append(
                f"    {section.section_id}: Optional[{section_class}] = Field("
                f'default=None, description="{section.section_title}")'
            )
        
        # Add standalone fields
        for field in page.standalone_fields:
            lines.append(self._generate_field_line(field))
        
        # Add standalone table references
        for table in page.standalone_tables:
            table_class = self._to_class_name(f"{table.table_id}_row")
            lines.append(
                f"    {table.table_id}: list[{table_class}] = Field("
                f"default_factory=list, "
                f'description="{table.table_title or table.table_id}")'
            )
        
        if not page.sections and not page.standalone_fields and not page.standalone_tables:
            lines.append("    pass")
        
        lines.append("")
        return "\n".join(lines)
    
    def _generate_form_extraction_model(self, form: FormSchema) -> str:
        """Generate the main form extraction model."""
        class_name = f"{self._to_class_name(form.form_id)}Extraction"
        
        lines = [
            "# =============================================================================",
            "# MAIN EXTRACTION MODEL",
            "# =============================================================================",
            "",
            f"class {class_name}(BaseModel):",
            f'    """',
            f"    Complete extraction model for: {form.form_name}",
            f"    ",
            f"    Use this model with instructor to extract all data from filled forms.",
            f'    """',
            "",
            '    # Metadata',
            '    extraction_timestamp: Optional[datetime] = Field(default=None, description="When extraction occurred")',
            '    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")',
            '    needs_review: bool = Field(default=False, description="Form needs human review")',
            '    review_reasons: list[str] = Field(default_factory=list, description="Why review is needed")',
            "",
            "    # Page Data",
        ]
        
        for page in form.pages:
            page_class = f"Page{page.page_number}Data"
            lines.append(
                f"    page_{page.page_number}: Optional[{page_class}] = Field("
                f"default=None, "
                f'description="Page {page.page_number}: {page.page_title or "Untitled"}")'
            )
        
        lines.append("")
        lines.append("    # Field-level evidence (optional, for detailed tracking)")
        lines.append(
            "    field_evidence: list[ExtractedFieldValue] = Field("
            "default_factory=list, "
            'description="Detailed evidence for each extracted field")'
        )
        
        lines.append("")
        return "\n".join(lines)
    
    def generate_extractor_stub(self, form: FormSchema) -> Path:
        """
        Generate a stub extraction script.
        
        Args:
            form: The form schema
            
        Returns:
            Path to the generated file
        """
        filename = f"{form.form_id}_extractor.py"
        filepath = self.output_dir / filename
        
        class_name = f"{self._to_class_name(form.form_id)}Extraction"
        
        content = dedent(f'''
            """
            Extraction Script for: {form.form_name}
            
            This is a stub script for Phase 2 extraction.
            It demonstrates how to use the generated models with instructor
            to extract data from filled-in forms.
            
            Usage:
                python {filename} path/to/filled_form.pdf --output results.json
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
            
            from {form.form_id}_models import {class_name}
            
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
                media_type = {{"png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}}.get(suffix, "image/png")
                
                # This is a simplified extraction - in production you'd want to
                # use the full {class_name} model
                response = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    max_tokens=8192,
                    system=EXTRACTION_PROMPT,
                    messages=[
                        {{
                            "role": "user",
                            "content": [
                                {{
                                    "type": "image",
                                    "source": {{
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_data,
                                    }}
                                }},
                                {{
                                    "type": "text",
                                    "text": f"Extract all data from page {{page_number}}."
                                }}
                            ]
                        }}
                    ],
                    response_model={class_name},
                )
                
                return response.model_dump()
            
            
            @click.command()
            @click.argument("pdf_path", type=click.Path(exists=True))
            @click.option("--output", "-o", type=click.Path(), help="Output JSON file")
            def main(pdf_path: str, output: str):
                """Extract data from a filled form PDF."""
                
                console.print(f"[cyan]Extracting data from: {{pdf_path}}[/cyan]")
                
                # Initialize client
                client = instructor.from_anthropic(
                    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                )
                
                # TODO: Convert PDF to images and process each page
                # This stub shows the structure - implement full pipeline
                
                console.print("[yellow]Note: This is a stub script. Implement full extraction pipeline.[/yellow]")
                
                # Example output structure
                result = {{
                    "form_id": "{form.form_id}",
                    "extracted_at": datetime.now().isoformat(),
                    "pages": [],
                    "needs_review": False,
                }}
                
                if output:
                    with open(output, "w") as f:
                        json.dump(result, f, indent=2)
                    console.print(f"[green]Saved to: {{output}}[/green]")
                else:
                    console.print(json.dumps(result, indent=2))
            
            
            if __name__ == "__main__":
                main()
        ''')
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        console.print(f"[green]Generated extractor stub: {filename}[/green]")
        return filepath
