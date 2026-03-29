"""
Two-Stage LLM Extraction Pipeline (v3 - Unified Extract + Self-Verify)

Replaces the v2 six-stage pipeline with two stages:
  1. Unified Visual Extraction — single VLM pass per page that detects
     handwriting, circles, checkmarks, dates, and maps to schema fields.
  2. Self-Verification — second VLM pass that re-examines the image to
     catch misreads, missed fields, and incorrect circle/checkbox calls.

Primary: Qwen2.5-VL-32B via Together AI / Fireworks AI (OpenAI-compatible).
Fallback: Claude Sonnet 4 via Anthropic API.
Uses instructor for structured outputs with both providers.
"""

import base64
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

import anthropic
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, model_validator
from rich.console import Console

from ..models.annotations import (
    PageExtractionResult,
    FormExtractionResult,
)
from ..models import FormSchema, PageSchema

console = Console()
logger = logging.getLogger(__name__)


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
    
    process_fields(page_schema.standalone_fields)
    
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
# STAGE RESPONSE MODELS (v3 - Two-Stage: Unified Extract + Self-Verify)
# =============================================================================

class UnifiedFieldExtraction(BaseModel):
    """Stage 1: Single-pass visual extraction replacing old stages 1-5."""

    class ExtractedField(BaseModel):
        field_id: str = Field(description="Exact field_id from the schema")
        value: Optional[str] = None
        is_checked: Optional[bool] = Field(default=None, description="For yes_no: true=YES, false=NO, null=unanswered")
        circled_options: list[str] = Field(default_factory=list, description="For circled_selection fields only, EXACT spelling from schema")
        confidence: float = Field(ge=0.0, le=1.0)
        has_correction: bool = Field(default=False, description="Was something crossed out and changed")
        original_value: Optional[str] = Field(default=None, description="If corrected, the original value before correction")
        annotation_note: Optional[str] = Field(default=None, description="Any freeform handwritten text near this field (margin notes, arrows, brackets)")

        @model_validator(mode="before")
        @classmethod
        def _normalize_llm_quirks(cls, data: Any) -> Any:
            """Handle common LLM output variations (e.g. table_id instead of field_id)."""
            if not isinstance(data, dict):
                return data
            if "table_id" in data and "field_id" not in data:
                data["field_id"] = data.pop("table_id")
            # Serialize any list/dict value to JSON string (handles rows, body_part arrays, etc.)
            for key in ("rows", "body_part", "items", "entries"):
                if key in data and "value" not in data:
                    import json as _json
                    data["value"] = _json.dumps(data.pop(key))
                    break
            if isinstance(data.get("value"), (list, dict)):
                import json as _json
                data["value"] = _json.dumps(data["value"])
            if not data.get("confidence"):
                data["confidence"] = 0.8
            if data.get("circled_options") is None:
                data["circled_options"] = []
            return data

    fields: list[ExtractedField] = Field(description="All extracted fields mapped to schema")
    unmapped_text: list[str] = Field(default_factory=list, description="Handwriting that does not map to any schema field")
    page_legibility: str = Field(description="'excellent', 'good', 'fair', or 'poor'")


class VerificationResult(BaseModel):
    """Stage 2: Self-verification against original image."""

    class FieldCorrection(BaseModel):
        field_id: str
        old_value: Any = Field(description="What Stage 1 returned")
        corrected_value: Any = Field(description="What the image actually shows")
        correction_reason: str = Field(description="Why it was wrong")

    class NewlyFoundField(BaseModel):
        field_id: str = Field(description="Schema field_id that Stage 1 missed")
        value: Optional[str] = None
        is_checked: Optional[bool] = None
        circled_options: list[str] = Field(default_factory=list)
        confidence: float = Field(ge=0.0, le=1.0)

    corrections: list[FieldCorrection] = Field(default_factory=list)
    newly_found_fields: list[NewlyFoundField] = Field(default_factory=list)
    confirmed_count: int = Field(description="Number of fields confirmed correct")
    overall_confidence: float = Field(ge=0.0, le=1.0, description="Verifier's overall assessment of extraction quality")


# =============================================================================
# PROMPTS (v3 - Two-Stage)
# =============================================================================

