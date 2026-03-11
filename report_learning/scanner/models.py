"""Pydantic models for scanned report content -- slim version.

Focuses on text content and structure, not per-character formatting.
"""

from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class ContentClassification(str, Enum):
    STATIC = "static"
    DYNAMIC_DIRECT = "dynamic_direct"
    DYNAMIC_FORMATTED = "dynamic_formatted"
    DYNAMIC_NARRATIVE = "dynamic_narrative"
    DYNAMIC_LIST = "dynamic_list"
    DYNAMIC_TABLE = "dynamic_table"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class ReportElement(BaseModel):
    """A single structural element from a report -- minimal representation."""
    id: str
    type: str = Field(description="heading | paragraph | table")
    text: str = Field(default="")
    bold: bool = False
    alignment: str = "left"
    heading_level: Optional[int] = None
    table_cells: Optional[list[list[str]]] = Field(
        default=None, description="Rows of columns, just text. Only for tables.",
    )
    section_id: Optional[str] = Field(default=None, exclude=True)
    element_id: Optional[str] = Field(default=None, exclude=True)


class ReportSection(BaseModel):
    """A logical section: a heading + all elements until the next heading."""
    id: str
    heading: str
    heading_level: int = 2
    elements: list[ReportElement] = Field(default_factory=list)


class ScannedReport(BaseModel):
    """Complete scanned output for one report -- section-grouped."""
    report_id: str
    filename: str
    total_sections: int = 0
    total_elements: int = 0
    sections: list[ReportSection] = Field(default_factory=list)
    preamble: list[ReportElement] = Field(
        default_factory=list,
        description="Elements before the first heading",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def flat_elements(self) -> list[ReportElement]:
        """All elements across all sections with section_id/element_id attached."""
        elems: list[ReportElement] = []
        for el in self.preamble:
            el.section_id = "_preamble"
            el.element_id = el.id
            elems.append(el)
        for sec in self.sections:
            for el in sec.elements:
                el.section_id = sec.id
                el.element_id = el.id
                elems.append(el)
        return elems

    @property
    def detected_patient_name(self) -> str | None:
        """Extract patient name from report metadata or header elements."""
        if self.metadata.get("patient_name"):
            return self.metadata["patient_name"]
        first = last = None
        for sec in self.sections:
            for el in sec.elements:
                t = el.text.strip()
                tl = t.lower()
                if tl.startswith("last name:"):
                    last = t.split(":", 1)[1].strip()
                elif tl.startswith("first name:"):
                    first = t.split(":", 1)[1].strip()
                elif tl.startswith("re:") or tl.startswith("patient:"):
                    return t.split(":", 1)[1].strip()[:80]
            if first or last:
                return f"{first or ''} {last or ''}".strip()
        return None


# ---------------------------------------------------------------------------
# Template differ output models
# ---------------------------------------------------------------------------

class SlotType(str, Enum):
    STATIC = "static"
    DYNAMIC_DIRECT = "dynamic_direct"
    DYNAMIC_NARRATIVE = "dynamic_narrative"
    DYNAMIC_LIST = "dynamic_list"
    DYNAMIC_TABLE = "dynamic_table"
    CONDITIONAL = "conditional"


class TemplateSlot(BaseModel):
    """One slot in the template -- either static text or a dynamic placeholder."""
    slot_type: SlotType
    static_text: Optional[str] = Field(
        default=None, description="Exact text if static",
    )
    label: Optional[str] = Field(
        default=None, description="Field label if dynamic_direct (e.g. 'Last Name')",
    )
    example_values: list[str] = Field(
        default_factory=list,
        description="Sample values seen across reports (for dynamic slots)",
    )
    element_index: int = Field(
        default=0, description="Position within the section",
    )


class TemplateSection(BaseModel):
    """One section in the canonical template."""
    id: str
    heading: str
    appears_in: int = Field(description="Number of reports containing this section")
    total_reports: int = 32
    is_required: bool = True
    classification: ContentClassification = ContentClassification.UNKNOWN
    slots: list[TemplateSlot] = Field(default_factory=list)


class ReportTemplate(BaseModel):
    """The canonical report template derived from cross-report diffing."""
    total_reports_analyzed: int
    total_sections: int = 0
    sections: list[TemplateSection] = Field(default_factory=list)
    section_order: list[str] = Field(
        default_factory=list, description="Canonical section ordering by id",
    )
    conditional_sections: list[str] = Field(
        default_factory=list, description="Section ids that don't appear in all reports",
    )
