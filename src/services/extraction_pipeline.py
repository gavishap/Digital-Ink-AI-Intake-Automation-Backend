"""
Multi-Stage LLM Extraction Pipeline (v2 - Schema-Guided with Dual-Image Support)

A sophisticated pipeline for extracting both structured field data
AND free-form annotations, spatial relationships, and connected elements
from filled medical forms.

KEY IMPROVEMENTS (v2):
- Dual-image extraction: Compare blank template with filled form
- Schema-guided detection: Use schema to constrain what we look for
- Conservative spatial analysis: Only report brackets that visually exist
- Robust date parsing: Year context and digit disambiguation
- Full schema utilization in all 6 stages

Pipeline Stages:
1. Visual Element Detection - Schema-guided, differential from blank
2. OCR & Transcription - Format-aware with year context
3. Spatial Analysis - Conservative, schema-constrained
4. Field Value Extraction - Strict schema field mapping
5. Semantic Understanding - Form-context aware
6. Validation & Cross-Reference - Schema-aware validation

Primary: Qwen2.5-VL-32B via Fireworks AI (OpenAI-compatible API).
Fallback: Claude Sonnet 4 via Anthropic API.
Uses instructor for structured outputs with both providers.
"""

import base64
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

import anthropic
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from rich.console import Console

from ..models.annotations import (
    VisualElement,
    VisualMarkType,
    BoundingBox,
    SpatialConnection,
    AnnotationGroup,
    FreeFormAnnotation,
    CircledSelection,
    CrossPageReference,
    PageExtractionResult,
    FormExtractionResult,
)
from ..models import FormSchema, PageSchema

console = Console()


# =============================================================================
# SCHEMA HELPER FUNCTIONS
# =============================================================================

def extract_circled_selection_options(page_schema: Optional[PageSchema]) -> dict[str, list[str]]:
    """Extract all circled_selection field options from schema."""
    options_map = {}
    if not page_schema:
        return options_map
    
    def process_fields(fields):
        for field in fields:
            if field.field_type == "circled_selection" and field.options:
                options_map[field.field_id] = field.options
    
    # Process standalone fields
    process_fields(page_schema.standalone_fields)
    
    # Process section fields
    for section in page_schema.sections:
        process_fields(section.fields)
        for subsection in getattr(section, 'subsections', []):
            process_fields(subsection.fields)
    
    return options_map


def extract_date_fields(page_schema: Optional[PageSchema]) -> list[dict]:
    """Extract all date field info from schema."""
    date_fields = []
    if not page_schema:
        return date_fields
    
    def process_fields(fields):
        for field in fields:
            if field.field_type == "date":
                date_fields.append({
                    "field_id": field.field_id,
                    "field_label": field.field_label,
                    "expected_format": field.expected_format or "MM/DD/YYYY",
                    "position": field.position_description,
                })
    
    process_fields(page_schema.standalone_fields)
    for section in page_schema.sections:
        process_fields(section.fields)
    
    return date_fields


def get_schema_summary(page_schema: Optional[PageSchema]) -> str:
    """Generate a concise schema summary for prompts."""
    if not page_schema:
        return "No schema provided - extract all visible handwritten content."
    
    summary_parts = []
    summary_parts.append(f"Page {page_schema.page_number}: {page_schema.page_title or 'Untitled'}")
    
    field_count = 0
    field_types = {}
    
    def count_fields(fields):
        nonlocal field_count
        for field in fields:
            field_count += 1
            ft = field.field_type
            field_types[ft] = field_types.get(ft, 0) + 1
    
    count_fields(page_schema.standalone_fields)
    for section in page_schema.sections:
        count_fields(section.fields)
    
    summary_parts.append(f"Total fields: {field_count}")
    summary_parts.append(f"Field types: {', '.join(f'{k}({v})' for k, v in field_types.items())}")
    
    return "\n".join(summary_parts)


def get_field_by_role(page_schema: Optional[PageSchema], role_keywords: list[str]) -> Optional[str]:
    """Find field ID that matches role keywords (e.g., 'nurse', 'patient')."""
    if not page_schema:
        return None
    
    def search_fields(fields):
        for field in fields:
            label_lower = field.field_label.lower()
            id_lower = field.field_id.lower()
            for keyword in role_keywords:
                if keyword in label_lower or keyword in id_lower:
                    return field.field_id
        return None
    
    result = search_fields(page_schema.standalone_fields)
    if result:
        return result
    
    for section in page_schema.sections:
        result = search_fields(section.fields)
        if result:
            return result
    
    return None


# =============================================================================
# STAGE RESPONSE MODELS (for instructor structured output)
# =============================================================================

class Stage1_VisualElements(BaseModel):
    """Stage 1: Key visual elements (handwriting and marks only)."""
    
    class DetectedElement(BaseModel):
        element_id: str
        element_type: str = Field(description="'handwriting', 'checkmark', 'circle', 'bracket', 'margin_note', 'unknown'")
        description: str = Field(description="BRIEF description, max 20 words")
        location: str = Field(description="'top-left', 'top-center', 'top-right', 'middle-left', etc.")
        is_handwritten: bool = Field(default=True)
        mark_type: Optional[str] = Field(default=None)
        
    elements: list[DetectedElement] = Field(description="Key visual elements detected", max_length=100)
    total_handwritten: int
    total_marks: int
    has_groupings: bool = Field(default=False)
    has_margin_notes: bool = Field(default=False)
    complexity: str = Field(description="'simple', 'moderate', 'complex'")


