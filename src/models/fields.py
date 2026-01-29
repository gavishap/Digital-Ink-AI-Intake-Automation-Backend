"""
Models for form fields, tables, and their schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .field_types import FieldType, DataType


class ConditionalLogic(BaseModel):
    """Defines conditional display/requirement logic for fields."""
    
    depends_on_field: str = Field(
        description="field_id of the parent field this depends on"
    )
    condition: str = Field(
        description="Condition to evaluate, e.g., 'equals', 'not_empty', 'contains'"
    )
    condition_value: Optional[str] = Field(
        default=None,
        description="Value to compare against for the condition"
    )
    action: str = Field(
        default="show",
        description="Action when condition is met: 'show', 'require', 'hide'"
    )


class FormFieldSchema(BaseModel):
    """Schema for a single form field."""
    
    field_id: str = Field(
        description="Unique snake_case identifier for this field"
    )
    field_label: str = Field(
        description="The printed text/label on the form"
    )
    field_type: FieldType = Field(
        description="Type of field (text, checkbox, etc.)"
    )
    data_type: DataType = Field(
        default=DataType.STRING,
        description="Python data type for the field value"
    )
    expected_format: Optional[str] = Field(
        default=None,
        description="Expected format, e.g., 'MM/DD/YYYY', '(XXX) XXX-XXXX'"
    )
    options: Optional[list[str]] = Field(
        default=None,
        description="List of choices for selection fields"
    )
    scale_min: Optional[int] = Field(
        default=None,
        description="Minimum value for numeric scales"
    )
    scale_max: Optional[int] = Field(
        default=None,
        description="Maximum value for numeric scales"
    )
    scale_labels: Optional[dict[str, str]] = Field(
        default=None,
        description="Labels for scale endpoints, e.g., {'0': 'No Pain', '10': 'Worst Pain'}"
    )
    is_required: bool = Field(
        default=False,
        description="Whether this field is required"
    )
    parent_field_id: Optional[str] = Field(
        default=None,
        description="field_id of parent field for sub-questions"
    )
    conditional_logic: Optional[ConditionalLogic] = Field(
        default=None,
        description="Conditional display/requirement logic"
    )
    section_name: Optional[str] = Field(
        default=None,
        description="Name of the section this field belongs to"
    )
    position_description: Optional[str] = Field(
        default=None,
        description="Relative location on page (top, middle, bottom, left, right)"
    )
    extraction_hints: Optional[str] = Field(
        default=None,
        description="Tips for the extraction phase"
    )
    helper_text: Optional[str] = Field(
        default=None,
        description="Instructions or helper text associated with this field"
    )


class TableColumnSchema(BaseModel):
    """Schema for a table column."""
    
    column_id: str = Field(
        description="Unique identifier for this column"
    )
    header: str = Field(
        description="Column header text"
    )
    data_type: DataType = Field(
        default=DataType.STRING,
        description="Data type for values in this column"
    )
    width_hint: Optional[str] = Field(
        default=None,
        description="Relative width: 'narrow', 'medium', 'wide'"
    )


class TableSchema(BaseModel):
    """Schema for a table on the form."""
    
    table_id: str = Field(
        description="Unique identifier for this table"
    )
    table_title: Optional[str] = Field(
        default=None,
        description="Title/header of the table"
    )
    columns: list[TableColumnSchema] = Field(
        description="List of column definitions"
    )
    row_type: str = Field(
        default="dynamic",
        description="'fixed' = pre-printed rows, 'dynamic' = user adds rows"
    )
    expected_rows: Optional[int] = Field(
        default=None,
        description="Number of expected rows if fixed"
    )
    row_labels: Optional[list[str]] = Field(
        default=None,
        description="Labels for each row if fixed rows have labels"
    )
    section_name: Optional[str] = Field(
        default=None,
        description="Name of the section this table belongs to"
    )
    extraction_hints: Optional[str] = Field(
        default=None,
        description="Tips for extracting table data"
    )
