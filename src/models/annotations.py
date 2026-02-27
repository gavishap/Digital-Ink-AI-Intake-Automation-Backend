"""
Models for complex annotations, spatial relationships, and free-form marks.

Handles:
- Brackets, lines, arrows connecting elements
- Margin notes and free-form text
- Groupings of related items
- Cross-page references
- Ambiguous marks requiring review
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class VisualMarkType(str, Enum):
    """Types of visual marks on forms beyond standard fields."""
    
    # Connecting marks
    BRACKET_LEFT = "bracket_left"       # { connecting items on right
    BRACKET_RIGHT = "bracket_right"     # } connecting items on left
    BRACKET_TOP = "bracket_top"         # ⌐ connecting items below
    BRACKET_BOTTOM = "bracket_bottom"   # ⌊ connecting items above
    LINE_HORIZONTAL = "line_horizontal"
    LINE_VERTICAL = "line_vertical"
    LINE_DIAGONAL = "line_diagonal"
    ARROW = "arrow"
    CURVED_LINE = "curved_line"
    
    # Selection marks
    CIRCLE = "circle"                   # Circled item
    UNDERLINE = "underline"
    HIGHLIGHT = "highlight"
    STRIKETHROUGH = "strikethrough"     # Crossed out / changed answer
    DOUBLE_UNDERLINE = "double_underline"
    WAVY_UNDERLINE = "wavy_underline"
    
    # Text marks
    MARGIN_NOTE = "margin_note"         # Text written in margins
    INTERLINEAR_NOTE = "interlinear_note"  # Text between lines
    ANNOTATION_CALLOUT = "annotation_callout"  # Note with arrow pointing to something
    
    # Reference marks
    ASTERISK = "asterisk"
    CHECKMARK = "checkmark"
    X_MARK = "x_mark"
    QUESTION_MARK = "question_mark"     # Patient unsure
    EXCLAMATION_MARK = "exclamation_mark"  # Emphasis
    STAR = "star"                       # Star symbol
    PLUS_SIGN = "plus_sign"
    MINUS_SIGN = "minus_sign"
    
    # Grouping
    BOX_DRAWN = "box_drawn"             # Hand-drawn box around items
    ENCLOSURE = "enclosure"             # Any enclosing shape
    
    # Catch-all for unknown marks
    OTHER = "other"                     # Unknown mark type - see description
    UNKNOWN = "unknown"                 # Unrecognizable mark - needs review


class BoundingBox(BaseModel):
    """Pixel coordinates for an element's location."""
    
    x: int = Field(description="Left edge X coordinate")
    y: int = Field(description="Top edge Y coordinate")
    width: int = Field(description="Width in pixels")
    height: int = Field(description="Height in pixels")
    
    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def right(self) -> int:
        return self.x + self.width
    
    @property
    def bottom(self) -> int:
        return self.y + self.height


class VisualElement(BaseModel):
    """Any detected visual element on the page."""
    
    element_id: str = Field(description="Unique identifier")
    element_type: str = Field(description="Type: 'printed_text', 'handwriting', 'mark', 'field_value'")
    bbox: BoundingBox = Field(description="Location on page")
    content: Optional[str] = Field(default=None, description="Text content if applicable")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    
    # For marks - flexible to handle ANY type of mark
    mark_type: Optional[VisualMarkType] = Field(
        default=None,
        description="Known mark type from enum. Use OTHER/UNKNOWN for novel marks."
    )
    mark_type_raw: Optional[str] = Field(
        default=None,
        description="Free-form description if mark_type is OTHER/UNKNOWN, e.g., 'hand-drawn star', 'squiggly line', 'smiley face'"
    )
    mark_description: Optional[str] = Field(
        default=None,
        description="Detailed description of the mark's appearance and apparent purpose"
    )
    mark_inferred_meaning: Optional[str] = Field(
        default=None,
        description="What this mark likely means in context, e.g., 'emphasis', 'approval', 'question'"
    )
    
    # For text
    is_handwritten: bool = Field(default=False)
    
    # For field values
    associated_field_id: Optional[str] = Field(
        default=None, 
        description="If this is a value for a known field"
    )


