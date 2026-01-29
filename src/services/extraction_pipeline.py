"""
Multi-Stage LLM Extraction Pipeline

A sophisticated pipeline for extracting both structured field data
AND free-form annotations, spatial relationships, and connected elements
from filled medical forms.

Pipeline Stages:
1. Visual Element Detection - Find all marks, text, annotations
2. OCR & Transcription - Extract handwritten text
3. Spatial Analysis - Detect brackets, lines, arrows, connections
4. Field Value Extraction - Map values to known fields
5. Semantic Understanding - Interpret annotations and groups
6. Validation & Cross-Reference - Verify and link across pages

Uses Claude Opus 4.5 with instructor for structured outputs.
"""

import base64
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

import anthropic
import instructor
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
        
    elements: list[DetectedElement] = Field(description="Key elements only - max 50", max_length=50)
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
        confidence: float = Field(ge=0.0, le=1.0)
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
        confidence: float = Field(ge=0.0, le=1.0)
        
    connections: list[Connection]
    has_complex_groupings: bool
    grouping_summary: str = Field(description="Summary of all groupings found")


class Stage4_FieldValues(BaseModel):
    """Stage 4: Values mapped to known form fields."""
    
    class FieldValue(BaseModel):
        field_id: str
        field_label: str
        extracted_value: Optional[str]
        value_type: str = Field(description="'text', 'date', 'number', 'yes_no', 'checkbox', 'circled', 'multiple_choice'")
        is_checked: Optional[bool] = Field(default=None, description="For checkboxes/yes-no")
        circled_options: list[str] = Field(default_factory=list, description="For circled selections")
        confidence: float = Field(ge=0.0, le=1.0)
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
        confidence: float = Field(ge=0.0, le=1.0)
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
    overall_confidence: float = Field(ge=0.0, le=1.0)
    extraction_quality: str = Field(description="'high', 'medium', 'low'")
    total_items_for_review: int
    summary: str


# =============================================================================
# PROMPTS FOR EACH STAGE
# =============================================================================

STAGE1_PROMPT = """You are analyzing a filled medical form image. Identify the KEY visual elements - focus on HANDWRITTEN content and ANNOTATIONS, not printed text.

FOCUS ON:
1. **Handwriting** - Names, dates, numbers, notes, signatures
2. **Checked/Marked Items** - Checkmarks, X marks, circles on options
3. **Brackets/Groupings** - Any marks connecting multiple items
4. **Margin Notes** - Text written outside normal fields
5. **Unusual Marks** - Stars, arrows, or other symbols

DO NOT list every printed label - only note handwritten values and marks.

For each element, provide:
- A unique ID (hw_1, mark_1, etc.)
- Type (handwriting, checkmark, circle, bracket, margin_note, unknown)
- Brief description
- Approximate location (top/middle/bottom, left/center/right)

Keep descriptions CONCISE. Only include elements that have handwritten content or marks.
Limit to the 50 MOST IMPORTANT elements if page is very busy."""


STAGE2_PROMPT = """You are an expert medical form OCR system. Transcribe ALL handwritten text from this form.

For each handwritten element identified:
1. **Transcribe exactly** what is written (preserve spelling, abbreviations)
2. **Normalize** where appropriate (e.g., dates to MM/DD/YYYY)
3. **Classify** the text type (name, date, medication, note, etc.)
4. **Assess confidence** in your reading
5. **List alternatives** if ambiguous

HANDWRITING TIPS:
- Medical abbreviations are common (BID, TID, PRN, mg, etc.)
- Numbers can look like letters (0 vs O, 1 vs l)
- Medications have standard spellings - use your knowledge
- Dates may be partial (month/year only)
- Watch for corrections/cross-outs

For ILLEGIBLE text, describe what you can see and mark as low confidence."""


STAGE3_PROMPT = """Analyze the SPATIAL RELATIONSHIPS between elements on this medical form.

Look for:
1. **Brackets { }** - Often group medications or items with a shared note
   - What items does the bracket encompass?
   - Is there text next to the bracket explaining the group?
   
2. **Lines** - Connect related items
   - What two elements does the line connect?
   - Is it indicating a relationship or correction?
   
3. **Arrows →** - Point from one thing to another
   - What is the source?
   - What is the target?
   - What does this connection mean?
   
4. **Enclosures** - Boxes or circles around groups
   - What items are enclosed together?
   - Is there a label?

5. **Annotations near fields** - Notes written next to form fields
   - Which field does the note relate to?
   - What additional information does it provide?

For the medication list with brackets (if present):
- The bracket typically groups medications by a shared characteristic
- The note next to the bracket explains WHY they're grouped
- Common groupings: "stopped taking", "still taking", "started after injury", "as needed"

Return ALL spatial connections with their semantic meaning."""


