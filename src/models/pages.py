"""
Models for form pages.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .fields import FormFieldSchema, TableSchema
from .sections import SectionSchema


class PageSchema(BaseModel):
    """Schema for a single page of the form."""
    
    page_number: int = Field(
        description="Page number (1-indexed)"
    )
    page_title: Optional[str] = Field(
        default=None,
        description="Title of this page if present"
    )
    sections: list[SectionSchema] = Field(
        default_factory=list,
        description="Organized sections on this page"
    )
    standalone_fields: list[FormFieldSchema] = Field(
        default_factory=list,
        description="Fields not belonging to any section"
    )
    standalone_tables: list[TableSchema] = Field(
        default_factory=list,
        description="Tables not belonging to any section"
    )
    complexity_score: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Complexity score 1-10 (helps estimate extraction difficulty)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any notes about this page (references to other pages, etc.)"
    )
    
    @property
    def total_fields(self) -> int:
        """Count total fields on this page."""
        count = len(self.standalone_fields)
        for section in self.sections:
            count += len(section.fields)
            for subsection in section.subsections:
                count += len(subsection.fields)
        return count
    
    @property
    def total_tables(self) -> int:
        """Count total tables on this page."""
        count = len(self.standalone_tables)
        for section in self.sections:
            count += len(section.tables)
        return count
