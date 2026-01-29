"""
Claude-based form structure analyzer using instructor for structured outputs.
"""

import base64
import os
from pathlib import Path
from typing import Optional

import anthropic
import instructor
from pydantic import BaseModel, Field
from rich.console import Console

from ..models import (
    PageSchema,
    SectionSchema,
    FormFieldSchema,
    TableSchema,
    TableColumnSchema,
    FieldType,
    DataType,
)

console = Console()


# =============================================================================
# ANALYSIS PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a medical form structure analyzer extracting INPUT FIELD SCHEMA from blank forms.

## CRITICAL: WHAT COUNTS AS A FIELD
Only count ACTUAL INPUT AREAS where data gets written/marked:
- Text input lines/boxes (where someone writes)
- Checkboxes/radio buttons (where someone marks)
- Signature/initials areas
- Date blanks (___/___/___)

## WHAT IS NOT A FIELD (DO NOT COUNT THESE):
- Section titles/headers (just labels, not inputs)
- Instruction text ("Please complete...", "Circle one:")
- Column/row headers in tables (the labels, not the cells)
- Static printed text
- Page numbers
- Form titles

## FIELD TYPES:
- text_short: Single-line input (name, word)
- text_long: Multi-line/paragraph input
- text_numeric: Number-only input (age, times per night)
- date: Date field (MM/DD/YYYY format)
- phone/email: Contact fields
- yes_no: YES/NO question (count as ONE field per question)
- checkbox_single: One standalone checkbox
- checkbox_multi: Group of checkboxes (count as ONE field with options array)
- radio_group: Mutually exclusive options (count as ONE field)
- circled_selection: Options to circle (count as ONE field with all options listed)
- numeric_scale/vas_scale: Pain scales
- signature/initials: Signature areas
- medication_list: Medication listing area

## KEY RULES:
1. YES/NO question = 1 field (not 2 separate checkboxes)
2. Group of checkboxes with one label = 1 field with multiple options
3. List of medications to circle = 1 circled_selection field with options array
4. Table = 1 TableSchema (not separate fields per cell)
5. Sub-questions under "If YES:" are separate fields linked via parent_field_id
6. Multi-part date (___/___/___) = 1 date field

