"""
Models for form sections and their organization.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .fields import FormFieldSchema, TableSchema


class SectionSchema(BaseModel):
    """Schema for a section of the form."""
    
    section_id: str = Field(
        description="Unique identifier for this section"
    )
    section_title: str = Field(
        description="Title of the section as printed on form"
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Instructions or description for this section"
    )
    fields: list[FormFieldSchema] = Field(
        default_factory=list,
        description="List of fields in this section"
    )
    tables: list[TableSchema] = Field(
        default_factory=list,
        description="List of tables in this section"
    )
    subsections: list["SectionSchema"] = Field(
        default_factory=list,
        description="Nested subsections"
    )
    position_description: Optional[str] = Field(
        default=None,
        description="Where this section appears on the page"
    )


# Allow forward reference for nested subsections
SectionSchema.model_rebuild()