class SpatialConnection(BaseModel):
    """
    Represents a spatial relationship between elements.
    E.g., a bracket connecting multiple items to a note.
    """
    
    connection_id: str = Field(description="Unique identifier")
    connection_type: str = Field(
        description="Type: 'bracket_groups', 'arrow_points_to', 'line_connects', 'annotation_refers_to'"
    )
    
    # The connecting mark itself
    connector_element_id: str = Field(
        description="ID of the bracket/line/arrow element"
    )
    
    # What it connects
    source_element_ids: list[str] = Field(
        description="Elements being grouped/pointed from"
    )
    target_element_ids: list[str] = Field(
        description="Elements being pointed to (e.g., the annotation text)"
    )
    
    # Semantic meaning
    relationship_meaning: Optional[str] = Field(
        default=None,
        description="What this connection means, e.g., 'these medications were stopped'"
    )
    
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = Field(default=False)
    review_reason: Optional[str] = Field(default=None)


class AnnotationGroup(BaseModel):
    """
    A group of related elements connected by visual marks.
    E.g., medications grouped by a bracket with a shared note.
    """
    
    group_id: str = Field(description="Unique identifier")
    group_type: str = Field(
        description="Type: 'medication_status', 'conditional_answer', 'cross_reference', 'correction'"
    )
    
    # The items in this group
    member_element_ids: list[str] = Field(description="IDs of grouped elements")
    
    # The annotation/note for this group
    annotation_text: Optional[str] = Field(
        default=None,
        description="The handwritten note explaining this group"
    )
    annotation_element_id: Optional[str] = Field(default=None)
    
    # Semantic interpretation
    interpretation: str = Field(
        description="What this grouping means semantically"
    )
    
    # For cross-references
    references_page: Optional[int] = Field(
        default=None,
        description="If this references another page"
    )
    references_section: Optional[str] = Field(default=None)
    
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = Field(default=False)


class FreeFormAnnotation(BaseModel):
    """
    A free-form annotation not tied to a specific field.
    Could be margin notes, additional information, etc.
    """
    
    annotation_id: str = Field(description="Unique identifier")
    page_number: int
    
    # Location
    bbox: BoundingBox
    position_description: str = Field(
        description="Where on page: 'top_margin', 'bottom_margin', 'left_margin', 'right_margin', 'between_sections', 'inline'"
    )
    
    # Content
    raw_text: str = Field(description="Raw transcribed text")
    normalized_text: Optional[str] = Field(
        default=None,
        description="Cleaned/interpreted text"
    )
    
    # What it relates to
    relates_to_field_ids: list[str] = Field(
        default_factory=list,
        description="Field IDs this annotation relates to"
    )
    relates_to_section: Optional[str] = Field(default=None)
    
    # Semantic meaning
    annotation_purpose: str = Field(
        description="Purpose: 'clarification', 'additional_info', 'correction', 'cross_reference', 'instruction', 'question'"
    )
    semantic_meaning: str = Field(
        description="What this annotation means in context"
    )
    
    # Confidence
    ocr_confidence: float = Field(ge=0.0, le=1.0)
    interpretation_confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = Field(default=False)
    review_reason: Optional[str] = Field(default=None)


class CircledSelection(BaseModel):
    """
    An item circled from a printed list (like medications).
    """
    
    selection_id: str
    page_number: int
    
    # What was circled
    circled_text: str = Field(description="The printed text that was circled")
    bbox: BoundingBox
    
    # Context
    from_list_title: Optional[str] = Field(
        default=None,
        description="Title of the list this came from, e.g., 'Please circle medications you are taking'"
    )
    list_field_id: Optional[str] = Field(default=None)
    
    # Additional marks
    has_additional_annotation: bool = Field(default=False)
    additional_annotation: Optional[str] = Field(
        default=None,
        description="Any additional writing near the circled item"
    )
    
    confidence: float = Field(ge=0.0, le=1.0)


class CrossPageReference(BaseModel):
    """
    A reference from one page to another.
    E.g., 'See attached sheet', 'continued on page 3'
    """
    
    reference_id: str
    source_page: int
    source_field_id: Optional[str] = Field(default=None)
    
    # The reference text
    reference_text: str = Field(description="The text of the reference, e.g., 'See Sheet'")
    bbox: BoundingBox
    
    # Where it points
    target_page: Optional[int] = Field(
        default=None,
        description="Target page number if identifiable"
    )
    target_description: Optional[str] = Field(
        default=None,
        description="Description of what it references"
    )
    
    # Resolution
    is_resolved: bool = Field(
        default=False,
        description="Whether we found and linked the referenced content"
    )
    resolved_content_summary: Optional[str] = Field(default=None)