STAGE4_PROMPT = """Map extracted values to the known form fields.

For each form field in the schema:
1. Find the corresponding handwritten/marked value
2. Extract the value appropriately for the field type:
   - **Yes/No fields**: Which option is circled/checked?
   - **Checkboxes**: Is it checked? (checkmark, X, or filled)
   - **Text fields**: What is written?
   - **Date fields**: Parse to standard format
   - **Selection lists**: Which items are circled?
   
HANDLE CORRECTIONS:
- If something is crossed out, note the ORIGINAL value
- The CURRENT value is what's written after correction
- Mark that a correction was made

HANDLE UNCLEAR VALUES:
- If you can't read it clearly, provide your best guess
- List alternative readings
- Mark confidence as low

Form Schema for this page:
{schema}

Elements detected:
{elements}

Text extracted:
{texts}"""


STAGE5_PROMPT = """Provide SEMANTIC INTERPRETATION of all annotations and groupings.

You have:
- Elements: {elements}
- Text extractions: {texts}  
- Spatial connections: {connections}

For EACH annotation/note, explain:
1. **What it literally says**
2. **What it MEANS in context** (medical/clinical significance)
3. **What it relates to** (which fields, which items)
4. **Why the patient wrote it** (clarification, additional info, etc.)

For GROUPED ITEMS (via brackets/lines):
1. **What items are grouped**
2. **What the grouping means** (e.g., "these medications were stopped after injury")
3. **Clinical significance** (relevant for treatment decisions?)

For CROSS-REFERENCES ("See attached", etc.):
1. **What does it reference**
2. **Why is there a separate sheet** (more space needed? continuation?)

MEDICAL CONTEXT:
- This is an orofacial pain / dental trauma examination
- Medication histories are crucial for treatment planning
- Injury timelines matter for workers' compensation
- "Pre-injury" vs "Post-injury" distinctions are important

Provide clinical interpretation where relevant."""


STAGE6_PROMPT = """Perform final VALIDATION of the extraction.

Review ALL extracted data for:

1. **Legibility Issues**
   - Any text that's uncertain
   - Alternative readings that should be flagged

2. **Ambiguous Marks**
   - Checkmarks vs stray marks
   - Unclear circles or selections

3. **Contradictions**
   - Field says YES but explanation says NO
   - Conflicting information

4. **Missing Data**
   - Required fields that are blank
   - Incomplete information

5. **Unclear Connections**
   - Brackets/lines with uncertain targets
   - Annotations with unclear referents

6. **Cross-Validations**
   - Does the medication list match circled medications?
   - Do dates make sense (injury date before exam date)?
   - Is patient name consistent across pages?

For EACH issue found:
- Describe the problem
- Suggest resolution if possible
- Flag for human review if needed

Calculate overall confidence score and quality assessment.

Data to validate:
- Fields: {fields}
- Annotations: {annotations}
- Groups: {groups}
- Cross-references: {references}"""


# =============================================================================
# EXTRACTION PIPELINE CLASS
# =============================================================================