class Stage2_TextExtraction(BaseModel):
    """Stage 2: OCR results for all text elements."""
    
    class ExtractedText(BaseModel):
        element_id: str
        raw_text: str = Field(description="Exact transcription of handwriting")
        normalized_text: Optional[str] = Field(default=None, description="Cleaned/standardized version")
        text_type: str = Field(description="'name', 'date', 'number', 'medication', 'note', 'address', 'phone', 'other'")
        confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        is_legible: bool
        alternative_readings: list[str] = Field(default_factory=list, description="If ambiguous, other possible readings")
        
    extracted_texts: list[ExtractedText]
    overall_legibility: str = Field(description="'excellent', 'good', 'fair', 'poor'")


class Stage3_SpatialRelationships(BaseModel):
    """Stage 3: Detected spatial relationships and connections."""
    
    class Connection(BaseModel):
        connection_id: str
        connector_type: str = Field(description="'bracket', 'line', 'arrow', 'enclosure'")
        connector_element_id: str
        connects_elements: list[str] = Field(description="Element IDs being connected/grouped")
        points_to_element: Optional[str] = Field(default=None, description="If arrow, what it points to")
        annotation_text: Optional[str] = Field(default=None, description="Any text associated with this grouping")
        inferred_meaning: str = Field(description="What this connection seems to mean")
        confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        
    connections: list[Connection]
    has_complex_groupings: bool
    grouping_summary: str = Field(description="Summary of all groupings found")


class Stage4_FieldValues(BaseModel):
    """Stage 4: Values mapped to known form fields."""
    
    class FieldValue(BaseModel):
        field_id: str
        field_label: str
        extracted_value: Optional[str] = None
        value_type: str = Field(description="'text', 'date', 'number', 'yes_no', 'checkbox', 'circled', 'multiple_choice'")
        is_checked: Optional[bool] = Field(default=None, description="For checkboxes/yes-no")
        circled_options: Optional[list[str]] = Field(default_factory=list, description="For circled selections")
        confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        has_correction: bool = Field(default=False, description="Was something crossed out and changed")
        original_value: Optional[str] = Field(default=None, description="If corrected, the original value")
        
    field_values: list[FieldValue]
    unmapped_handwriting: list[str] = Field(description="Handwritten items that don't map to known fields")


class Stage5_SemanticAnalysis(BaseModel):
    """Stage 5: Semantic understanding of annotations and groups."""
    
    class AnnotationInterpretation(BaseModel):
        annotation_id: str
        raw_text: str
        interpretation: str = Field(description="What this annotation means in medical/form context")
        purpose: str = Field(description="'clarification', 'additional_info', 'correction', 'cross_reference', 'grouping_label', 'instruction'")
        relates_to_fields: list[str] = Field(default_factory=list)
        relates_to_elements: list[str] = Field(default_factory=list)
        clinical_relevance: Optional[str] = Field(default=None, description="Medical significance if any")
        confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
        needs_human_review: bool
        review_reason: Optional[str] = Field(default=None)
        
    class GroupInterpretation(BaseModel):
        group_id: str
        member_elements: list[str]
        group_meaning: str = Field(description="What this group represents")
        annotation_text: Optional[str]
        medical_interpretation: str = Field(description="Clinical meaning of this grouping")
        
    annotations: list[AnnotationInterpretation]
    groups: list[GroupInterpretation]
    cross_page_references: list[dict] = Field(description="References to other pages/sheets")
    overall_interpretation: str = Field(description="Summary of all annotations and their meanings")


class Stage6_Validation(BaseModel):
    """Stage 6: Validation and quality assessment."""
    
    class ValidationIssue(BaseModel):
        issue_id: str
        issue_type: str = Field(description="'illegible', 'ambiguous', 'contradictory', 'missing', 'unclear_connection'")
        affected_elements: list[str]
        description: str
        suggested_resolution: Optional[str] = Field(default=None)
        requires_human_review: bool
        
    class CrossValidation(BaseModel):
        check_type: str
        elements_checked: list[str]
        passed: bool
        notes: Optional[str] = Field(default=None)
        
    validation_issues: list[ValidationIssue]
    cross_validations: list[CrossValidation]
    overall_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    extraction_quality: str = Field(description="'high', 'medium', 'low'")
    total_items_for_review: int
    summary: str


# =============================================================================
# PROMPTS FOR EACH STAGE (v2 - Schema-Guided)
# =============================================================================

