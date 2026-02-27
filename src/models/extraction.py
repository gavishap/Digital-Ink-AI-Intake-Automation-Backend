"""
Models for extraction phase (Phase 2).
These are included in generated templates for use with instructor.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field

from .field_types import MarkType


class SourceEvidence(BaseModel):
    """
    Tracks where extracted data came from on the form.
    Use this in Phase 2 to maintain audit trail of extractions.
    """
    
    page_number: int = Field(
        description="Page number where value was found"
    )
    anchor_text: str = Field(
        description="The printed label/text near the extracted value"
    )
    mark_type: MarkType = Field(
        description="Type of mark (handwriting, circle, check, etc.)"
    )
    raw_handwriting: Optional[str] = Field(
        default=None,
        description="Exactly what is written before cleanup/normalization"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1 for this extraction"
    )
    pertains_to: str = Field(
        description="What this value means/represents"
    )
    needs_review: bool = Field(
        default=False,
        description="Flag if this extraction needs human review"
    )
    review_reason: Optional[str] = Field(
        default=None,
        description="Reason why this needs review"
    )
    bounding_box: Optional[dict[str, int]] = Field(
        default=None,
        description="Pixel coordinates {x, y, width, height} if available"
    )


class ExtractedFieldValue(BaseModel):
    """
    Represents an extracted value from a filled form.
    Use this model in Phase 2 extraction.
    """
    
    field_id: str = Field(
        description="The field_id this value corresponds to"
    )
    raw_value: Optional[str] = Field(
        default=None,
        description="Raw extracted value before normalization"
    )
    normalized_value: Any = Field(
        default=None,
        description="Cleaned/standardized value"
    )
    is_empty: bool = Field(
        default=False,
        description="True if field was left blank"
    )
    evidence: Optional[SourceEvidence] = Field(
        default=None,
        description="Evidence for where this came from"
    )
    
    # Additional context for complex cases
    both_options_marked: bool = Field(
        default=False,
        description="For yes/no fields: both were marked (needs review)"
    )
    crossed_out_values: list[str] = Field(
        default_factory=list,
        description="Values that were crossed out/changed"
    )
    see_attached_reference: Optional[str] = Field(
        default=None,
        description="If field says 'see attached', reference to where"
    )


# =============================================================================
# EXTRACTION TIPS FOR PHASE 2
# =============================================================================
"""
HANDWRITING EXTRACTION TIPS (for Phase 2 - include as comments/notes):

Based on real medical form extraction experience:

1. For handwriting fields, the extraction should capture:
   - raw_handwriting: Exactly what is written (before cleanup)
   - normalized_value: Cleaned/standardized version
   - confidence: 0-1 score
   - needs_review: boolean flag

2. For circled selections, watch for:
   - Both options marked (flag for review)
   - Partial circles or unclear marks
   - Crossed-out selections (changed answers)

3. For tables, extraction should:
   - Handle "See attached sheet" references
   - Capture handwritten notes in margins
   - Handle merged cells or spanning entries

4. Context-based inference:
   - Use patient demographics to help decode unclear writing
   - Use medical terminology knowledge to fill gaps
   - Use surrounding answers for context

5. Common mark types to detect:
   - handwriting (cursive or print)
   - circle (around printed option)
   - checkmark (✓)
   - x_mark (X)
   - crossed_out (strikethrough)
   - arrow (pointing to something)

6. VAS/Pain scales:
   - May be marked with X, line, or circle
   - May include written number
   - Watch for marks between numbers

7. Medication lists:
   - Often have inconsistent formatting
   - May reference "see attached"
   - Watch for abbreviations (BID, TID, PRN, etc.)

8. Dates:
   - Multiple formats possible (MM/DD/YY, MM/DD/YYYY, M/D/YY)
   - May be partial (month/year only)
   - Watch for ambiguous formats (is 01/02/24 Jan 2 or Feb 1?)
"""