UNIFIED_EXTRACTION_PROMPT = """You are an expert medical form extraction system. Extract ALL field values from this filled form page in a SINGLE pass.

{dual_image_instruction}

SCHEMA CONTEXT:
{schema_summary}

PAGE SCHEMA (defines ALL valid fields and their types):
{schema_json}

CIRCLED SELECTION FIELDS - VALID OPTIONS ONLY:
{circled_options_text}

DATE FIELDS ON THIS PAGE:
{date_fields_info}

FIELD ROLE AWARENESS:
{field_roles}

=== EXTRACTION RULES ===

1. **field_id**: Use the EXACT field_id from the schema. Do NOT invent field IDs.

2. **CANCELLED/VOIDED marks (all field types)**:
   - A circle with a line, slash, or X drawn THROUGH it (strikethrough circle / "no entry" symbol) means CANCELLED — return null for that field.
   - A circle with a line through it is DIFFERENT from a normal selection circle.

3. **yes_no fields**:
   - Each numbered question has "YES" and "NO" printed on THE SAME LINE as the question text.
   - CRITICAL: Every question has its OWN YES/NO pair. Do NOT let a circle from one question bleed into an adjacent question's row. Match each circle to the YES or NO on the SAME horizontal line.
   - A circle, line, or mark can be ANY color (red, pink, blue, black, etc.).
   - ONLY the word clearly INSIDE a circle or with a mark drawn through/around it is the answer.
   - If a circle is near a word but the word is not inside it, that word is NOT selected.
   - If a line touches or crosses through a word, that word IS the selected answer.
   - **CRITICAL: Printed text alone is NOT a selection. The words "Yes" and "No" appear pre-printed on EVERY question — that does NOT mean either is selected. You MUST see a hand-drawn mark (circle, underline, strikethrough, checkmark) to report a selection. If neither word has any hand-drawn mark, return null for BOTH value and is_checked.**
   - Output: Set BOTH value AND is_checked. value="YES" and is_checked=true when YES is marked; value="NO" and is_checked=false when NO is marked; both null if unanswered.

4. **circled_selection fields** (medications, multi-option lists, numeric scales):
   - ONLY report options where the printed word/number is clearly INSIDE a hand-drawn circle or has a pen mark through it.
   - If a circle is drawn around one word and merely TOUCHES or OVERLAPS an adjacent word, the adjacent word is NOT circled.
   - A circle with a line/slash/X through it means CANCELLED — remove from selected list.
   - **For numeric scale tables (e.g. 0 1 2 3 columns):** The printed column headers "0", "1", "2", "3" are NOT selections — only report a number if you can see a hand-drawn circle or pen mark specifically on that number. Most numbers in the row will have NO marking at all.
   - Output: circled_options with EXACT spelling from schema options.
   - If an item appears circled but isn't in the schema options array, DO NOT include it.
   - Handwritten text near printed options is a SEPARATE field — do not put in circled_options.

5. **checkbox_multi fields** (multi-select lists like Driver/Passenger/Right Rear Seat):
   - These are printed option lists where zero, one, or more items can be selected.
   - **CRITICAL: Printed text alone is NOT a selection.** All options appear pre-printed on the form whether or not they are selected. You MUST see a hand-drawn mark (circle, underline, checkmark, or pen mark on/around the word) to report it as selected.
   - If NO options have any visible hand-drawn mark, return an EMPTY circled_options list and null value.
   - Stray ink marks, margin annotations, or marks on adjacent lines do NOT count as selections.
   - Some sections are conditional (e.g. "If MVA" sections apply only to motor vehicle accidents). If the entire section appears blank with no marks, return empty/null for ALL fields in that section.

5. **date fields**:
   - Current year context: {current_year}. Expected format: MM/DD/YYYY.
   - Common handwriting confusions: "1" vs "7" (1 has no top stroke, 7 does), "6" vs "9" (loop position), "0" vs "6" (0 is closed, 6 has tail).

6. **text fields**: Transcribe handwritten text exactly as written.

7. **Annotations & margin notes**:
   - If there is handwritten text near a field that is NOT the field's direct value (margin notes, arrows, brackets grouping items), put it in annotation_note for the nearest relevant field.
   - If handwritten text cannot be associated with any schema field, add it to unmapped_text.

8. **Confidence rules**:
   - 0.9-1.0: Clear, unambiguous reading
   - 0.7-0.89: Likely correct but minor ambiguity
   - 0.5-0.69: Uncertain — still include the value but at lower confidence
   - Below 0.5: Very uncertain — still include with your best reading

BE CONSERVATIVE with circles: only report a circle if you clearly see a hand-drawn circle around the text. Do NOT guess or infer circles."""