STAGE1_PROMPT_TEMPLATE = """You are analyzing a FILLED medical form to identify handwritten content and marks.

{dual_image_instruction}

SCHEMA CONTEXT:
{schema_summary}

CIRCLED SELECTION FIELDS - VALID OPTIONS ONLY:
{circled_options_text}

CRITICAL RULES FOR CIRCLE DETECTION:
1. For medication lists or selection fields, ONLY report a circle if the circled text EXACTLY matches an option listed above
2. Do NOT guess or infer circles - you must see a clear hand-drawn circle around the text
3. If you're uncertain whether something is circled, DO NOT report it
4. Printed text without circles should NOT be reported as circled

WHAT TO DETECT:
1. **Handwriting** - Names, dates, numbers, notes written in fields
2. **Circles around options** - ONLY around text that matches schema options above
3. **Checkmarks/X marks** - On YES/NO or checkbox fields
4. **Margin notes** - Additional text written outside normal fields

WHAT TO IGNORE:
- All printed text (it's on the blank form too)
- Text that is NOT circled even if it appears in a selection list
- Smudges or artifacts that aren't clear marks

For each element, provide:
- A unique ID (hw_1, mark_1, circle_1, etc.)
- Type (handwriting, checkmark, circle, margin_note)
- Brief description (max 15 words)
- Location (top/middle/bottom, left/center/right)

BE CONSERVATIVE: Only report elements you are confident exist as handwritten additions."""


STAGE2_PROMPT_TEMPLATE = """You are an expert medical form OCR system. Transcribe handwritten text with high accuracy.

{dual_image_instruction}

DATE FIELDS ON THIS PAGE:
{date_fields_info}

CRITICAL DATE PARSING RULES:
1. Current year context: Forms are from year {current_year}
2. Expected date format: {date_format}
3. If year looks like 2019, 2020, etc. but context suggests {current_year}, prefer {current_year}
4. Common handwriting confusions to watch for:
   - "1" vs "7": A "1" has NO horizontal stroke at top; "7" HAS a horizontal stroke
   - "2" vs "8": A "2" has an open bottom; "8" has two closed loops
   - "6" vs "9": Check the loop position (top vs bottom)
   - "0" vs "6": A "0" is fully closed; "6" has a tail

For EACH handwritten element:
1. **Transcribe exactly** what is written
2. **For dates**: Parse carefully using the rules above
3. **Provide confidence** (0.0-1.0) for your reading
4. **List alternatives** if the text is ambiguous

If a date component is unclear, provide your best reading AND alternatives.
Example: If you see "1/1/2026" where the first "1" could be "7":
- raw_text: "1/1/2026"
- alternative_readings: ["7/1/2026"]
- confidence: 0.7 (indicate uncertainty)

HANDWRITING TIPS:
- Medical abbreviations: BID, TID, PRN, mg, etc.
- Names often have capital first letters
- Dates are usually in MM/DD/YYYY or M/D/YYYY format"""


STAGE3_PROMPT_TEMPLATE = """Analyze spatial relationships on this form - BE VERY CONSERVATIVE.

{dual_image_instruction}

CRITICAL RULES - READ CAREFULLY:
1. A bracket MUST be a clearly visible hand-drawn bracket shape {{ or }}
2. Do NOT infer brackets from proximity or alignment of items
3. If no clear hand-drawn connecting marks exist, return an EMPTY connections list
4. Lines must be clearly hand-drawn lines, not printed dividers
5. Arrows must be clearly hand-drawn arrows with arrowheads

WHAT COUNTS AS A BRACKET:
- A curved or angular mark that physically groups multiple items
- Must be clearly hand-drawn (not printed)
- Usually has annotation text next to it explaining the grouping

WHAT DOES NOT COUNT:
- Items that happen to be near each other
- Printed lines or dividers on the form
- Mental groupings you infer from content
- Circles around individual items (those are selections, not groupings)

IF YOU DON'T SEE CLEAR HAND-DRAWN BRACKETS, LINES, OR ARROWS:
- Return connections: []
- Return has_complex_groupings: false
- Return grouping_summary: "No hand-drawn spatial connections detected"

This is CRITICAL: Do not hallucinate groupings that don't visually exist."""


STAGE4_PROMPT_TEMPLATE = """Map extracted values to schema fields. USE THE SCHEMA AS YOUR STRICT GUIDE.

PAGE SCHEMA (this defines ALL valid fields and options):
{schema_json}

EXTRACTED ELEMENTS:
{elements}

EXTRACTED TEXT:
{texts}

FIELD MAPPING RULES:

1. **field_id**: Use the EXACT field_id from the schema in your output

2. **yes_no fields**: 
   - Each question has "YES" and "NO" printed on the form. The patient circles or marks ONE word.
   - A circle, line, or mark can be ANY color (red, pink, blue, black, etc.).
   - ONLY the word that is clearly INSIDE a circle or has a mark drawn through/around it is the answer.
   - If a circle is near a word but the word is not inside it, that word is NOT selected.
   - If a line touches or crosses through a word, that word IS the selected answer.
   - If neither YES nor NO has any marking at all, the question was left unanswered — leave as null.
   - Output: is_checked=true for YES, is_checked=false for NO, null if unanswered.
   - Read the field's extraction_hints for question-specific guidance.

3. **circled_selection fields** (like medications):
   - ONLY report options where the printed word is clearly INSIDE a drawn circle.
   - CRITICAL: If a circle is drawn around one word and merely TOUCHES or OVERLAPS an adjacent word, the adjacent word is NOT circled — only the word the circle encloses counts.
   - Output: circled_options=["option1", "option2"] with EXACT spelling from schema
   - If an item appears circled but isn't in the options array, DO NOT include it
   - If there is handwritten text near the printed options, that is a SEPARATE field (e.g. additional medications written by hand) — do not confuse with circled printed text.
   
4. **date fields**:
   - Use the schema's expected_format (usually MM/DD/YYYY)
   - Output the date in that format

5. **text fields**:
   - Transcribe the handwritten text exactly
   - Note if the field appears empty

IMPORTANT FIELD ROLE AWARENESS:
{field_roles}

Example output for circled medications:
If schema has: "options": ["Zolpidem", "Ultram", "Tylenol", ...]
And only "Zolpidem" and "Ultram" are circled, output:
{{"field_id": "p1_current_medications", "circled_options": ["Zolpidem", "Ultram"]}}

Do NOT include medications that aren't circled, even if they're in the schema.
If the patient wrote additional medications by hand near the list, put those in the appropriate text field (e.g. p1_additional_medications_written), NOT in the circled_options."""


