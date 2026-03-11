"""Pydantic models for extraction-to-report correlations."""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class DataSource(str, Enum):
    EXAM = "exam"
    LAWYER_COVER = "lawyer_cover"
    BOTH = "both"


class TransformationType(str, Enum):
    DIRECT = "direct"
    FORMATTED = "formatted"
    NARRATIVE = "narrative"
    LIST_ASSEMBLY = "list_assembly"
    TABLE_POPULATION = "table_population"
    CONDITIONAL = "conditional"
    AGGREGATED = "aggregated"
    STATIC = "static"


class ElementMapping(BaseModel):
    """Maps a single report element back to its extraction source fields."""
    report_element_id: str
    report_section_id: str
    report_text: str = Field(description="The actual text in the report for this element")
    data_source: DataSource = Field(
        default=DataSource.EXAM,
        description="Where the source data originates: exam form, lawyer cover page, or both",
    )
    source_field_ids: list[str] = Field(
        description="Extraction field_id(s) that produced this element"
    )
    transformation: TransformationType
    transformation_notes: Optional[str] = Field(
        default=None,
        description="How the data was transformed (date reformatted, fields combined, etc.)",
    )
    format_pattern: Optional[str] = Field(
        default=None,
        description="Format string or pattern used (e.g. '{last}, {first}' or 'MM/DD/YYYY')",
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class PairCorrelation(BaseModel):
    """Complete correlation result for one report+extraction pair."""
    report_id: str
    extraction_id: str
    patient_name: Optional[str] = None
    mappings: list[ElementMapping] = Field(default_factory=list)
    unmapped_report_elements: list[str] = Field(
        default_factory=list,
        description="Report element_ids that could not be mapped to any extraction field",
    )
    unmapped_extraction_fields: list[str] = Field(
        default_factory=list,
        description="Extraction field_ids not found in the report",
    )
    mapping_coverage: float = Field(
        default=0.0,
        description="Fraction of dynamic report elements successfully mapped",
    )


# -- Instructor response model for LLM Call 2 (per-pair mapping) --


class LLMElementMapping(BaseModel):
    """LLM output for a single element mapping."""
    report_element_id: str
    data_source: DataSource = Field(
        description="'exam' if source data is from the orofacial pain form, "
                    "'lawyer_cover' if from the lawyer intro pages, 'both' if combined",
    )
    source_field_ids: list[str] = Field(
        description="field_id values from the extraction result"
    )
    transformation: TransformationType
    transformation_notes: str = Field(
        description="The RULE for generating this report element from the extraction data. "
                    "Be specific: e.g. 'If q1_heart_problems=YES, include paragraph. "
                    "If q1_heart_problems_details has text, append it.' or "
                    "'Combine p5_employer_name + p5_job_title + p5_years_employed into sentence.'"
    )
    format_pattern: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class LLMPairCorrelationResult(BaseModel):
    """Full LLM response for correlating one report+extraction pair."""
    mappings: list[LLMElementMapping]
    unmapped_report_elements: list[str] = Field(
        default_factory=list,
        description="Element IDs from the report that have no extraction source",
    )
    unmapped_extraction_fields: list[str] = Field(
        default_factory=list,
        description="field_ids from extraction that don't appear in the report",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any observations about the mapping",
    )


# -- Models for cross-report pattern analysis (LLM Call 3) --


class SectionPattern(BaseModel):
    """Pattern observed for a single report section across all reports."""
    section_id: str
    title: str
    appears_in_count: int = Field(description="How many reports contain this section")
    is_required: bool = Field(description="True if section appears in all reports")
    typical_position: int = Field(description="Most common ordering position")
    dominant_transformation: TransformationType
    primary_data_source: DataSource = Field(
        default=DataSource.EXAM,
        description="Where this section's data typically originates",
    )
    source_fields: list[str] = Field(
        description="Union of all field_ids used across all reports for this section"
    )
    consistent_fields: list[str] = Field(
        description="field_ids used in EVERY report for this section"
    )
    optional_fields: list[str] = Field(
        default_factory=list,
        description="field_ids used in some but not all reports",
    )
    conditional_trigger: Optional[str] = Field(
        default=None,
        description="If conditional, the exact rule: e.g. 'Include when q10_breathing_problems=YES' "
                    "or 'Include when any orthopedic VAS > 0'",
    )
    generation_rule: Optional[str] = Field(
        default=None,
        description="Complete rule for generating this section from extraction data, "
                    "including conditional logic, field assembly order, and prose template",
    )
    formatting_notes: Optional[str] = None
    narrative_style_notes: Optional[str] = Field(
        default=None,
        description="For narrative sections: the prose formula and consistent writing style",
    )


class CrossReportPatterns(BaseModel):
    """Full result of analysing all 20 correlations together."""
    total_reports_analysed: int
    section_patterns: list[SectionPattern] = Field(default_factory=list)
    universal_sections: list[str] = Field(
        description="section_ids present in every report"
    )
    conditional_sections: list[str] = Field(
        description="section_ids present in some but not all reports"
    )
    static_text_blocks: list[dict[str, str]] = Field(
        default_factory=list,
        description="Boilerplate text blocks identical across all reports [{section_id, text}]",
    )
    field_usage_summary: dict[str, int] = Field(
        default_factory=dict,
        description="field_id -> count of reports that use it",
    )
    report_ordering: list[str] = Field(
        description="Canonical section ordering (section_ids in order)"
    )
    observations: Optional[str] = Field(
        default=None,
        description="General observations about patterns across reports",
    )