class ExtractionPipeline:
    """
    Multi-stage extraction pipeline for filled medical forms.
    
    Uses Claude Sonnet 4 by default (5x cheaper than Opus).
    Use --model claude-opus-4-5-20251101 for very complex forms.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",  # Default to Sonnet for cost
        max_tokens: int = 16000,  # High enough for complex filled forms
    ):
        import os
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        
        self.model = model
        self.max_tokens = max_tokens
        
        # Create instructor-patched client
        self.client = instructor.from_anthropic(
            anthropic.Anthropic(api_key=self.api_key)
        )
    
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
    
    def _call_claude(
        self,
        prompt: str,
        image_data: str,
        media_type: str,
        response_model: type[BaseModel],
        stage_name: str,
    ) -> BaseModel:
        """Make a Claude API call with structured output."""
        
        console.print(f"  [dim]Running {stage_name}...[/dim]")
        
        try:
            result = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
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
                            "text": prompt,
                        }
                    ]
                }],
                response_model=response_model,
            )
            console.print(f"  [green]{stage_name} complete[/green]")
            return result
            
        except Exception as e:
            console.print(f"  [red]{stage_name} failed: {e}[/red]")
            raise
    
    def extract_page(
        self,
        image_path: Path,
        page_number: int,
        page_schema: Optional[PageSchema] = None,
    ) -> PageExtractionResult:
        """
        Extract all data from a single page using the multi-stage pipeline.
        
        Args:
            image_path: Path to page image
            page_number: Page number
            page_schema: Optional schema for known fields
            
        Returns:
            Complete PageExtractionResult
        """
        console.print(f"\n[bold cyan]Processing Page {page_number}[/bold cyan]")
        
        # Load image
        image_data, media_type = self._load_image(image_path)
        
        # Stage 1: Visual Element Detection
        stage1 = self._call_claude(
            STAGE1_PROMPT,
            image_data,
            media_type,
            Stage1_VisualElements,
            "Stage 1: Visual Element Detection"
        )
        
        # Stage 2: Text Extraction
        stage2 = self._call_claude(
            STAGE2_PROMPT,
            image_data,
            media_type,
            Stage2_TextExtraction,
            "Stage 2: Text Extraction (OCR)"
        )
        
        # Stage 3: Spatial Relationships
        stage3_prompt = STAGE3_PROMPT
        stage3 = self._call_claude(
            stage3_prompt,
            image_data,
            media_type,
            Stage3_SpatialRelationships,
            "Stage 3: Spatial Relationship Analysis"
        )
        
        # Stage 4: Field Value Mapping
        schema_str = page_schema.model_dump_json(indent=2) if page_schema else "No schema provided"
        elements_str = json.dumps([e.model_dump() for e in stage1.elements], indent=2)
        texts_str = json.dumps([t.model_dump() for t in stage2.extracted_texts], indent=2)
        
        stage4_prompt = STAGE4_PROMPT.format(
            schema=schema_str,
            elements=elements_str,
            texts=texts_str,
        )
        stage4 = self._call_claude(
            stage4_prompt,
            image_data,
            media_type,
            Stage4_FieldValues,
            "Stage 4: Field Value Extraction"
        )
        
        # Stage 5: Semantic Analysis
        connections_str = json.dumps([c.model_dump() for c in stage3.connections], indent=2)
        
        stage5_prompt = STAGE5_PROMPT.format(
            elements=elements_str,
            texts=texts_str,
            connections=connections_str,
        )
        stage5 = self._call_claude(
            stage5_prompt,
            image_data,
            media_type,
            Stage5_SemanticAnalysis,
            "Stage 5: Semantic Analysis"
        )
        
        # Stage 6: Validation
        fields_str = json.dumps([f.model_dump() for f in stage4.field_values], indent=2)
        annotations_str = json.dumps([a.model_dump() for a in stage5.annotations], indent=2)
        groups_str = json.dumps([g.model_dump() for g in stage5.groups], indent=2)
        refs_str = json.dumps(stage5.cross_page_references, indent=2)
        
        stage6_prompt = STAGE6_PROMPT.format(
            fields=fields_str,
            annotations=annotations_str,
            groups=groups_str,
            references=refs_str,
        )
        stage6 = self._call_claude(
            stage6_prompt,
            image_data,
            media_type,
            Stage6_Validation,
            "Stage 6: Validation"
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
    ) -> FormExtractionResult:
        """
        Extract data from an entire multi-page form with parallel processing.
        
        Args:
            image_paths: List of page image paths (in order)
            form_schema: Optional schema for known fields
            form_name: Name for this form
            max_workers: Number of concurrent page processors (default 4)
            progress_callback: Called with (completed_count, total_count, percentage)
            
        Returns:
            Complete FormExtractionResult
        """
        total_pages = len(image_paths)
        console.print(f"\n[bold]Extracting form: {form_name}[/bold]")
        console.print(f"Total pages: {total_pages}")
        console.print(f"Processing with {max_workers} parallel workers")
        
        # Prepare page schemas
        page_schemas = [None] * total_pages
        if form_schema:
            for i in range(min(total_pages, len(form_schema.pages))):
                page_schemas[i] = form_schema.pages[i]
        
        # Track progress with thread safety
        completed_count = 0
        lock = threading.Lock()
        
        def process_page(args: tuple) -> tuple[int, PageExtractionResult]:
            """Process a single page and return (index, result)."""
            nonlocal completed_count
            idx, image_path, page_schema = args
            
            # Extract the page (idx is 0-based, page_number is 1-based)
            result = self.extract_page(image_path, idx + 1, page_schema)
            
            # Update progress thread-safely
            with lock:
                completed_count += 1
                if progress_callback:
                    percentage = round((completed_count / total_pages) * 100, 1)
                    progress_callback(completed_count, total_pages, percentage)
            
            return idx, result
        
        # Prepare arguments for parallel processing
        args_list = [
            (i, path, page_schemas[i])
            for i, path in enumerate(image_paths)
        ]
        
        # Process pages in parallel
        pages = [None] * total_pages
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_page, args) for args in args_list]
            
            for future in as_completed(futures):
                try:
                    idx, result = future.result()
                    pages[idx] = result
                except Exception as e:
                    console.print(f"[red]Error processing page: {e}[/red]")
                    raise
        
        # Resolve cross-page references
        resolved_references = self._resolve_cross_references(pages)
        
        # Calculate overall metrics
        total_confidence = sum(p.overall_confidence for p in pages) / len(pages) if pages else 0
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