STAGE5_PROMPT_TEMPLATE = """Provide semantic interpretation of extracted annotations.

FORM CONTEXT:
{form_context}

EXTRACTED DATA:
- Elements: {elements}
- Text extractions: {texts}  
- Spatial connections: {connections}

INTERPRETATION GUIDELINES:

For ANNOTATIONS/NOTES, explain:
1. What it literally says
2. What it means in context
3. Which field(s) it relates to

For GROUPINGS (only if spatial connections were detected):
1. What items are grouped
2. What the grouping indicates
3. Clinical significance if any

IMPORTANT: If no spatial connections were detected (empty list), do NOT create or infer any groupings.

Keep interpretations factual and based on what's actually written, not inferred."""


STAGE6_PROMPT_TEMPLATE = """Perform final validation of the extraction.

SCHEMA CONTEXT:
{schema_summary}

EXTRACTED DATA:
- Fields: {fields}
- Annotations: {annotations}
- Groups: {groups}

VALIDATION CHECKS:

1. **Date Validation**
   - Are dates in valid ranges? (month 1-12, day 1-31)
   - Are years reasonable? (2020-{current_year} expected)
   - Flag any date before 2020 for review

2. **Circled Selection Validation**
   - Were only valid schema options reported as circled?
   - Flag if circled items seem inconsistent

3. **Field Completeness**
   - Note which required fields are blank
   - Note which fields have values

4. **Logical Consistency**
   - Check for contradictions (e.g., "NO" to a condition but taking related medication)
   - Note any inconsistencies for review

5. **Confidence Assessment**
   - Overall extraction quality
   - Items that need human verification

IMPORTANT: Only flag real issues based on the data. Do not create issues that don't exist.

Calculate overall confidence based on:
- Legibility of handwriting
- Completeness of extraction
- Consistency of data"""


# =============================================================================
# EXTRACTION PIPELINE CLASS
# =============================================================================