VERIFICATION_PROMPT = """You are verifying a medical form extraction. You will see the FILLED form image and the extraction results from a first pass.

LOOK AT THE IMAGE CAREFULLY and verify each extracted value.

EXTRACTION RESULTS TO VERIFY:
{extraction_json}

SCHEMA CONTEXT:
{schema_summary}

=== VERIFICATION PRIORITIES (in order of importance) ===

**PRIORITY 0 — BLANK/UNANSWERED detection (check FIRST before anything else):**
   - Before verifying individual values, scan the image for sections that are ENTIRELY BLANK (no handwriting, no circles, no marks at all).
   - If a yes_no field or checkbox_multi field has a non-null value but you see NO hand-drawn mark on the printed options, CORRECT it to null. Printed text appearing on the form does NOT count as a selection — only hand-drawn ink does.
   - Conditional sections (e.g. "If MVA" sections) are often entirely blank when they don't apply to the patient. If the section has no marks at all, all fields in that section should be null/empty.

**PRIORITY 1 — YES/NO fields (most common errors):**
   - For EACH yes_no question, look at the YES and NO printed on THAT question's own horizontal line.
   - Determine which word (YES or NO) has a hand-drawn circle, mark, or line on it. The mark can be any color.
   - CRITICAL: Do NOT let a circle from one question's row influence the adjacent question. Each row is independent.
   - Verify that value and is_checked agree: value="YES" ↔ is_checked=true, value="NO" ↔ is_checked=false.
   - **CRITICAL: If NEITHER Yes nor No has a visible hand-drawn mark, the field MUST be null. Printed text is NOT a mark. Correct any non-null value to null if you cannot see hand-drawn ink on either option.**
   - **CONSERVATIVE RULE for ambiguous marks: Only correct a YES/NO field if you are NEAR-CERTAIN (>90% confident) the first pass is wrong.** If the mark is at all ambiguous — could plausibly be on either word — leave it as-is.

**PRIORITY 2 — Circled selections and checkbox_multi fields:**
   - Is the circle truly around that specific word, or does it belong to a neighboring word?
   - Are any circled items missing or falsely included?
   - **CRITICAL: If no hand-drawn mark exists on any option, correct circled_options to an empty list.** Printed option text alone is NEVER a selection.
   - **For numeric scale tables (e.g. 0 1 2 3 columns):** The printed column numbers are NOT selections. Only a number with a visible hand-drawn pen mark on it should be in circled_options. If the model reported "1" for every row, re-examine each row carefully — most rows likely have "0" or another number circled, not "1".
   - **For Epworth tables specifically:** After verifying all 8 rows, sum them and check against p11_epworth_total_score. If your corrected sum does NOT match the written total score, your corrections are likely wrong — revert them and trust the original extraction.

**PRIORITY 3 — Date fields:**
   - Verify each digit. Common confusions: "1" vs "7", "3" vs "5", "9" vs "4".
   - Do NOT assume a year is wrong just because it seems recent. Only correct a year if the digits are clearly different from what was extracted.
   - Apply the same conservative rule as text fields: only correct a date if you are HIGHLY CONFIDENT it is wrong. If the digits are plausible and could match the handwriting, leave them as-is.

**PRIORITY 4 — Text and name fields (BE CONSERVATIVE):**
   - The first-pass model had BOTH a blank template AND the filled form for comparison, giving it an advantage for reading handwriting. You only see the filled form.
   - Only correct a text/name field if you are HIGHLY CONFIDENT the first pass is wrong (obvious misread, missing word, or clearly different characters).
   - Do NOT correct a text field just because you read ambiguous handwriting slightly differently. If it is plausible, leave it as-is.
   - Names are especially sensitive — do not change spelling unless the letters are unambiguously different.

=== OTHER INSTRUCTIONS ===

1. Look for fields the first pass MISSED ENTIRELY:
   - Check every schema field against the image
   - If you see handwriting for a field that has no extraction, add it to newly_found_fields

2. Set overall_confidence based on the quality of the original extraction:
   - 0.9+ if very few or no corrections needed
   - 0.7-0.89 if minor corrections needed
   - 0.5-0.69 if significant corrections needed
   - Below 0.5 if extraction was largely wrong

Return ONLY actual corrections where you are confident. Do NOT repeat correct values. Do NOT second-guess plausible handwriting reads."""


