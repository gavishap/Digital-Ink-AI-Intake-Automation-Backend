"""
Enumerations for field types, mark types, and data types.
"""

from enum import Enum


class FieldType(str, Enum):
    """All possible field types found on medical forms."""
    
    # Text inputs
    TEXT_SHORT = "text_short"
    TEXT_LONG = "text_long"
    TEXT_NUMERIC = "text_numeric"
    
    # Date/time fields
    DATE = "date"
    DATE_PARTIAL = "date_partial"  # Month/Year only
    TIME = "time"
    DATETIME = "datetime"
    
    # Contact fields
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS_FULL = "address_full"
    ADDRESS_STREET = "address_street"
    ADDRESS_CITY = "address_city"
    ADDRESS_STATE = "address_state"
    ADDRESS_ZIP = "address_zip"
    
    # Selection fields
    YES_NO = "yes_no"
    YES_NO_NA = "yes_no_na"
    YES_NO_SOMETIMES = "yes_no_sometimes"
    CHECKBOX_SINGLE = "checkbox_single"
    CHECKBOX_MULTI = "checkbox_multi"
    RADIO_GROUP = "radio_group"
    CIRCLED_SELECTION = "circled_selection"
    
    # Numeric fields
    NUMERIC_SCALE = "numeric_scale"
    VAS_SCALE = "vas_scale"  # Visual Analog Scale
    PERCENTAGE = "percentage"
    
    # Special fields
    SIGNATURE = "signature"
    INITIALS = "initials"
    TABLE_ROW = "table_row"
    BODY_DIAGRAM = "body_diagram"
    
    # Other
    CALCULATED = "calculated"  # Auto-calculated from other fields
    STATIC_TEXT = "static_text"  # Instructions, helper text
    MEDICATION_LIST = "medication_list"  # Special list for medications


class MarkType(str, Enum):
    """Types of marks patients can make on forms."""
    
    HANDWRITING = "handwriting"  # Cursive or print text
    CIRCLE = "circle"  # Circle around printed option
    CHECKMARK = "checkmark"  # ✓
    X_MARK = "x_mark"  # X
    CROSSED_OUT = "crossed_out"  # Strikethrough
    ARROW = "arrow"  # Pointing to something
    UNDERLINE = "underline"
    FILL_IN_BLANK = "fill_in_blank"


class DataType(str, Enum):
    """Python/JSON data types for field values."""
    
    STRING = "string"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    OPTIONAL_STRING = "Optional[str]"
    OPTIONAL_INT = "Optional[int]"
    OPTIONAL_FLOAT = "Optional[float]"
    OPTIONAL_BOOL = "Optional[bool]"
    OPTIONAL_DATE = "Optional[date]"
    LIST_STRING = "List[str]"
    LIST_DICT = "List[dict]"