## OUTPUT FORMAT:
- Group fields into logical sections
- Use snake_case field_ids prefixed with p{page_num}_
- List options in the 'options' array for selection fields
- Keep extraction_hints brief and useful"""


# =============================================================================
# RESPONSE MODEL FOR CLAUDE
# =============================================================================

class AnalyzedPage(BaseModel):
    """Response model for page analysis."""
    
    page_title: Optional[str] = Field(
        default=None,
        description="Title at top of this page if present"
    )
    sections: list[SectionSchema] = Field(
        default_factory=list,
        description="Organized sections found on this page"
    )
    standalone_fields: list[FormFieldSchema] = Field(
        default_factory=list,
        description="Fields not in any clear section"
    )
    standalone_tables: list[TableSchema] = Field(
        default_factory=list,
        description="Tables not in any clear section"
    )
    complexity_score: int = Field(
        default=5,
        ge=1,
        le=10,
        description="1-10 score of extraction difficulty"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes about cross-page references, special considerations"
    )


# =============================================================================
# FORM ANALYZER CLASS
# =============================================================================

class FormAnalyzer:
    """
    Analyzes blank form images using Claude to extract structure.
    Uses instructor for structured Pydantic outputs.
    
    COST OPTIMIZATION NOTES:
    - Default model is Sonnet 4 (5x cheaper than Opus)
    - Use --model claude-opus-4-5-20251101 for complex/dense forms
    - Lower DPI (150) works for most forms
    - Images are compressed before sending
    """
    
    # Model pricing reference (per million tokens):
    # claude-sonnet-4-20250514: $3 input, $15 output
    # claude-opus-4-5-20251101: $15 input, $75 output
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",  # Default to Sonnet for cost
        max_tokens: int = 16000,  # High enough for very complex pages
    ):
        """
        Initialize the analyzer.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: Sonnet 4 for cost efficiency)
            max_tokens: Max tokens for response (16000 handles complex pages)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in environment or pass api_key parameter."
            )
        
        self.model = model
        self.max_tokens = max_tokens
        
        # Create instructor-patched client
        self.client = instructor.from_anthropic(
            anthropic.Anthropic(api_key=self.api_key)
        )
    
    def _load_image_as_base64(
        self, 
        image_path: Path, 
        max_dimension: int = 1568,  # Claude's recommended max for vision
        jpeg_quality: int = 85,
    ) -> tuple[str, str]:
        """
        Load an image file, optimize it for Claude, and return base64 data.
        
        Cost optimization: Resizes large images and converts to JPEG for
        smaller payload (fewer input tokens = lower cost).
        
        Args:
            image_path: Path to image file
            max_dimension: Max width/height (1568 is Claude's sweet spot)
            jpeg_quality: JPEG compression quality (85 is good balance)
            
        Returns:
            Tuple of (base64_data, media_type)
        """
        try:
            from PIL import Image
            import io
            
            # Load and potentially resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if larger than max_dimension (maintains aspect ratio)
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save as JPEG to buffer (much smaller than PNG)
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=jpeg_quality, optimize=True)
                buffer.seek(0)
                
                image_data = base64.standard_b64encode(buffer.read()).decode("utf-8")
                return image_data, "image/jpeg"
                
        except ImportError:
            # Fallback: load raw file without optimization
            console.print("[yellow]Warning: PIL not available, sending uncompressed image[/yellow]")
            suffix = image_path.suffix.lower()
            media_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_types.get(suffix, "image/png")
            
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            
            return image_data, media_type
    
    def analyze_page(
        self,
        image_path: Path,
        page_number: int,
        form_name: str,
        previous_context: Optional[str] = None,
    ) -> PageSchema:
        """
        Analyze a single page image and extract its structure.
        
        Args:
            image_path: Path to the page image
            page_number: Page number (1-indexed)
            form_name: Name of the form (for field_id prefixes)
            previous_context: Optional context from previous pages
            
        Returns:
            PageSchema with extracted structure
        """
        console.print(f"  [cyan]Analyzing page {page_number}...[/cyan]")
        
        # Load image
        image_data, media_type = self._load_image_as_base64(image_path)
        
        # Build user message (concise to reduce input tokens)
        context_note = f"\nPrevious: {previous_context}" if previous_context else ""
        
        user_content = [
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
                "text": f"""Page {page_number} of "{form_name}". Extract INPUT fields only.

REMEMBER:
- 1 YES/NO question = 1 yes_no field (not 2)
- Checkbox group = 1 checkbox_multi with options array
- Circled options list = 1 circled_selection with options array  
- Table = 1 TableSchema (cells aren't separate fields)
- Section titles/headers are NOT fields

Use p{page_number}_ prefix for field_ids.{context_note}"""
            }
        ]
        
        # Call Claude with instructor for structured output
        try:
            result: AnalyzedPage = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                response_model=AnalyzedPage,
            )
            
            # Convert to PageSchema
            page_schema = PageSchema(
                page_number=page_number,
                page_title=result.page_title,
                sections=result.sections,
                standalone_fields=result.standalone_fields,
                standalone_tables=result.standalone_tables,
                complexity_score=result.complexity_score,
                notes=result.notes,
            )
            
            console.print(
                f"  [green]Page {page_number}: "
                f"{page_schema.total_fields} fields, "
                f"{page_schema.total_tables} tables, "
                f"{len(page_schema.sections)} sections[/green]"
            )
            
            return page_schema
            
        except Exception as e:
            console.print(f"  [red]Error analyzing page {page_number}: {e}[/red]")
            raise
    
    def generate_context_summary(self, pages: list[PageSchema]) -> str:
        """
        Generate a summary of analyzed pages for context.
        
        Args:
            pages: List of already analyzed pages
            
        Returns:
            Summary string for context
        """
        if not pages:
            return ""
        
        summaries = []
        for page in pages:
            field_ids = []
            for f in page.standalone_fields:
                field_ids.append(f.field_id)
            for section in page.sections:
                for f in section.fields:
                    field_ids.append(f.field_id)
            
            summaries.append(
                f"Page {page.page_number}: {page.page_title or 'Untitled'} - "
                f"Fields: {', '.join(field_ids[:5])}{'...' if len(field_ids) > 5 else ''}"
            )
        
        return "\n".join(summaries)