# =============================================================================
# EXTRACTION PIPELINE CLASS
# =============================================================================

class ExtractionPipeline:
    """
    Two-stage extraction pipeline for filled medical forms.
    
    Stage 1: Unified Visual Extraction (replaces old stages 1-5)
    Stage 2: Self-Verification (replaces old stage 6, now image-aware)
    
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
                anthropic.Anthropic(api_key=anthropic_key, timeout=600.0)
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
        max_dimension: int = 2048,
        jpeg_quality: int = 95,
    ) -> tuple[str, str]:
        """Load image, compress it, and return as base64."""
        try:
            from PIL import Image
            import io
            
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=jpeg_quality, optimize=True)
                buffer.seek(0)
                
                image_data = base64.standard_b64encode(buffer.read()).decode("utf-8")
                return image_data, "image/jpeg"
                
        except ImportError:
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
            max_retries=2,
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
    
    # =========================================================================
    # TWO-STAGE EXTRACTION
    # =========================================================================

    def extract_page(
        self,
        image_path: Path,
        page_number: int,
        page_schema: Optional[PageSchema] = None,
        blank_image_path: Optional[Path] = None,
        extraction_mode: str = "differential",
        force_provider: Optional[str] = None,
    ) -> PageExtractionResult:
        """Extract all data from a single page using the two-stage pipeline.
        
        Stage 1: Unified Visual Extraction (schema-guided, dual-image)
        Stage 2: Self-Verification (re-examines image to catch errors)
        
        Args:
            image_path: Path to filled page image
            page_number: Page number
            page_schema: Optional schema for known fields
            blank_image_path: Optional blank template image for differential comparison
            extraction_mode: "differential" (handwritten only) or "full_page" (all text)
            force_provider: If "claude", force Claude for both stages
        """
        mode_label = "full-page OCR" if extraction_mode == "full_page" else "differential"
        console.print(f"\n[bold cyan]Processing Page {page_number} ({mode_label})[/bold cyan]")
        
        image_data, media_type = self._load_image(image_path)
        
        blank_data, blank_type = None, None
        if extraction_mode != "full_page" and blank_image_path and blank_image_path.exists():
            blank_data, blank_type = self._load_image(blank_image_path)
            console.print(f"  [dim]Using blank template for comparison[/dim]")
        
        current_year = datetime.now().year
        schema_summary = get_schema_summary(page_schema)
        circled_options = extract_circled_selection_options(page_schema)
        date_fields = extract_date_fields(page_schema)
        field_roles = self._get_field_roles(page_schema)
        
        if extraction_mode == "full_page":
            dual_image_instruction = (
                "Extract ALL visible text on this page — both PRINTED labels/form fields "
                "AND handwritten entries.\nThis is an administrative or legal page where "
                "printed text IS important data.\nCapture every field label and its value, "
                "whether printed or handwritten."
            )
        elif blank_data:
            dual_image_instruction = (
                "IMAGE 1 (first image): BLANK template form — shows what the form looks like unfilled\n"
                "IMAGE 2 (second image): FILLED form — contains handwritten content to extract\n\n"
                "TASK: Identify ONLY what is DIFFERENT between the blank and filled form.\n"
                "- Handwriting that appears in the filled form but not the blank\n"
                "- Circles/marks that appear in the filled form but not the blank\n"
                "- Do NOT report printed text that appears in both images"
            )
        else:
            dual_image_instruction = "Analyzing a single filled form image. Focus on handwritten content and marks only."
        
        schema_json = page_schema.model_dump_json(indent=2) if page_schema else '{"note": "No schema provided"}'
        
        # === STAGE 1: Unified Visual Extraction ===
        stage1_prompt = UNIFIED_EXTRACTION_PROMPT.format(
            dual_image_instruction=dual_image_instruction,
            schema_summary=schema_summary,
            schema_json=schema_json,
            circled_options_text=self._format_circled_options(circled_options),
            date_fields_info=self._format_date_fields(date_fields),
            field_roles=field_roles,
            current_year=current_year,
        )
        
        try:
            extraction = self._call_llm(
                stage1_prompt,
                image_data,
                media_type,
                UnifiedFieldExtraction,
                "Stage 1: Unified Visual Extraction",
                blank_image_data=blank_data,
                blank_media_type=blank_type,
                force_provider=force_provider,
            )
        except Exception as e:
            console.print(f"[red]Stage 1 failed for page {page_number}: {e}[/red]")
            return PageExtractionResult(
                page_number=page_number,
                overall_confidence=0.0,
                items_needing_review=1,
                review_reasons=[f"Extraction failed: {e}"],
            )
        
        # === STAGE 2: Cross-Model Verification ===
        # Use Claude for verification when available to get an independent second opinion.
        # Same-model verification has identical blind spots; cross-model catches more.
        extraction_json = json.dumps(
            [f.model_dump() for f in extraction.fields],
            indent=2,
        )
        
        stage2_prompt = VERIFICATION_PROMPT.format(
            extraction_json=extraction_json,
            schema_summary=schema_summary,
        )
        
        verify_provider = force_provider
        if verify_provider is None and self.claude_client and self.qwen_client:
            verify_provider = "claude"
        
        verification: Optional[VerificationResult] = None
        try:
            verification = self._call_llm(
                stage2_prompt,
                image_data,
                media_type,
                VerificationResult,
                "Stage 2: Cross-Model Verification",
                force_provider=verify_provider,
            )
        except Exception as e:
            console.print(f"[yellow]Stage 2 (verification) failed for page {page_number}: {e}[/yellow]")
            console.print(f"[yellow]Using unverified Stage 1 results[/yellow]")
        
        # === Apply corrections ===
        if verification:
            self._apply_corrections(extraction, verification)
        
        result = self._build_page_result(page_number, extraction, verification)
        
        corrections_count = len(verification.corrections) if verification else 0
        new_fields_count = len(verification.newly_found_fields) if verification else 0
        console.print(
            f"[green]Page {page_number} complete: "
            f"{len(result.field_values)} fields, "
            f"{corrections_count} corrections, "
            f"{new_fields_count} newly found, "
            f"{result.items_needing_review} items for review[/green]"
        )
        
        return result
    
    def _apply_corrections(
        self,
        extraction: UnifiedFieldExtraction,
        verification: VerificationResult,
    ) -> None:
        """Apply Stage 2 corrections to Stage 1 extraction in-place."""
        fields_by_id = {f.field_id: f for f in extraction.fields}
        
        for correction in verification.corrections:
            field = fields_by_id.get(correction.field_id)
            if not field:
                continue
            
            corrected = correction.corrected_value
            if isinstance(corrected, str):
                field.value = corrected
                if corrected.upper() in ("YES", "NO"):
                    field.is_checked = corrected.upper() == "YES"
            elif isinstance(corrected, bool):
                field.is_checked = corrected
                field.value = "YES" if corrected else "NO"
            elif isinstance(corrected, list):
                field.circled_options = corrected
            elif corrected is None:
                field.value = None
                field.is_checked = None
                field.circled_options = []
            
            if not field.has_correction:
                field.has_correction = True
                field.original_value = str(correction.old_value) if correction.old_value is not None else None
            
            logger.debug(
                "Page correction: %s — %s → %s (%s)",
                correction.field_id, correction.old_value,
                correction.corrected_value, correction.correction_reason,
            )
        
        for new_field in verification.newly_found_fields:
            if new_field.field_id not in fields_by_id:
                extraction.fields.append(UnifiedFieldExtraction.ExtractedField(
                    field_id=new_field.field_id,
                    value=new_field.value,
                    is_checked=new_field.is_checked,
                    circled_options=new_field.circled_options,
                    confidence=new_field.confidence,
                ))
    
    def _build_page_result(
        self,
        page_number: int,
        extraction: UnifiedFieldExtraction,
        verification: Optional[VerificationResult],
    ) -> PageExtractionResult:
        """Convert unified extraction + verification into PageExtractionResult."""
        field_values: dict[str, Any] = {}
        low_confidence_count = 0
        review_reasons: list[str] = []
        
        for field in extraction.fields:
            value = field.value
            if value is None and field.is_checked is not None:
                value = "YES" if field.is_checked else "NO"
            elif value is None and len(field.circled_options) == 1:
                # Single circled selection — promote the one selected option to value
                value = field.circled_options[0]

            field_values[field.field_id] = {
                "value": value,
                "is_checked": field.is_checked,
                "circled_options": field.circled_options,
                "confidence": field.confidence,
                "has_correction": field.has_correction,
                "original_value": field.original_value,
                "annotation_note": field.annotation_note,
            }
            if field.confidence < 0.6:
                low_confidence_count += 1
        
        if verification:
            overall_confidence = verification.overall_confidence
            for c in verification.corrections:
                review_reasons.append(f"{c.field_id}: {c.correction_reason}")
        else:
            confidences = [f.confidence for f in extraction.fields] if extraction.fields else [0.0]
            overall_confidence = sum(confidences) / len(confidences)
        
        if extraction.page_legibility in ("poor", "fair"):
            review_reasons.append(f"Page legibility: {extraction.page_legibility}")
        
        if low_confidence_count > 0:
            review_reasons.append(f"{low_confidence_count} field(s) below 0.6 confidence")
        
        return PageExtractionResult(
            page_number=page_number,
            field_values=field_values,
            visual_elements=[],
            spatial_connections=[],
            annotation_groups=[],
            free_form_annotations=[],
            circled_selections=[],
            cross_page_references=[],
            unknown_marks=[],
            overall_confidence=min(max(overall_confidence, 0.0), 1.0),
            items_needing_review=low_confidence_count + (len(verification.corrections) if verification else 0),
            review_reasons=review_reasons,
        )
    
    # =========================================================================
    # MULTI-PAGE FORM EXTRACTION
    # =========================================================================

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
        """Extract data from an entire multi-page form with parallel processing."""
        total_pages = len(image_paths)
        console.print(f"\n[bold]Extracting form: {form_name}[/bold]")
        console.print(f"Total pages: {total_pages}")
        console.print(f"Processing with {max_workers} parallel workers")
        
        if blank_image_paths:
            console.print(f"[cyan]Using blank templates for differential extraction[/cyan]")
        
        page_schemas = [None] * total_pages
        if form_schema:
            for i in range(min(total_pages, len(form_schema.pages))):
                page_schemas[i] = form_schema.pages[i]
        
        blank_paths = [None] * total_pages
        if blank_image_paths:
            for i in range(min(total_pages, len(blank_image_paths))):
                blank_paths[i] = blank_image_paths[i]
        
        completed_count = 0
        lock = threading.Lock()
        
        def process_page(args: tuple) -> tuple[int, PageExtractionResult]:
            nonlocal completed_count
            idx, image_path, page_schema, blank_path = args
            
            result = self.extract_page(
                image_path, 
                idx + 1, 
                page_schema,
                blank_image_path=blank_path,
                extraction_mode=extraction_mode,
            )
            
            with lock:
                completed_count += 1
                if progress_callback:
                    percentage = round((completed_count / total_pages) * 100, 1)
                    progress_callback(completed_count, total_pages, percentage)
            
            return idx, result
        
        args_list = [
            (i, path, page_schemas[i], blank_paths[i])
            for i, path in enumerate(image_paths)
        ]
        
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
        
        for i, p in enumerate(pages):
            if p is None:
                pages[i] = PageExtractionResult(
                    page_number=i + 1,
                    overall_confidence=0.0,
                    items_needing_review=1,
                    review_reasons=[f"Page {i + 1} extraction failed"],
                )
        
        successful = [p for p in pages if p.overall_confidence > 0]
        total_confidence = sum(p.overall_confidence for p in successful) / len(successful) if successful else 0
        total_review = sum(p.items_needing_review for p in pages)
        all_reasons = []
        for p in pages:
            all_reasons.extend(p.review_reasons)
        
        patient_name = None
        patient_dob = None
        form_date = None
        if pages and pages[0].field_values:
            for field_id, value in pages[0].field_values.items():
                if "name" in field_id.lower() and not patient_name:
                    patient_name = value.get("value")
                if "dob" in field_id.lower() or "birth" in field_id.lower():
                    patient_dob = value.get("value")
                if "date" in field_id.lower() and "birth" not in field_id.lower():
                    form_date = value.get("value")
        
        return FormExtractionResult(
            form_id=form_name.lower().replace(" ", "_"),
            form_name=form_name,
            extraction_timestamp=datetime.now().isoformat(),
            pages=pages,
            resolved_references=[],
            overall_confidence=total_confidence,
            total_items_needing_review=total_review,
            all_review_reasons=all_reasons,
            patient_name=patient_name,
            patient_dob=patient_dob,
            form_date=form_date,
        )
