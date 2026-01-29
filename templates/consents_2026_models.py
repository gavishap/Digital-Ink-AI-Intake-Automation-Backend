
"""
Pydantic Models for: consents_2026
Form ID: consents_2026

Generated on: 2026-01-16T13:08:00.552234
Total Pages: 3
Total Fields: 68

These models are designed for use with the `instructor` package
to extract data from filled-in versions of this form.

Usage:
    import instructor
    import anthropic
    from consents_2026_models import Consents2026Extraction

    client = instructor.from_anthropic(anthropic.Anthropic())

    result = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=8192,
        messages=[...],
        response_model=Consents2026Extraction,
    )
"""


from datetime import date, datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# Field Options Enums
class P3TransactionTypeOptions(str, Enum):
    STATEMENT_OF_ACTUAL_SERVICES = "Statement of Actual Services"
    REQUEST_FOR_PREDETERMINATION_PREAUTHORIZATION = "Request for Predetermination/Preauthorization"
    EPSDT_TITLE_XIX = "EPSDT/Title XIX"

class P3GenderOptions(str, Enum):
    M = "M"
    F = "F"

class P3PatientRelationshipOptions(str, Enum):
    SELF = "Self"
    SPOUSE = "Spouse"
    DEPENDENT_CHILD = "Dependent Child"
    OTHER = "Other"

class P3PolicyholderGenderOptions(str, Enum):
    M = "M"
    F = "F"

class P3RelationshipToPolicyholderOptions(str, Enum):
    SELF = "Self"
    SPOUSE = "Spouse"
    DEPENDENT_CHILD = "Dependent Child"
    OTHER = "Other"

class P3StudentStatusOptions(str, Enum):
    FTS = "FTS"
    PTS = "PTS"

class P3PatientGenderOptions(str, Enum):
    M = "M"
    F = "F"

class P3MissingTeethPermanentOptions(str, Enum):
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"
    VALUE_4 = "4"
    VALUE_5 = "5"
    VALUE_6 = "6"
    VALUE_7 = "7"
    VALUE_8 = "8"
    VALUE_9 = "9"
    VALUE_10 = "10"
    VALUE_11 = "11"
    VALUE_12 = "12"
    VALUE_13 = "13"
    VALUE_14 = "14"
    VALUE_15 = "15"
    VALUE_16 = "16"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    VALUE_32 = "32"
    VALUE_31 = "31"
    VALUE_30 = "30"
    VALUE_29 = "29"
    VALUE_28 = "28"
    VALUE_27 = "27"
    VALUE_26 = "26"
    VALUE_25 = "25"
    VALUE_24 = "24"
    VALUE_23 = "23"
    VALUE_22 = "22"
    VALUE_21 = "21"
    VALUE_20 = "20"
    VALUE_19 = "19"
    VALUE_18 = "18"
    VALUE_17 = "17"
    T = "T"
    S = "S"
    R = "R"
    Q = "Q"
    P = "P"
    O = "O"
    N = "N"
    M = "M"
    L = "L"
    K = "K"

