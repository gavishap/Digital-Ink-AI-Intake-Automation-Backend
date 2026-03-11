"""Pydantic models for report generation rules."""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ..correlator.models import TransformationType


class ContentType(str, Enum):
    STATIC_TEXT = "static_text"
    DIRECT_FILL = "direct_fill"
    FORMATTED_FILL = "formatted_fill"
    NARRATIVE = "narrative"
    LIST = "list"
    TABLE = "table"
    CONDITIONAL_BLOCK = "conditional_block"


class FormattingRule(BaseModel):
    """Formatting to apply when generating report content."""
    font_name: Optional[str] = "Arial"
    font_size: Optional[float] = 11.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    alignment: Optional[str] = None
    color: Optional[str] = None
    all_caps: bool = False


class ConditionalRule(BaseModel):
    """Logic that determines whether a section/element is included."""
    field_id: str = Field(description="Extraction field_id to evaluate")
    operator: str = Field(
        description="Operator: exists, not_empty, equals, not_equals, contains, greater_than"
    )
    value: Optional[str] = Field(
        default=None, description="Value to compare against (for equals/contains)"
    )
    combine: str = Field(
        default="and",
        description="How to combine with other conditions: and, or",
    )


class FewShotExample(BaseModel):
    """Input/output pair for narrative generation."""
    input_fields: dict[str, Any] = Field(
        description="Extraction field values that were the input"
    )
    output_text: str = Field(
        description="The actual report text that was generated from those inputs"
    )


class TableColumnRule(BaseModel):
    """Definition for a single column in a generated table."""
    header: str
    source_field_id: Optional[str] = None
    width_percent: Optional[float] = None
    formatting: Optional[FormattingRule] = None


class SectionRule(BaseModel):
    """Complete rule for generating one report section."""
    section_id: str
    title: str
    ordering: int = Field(description="Position in the report (0-based)")
    page_break_before: bool = False
    is_required: bool = True
    content_type: ContentType

    # For STATIC_TEXT
    static_content: Optional[str] = Field(
        default=None,
        description="Exact boilerplate text to insert",
    )

    # For DIRECT_FILL / FORMATTED_FILL
    source_field_ids: list[str] = Field(default_factory=list)
    template: Optional[str] = Field(
        default=None,
        description="Template string with {field_id} placeholders",
    )
    format_pattern: Optional[str] = Field(
        default=None,
        description="Format pattern (e.g. date format, phone format)",
    )

    # For NARRATIVE
    generation_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for LLM narrative generation",
    )
    few_shot_examples: list[FewShotExample] = Field(default_factory=list)
    max_tokens: int = 500

    # For LIST
    list_field_id: Optional[str] = Field(
        default=None,
        description="Extraction field_id containing the list items",
    )
    list_bullet_style: str = "bullet"

    # For TABLE
    table_columns: list[TableColumnRule] = Field(default_factory=list)
    table_row_source_field: Optional[str] = Field(
        default=None,
        description="field_id containing list of row data dicts",
    )

    # For CONDITIONAL_BLOCK
    conditions: list[ConditionalRule] = Field(default_factory=list)
    child_sections: list["SectionRule"] = Field(
        default_factory=list,
        description="Nested sections shown when condition is met",
    )

    # Formatting
    title_formatting: Optional[FormattingRule] = None
    content_formatting: Optional[FormattingRule] = None

    # Metadata
    notes: Optional[str] = None


class ReportRules(BaseModel):
    """Complete ruleset for generating an entire clinical report."""
    report_name: str
    report_description: Optional[str] = None
    total_estimated_pages: int = 1
    sections: list[SectionRule] = Field(default_factory=list)
    global_formatting: FormattingRule = Field(default_factory=FormattingRule)
    field_id_glossary: dict[str, str] = Field(
        default_factory=dict,
        description="field_id -> human-readable description",
    )
    generation_notes: Optional[str] = None
    version: str = "1.0"


# -- LLM response models for rule generation (Call 4) --


class LLMSectionRule(BaseModel):
    """LLM output for a single section rule."""
    section_id: str
    title: str
    ordering: int
    page_break_before: bool = False
    is_required: bool = True
    content_type: ContentType
    static_content: Optional[str] = None
    source_field_ids: list[str] = Field(default_factory=list)
    template: Optional[str] = None
    format_pattern: Optional[str] = None
    generation_prompt: Optional[str] = None
    few_shot_examples: list[FewShotExample] = Field(default_factory=list)
    list_field_id: Optional[str] = None
    table_columns: list[TableColumnRule] = Field(default_factory=list)
    table_row_source_field: Optional[str] = None
    conditions: list[ConditionalRule] = Field(default_factory=list)
    notes: Optional[str] = None


class LLMReportRulesResult(BaseModel):
    """Full LLM response for rule generation."""
    report_name: str
    sections: list[LLMSectionRule]
    field_id_glossary: dict[str, str] = Field(default_factory=dict)
    generation_notes: Optional[str] = None


# -- LLM response models for validation (Calls 5-6) --


class SectionScore(BaseModel):
    """Validation score for a single section."""
    section_id: str
    structure_match: float = Field(ge=0.0, le=1.0, description="Did the section appear correctly?")
    data_accuracy: float = Field(ge=0.0, le=1.0, description="Are the right values in the right places?")
    narrative_quality: float = Field(
        ge=0.0, le=1.0,
        description="For narrative sections: does the generated text convey the same info?",
    )
    overall: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Validation result for one generated-vs-original comparison."""
    report_id: str
    section_scores: list[SectionScore] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0)
    missing_sections: list[str] = Field(default_factory=list)
    extra_sections: list[str] = Field(default_factory=list)
    critical_issues: list[str] = Field(default_factory=list)


class RuleRefinement(BaseModel):
    """Suggested improvement for a weak rule."""
    section_id: str
    issue: str
    suggested_change: str
    priority: str = Field(description="high, medium, low")


class LLMValidationResult(BaseModel):
    """LLM response for validation of one report."""
    section_scores: list[SectionScore]
    missing_sections: list[str] = Field(default_factory=list)
    extra_sections: list[str] = Field(default_factory=list)
    critical_issues: list[str] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=1.0)


class LLMRefinementResult(BaseModel):
    """LLM response for rule refinement suggestions."""
    refinements: list[RuleRefinement]
    summary: str