class ExtractionPipeline:
    """
    Multi-stage extraction pipeline for filled medical forms.
    
    Priority: Together AI (Llama 4 Maverick) > Fireworks AI > Claude
    """
    
    TOGETHER_MODEL = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    TOGETHER_BASE_URL = "https://api.together.xyz/v1"
    FIREWORKS_MODEL = "accounts/fireworks/models/qwen2p5-vl-32b-instruct"
    FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 32000,
    ):
        import os
        self.max_tokens = max_tokens
        self._used_fallback = False
        
        together_key = os.getenv("TOGETHER_API_KEY")
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        
        if together_key:
            self.qwen_client = instructor.from_openai(
                OpenAI(
                    api_key=together_key,
                    base_url=self.TOGETHER_BASE_URL,
                    timeout=300.0,
                ),
                mode=instructor.Mode.JSON,
            )
            self.qwen_model = model or self.TOGETHER_MODEL
        elif fireworks_key:
            self.qwen_client = instructor.from_openai(
                OpenAI(
                    api_key=fireworks_key,
                    base_url=self.FIREWORKS_BASE_URL,
                    timeout=300.0,
                ),
                mode=instructor.Mode.JSON,
            )
            self.qwen_model = model or self.FIREWORKS_MODEL
        else:
            self.qwen_client = None
            self.qwen_model = None
        
        anthropic_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.claude_client = instructor.from_anthropic(
                anthropic.Anthropic(api_key=anthropic_key)
            )
            self.claude_model = self.CLAUDE_MODEL
        else:
            self.claude_client = None
            self.claude_model = None
        
        if not self.qwen_client and not self.claude_client:
            raise ValueError(
                "No LLM configured. Set TOGETHER_API_KEY, FIREWORKS_API_KEY, or ANTHROPIC_API_KEY."
            )
        
        providers = []
        if self.qwen_client:
            provider_name = "Together AI" if together_key else "Fireworks"
            providers.append(f"Qwen VL via {provider_name} (primary)")
        if self.claude_client:
            providers.append(f"Claude ({'fallback' if self.qwen_client else 'primary'})")
        console.print(f"[bold]LLM providers: {', '.join(providers)}[/bold]")
    
    @property
    def model_used(self) -> str:
        if self._used_fallback or not self.qwen_client:
            return self.claude_model or "unknown"
        return self.qwen_model or "unknown"
    
    def _load_image(
        self, 
        image_path: Path,
        max_dimension: int = 1568,
        jpeg_quality: int = 85,
    ) -> tuple[str, str]:
        """Load image, compress it, and return as base64.
        
        Cost optimization: Smaller images = fewer input tokens = lower cost.
        """
        try:
            from PIL import Image
            import io
            
            with Image.open(image_path) as img:
                # Convert to RGB for JPEG
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Compress as JPEG
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=jpeg_quality, optimize=True)
                buffer.seek(0)
                
                image_data = base64.standard_b64encode(buffer.read()).decode("utf-8")
                return image_data, "image/jpeg"
                
        except ImportError:
            # Fallback without compression
            suffix = image_path.suffix.lower()
            media_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg", 
                ".jpeg": "image/jpeg",
            }
            media_type = media_types.get(suffix, "image/png")
            
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            
            return image_data, media_type
    
    def _call_qwen(
        self,
        prompt: str,
        image_data: str,
        media_type: str,
        response_model: type[BaseModel],
        blank_image_data: Optional[str] = None,
        blank_media_type: Optional[str] = None,
    ) -> BaseModel:
        """Call Qwen VL via OpenAI-compatible endpoint (Together AI or Fireworks)."""
        content = []
        if blank_image_data:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{blank_media_type or media_type};base64,{blank_image_data}"}
            })
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{image_data}"}
        })
        content.append({"type": "text", "text": prompt})
        
        return self.qwen_client.chat.completions.create(
            model=self.qwen_model,
            max_tokens=self.max_tokens,
            temperature=0.0,
            messages=[{"role": "user", "content": content}],
            response_model=response_model,
            max_retries=2,
        )
    
    def _call_claude(
        self,
        prompt: str,
        image_data: str,
        media_type: str,
        response_model: type[BaseModel],
        blank_image_data: Optional[str] = None,
        blank_media_type: Optional[str] = None,
    ) -> BaseModel:
        """Call Claude via Anthropic API (fallback)."""
        content = []
        if blank_image_data:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": blank_media_type or media_type, "data": blank_image_data}
            })
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_data}
        })
        content.append({"type": "text", "text": prompt})
        
        return self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": content}],
            response_model=response_model,
        )
    
    def _call_llm(
        self,
        prompt: str,
        image_data: str,
        media_type: str,
        response_model: type[BaseModel],
        stage_name: str,
        blank_image_data: Optional[str] = None,
        blank_media_type: Optional[str] = None,
        force_provider: Optional[str] = None,
    ) -> BaseModel:
        """Call primary vision LLM. No automatic fallback to Claude.
        
        Args:
            force_provider: If "claude", bypass primary and use Claude directly.
        """
        provider_label = f" [{force_provider}]" if force_provider else ""
        console.print(f"  [dim]Running {stage_name}{provider_label}...[/dim]")
        
        call_args = (prompt, image_data, media_type, response_model, blank_image_data, blank_media_type)
        
        if force_provider == "claude":
            if not self.claude_client:
                raise RuntimeError("Claude requested but ANTHROPIC_API_KEY not set")
            result = self._call_claude(*call_args)
            console.print(f"  [green]{stage_name} complete (Claude)[/green]")
            return result
        
        if self.qwen_client:
            result = self._call_qwen(*call_args)
            console.print(f"  [green]{stage_name} complete[/green]")
            return result
        
        if self.claude_client:
            result = self._call_claude(*call_args)
            self._used_fallback = True
            console.print(f"  [green]{stage_name} complete (Claude)[/green]")
            return result
        
        raise RuntimeError("No LLM client available")
    
    def _format_circled_options(self, options_map: dict[str, list[str]]) -> str:
        """Format circled selection options for prompt."""
        if not options_map:
            return "No circled selection fields on this page."
        
        lines = []
        for field_id, options in options_map.items():
            lines.append(f"\nField: {field_id}")
            lines.append(f"Valid options: {', '.join(options)}")
        return "\n".join(lines)
    
    def _format_date_fields(self, date_fields: list[dict]) -> str:
        """Format date field info for prompt."""
        if not date_fields:
            return "No date fields identified in schema."
        
        lines = []
        for df in date_fields:
            lines.append(f"- {df['field_id']} ({df['field_label']}): format {df['expected_format']}")
        return "\n".join(lines)
    
    def _get_field_roles(self, page_schema: Optional[PageSchema]) -> str:
        """Generate field role awareness text."""
        if not page_schema:
            return ""
        
        roles = []
        nurse_field = get_field_by_role(page_schema, ['nurse'])
        patient_field = get_field_by_role(page_schema, ['patient', 'name'])
        
        if nurse_field:
            roles.append(f"- '{nurse_field}' is for the NURSE name (not the patient)")
        if patient_field and patient_field != nurse_field:
            roles.append(f"- '{patient_field}' is for the PATIENT name")
        
        return "\n".join(roles) if roles else "No special field roles identified."
    
    def extract_page(
        self,
        image_path: Path,
        page_number: int,
        page_schema: Optional[PageSchema] = None,
        blank_image_path: Optional[Path] = None,
        extraction_mode: str = "differential",
        force_provider: Optional[str] = None,
    ) -> PageExtractionResult:
        """
        Extract all data from a single page using the multi-stage pipeline.
        
        Args:
            image_path: Path to filled page image
            page_number: Page number
            page_schema: Optional schema for known fields
            blank_image_path: Optional path to blank template image for comparison
            extraction_mode: "differential" (handwritten only, uses blank template)
                           or "full_page" (all text including printed, for lawyer pages)
            
        Returns:
            Complete PageExtractionResult
        """
        mode_label = "full-page OCR" if extraction_mode == "full_page" else "differential"
        console.print(f"\n[bold cyan]Processing Page {page_number} ({mode_label})[/bold cyan]")
        
        # Load filled form image
        image_data, media_type = self._load_image(image_path)
        
        # In full_page mode, skip blank template (we want ALL text)
        blank_data, blank_type = None, None
        if extraction_mode != "full_page" and blank_image_path and blank_image_path.exists():
            blank_data, blank_type = self._load_image(blank_image_path)
            console.print(f"  [dim]Using blank template for comparison[/dim]")
        
        # Prepare schema-derived information
        current_year = datetime.now().year
        schema_summary = get_schema_summary(page_schema)
        circled_options = extract_circled_selection_options(page_schema)
        date_fields = extract_date_fields(page_schema)
        field_roles = self._get_field_roles(page_schema)
        
        # Dual-image / full-page instruction
        if extraction_mode == "full_page":
            dual_image_instruction = """Extract ALL visible text on this page — both PRINTED labels/form fields AND handwritten entries.
This is an administrative or legal page where printed text IS important data.
Capture every field label and its value, whether printed or handwritten."""
        elif blank_data:
            dual_image_instruction = """IMAGE 1 (first image): BLANK template form - shows what the form looks like unfilled
IMAGE 2 (second image): FILLED form - contains handwritten content to extract

TASK: Identify ONLY what is DIFFERENT between the blank and filled form.
- Handwriting that appears in the filled form but not the blank
- Circles/marks that appear in the filled form but not the blank
- Do NOT report printed text that appears in both images"""
        else:
            dual_image_instruction = """Analyzing a single filled form image. Focus on handwritten content and marks only."""
        
        # Stage 1: Visual Element Detection (Schema-guided)
        stage1_prompt = STAGE1_PROMPT_TEMPLATE.format(
            dual_image_instruction=dual_image_instruction,
            schema_summary=schema_summary,
            circled_options_text=self._format_circled_options(circled_options),
        )
        stage1 = self._call_llm(
            stage1_prompt,
            image_data,
            media_type,
            Stage1_VisualElements,
            "Stage 1: Visual Element Detection",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Stage 2: Text Extraction (with date parsing rules)
        stage2_prompt = STAGE2_PROMPT_TEMPLATE.format(
            dual_image_instruction=dual_image_instruction,
            date_fields_info=self._format_date_fields(date_fields),
            current_year=current_year,
            date_format="MM/DD/YYYY",
        )
        stage2 = self._call_llm(
            stage2_prompt,
            image_data,
            media_type,
            Stage2_TextExtraction,
            "Stage 2: Text Extraction (OCR)",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Stage 3: Spatial Relationships (Conservative)
        stage3_prompt = STAGE3_PROMPT_TEMPLATE.format(
            dual_image_instruction=dual_image_instruction,
        )
        stage3 = self._call_llm(
            stage3_prompt,
            image_data,
            media_type,
            Stage3_SpatialRelationships,
            "Stage 3: Spatial Relationship Analysis",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Stage 4: Field Value Mapping (Schema-strict)
        schema_json = page_schema.model_dump_json(indent=2) if page_schema else '{"note": "No schema provided"}'
        elements_str = json.dumps([e.model_dump() for e in stage1.elements], indent=2)
        texts_str = json.dumps([t.model_dump() for t in stage2.extracted_texts], indent=2)
        
        stage4_prompt = STAGE4_PROMPT_TEMPLATE.format(
            schema_json=schema_json,
            elements=elements_str,
            texts=texts_str,
            field_roles=field_roles,
        )
        stage4 = self._call_llm(
            stage4_prompt,
            image_data,
            media_type,
            Stage4_FieldValues,
            "Stage 4: Field Value Extraction",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Stage 5: Semantic Analysis (Form-context aware)
        connections_str = json.dumps([c.model_dump() for c in stage3.connections], indent=2)
        form_context = page_schema.page_title if page_schema else "Medical form"
        
        stage5_prompt = STAGE5_PROMPT_TEMPLATE.format(
            form_context=form_context,
            elements=elements_str,
            texts=texts_str,
            connections=connections_str,
        )
        stage5 = self._call_llm(
            stage5_prompt,
            image_data,
            media_type,
            Stage5_SemanticAnalysis,
            "Stage 5: Semantic Analysis",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Stage 6: Validation (Schema-aware)
        fields_str = json.dumps([f.model_dump() for f in stage4.field_values], indent=2)
        annotations_str = json.dumps([a.model_dump() for a in stage5.annotations], indent=2)
        groups_str = json.dumps([g.model_dump() for g in stage5.groups], indent=2)
        
        stage6_prompt = STAGE6_PROMPT_TEMPLATE.format(
            schema_summary=schema_summary,
            fields=fields_str,
            annotations=annotations_str,
            groups=groups_str,
            current_year=current_year,
        )
        stage6 = self._call_llm(
            stage6_prompt,
            image_data,
            media_type,
            Stage6_Validation,
            "Stage 6: Validation",
            blank_image_data=blank_data,
            blank_media_type=blank_type,
            force_provider=force_provider,
        )
        
        # Build final result
        result = self._build_page_result(
            page_number,
            stage1, stage2, stage3, stage4, stage5, stage6
        )
        
        console.print(f"[green]Page {page_number} complete: "
                     f"{len(result.field_values)} fields, "
                     f"{len(result.annotation_groups)} groups, "
                     f"{result.items_needing_review} items for review[/green]")
        
        return result
    
    def _build_page_result(
        self,
        page_number: int,
        stage1: Stage1_VisualElements,
        stage2: Stage2_TextExtraction,
        stage3: Stage3_SpatialRelationships,
        stage4: Stage4_FieldValues,
        stage5: Stage5_SemanticAnalysis,
        stage6: Stage6_Validation,
    ) -> PageExtractionResult:
        """Combine all stage results into final PageExtractionResult."""
        
        def location_to_bbox(location: str) -> BoundingBox:
            """Convert location string to approximate bounding box."""
            loc = location.lower()
            # Default position
            x, y = 50, 50
            # Horizontal position
            if "left" in loc:
                x = 10
            elif "right" in loc:
                x = 80
            elif "center" in loc:
                x = 45
            # Vertical position
            if "top" in loc:
                y = 10
            elif "bottom" in loc:
                y = 80
            elif "middle" in loc:
                y = 45
            return BoundingBox(x=x, y=y, width=20, height=10)
        
        # Convert visual elements
        visual_elements = []
        for elem in stage1.elements:
            bbox = location_to_bbox(getattr(elem, 'location', 'middle-center'))
            visual_elements.append(VisualElement(
                element_id=elem.element_id,
                element_type=elem.element_type,
                bbox=bbox,
                content=elem.description,
                confidence=0.9,
                is_handwritten=getattr(elem, 'is_handwritten', True),
                mark_type=VisualMarkType(elem.mark_type) if elem.mark_type and elem.mark_type in [e.value for e in VisualMarkType] else None,
            ))
        
        # Convert field values
        field_values = {}
        for fv in stage4.field_values:
            field_values[fv.field_id] = {
                "value": fv.extracted_value,
                "is_checked": fv.is_checked,
                "circled_options": fv.circled_options,
                "confidence": fv.confidence,
                "has_correction": fv.has_correction,
                "original_value": fv.original_value,
            }
        
        # Convert spatial connections
        spatial_connections = []
        for conn in stage3.connections:
            spatial_connections.append(SpatialConnection(
                connection_id=conn.connection_id,
                connection_type=conn.connector_type,
                connector_element_id=conn.connector_element_id,
                source_element_ids=conn.connects_elements,
                target_element_ids=[conn.points_to_element] if conn.points_to_element else [],
                relationship_meaning=conn.inferred_meaning,
                confidence=conn.confidence,
                needs_review=conn.confidence < 0.7,
            ))
        
        # Convert annotation groups
        annotation_groups = []
        for group in stage5.groups:
            annotation_groups.append(AnnotationGroup(
                group_id=group.group_id,
                group_type="medication_status" if "medication" in group.group_meaning.lower() else "general",
                member_element_ids=group.member_elements,
                annotation_text=group.annotation_text,
                interpretation=group.medical_interpretation,
                confidence=0.8,
                needs_review=False,
            ))
        
        # Convert free-form annotations
        free_form_annotations = []
        for ann in stage5.annotations:
            free_form_annotations.append(FreeFormAnnotation(
                annotation_id=ann.annotation_id,
                page_number=page_number,
                bbox=BoundingBox(x=0, y=0, width=100, height=20),  # Placeholder
                position_description="inline",
                raw_text=ann.raw_text,
                normalized_text=ann.interpretation,
                relates_to_field_ids=ann.relates_to_fields,
                annotation_purpose=ann.purpose,
                semantic_meaning=ann.interpretation,
                ocr_confidence=ann.confidence,
                interpretation_confidence=ann.confidence,
                needs_review=ann.needs_human_review,
                review_reason=ann.review_reason,
            ))
        
        # Convert cross-page references
        cross_page_references = []
        for ref in stage5.cross_page_references:
            cross_page_references.append(CrossPageReference(
                reference_id=f"ref_{page_number}_{len(cross_page_references)}",
                source_page=page_number,
                reference_text=ref.get("text", ""),
                bbox=BoundingBox(x=0, y=0, width=100, height=20),
                target_description=ref.get("target", ""),
                is_resolved=False,
            ))
        
        return PageExtractionResult(
            page_number=page_number,
            field_values=field_values,
            visual_elements=visual_elements,
            spatial_connections=spatial_connections,
            annotation_groups=annotation_groups,
            free_form_annotations=free_form_annotations,
            circled_selections=[],  # Extracted from field_values
            cross_page_references=cross_page_references,
            overall_confidence=stage6.overall_confidence,
            items_needing_review=stage6.total_items_for_review,
            review_reasons=[issue.description for issue in stage6.validation_issues if issue.requires_human_review],
        )
    
    def extract_form(
        self,
        image_paths: list[Path],
        form_schema: Optional[FormSchema] = None,
        form_name: str = "extracted_form",
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        blank_image_paths: Optional[list[Path]] = None,
        extraction_mode: str = "differential",
    ) -> FormExtractionResult:
        """
        Extract data from an entire multi-page form with parallel processing.
        
        Args:
            image_paths: List of filled page image paths (in order)
            form_schema: Optional schema for known fields
            form_name: Name for this form
            max_workers: Number of concurrent page processors (default 4)
            progress_callback: Called with (completed_count, total_count, percentage)
            blank_image_paths: Optional list of blank template image paths for comparison
            
        Returns:
            Complete FormExtractionResult
        """
        total_pages = len(image_paths)
        console.print(f"\n[bold]Extracting form: {form_name}[/bold]")
        console.print(f"Total pages: {total_pages}")
        console.print(f"Processing with {max_workers} parallel workers")
        
        if blank_image_paths:
            console.print(f"[cyan]Using blank templates for differential extraction[/cyan]")
        
        # Prepare page schemas
        page_schemas = [None] * total_pages
        if form_schema:
            for i in range(min(total_pages, len(form_schema.pages))):
                page_schemas[i] = form_schema.pages[i]
        
        # Prepare blank image paths (pad with None if not enough)
        blank_paths = [None] * total_pages
        if blank_image_paths:
            for i in range(min(total_pages, len(blank_image_paths))):
                blank_paths[i] = blank_image_paths[i]
        
        # Track progress with thread safety
        completed_count = 0
        lock = threading.Lock()
        
        def process_page(args: tuple) -> tuple[int, PageExtractionResult]:
            """Process a single page and return (index, result)."""
            nonlocal completed_count
            idx, image_path, page_schema, blank_path = args
            
            result = self.extract_page(
                image_path, 
                idx + 1, 
                page_schema,
                blank_image_path=blank_path,
                extraction_mode=extraction_mode,
            )
            
            # Update progress thread-safely
            with lock:
                completed_count += 1
                if progress_callback:
                    percentage = round((completed_count / total_pages) * 100, 1)
                    progress_callback(completed_count, total_pages, percentage)
            
            return idx, result
        
        # Prepare arguments for parallel processing
        args_list = [
            (i, path, page_schemas[i], blank_paths[i])
            for i, path in enumerate(image_paths)
        ]
        
        # Process pages in parallel
        pages = [None] * total_pages
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_page, args) for args in args_list]
            
            for future in as_completed(futures):
                try:
                    idx, result = future.result(timeout=600)
                    pages[idx] = result
                except Exception as e:
                    console.print(f"[red]Error processing page: {e}[/red]")
                    console.print(f"[yellow]Skipping page, continuing...[/yellow]")
        
        # Fill in None pages with empty results
        for i, p in enumerate(pages):
            if p is None:
                pages[i] = PageExtractionResult(
                    page_number=i + 1,
                    overall_confidence=0.0,
                    items_needing_review=1,
                    review_reasons=[f"Page {i + 1} extraction failed"],
                )
        
        # Resolve cross-page references
        resolved_references = self._resolve_cross_references(pages)
        
        # Calculate overall metrics
        successful = [p for p in pages if p.overall_confidence > 0]
        total_confidence = sum(p.overall_confidence for p in successful) / len(successful) if successful else 0
        total_review = sum(p.items_needing_review for p in pages)
        all_reasons = []
        for p in pages:
            all_reasons.extend(p.review_reasons)
        
        # Extract patient info from first page
        patient_name = None
        patient_dob = None
        form_date = None
        if pages and pages[0].field_values:
            for field_id, value in pages[0].field_values.items():
                if "name" in field_id.lower() and not patient_name:
                    patient_name = value.get("value")
                if "dob" in field_id.lower() or "birth" in field_id.lower():
                    patient_dob = value.get("value")
                if "date" in field_id.lower() and not "birth" in field_id.lower():
                    form_date = value.get("value")
        
        return FormExtractionResult(
            form_id=form_name.lower().replace(" ", "_"),
            form_name=form_name,
            extraction_timestamp=datetime.now().isoformat(),
            pages=pages,
            resolved_references=resolved_references,
            overall_confidence=total_confidence,
            total_items_needing_review=total_review,
            all_review_reasons=all_reasons,
            patient_name=patient_name,
            patient_dob=patient_dob,
            form_date=form_date,
        )
    
    def _resolve_cross_references(
        self,
        pages: list[PageExtractionResult],
    ) -> list[CrossPageReference]:
        """Attempt to resolve cross-page references."""
        resolved = []
        
        for page in pages:
            for ref in page.cross_page_references:
                # Try to find the target
                ref_text_lower = ref.reference_text.lower()
                
                # Look for "see attached", "see sheet", "continued"
                if "attached" in ref_text_lower or "sheet" in ref_text_lower:
                    # Usually refers to next page or last page
                    if page.page_number < len(pages):
                        ref.target_page = page.page_number + 1
                        ref.is_resolved = True
                        ref.resolved_content_summary = f"References page {ref.target_page}"
                
                resolved.append(ref)
        
        return resolved