class P3MissingTeethPrimaryOptions(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    T = "T"
    S = "S"
    R = "R"
    Q = "Q"
    P = "P"
    O = "O"
    N = "N"
    M = "M"
    L = "L"
    K = "K"

class P3PlaceOfTreatmentOptions(str, Enum):
    PROVIDER_S_OFFICE = "Provider's Office"
    HOSPITAL = "Hospital"
    ECF = "ECF"
    OTHER = "Other"

class P3TreatmentResultOptions(str, Enum):
    OCCUPATIONAL_ILLNESS_INJURY = "Occupational Illness/Injury"
    AUTO_ACCIDENT = "Auto accident"
    OTHER_ACCIDENT = "Other accident"



# =============================================================================
# EXTRACTION EVIDENCE MODELS
# =============================================================================

class MarkType(str, Enum):
    """Types of marks found on forms."""
    HANDWRITING = "handwriting"
    CIRCLE = "circle"
    CHECKMARK = "checkmark"
    X_MARK = "x_mark"
    CROSSED_OUT = "crossed_out"
    ARROW = "arrow"
    UNDERLINE = "underline"
    FILL_IN_BLANK = "fill_in_blank"


class SourceEvidence(BaseModel):
    """
    Tracks where extracted data came from on the form.
    Include this for audit trail and review flagging.
    """
    page_number: int = Field(description="Page number where value was found")
    anchor_text: str = Field(description="The printed label near the value")
    mark_type: MarkType = Field(description="Type of mark (handwriting, circle, etc.)")
    raw_handwriting: Optional[str] = Field(default=None, description="Exactly what is written")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    pertains_to: str = Field(description="What this value means")
    needs_review: bool = Field(default=False, description="Flag for human review")
    review_reason: Optional[str] = Field(default=None, description="Why review is needed")


class ExtractedFieldValue(BaseModel):
    """Generic extracted field value with evidence."""
    field_id: str = Field(description="The field this value corresponds to")
    raw_value: Optional[str] = Field(default=None, description="Raw extracted value")
    normalized_value: Any = Field(default=None, description="Cleaned/standardized value")
    is_empty: bool = Field(default=False, description="True if field was blank")
    evidence: Optional[SourceEvidence] = Field(default=None, description="Extraction evidence")
    both_options_marked: bool = Field(default=False, description="Both yes/no marked")
    crossed_out_values: list[str] = Field(default_factory=list, description="Changed answers")
    see_attached_reference: Optional[str] = Field(default=None, description="Reference to attachment")


class P3RecordOfServicesRow(BaseModel):
    """Row data for RECORD OF SERVICES PROVIDED."""

    procedure_date: Optional[date] = Field(default=None, description="Procedure Date (MM/DD/CCYY)")
    area_of_cavity: Optional[str] = Field(default=None, description="Area of Oral Cavity")
    tooth_system: Optional[str] = Field(default=None, description="Tooth System/Tooth Number(s)")
    tooth_numbers: Optional[str] = Field(default=None, description="Tooth Number(s) or Letter(s)")
    tooth_surface: Optional[str] = Field(default=None, description="Tooth Surface")
    procedure_code: Optional[str] = Field(default=None, description="Procedure Code")
    description: Optional[str] = Field(default=None, description="Description")
    fee: Optional[float] = Field(default=None, description="Fee")
class P2PatientInfo(BaseModel):
    """
    Patient Information
    """

    p2_patient_name: str = Field(description="Patient name:")
    p2_practice_physician: str = Field(description="Practice Physician:")
class P2ConsentSignatures(BaseModel):
    """
    Signatures
    """

    p2_patient_signature: str = Field(description="Patient signature")
    p2_patient_signature_date: date = Field(description="Date (Format: MM/DD/YYYY)")
    p2_witness_signature: Optional[str] = Field(default=None, description="Witness signature")
    p2_witness_signature_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class P3P3HeaderInformation(BaseModel):
    """
    HEADER INFORMATION
    """

    p3_transaction_type: list[str] = Field(default=None, description="Type of Transaction (Mark all applicable boxes)")  # Options: Statement of Actual Services, Request for Predetermination/Preauthorization, EPSDT/Title XIX
    p3_predetermination_number: Optional[str] = Field(default=None, description="Predetermination/Preauthorization Number")
class P3P3InsuranceCompany(BaseModel):
    """
    INSURANCE COMPANY/DENTAL BENEFIT PLAN INFORMATION
    """

    p3_company_plan_info: Optional[str] = Field(default=None, description="Company/Plan Name, Address, City, State, Zip Code")
class P3P3OtherCoverage(BaseModel):
    """
    OTHER COVERAGE
    """

    p3_other_dental_coverage: Optional[str] = Field(default=None, description="Other Dental or Medical Coverage?")
    p3_policyholder_subscriber_name: Optional[str] = Field(default=None, description="Name of Policyholder/Subscriber in #4 (Last, First, Middle Initial, Suffix)")
    p3_date_of_birth: Optional[date] = Field(default=None, description="Date of Birth (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_gender: Optional[str] = Field(default=None, description="Gender")  # Options: M, F
    p3_policyholder_id: Optional[str] = Field(default=None, description="Policyholder/Subscriber ID (SSN or ID#)")
    p3_plan_group_number: Optional[str] = Field(default=None, description="Plan/Group Number")
    p3_patient_relationship: Optional[str] = Field(default=None, description="Patient's Relationship to Person Named in #5")  # Options: Self, Spouse, Dependent Child, Other
    p3_other_insurance_info: Optional[str] = Field(default=None, description="Other Insurance Company/Dental Benefit Plan Name, Address, City, State, Zip Code")
class P3P3PolicyholderSubscriber(BaseModel):
    """
    POLICYHOLDER/SUBSCRIBER INFORMATION
    """

    p3_policyholder_name_info: Optional[str] = Field(default=None, description="Policyholder/Subscriber Name (Last, First, Middle Initial, Suffix), Address, City, State, Zip Code")
    p3_policyholder_birth_date: Optional[date] = Field(default=None, description="Date of Birth (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_policyholder_gender: Optional[str] = Field(default=None, description="Gender")  # Options: M, F
    p3_policyholder_id_number: Optional[str] = Field(default=None, description="Policyholder/Subscriber ID (SSN or ID#)")
    p3_plan_group_number_2: Optional[str] = Field(default=None, description="Plan/Group Number")
    p3_employer_name: Optional[str] = Field(default=None, description="Employer Name")
class P3P3PatientInformation(BaseModel):
    """
    PATIENT INFORMATION
    """

    p3_relationship_to_policyholder: Optional[str] = Field(default=None, description="Relationship to Policyholder/Subscriber in #12 Above")  # Options: Self, Spouse, Dependent Child, Other
    p3_student_status: Optional[str] = Field(default=None, description="Student Status")  # Options: FTS, PTS
    p3_patient_name_address: Optional[str] = Field(default=None, description="Name (Last, First, Middle Initial, Suffix), Address, City, State, Zip Code")
    p3_patient_birth_date: Optional[date] = Field(default=None, description="Date of Birth (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_patient_gender: Optional[str] = Field(default=None, description="Gender")  # Options: M, F
    p3_patient_account_number: Optional[str] = Field(default=None, description="Patient ID/Account # (Assigned by Dentist)")
class P3P3MissingTeeth(BaseModel):
    """
    MISSING TEETH INFORMATION
    """

    p3_missing_teeth_permanent: list[str] = Field(default=None, description="Place an 'X' on each missing tooth - Permanent")  # Options: 1, 2, 3, 4, 5...
    p3_missing_teeth_primary: list[str] = Field(default=None, description="Place an 'X' on each missing tooth - Primary")  # Options: A, B, C, D, E...
    p3_other_fee: Optional[str] = Field(default=None, description="Other Fee(s)")
    p3_total_fee: Optional[float] = Field(default=None, description="Total Fee")
    p3_remarks: Optional[str] = Field(default=None, description="Remarks")
class P3P3Authorizations(BaseModel):
    """
    AUTHORIZATIONS
    """

    p3_patient_guardian_signature: Optional[str] = Field(default=None, description="Patient/Guardian signature")
    p3_patient_signature_date: Optional[date] = Field(default=None, description="Date")
    p3_subscriber_signature: Optional[str] = Field(default=None, description="Subscriber signature")
    p3_subscriber_signature_date: Optional[date] = Field(default=None, description="Date")
class P3P3AncillaryClaim(BaseModel):
    """
    ANCILLARY CLAIM/TREATMENT INFORMATION
    """

    p3_place_of_treatment: Optional[str] = Field(default=None, description="Place of Treatment")  # Options: Provider's Office, Hospital, ECF, Other
    p3_number_of_enclosures: Optional[int] = Field(default=None, description="Number of Enclosures (00 to 99)")
    p3_treatment_orthodontics: Optional[str] = Field(default=None, description="Is Treatment for Orthodontics?")
    p3_date_appliance_placed: Optional[date] = Field(default=None, description="Date Appliance Placed (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_months_of_treatment: Optional[int] = Field(default=None, description="Months of Treatment Remaining")
    p3_replacement_prosthesis: Optional[str] = Field(default=None, description="Replacement of Prosthesis?")
    p3_date_prior_placement: Optional[date] = Field(default=None, description="Date Prior Placement (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_treatment_result: Optional[str] = Field(default=None, description="Treatment Resulting from")  # Options: Occupational Illness/Injury, Auto accident, Other accident
    p3_date_of_accident: Optional[date] = Field(default=None, description="Date of Accident (MM/DD/CCYY) (Format: MM/DD/YYYY)")
    p3_auto_accident_state: Optional[str] = Field(default=None, description="Auto Accident State")
class P3P3BillingDentist(BaseModel):
    """
    BILLING DENTIST OR DENTAL ENTITY
    """

    p3_billing_name_address: Optional[str] = Field(default=None, description="Name, Address, City, State, Zip Code")
    p3_billing_npi: Optional[str] = Field(default=None, description="NPI")
    p3_billing_license_number: Optional[str] = Field(default=None, description="License Number")
    p3_billing_ssn_tin: Optional[str] = Field(default=None, description="SSN or TIN")
    p3_billing_phone_1: Optional[str] = Field(default=None, description="Phone")
    p3_billing_additional_provider_id: Optional[str] = Field(default=None, description="Additional Provider ID")
    p3_billing_phone_2: Optional[str] = Field(default=None, description="Phone")
    p3_billing_additional_provider_id_2: Optional[str] = Field(default=None, description="Additional Provider ID")
class P3P3TreatingDentist(BaseModel):
    """
    TREATING DENTIST AND TREATMENT LOCATION INFORMATION
    """

    p3_treating_dentist_signature: Optional[str] = Field(default=None, description="Signed (Treating Dentist)")
    p3_treating_dentist_date: Optional[date] = Field(default=None, description="Date")
    p3_treating_dentist_npi: Optional[str] = Field(default=None, description="NPI")
    p3_treating_dentist_license: Optional[str] = Field(default=None, description="License Number")
    p3_treating_dentist_address: Optional[str] = Field(default=None, description="Address, City, State, Zip Code")
    p3_treating_dentist_provider_specialty: Optional[str] = Field(default=None, description="Provider Specialty Code")
class Page1Data(BaseModel):
    """
    Page 1: AUTHORIZATION FOR RELEASE OF HEALTH CARE INFORMATION TO AGENT(S) UNDER HIPAA AND CALIFORNIA LAW
    Complexity: 3/10
    """

    p1_patient_name: str = Field(description="I")
    p1_location_address: str = Field(description="at")
    p1_date: date = Field(description="Date (Format: MM/DD/YYYY)")
    p1_principal_name_printed: str = Field(description="Principal name (Printed)")
    p1_signature_principal: str = Field(description="Signature of Principal")
    p1_interpreter: Optional[str] = Field(default=None, description="Interpreter")
class Page2Data(BaseModel):
    """
    Page 2: THE DENTAL TRAUMA CENTER - E-MAIL CONSENT FORM
    Complexity: 4/10
    """

    patient_info: Optional[P2PatientInfo] = Field(default=None, description="Patient Information")
    consent_signatures: Optional[P2ConsentSignatures] = Field(default=None, description="Signatures")
class Page3Data(BaseModel):
    """
    Page 3: ADA Dental Claim Form
    Complexity: 8/10
    """

    p3_header_information: Optional[P3P3HeaderInformation] = Field(default=None, description="HEADER INFORMATION")
    p3_insurance_company: Optional[P3P3InsuranceCompany] = Field(default=None, description="INSURANCE COMPANY/DENTAL BENEFIT PLAN INFORMATION")
    p3_other_coverage: Optional[P3P3OtherCoverage] = Field(default=None, description="OTHER COVERAGE")
    p3_policyholder_subscriber: Optional[P3P3PolicyholderSubscriber] = Field(default=None, description="POLICYHOLDER/SUBSCRIBER INFORMATION")
    p3_patient_information: Optional[P3P3PatientInformation] = Field(default=None, description="PATIENT INFORMATION")
    p3_missing_teeth: Optional[P3P3MissingTeeth] = Field(default=None, description="MISSING TEETH INFORMATION")
    p3_authorizations: Optional[P3P3Authorizations] = Field(default=None, description="AUTHORIZATIONS")
    p3_ancillary_claim: Optional[P3P3AncillaryClaim] = Field(default=None, description="ANCILLARY CLAIM/TREATMENT INFORMATION")
    p3_billing_dentist: Optional[P3P3BillingDentist] = Field(default=None, description="BILLING DENTIST OR DENTAL ENTITY")
    p3_treating_dentist: Optional[P3P3TreatingDentist] = Field(default=None, description="TREATING DENTIST AND TREATMENT LOCATION INFORMATION")
    p3_record_of_services: list[P3RecordOfServicesRow] = Field(default_factory=list, description="RECORD OF SERVICES PROVIDED")
# =============================================================================
# MAIN EXTRACTION MODEL
# =============================================================================

class Consents2026Extraction(BaseModel):
    """
    Complete extraction model for: consents_2026
    
    Use this model with instructor to extract all data from filled forms.
    """

    # Metadata
    extraction_timestamp: Optional[datetime] = Field(default=None, description="When extraction occurred")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    needs_review: bool = Field(default=False, description="Form needs human review")
    review_reasons: list[str] = Field(default_factory=list, description="Why review is needed")

    # Page Data
    page_1: Optional[Page1Data] = Field(default=None, description="Page 1: AUTHORIZATION FOR RELEASE OF HEALTH CARE INFORMATION TO AGENT(S) UNDER HIPAA AND CALIFORNIA LAW")
    page_2: Optional[Page2Data] = Field(default=None, description="Page 2: THE DENTAL TRAUMA CENTER - E-MAIL CONSENT FORM")
    page_3: Optional[Page3Data] = Field(default=None, description="Page 3: ADA Dental Claim Form")

    # Field-level evidence (optional, for detailed tracking)
    field_evidence: list[ExtractedFieldValue] = Field(default_factory=list, description="Detailed evidence for each extracted field")