class UnknownMark(BaseModel):
    """
    A mark that doesn't fit any known category.
    Captures novel symbols, unusual drawings, or unrecognizable marks.
    These always need human review.
    """
    
    mark_id: str = Field(description="Unique identifier")
    page_number: int
    bbox: BoundingBox
    
    # Description of what was seen
    visual_description: str = Field(
        description="Detailed description of the mark's appearance, e.g., 'hand-drawn star with 5 points', 'wavy vertical line', 'small triangle symbol'"
    )
    approximate_shape: Optional[str] = Field(
        default=None,
        description="Closest geometric description: 'circular', 'linear', 'angular', 'curved', 'complex'"
    )
    approximate_size: Optional[str] = Field(
        default=None,
        description="Relative size: 'tiny', 'small', 'medium', 'large'"
    )
    
    # Context and interpretation
    nearby_text: Optional[str] = Field(
        default=None,
        description="Printed or handwritten text near this mark"
    )
    position_context: str = Field(
        description="Where on page: 'next_to_field', 'in_margin', 'between_sections', 'over_text', 'standalone'"
    )
    possible_meanings: list[str] = Field(
        default_factory=list,
        description="Possible interpretations of what this mark could mean"
    )
    best_guess_meaning: Optional[str] = Field(
        default=None,
        description="Most likely interpretation based on context"
    )
    
    # Association with structured data
    likely_relates_to_field_ids: list[str] = Field(
        default_factory=list,
        description="Field IDs this mark might relate to"
    )
    likely_relates_to_section: Optional[str] = Field(default=None)
    
    # Always needs review
    confidence: float = Field(ge=0.0, le=1.0, default=0.3, description="Low confidence by default for unknown marks")
    needs_review: bool = Field(default=True, description="Unknown marks always need review")
    review_priority: str = Field(
        default="medium",
        description="'low', 'medium', 'high' based on potential clinical relevance"
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        description="Notes for the human reviewer about this mark"
    )


class PageExtractionResult(BaseModel):
    """
    Complete extraction result for a single page.
    Combines structured fields with free-form annotations.
    """
    
    page_number: int
    
    # Standard field extractions
    field_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of field_id to extracted value"
    )
    
    # All detected visual elements
    visual_elements: list[VisualElement] = Field(default_factory=list)
    
    # Spatial connections (brackets, lines, arrows)
    spatial_connections: list[SpatialConnection] = Field(default_factory=list)
    
    # Grouped annotations
    annotation_groups: list[AnnotationGroup] = Field(default_factory=list)
    
    # Unknown/novel marks that need human review
    unknown_marks: list[UnknownMark] = Field(
        default_factory=list,
        description="Marks that don't fit known categories - always flagged for review"
    )
    
    # Free-form annotations
    free_form_annotations: list[FreeFormAnnotation] = Field(default_factory=list)
    
    # Circled selections
    circled_selections: list[CircledSelection] = Field(default_factory=list)
    
    # Cross-page references
    cross_page_references: list[CrossPageReference] = Field(default_factory=list)
    
    # Quality metrics
    overall_confidence: float = Field(ge=0.0, le=1.0)
    items_needing_review: int = Field(default=0)
    review_reasons: list[str] = Field(default_factory=list)


class FormExtractionResult(BaseModel):
    """
    Complete extraction result for an entire form.
    """
    
    form_id: str
    form_name: str
    extraction_timestamp: str
    
    # Per-page results
    pages: list[PageExtractionResult] = Field(default_factory=list)
    
    # Cross-page data
    resolved_references: list[CrossPageReference] = Field(
        default_factory=list,
        description="References that have been resolved across pages"
    )
    
    # Aggregate quality
    overall_confidence: float = Field(ge=0.0, le=1.0)
    total_items_needing_review: int = Field(default=0)
    all_review_reasons: list[str] = Field(default_factory=list)
    
    # Patient identification (if extracted)
    patient_name: Optional[str] = Field(default=None)
    patient_dob: Optional[str] = Field(default=None)
    form_date: Optional[str] = Field(default=None)
