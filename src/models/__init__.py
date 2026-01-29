"""
Pydantic models for form schema representation.
"""

from .field_types import FieldType, MarkType, DataType
from .fields import (
    ConditionalLogic,
    FormFieldSchema,
    TableColumnSchema,
    TableSchema,
)
from .sections import SectionSchema
from .pages import PageSchema
from .form import FormSchema, FieldLocation
from .extraction import SourceEvidence, ExtractedFieldValue
from .annotations import (
    VisualMarkType,
    BoundingBox,
    VisualElement,
    SpatialConnection,
    AnnotationGroup,
    FreeFormAnnotation,
    CircledSelection,
    CrossPageReference,
    UnknownMark,
    PageExtractionResult,
    FormExtractionResult,
)

__all__ = [
    # Enums
    "FieldType",
    "MarkType",
    "DataType",
    "VisualMarkType",
    # Field models
    "ConditionalLogic",
    "FormFieldSchema",
    "TableColumnSchema",
    "TableSchema",
    # Structure models
    "SectionSchema",
    "PageSchema",
    "FormSchema",
    "FieldLocation",
    # Extraction models
    "SourceEvidence",
    "ExtractedFieldValue",
    # Annotation models
    "BoundingBox",
    "VisualElement",
    "SpatialConnection",
    "AnnotationGroup",
    "FreeFormAnnotation",
    "CircledSelection",
    "CrossPageReference",
    "UnknownMark",
    "PageExtractionResult",
    "FormExtractionResult",
]
