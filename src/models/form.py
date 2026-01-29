"""
Models for complete form schema.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .pages import PageSchema


class FieldLocation(BaseModel):
    """Quick lookup for field location."""
    
    page_number: int
    section_id: Optional[str] = None
    position_description: Optional[str] = None


class FormSchema(BaseModel):
    """Complete schema for a multi-page form."""
    
    form_name: str = Field(
        description="Human-readable name for this form"
    )
    form_id: str = Field(
        description="Unique snake_case identifier for this form"
    )
    form_description: Optional[str] = Field(
        default=None,
        description="Description of what this form is used for"
    )
    total_pages: int = Field(
        description="Total number of pages in this form"
    )
    pages: list[PageSchema] = Field(
        description="List of all page schemas"
    )
    field_index: dict[str, FieldLocation] = Field(
        default_factory=dict,
        description="Dict mapping field_id to page/location for quick lookup"
    )
    cross_page_references: list[str] = Field(
        default_factory=list,
        description="Notes about references between pages (e.g., 'see attached sheet')"
    )
    extraction_notes: Optional[str] = Field(
        default=None,
        description="General notes for the extraction phase"
    )
    
    def build_field_index(self) -> None:
        """Build the field_index from pages."""
        self.field_index = {}
        for page in self.pages:
            # Index standalone fields
            for field in page.standalone_fields:
                self.field_index[field.field_id] = FieldLocation(
                    page_number=page.page_number,
                    section_id=None,
                    position_description=field.position_description
                )
            # Index section fields
            for section in page.sections:
                for field in section.fields:
                    self.field_index[field.field_id] = FieldLocation(
                        page_number=page.page_number,
                        section_id=section.section_id,
                        position_description=field.position_description
                    )
                # Index subsection fields
                for subsection in section.subsections:
                    for field in subsection.fields:
                        self.field_index[field.field_id] = FieldLocation(
                            page_number=page.page_number,
                            section_id=f"{section.section_id}.{subsection.section_id}",
                            position_description=field.position_description
                        )
    
    @property
    def total_fields(self) -> int:
        """Count total fields across all pages."""
        return sum(page.total_fields for page in self.pages)
    
    @property
    def total_tables(self) -> int:
        """Count total tables across all pages."""
        return sum(page.total_tables for page in self.pages)
    
    def get_field_by_id(self, field_id: str) -> Optional[tuple[int, "FormFieldSchema"]]:
        """
        Get a field by its ID.
        Returns (page_number, field) or None if not found.
        """
        from .fields import FormFieldSchema
        
        for page in self.pages:
            for field in page.standalone_fields:
                if field.field_id == field_id:
                    return (page.page_number, field)
            for section in page.sections:
                for field in section.fields:
                    if field.field_id == field_id:
                        return (page.page_number, field)
                for subsection in section.subsections:
                    for field in subsection.fields:
                        if field.field_id == field_id:
                            return (page.page_number, field)
        return None
