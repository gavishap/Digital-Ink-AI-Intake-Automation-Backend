
"""
Pydantic Models for: orofacial_exam
Form ID: orofacial_exam

Generated on: 2026-02-03T21:21:36.630499
Total Pages: 20
Total Fields: 583

These models are designed for use with the `instructor` package
to extract data from filled-in versions of this form.

Usage:
    import instructor
    import anthropic
    from orofacial_exam_models import OrofacialExamExtraction

    client = instructor.from_anthropic(anthropic.Anthropic())

    result = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=8192,
        messages=[...],
        response_model=OrofacialExamExtraction,
    )
"""


from datetime import date, datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# Field Options Enums
class P1GenderOptions(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class P1HeartProblemsTypesOptions(str, Enum):
    MURMUR = "Murmur"
    MITRAL_VALVE_PROBLEM = "Mitral Valve Problem"
    STENT = "Stent"
    PACEMAKER = "Pacemaker"
    RHEUMATIC_HEART_DISEASE = "Rheumatic Heart Disease"

class P1InfectiousDiseasesOptions(str, Enum):
    HIV = "HIV"
    HEPATITIS = "Hepatitis"
    TB = "TB"
    VD = "VD"

class P1BreathingProblemsTypesOptions(str, Enum):
    ASTHMA = "Asthma"
    SHORTNESS_OF_BREATH = "Shortness of Breath"

class P1AllergiesOptions(str, Enum):
    PENICILLIN = "Penicillin"
    SULFA = "Sulfa"
    ERYTHROMYCIN = "Erythromycin"
    SEASONAL_ALLERGIES = "Seasonal Allergies"

class P1CurrentMedicationsOptions(str, Enum):
    PRISTIQ = "Pristiq"
    WELLBUTRIN = "Wellbutrin"
    EFFEXOR = "Effexor"
    CELEXA = "Celexa"
    CYMBALTA = "Cymbalta"
    PROZAC = "Prozac"
    LEXAPRO = "Lexapro"
    ZOLOFT = "Zoloft"
    PAXIL = "Paxil"
    OMEPRAZOLE = "Omeprazole"
    PRILOSEC = "Prilosec"
    IBUPROFEN = "Ibuprofen"
    MOTRIN = "Motrin"
    ADVIL = "Advil"
    TYLENOL = "Tylenol"
    ALEVE = "Aleve"
    NAPROXEN = "Naproxen"
    NAPROSYN = "Naprosyn"
    FLEXERIL = "Flexeril"
    TRAMADOL = "Tramadol"
    HYDROCODONE = "Hydrocodone"
    VICODIN = "Vicodin"
    NORCO = "Norco"
    OXYCODONE = "Oxycodone"
    AMBIEN = "Ambien"
    ZOLPIDEM = "Zolpidem"
    ALPRAZOLAM = "Alprazolam"
    ULTRAM = "Ultram"
    GABAPENTIN = "Gabapentin"
    NEURONTIN = "Neurontin"
    METFORMIN = "Metformin"
    GLYBURIDE = "Glyburide"
    CYCLOBENZAPRINE = "Cyclobenzaprine"
    HYDROCHLOROTHIAZIDE = "Hydrochlorothiazide"
    LISINOPRIL = "Lisinopril"
    ATENOLOL = "Atenolol"
    THYROXINE = "Thyroxine"
    ATORVASTATIN = "Atorvastatin"

class P1MedicationsForConditionsOptions(str, Enum):
    DIABETES = "Diabetes"
    SLEEP = "Sleep"
    HIGH_BLOOD_PRESSURE = "High Blood Pressure"
    PAIN = "Pain"
    ANTI_INFLAMMATORY = "Anti-Inflammatory"
    CHOLESTEROL__SEE_ATTACHED_SHEET_ = "Cholesterol (see attached sheet)"

class P3MouthSymptomsOptions(str, Enum):
    """Shared options for all mouth symptom questions on page 3."""
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3BadBreathBeforeOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P3BadBreathAfterOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P3HalitosisReadingOptions(str, Enum):
    VALUE_1___NO_ODOR = "1 = No Odor"
    VALUE_2___SLIGHT_ODOR = "2 = Slight Odor"
    VALUE_3___MODERATE_ODOR = "3 = Moderate Odor"
    VALUE_4___STRONG_ODOR = "4 = Strong Odor"
    VALUE_5___INTENSE_ODOR = "5 = Intense Odor"

class P3TasteFeelsBlandOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3TastePerceptionChangeOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3TasteCovidRelatedOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3DoctorCovidDiagnosisOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3GerdWorkRelatedOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4HandDominanceOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P4RightBodyPartsInjuredOptions(str, Enum):
    SHOULDER = "Shoulder"
    ARM = "Arm"
    ELBOW = "Elbow"
    WRIST = "Wrist"
    HAND = "Hand"
    FINGERS = "Fingers"

class P4LeftBodyPartsInjuredOptions(str, Enum):
    SHOULDER = "Shoulder"
    ARM = "Arm"
    ELBOW = "Elbow"
    WRIST = "Wrist"
    HAND = "Hand"
    FINGERS = "Fingers"

class P5GenderOptions(str, Enum):
    M = "M"
    F = "F"

class P5HandDominanceOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P5JobRequirementsInitialOptions(str, Enum):
    DRIVING = "driving"
    WALKING = "walking"
    STANDING = "standing"
    SITTING = "sitting"
    SQUATTING = "squatting"
    TWISTING = "twisting"
    BENDING_FORWARD = "bending forward"
    SIDE_BENDING = "side bending"
    REACHING_BELOW_SHOULDER_LEVEL = "reaching below shoulder level"
    REACHING_ABOVE_SHOULDER_LEVEL = "reaching above shoulder level"
    PUSHING = "pushing"
    PULLING = "pulling"
    GRASPING = "grasping"
    GRIPPING = "gripping"

class P5ComputerMouseHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5WorkstationTypeOptions(str, Enum):
    DESK = "desk"
    CHAIR = "chair"
    WORK_STATION = "work station"

class P5MonitorLocationOptions(str, Enum):
    F = "F"
    R = "R"
    L = "L"

class P5PhoneCradleHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5CurrentWorkStatusOptions(str, Enum):
    DISABLED = "Disabled"
    STILL_WORKING_AT_THE_SAME_COMPANY = "Still working at the same company"
    NOT_WORKING_RETIRED = "Not Working/Retired"

class P5JobRequirementsCurrentOptions(str, Enum):
    DRIVING = "driving"
    WALKING = "walking"
    STANDING = "standing"
    SITTING = "sitting"
    SQUATTING = "squatting"
    TWISTING = "twisting"
    BENDING_FORWARD = "bending forward"
    SIDE_BENDING = "side bending"
    REACHING_BELOW_SHOULDER_LEVEL = "reaching below shoulder level"
    REACHING_ABOVE_SHOULDER_LEVEL = "reaching above shoulder level"
    PUSHING = "pushing"
    PULLING = "pulling"
    GRASPING = "grasping"
    GRIPPING = "gripping"

class P5CurrentComputerMouseHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5CurrentWorkstationTypeOptions(str, Enum):
    DESK = "desk"
    CHAIR = "chair"
    WORK_STATION = "work station"

class P5CurrentMonitorLocationOptions(str, Enum):
    F = "F"
    R = "R"
    L = "L"

class P5CurrentPhoneCradleHandOptions(str, Enum):
    R = "R"
    L = "L"

class P6MvaRoleOptions(str, Enum):
    DRIVER = "Driver"
    PASSENGER = "Passenger"
    RIGHT_REAR_SEAT = "Right Rear Seat"
    LEFT_REAR_SEAT = "Left Rear Seat"

class P6VehicleHitOnOptions(str, Enum):
    R = "R"
    L = "L"
    FRONT = "Front"
    REAR = "Rear"

class P6WearingSeatbeltOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P6AirbagDeployedOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P6ThrownAboutOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P6StruckMouthFaceOptions(str, Enum):
    STEERING_WHEEL = "Steering Wheel"
    DOOR = "Door"
    WINDOW = "Window"

class P6StruckBackOfHeadOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P6DirectTraumaFaceJawOptions(str, Enum):
    R = "R"
    L = "L"

class P6FracturedJawOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P7StressorsWorkOptions(str, Enum):
    HEAVY_WORKLOAD = "Heavy workload"
    LONG_OR_INFLEXIBLE_HOURS = "Long or inflexible hours"
    TIGHT_DEADLINES = "Tight deadlines"
    LACK_OF_CONTROL = "Lack of control"
    CONFLICTING_OR_UNCERTAIN_JOB_EXPECTATIONS = "Conflicting or uncertain job expectations"
    NIGHT_SHIFTS = "Night shifts"
    LACK_OF_SUPPORT = "Lack of support"
    BULLYING = "Bullying"
    POOR_RELATIONSHIPS = "Poor relationships"

class P7VertexLocationOptions(str, Enum):
    R = "R"
    L = "L"
    FOREHEAD = "Forehead"
    TEMPLE = "Temple"
    OCCIPUT = "Occiput"
    BEHIND_EYES = "Behind Eyes"

class P7FacialPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    B = "B"

class P7TmjPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    B = "B"

class P7NightguardStopReasonOptions(str, Enum):
    DOES_NOT_FIT = "Does not fit"
    LOST = "Lost"
    WORE_OUT = "Wore Out"
    BROKEN = "Broken"

class P7SurgeryBodyPartsOptions(str, Enum):
    NECK = "Neck"
    R_SHOULDER = "R Shoulder"
    L_SHOULDER = "L Shoulder"
    R_ARM = "R Arm"
    L_ARM = "L Arm"
    R_ELBOW = "R Elbow"
    L_ELBOW = "L Elbow"
    R_WRIST = "R Wrist"
    L_WRIST = "L Wrist"
    R_HAND = "R Hand"
    L_HAND = "L Hand"
    R_FINGERS = "R Fingers"
    L_FINGERS = "L Fingers"
    R_THUMB = "R Thumb"
    L_THUMB = "L Thumb"
    BACK = "Back"
    R_HIP = "R Hip"
    L_HIP = "L Hip"
    R_KNEE = "R Knee"
    L_KNEE = "L Knee"
    R_LEG = "R Leg"
    L_LEG = "L Leg"
    R_FEET = "R Feet"
    L_FEET = "L Feet"
    R_ANKLES = "R Ankles"
    L_ANKLES = "L Ankles"

class P9LastDentistVisitOptions(str, Enum):
    YEARS_AGO = "Years ago"
    MONTHS_AGO = "Months ago"
    WEEKS_AGO = "Weeks ago"
    OTHER = "Other"
    NEVER = "Never"

class P9RestorationsLocationOptions(str, Enum):
    UR = "UR"
    UL = "UL"
    LR = "LR"
    LL = "LL"

class P9RootCanalsLocationOptions(str, Enum):
    UR = "UR"
    UL = "UL"
    LR = "LR"
    LL = "LL"

class P9CrownsLocationOptions(str, Enum):
    UR = "UR"
    UL = "UL"
    LR = "LR"
    LL = "LL"

class P9ImplantsLocationOptions(str, Enum):
    UR = "UR"
    UL = "UL"
    LR = "LR"
    LL = "LL"

class P9PartialDentureLocationOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"

class P9CompleteDentureLocationOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"

class P9OralApplianceTypeOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"
    BRUXISM_ORAL_APPLIANCE = "Bruxism Oral Appliance"
    ORAL_SLEEP_APPLIANCE = "Oral Sleep Appliance"

class P10FrameSizeOptions(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"

class P10SnoresConditionOptions(str, Enum):
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10GaspsConditionOptions(str, Enum):
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10PalpitationsConditionOptions(str, Enum):
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10BreathingConditionOptions(str, Enum):
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10HeadacheLocationsOptions(str, Enum):
    ON_TOP_OF_HEAD = "On Top of Head"
    TEMPLE_R = "Temple R"
    TEMPLE_L = "Temple L"
    FOREHEAD_R = "Forehead R"
    FOREHEAD_L = "Forehead L"
    OCCIPITAL_R = "Occipital R"
    OCCIPITAL_L = "Occipital L"
    BEHIND_THE_EYES = "Behind the Eyes"

class P10HeadacheFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10HeadacheQualityOptions(str, Enum):
    DULL = "Dull"
    ACHING = "Aching"
    BURNING = "Burning"
    STABBING = "Stabbing"
    ELECTRICAL = "Electrical"
    SHARP = "Sharp"
    SHOOTING = "Shooting"
    NUMBNESS = "Numbness"
    PINS = "Pins"
    NEEDLES = "Needles"
    PULSING = "Pulsing"

class P10HeadacheSeverityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10RightFacePainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10RightFacePainQualityOptions(str, Enum):
    DULL = "Dull"
    ACHING = "Aching"
    BURNING = "Burning"
    STABBING = "Stabbing"
    ELECTRICAL = "Electrical"
    SHARP = "Sharp"
    SHOOTING = "Shooting"
    NUMBNESS = "Numbness"
    PINS = "Pins"
    NEEDLES = "Needles"
    PULSING = "Pulsing"

class P10RightFacePainSeverityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10LeftFacePainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10LeftFacePainQualityOptions(str, Enum):
    DULL = "Dull"
    ACHING = "Aching"
    BURNING = "Burning"
    STABBING = "Stabbing"
    ELECTRICAL = "Electrical"
    SHARP = "Sharp"
    SHOOTING = "Shooting"
    NUMBNESS = "Numbness"
    PINS = "Pins"
    NEEDLES = "Needles"
    PULSING = "Pulsing"

class P10LeftFacePainSeverityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10NoisesInTmjOptions(str, Enum):
    R = "R"
    L = "L"
    GRINDING = "Grinding"
    CLICKING = "Clicking"

class P10RightTmjPainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10RightTmjPainQualityOptions(str, Enum):
    DULL = "Dull"
    ACHING = "Aching"
    BURNING = "Burning"
    STABBING = "Stabbing"
    ELECTRICAL = "Electrical"
    SHARP = "Sharp"
    SHOOTING = "Shooting"
    NUMBNESS = "Numbness"
    PINS = "Pins"
    NEEDLES = "Needles"
    PULSING = "Pulsing"

class P10RightTmjPainSeverityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10LeftTmjPainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10LeftTmjPainQualityOptions(str, Enum):
    DULL = "Dull"
    ACHING = "Aching"
    BURNING = "Burning"
    STABBING = "Stabbing"
    ELECTRICAL = "Electrical"
    SHARP = "Sharp"
    SHOOTING = "Shooting"
    NUMBNESS = "Numbness"
    PINS = "Pins"
    NEEDLES = "Needles"
    PULSING = "Pulsing"

class P10LeftTmjPainSeverityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P11LockingFrequencyOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    CLOSED = "Closed"
    OPEN = "Open"

class P11LockingClosedFrequencyOptions(str, Enum):
    DAY = "day"
    WK = "wk"
    MONTH = "month"

class P11LockingOpenFrequencyOptions(str, Enum):
    DAY = "day"
    WK = "wk"
    MONTH = "month"

class P11DifficultPainfulChewOptions(str, Enum):
    FACE = "Face"
    TMJ = "TMJ"
    TEETH = "Teeth"
    R = "R"
    L = "L"

class P11FacialPainOptions(str, Enum):
    SMILING = "Smiling"
    YAWNING = "Yawning"

class P11SorenessFaceJawAwakeningOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    R = "R"
    L = "L"

class P11SpeechDysfunctionOptions(str, Enum):
    INDISTINCT_ARTICULATION = "Indistinct Articulation"
    HOARSENESS = "Hoarseness"
    COTTON_MOUTH = "Cotton Mouth"
    MISSING_UPPER_ANTERIOR_TEETH = "Missing Upper Anterior Teeth"
    CANNOT_TALK_FOR_LONG_PERIODS_OF_TIME_DUE_TO_PAIN = "Cannot Talk for Long Periods of Time Due to Pain"
    JAW_TIREDNESS = "Jaw Tiredness"
    CAN_SPEAK_MAX__TIME____MINUTES = "Can Speak Max. Time ___Minutes"

class P11VoiceChangesOptions(str, Enum):
    TONE = "Tone"
    PITCH = "Pitch"
    SLURRING = "Slurring"
    DROOLING = "Drooling"
    PEOPLE_ASKING_PATIENT_TO_REPEAT_THEMSELVES = "People Asking Patient To Repeat Themselves"

class P11EarProblemsOptions(str, Enum):
    R = "R"
    L = "L"
    BOTH = "Both"
    RINGING = "Ringing"
    PAIN = "Pain"
    PRESSURE = "Pressure"
    LOSS_OF_HEARING = "Loss of Hearing"
    ITCHING = "Itching"
    BUZZING = "Buzzing"
    STATIC = "Static"

class P12EatingHardChewyFoodPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ProlongedSpeakingPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12RepeatNotUnderstoodOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12IntenseKissingPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SleepInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SleepingPressurePainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SocialActivitiesInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12RelationshipInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ConcentrationInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12IrritableAngryOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ExperienceStressOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12TalkingAbilityOptions(str, Enum):
    YOU_CAN_TALK_AS_MUCH_AS_YOU_WANT_WITHOUT_FACIAL_PAIN__JAW_TIREDNESS_OR_DISCOMFORT = "You can talk as much as you want without facial pain, jaw tiredness or discomfort"
    YOU_CAN_TALK_AS_MUCH_AS_YOU_WANT__BUT_TALKING_CAUSES_SOME_FACIAL_PAIN__JAW_TIREDNESS_OR_DISCOMFORT = "You can talk as much as you want, but talking causes some facial pain, jaw tiredness or discomfort"
    YOU_CAN_NOT_TALK_AS_MUCH_AS_YOU_WANT_BECAUSE_OF_FACIAL_PAIN__JAW_TIREDNESS_OR_DISCOMFORT = "You can not talk as much as you want because of facial pain, jaw tiredness or discomfort"
    YOU_CAN_NOT_TALK_MUCH_AT_ALL_BECAUSE_OF_YOUR_FACIAL_PAIN__JAW_TIREDNESS_OR_DISCOMFORT = "You can not talk much at all because of your facial pain, jaw tiredness or discomfort"
    YOUR_FACIAL_PAIN_PREVENTS_YOU_FROM_TALKING_AT_ALL_EXCEPT_FOR_ANSWERING_YES_OR_NO_OR_ONLY_SOME_WORDS_AT_A_TIME = "Your facial pain prevents you from talking at all except for answering yes or no or only some words at a time"

class P12EatingAbilityOptions(str, Enum):
    YOU_CAN_EAT_AND_CHEW_ANYTHING_YOU_WANT_WITHOUT_FACIAL_PAIN__DISCOMFORT_OR_JAW_TIREDNESS = "You can eat and chew anything you want without facial pain, discomfort or jaw tiredness"
    YOU_CAN_EAT_AND_CHEW_MOST_ANYTHING_YOU_WANT__BUT_IT_SOMETIMES_CAUSES_FACIAL_PAIN__DISCOMFORT_OR_JAW_TIREDNESS = "You can eat and chew most anything you want, but it sometimes causes facial pain, discomfort or jaw tiredness"
    YOU_CANNOT_EAT_HARD_OR_CHEWY_FOODS__BECAUSE_IT_OFTEN_CAUSES_FACIAL_PAIN__DISCOMFORT_OR_JAW_TIREDNESS = "You cannot eat hard or chewy foods, because it often causes facial pain, discomfort or jaw tiredness"
    YOU_MUST_EAT_ONLY_SOFT_FOODS__CONSISTENCY_OF_SCRAMBLED_EGGS_OR_LESS__BECAUSE_OF_YOUR_FACIAL_PAIN__DISCOMFORT_OR_JAW_TIREDNESS = "You must eat only soft foods (consistency of scrambled eggs or less) because of your facial pain, discomfort or jaw tiredness"
    YOU_MUST_STAY_ON_A_LIQUID_DIET_BECAUSE_OF_YOUR_FACIAL_PAIN = "You must stay on a liquid diet because of your facial pain"

class P12HardFoodsRestrictionOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ChewyFoodsRestrictionOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SoftFoodsOnlyOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P13BrushingTeethSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13FlossingTeethSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13SpeakExtendedPeriodSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13SpeakingDifficultySeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13AskedToRepeatThemselvesSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13MasticationSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13TastingSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13TasteChangeTypeOptions(str, Enum):
    BITTER = "Bitter"
    METALLIC = "Metallic"
    BLAND = "Bland"

class P13SwallowingSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13BruxismSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P13KissingOralActivitiesSeverityOptions(str, Enum):
    NONE = "None"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P14TenderPhalangesOptions(str, Enum):
    R = "R"
    L = "L"

class P14FacialPalsyOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P14FacialAtrophyOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P14FacialHypertrophyOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P14TongueProtrusionOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"
    STRAIGHT = "Straight"

class P14MaxOpeningPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14RightLateralPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14LeftLateralPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14ProtrusionPainLocationOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14JawDeviationDirectionOptions(str, Enum):
    R = "R"
    L = "L"

class P14SFormDeviationOptions(str, Enum):
    R = "R"
    L = "L"

class P15ClassSelectionOptions(str, Enum):
    I = "I"
    II = "II"
    III = "III"

class P15CrossbiteOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"

class P15BiteTypeOptions(str, Enum):
    CLOSED_BITE = "Closed Bite"
    COLLAPSED_BITE = "Collapsed Bite"
    UNSTABLE_BITE = "Unstable Bite"

class P15OpenBiteOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"

class P15TongueThrustOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"
    BOTH_SIDES = "Both Sides"

class P15ToriLocationOptions(str, Enum):
    MAX = "Max"
    MAN = "Man"

class P15ScallopingOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SIGNIFICANT = "Significant"

class P15BuccalMucosalRidgingOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SIGNIFICANT = "Significant"

class P15OcclusalWearOptions(str, Enum):
    NONE_APPARENT = "None Apparent"
    RIGHT = "Right"
    LEFT = "Left"
    ANT_ = "Ant."
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SIGNIFICANT = "Significant"

class P15PatientHasOptions(str, Enum):
    FUD = "FUD"
    FLD = "FLD"
    UPD = "UPD"
    LPD = "LPD"

class P15FracturedDenturesOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"
    FULL = "Full"
    PARTIAL = "Partial"

class P15AbfractionsTeethOptions(str, Enum):
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
    VALUE_18 = "18"
    VALUE_19 = "19"
    VALUE_20 = "20"
    VALUE_21 = "21"
    VALUE_22 = "22"
    VALUE_23 = "23"
    VALUE_24 = "24"
    VALUE_25 = "25"
    VALUE_26 = "26"
    VALUE_27 = "27"
    VALUE_28 = "28"
    VALUE_29 = "29"
    VALUE_30 = "30"
    VALUE_31 = "31"

class P15MissingTeethOptions(str, Enum):
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
    VALUE_18 = "18"
    VALUE_19 = "19"
    VALUE_20 = "20"
    VALUE_21 = "21"
    VALUE_22 = "22"
    VALUE_23 = "23"
    VALUE_24 = "24"
    VALUE_25 = "25"
    VALUE_26 = "26"
    VALUE_27 = "27"
    VALUE_28 = "28"
    VALUE_29 = "29"
    VALUE_30 = "30"
    VALUE_31 = "31"

class P15MissingThirdMolarsOptions(str, Enum):
    VALUE_1 = "1"
    VALUE_16 = "16"
    VALUE_17 = "17"
    VALUE_32 = "32"

class P15GumRecessionTeethOptions(str, Enum):
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
    VALUE_18 = "18"
    VALUE_19 = "19"
    VALUE_20 = "20"
    VALUE_21 = "21"
    VALUE_22 = "22"
    VALUE_23 = "23"
    VALUE_24 = "24"
    VALUE_25 = "25"
    VALUE_26 = "26"
    VALUE_27 = "27"
    VALUE_28 = "28"
    VALUE_29 = "29"
    VALUE_30 = "30"
    VALUE_31 = "31"

class P19BuccalMucosalRidgingOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19OcclusalWearOptions(str, Enum):
    ANTERIOR = "Anterior"
    GENERALIZED = "Generalized"

class P19ErosionClassOptions(str, Enum):
    CLASS_I = "Class I"
    II = "II"
    III = "III"
    OCCLUSION = "Occlusion"

class P19DeviationTongueProtrusionOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19DeviationMandibleOpeningOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19FacialPalsyOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19OpenBiteOptions(str, Enum):
    ANTERIOR = "Anterior"
    RIGHT = "Right"
    LEFT = "Left"

class P19CrossBiteOptions(str, Enum):
    ANTERIOR = "Anterior"
    RIGHT = "Right"
    LEFT = "Left"

class P19CollapsedBiteOptions(str, Enum):
    UNSTABLE_BITE = "Unstable Bite"
    OFF_BITE = "Off Bite"

class P19HypertrophyMasseterOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"
    BILATERAL = "Bilateral"

class P19TongueTrustOptions(str, Enum):
    ANTERIOR = "Anterior"
    LATERAL = "Lateral"
    RIGHT = "Right"
    LEFT = "Left"

class P20TreatmentCheckboxesOptions(str, Enum):
    ORTHOTIC_APPLIANCE___RESILIENT_ORTHOTIC_OAOA_OSA_TRD_DIAGNOSTIC_SPLINT = "Orthotic Appliance / Resilient Orthotic OAOA OSA TRD Diagnostic Splint"
    CRANIOFACIAL_EXERCISES = "Craniofacial Exercises"
    TRIGGER_POINT_INJECTIONS = "Trigger Point Injections"
    SPHENOPALATINE_GANGLION_BLOCKS = "Sphenopalatine Ganglion Blocks"
    TRIGEMINAL_PHARYNGOPLASTY = "Trigeminal Pharyngoplasty"
    FMX = "FMX"
    PANOREX = "Panorex"
    MRI_IF_LOCKING_PERSISTS = "MRI if locking Persists"
    SURGICAL_CONSULTATION_IF_LOCKING_PERSISTS = "Surgical Consultation if Locking Persists"

class P20ConsultationsNeededOptions(str, Enum):
    SLEEP_STUDY_REPORT_NEEDED = "Sleep Study Report Needed"
    POLYSOMNOGRAM_NEEDED = "Polysomnogram Needed"
    PHYSICAL_THERAPY_TREATMENT_NEEDED = "Physical Therapy Treatment Needed"
    PSYCHOLOGICAL_CONSULTATION_NEEDED = "Psychological Consultation Needed"
    NEUROLOGICAL_CARE_NEEDED = "Neurological Care Needed"
    ORTHOPEDIC_CONSULTATION_NEEDED = "Orthopedic Consultation Needed"
    RHEUMATOLOGICAL_CONSULTATION_TO_RULE_OUT_FIBROMYALGIA_NEEDED = "Rheumatological Consultation to rule out Fibromyalgia Needed"

class P20InternalMedicineConsultsOptions(str, Enum):
    HBP = "HBP"
    DIABETES = "Diabetes"
    GERD = "GERD"
    KIDNEY = "Kidney"
    THYROID = "Thyroid"

class P20DentalConsultationsOptions(str, Enum):
    REFERRAL_FOR_EVALUATION_AND_TREATMENT_WITH_PROSTHODONTIC_PERIODONTIST_SPECIALIST = "Referral for Evaluation And Treatment with Prosthodontic/Periodontist Specialist"
    ORAL_SURGERY_CONSULTATION = "Oral Surgery Consultation"
    ORTHODONTIC_CONSULTATION = "Orthodontic Consultation"

class P20DentalConsultationReasonsOptions(str, Enum):
    TREATMENT_FOR_DECAY = "Treatment for Decay"
    FRACTURED_TEETH = "Fractured Teeth"
    XEROSTOMIA___PERIODONTAL_DISEASE = "Xerostomia / Periodontal Disease"

class P20PatientRecordsTasksOptions(str, Enum):
    PATIENT_TO_GET_DENTAL_RECORDS___FMX = "Patient to get Dental Records / FMX"
    PATIENT_TO_GET_PRESCRIPTIONS_FROM_PHARMACY = "Patient to get Prescriptions from Pharmacy"
    I_NEED_ALL_MEDICAL_AND_DENTAL_RECORDS = "I NEED ALL MEDICAL AND DENTAL RECORDS"



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


class P1DoctorCompletionTableRow(BaseModel):
    """Row data for BELOW THE LINE TO BE COMPLETED BY THE DOCTOR:.
    Doctor marks X/checkmark/arrow in cells. True = marked, False/None = empty.
    """

    condition: Optional[str] = Field(default=None, description="Condition name (row label)")
    dx_pre_injury: Optional[bool] = Field(default=None, description="DX Pre-Injury — True if marked (X, checkmark, or arrow)")
    increased_after_injury: Optional[bool] = Field(default=None, description="Increased After Injury — True if marked")
    dx_post_injury: Optional[bool] = Field(default=None, description="DX Post-Injury — True if marked")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P6OrthopedicInjuriesRow(BaseModel):
    """Row data for Orthopedic Injuries."""

    body_part: Optional[str] = Field(default=None, description="Orthopedic injuries to:")
    frequency: Optional[str] = Field(default=None, description="Freq.%")
    vas_score: Optional[str] = Field(default=None, description="VAS")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P8MvaInjuryTableRow(BaseModel):
    """Row data for MVA Injury Details."""

    mva_line: Optional[str] = Field(default=None, description="MVA")
    injured: Optional[str] = Field(default=None, description="Injured")
    no_facial_jaw_problems: Optional[bool] = Field(default=None, description="No facial/Jaw problems or pain")
    residual_problems: Optional[str] = Field(default=None, description="Residual Problems")
class P11EpworthSleepinessScale(BaseModel):
    """
    Epworth Sleepiness Scale (page 11, bottom section below Prior Injuries to Face/Jaw).
    Each activity scored 0-3: 0=would never doze, 1=slight, 2=moderate, 3=high chance.
    """

    p11_epworth_sitting_reading: Optional[int] = Field(default=None, description="Sitting and reading (0-3)")
    p11_epworth_watching_tv: Optional[int] = Field(default=None, description="Watching television (0-3)")
    p11_epworth_sitting_inactive: Optional[int] = Field(default=None, description="Sitting inactive in a public place (0-3)")
    p11_epworth_passenger_car: Optional[int] = Field(default=None, description="As a passenger in a car for an hour (0-3)")
    p11_epworth_lying_down_afternoon: Optional[int] = Field(default=None, description="Lying down to rest in the afternoon (0-3)")
    p11_epworth_sitting_talking: Optional[int] = Field(default=None, description="Sitting and talking to someone (0-3)")
    p11_epworth_sitting_after_lunch: Optional[int] = Field(default=None, description="Sitting quietly after lunch (0-3)")
    p11_epworth_car_traffic: Optional[int] = Field(default=None, description="In a car while stopped in traffic (0-3)")
    p11_epworth_total_score: Optional[int] = Field(default=None, description="Total Score (0-24, sum of all 8 rows)")
class P14MusclePalpationTableRow(BaseModel):
    """Row data for Tenderness: Palpable Taut Bands / Trigger Points."""

    muscle: Optional[str] = Field(default=None, description="Muscle")
    right_vas: Optional[str] = Field(default=None, description="Right VAS")
    left_vas: Optional[str] = Field(default=None, description="Left VAS")
    right_y_n: Optional[str] = Field(default=None, description="Right Y/N")
    left_y_n: Optional[str] = Field(default=None, description="Left Y/N")
    referral_pattern: Optional[str] = Field(default=None, description="Referral Pattern")
    wrp_to: Optional[str] = Field(default=None, description="WRP To")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstTableRow(BaseModel):
    """Row data for QST."""

    nerve_location: Optional[str] = Field(default=None, description="Nerve Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    seconds: Optional[int] = Field(default=None, description="Seconds")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstColdTableRow(BaseModel):
    """Row data for QST Cold."""

    nerve_location: Optional[str] = Field(default=None, description="Nerve Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstBilateralTableRow(BaseModel):
    """Row data for QST After Bilateral SPGB, if necessary."""

    nerve_location: Optional[str] = Field(default=None, description="Nerve Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    seconds: Optional[int] = Field(default=None, description="Seconds")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P1P1HeaderInfo(BaseModel):
    """
    Form Header Information
    """

    p1_if_qme_time_started: Optional[str] = Field(default=None, description="IF QME: TIME STARTED:")
    p1_if_qme_time_ended: Optional[str] = Field(default=None, description="TIME ENDED:")
    p1_nurse: Optional[str] = Field(default=None, description="Nurse:")
    p1_intp: Optional[str] = Field(default=None, description="INTP:")
    p1_cert_num: Optional[str] = Field(default=None, description="CERT #:")
class P1P1PatientDemographics(BaseModel):
    """
    Patient Demographics
    """

    p1_patient_name: str = Field(description="NAME:")
    p1_date: Optional[str] = Field(default=None, description="DATE: (Format: MM/DD/YYYY)")
    p1_primary_treating_physician: Optional[str] = Field(default=None, description="Primary Treating Physician: Dr.")
    p1_birth_date: Optional[str] = Field(default=None, description="Birth Date: (Format: MM/DD/YYYY)")
    p1_gender: Optional[str] = Field(default=None, description="Gender")  # Options: MALE, FEMALE
    p1_home_phone: Optional[str] = Field(default=None, description="Home Tel: (Format: (XXX) XXX-XXXX)")
    p1_cell_phone: Optional[str] = Field(default=None, description="Cell: (Format: (XXX) XXX-XXXX)")
    p1_email: Optional[str] = Field(default=None, description="Email:")
    p1_address: Optional[str] = Field(default=None, description="Address:")
    p1_attorney_name: Optional[str] = Field(default=None, description="Attorney's Name:")
    p1_attorney_phone: Optional[str] = Field(default=None, description="Attorney's Phone #:")
class P1P1MedicalHistory(BaseModel):
    """
    Medical History Questions
    """

    p1_heart_problems: Optional[str] = Field(default=None, description="Do you have any heart problems?")
    p1_heart_problems_types: Optional[str] = Field(default=None, description="Heart problem types")  # Options: Murmur, Mitral Valve Problem, Stent, Pacemaker, Defibrillator...
    p1_metal_joint_replacement: Optional[str] = Field(default=None, description="Do you have any metal joint replacements? (NOT DENTAL FILLINGS)")
    p1_high_blood_pressure: Optional[str] = Field(default=None, description="Do you have High Blood Pressure?")
    p1_diabetes: Optional[str] = Field(default=None, description="Do you have Diabetes?")
    p1_stomach_acids: Optional[str] = Field(default=None, description="Do you feel that stomach acids come up into your mouth or throat?")
    p1_kidney_problems: Optional[str] = Field(default=None, description="Do you have any Kidney problems?")
    p1_thyroid_problem: Optional[str] = Field(default=None, description="Do you have a Thyroid problem?")
    p1_infectious_diseases_yn: Optional[str] = Field(default=None, description="8. Do you have or have you had any of the following: HIV, Hepatitis, TB, VD?")  # Options: YES, NO
    p1_infectious_diseases: Optional[str] = Field(default=None, description="Infectious disease types (if Q8 is YES)")  # Options: HIV, Hepatitis, TB, VD
    p1_blood_thinners: Optional[str] = Field(default=None, description="9. Are you taking blood thinners?")
    p1_blood_thinners_which: Optional[str] = Field(default=None, description="Which one:")
    p1_breathing_problems: Optional[str] = Field(default=None, description="Do you have any breathing problems?")
    p1_breathing_problems_types: Optional[str] = Field(default=None, description="Breathing problem types")  # Options: Asthma, Shortness of Breath
    p1_numbness_pins_needles: Optional[str] = Field(default=None, description="Do you have any numbness or pins / needles feeling anywhere in your body?")
    p1_numbness_location: Optional[str] = Field(default=None, description="Where:")
    p1_liver_problems: Optional[str] = Field(default=None, description="Do you have any Liver problems?")
    p1_urinary_problems: Optional[str] = Field(default=None, description="Do you have any Urinary problems?")
    p1_awakens_night_urinate: Optional[str] = Field(default=None, description="14. Awakens at night to urinate?")  # Options: YES, NO
    p1_awakens_night_urinate_times: Optional[int] = Field(default=None, description="Times per night (if Q14 is YES)")
    p1_sleep_study_test: Optional[str] = Field(default=None, description="15. Have you ever had a Sleep Study Test?")
    p1_sleep_study_when: Optional[str] = Field(default=None, description="When:")
    p1_apnea_results: Optional[str] = Field(default=None, description="Apnea Results?")
    p1_cpap_mask: Optional[str] = Field(default=None, description="Have you ever been given a CPAP mask to use at night to help you breathe?")
    p1_morning_headache: Optional[str] = Field(default=None, description="Do you awaken in the morning with a headache in your temple/forehead areas?")
class P1P1Allergies(BaseModel):
    """
    History of Allergies
    """

    p1_allergies: Optional[str] = Field(default=None, description="History of Allergies:")  # Options: Penicillin, Sulfa, Erythromycin, Seasonal Allergies
class P1P1Medications(BaseModel):
    """
    Current Medications
    """

    p1_current_medications: Optional[str] = Field(default=None, description="Please circle medications you are taking?")  # Options: Pristiq, Wellbutrin, Effexor, Celexa, Cymbalta...
    p1_additional_medications_written: Optional[str] = Field(default=None, description="Additional medications written by hand near the printed list")
    p1_medications_for_conditions: Optional[str] = Field(default=None, description="Medications For:")  # Options: Diabetes, Sleep, High Blood Pressure, Pain, Anti-Inflammatory...
    p1_additional_conditions_written: Optional[str] = Field(default=None, description="Additional conditions written by hand below 'Medications For:' line")
class P2MedicationsBeforeInjury(BaseModel):
    """
    Medications Before Work Injury
    """

    p2_before_cannot_remember: Optional[bool] = Field(default=None, description="The patient cannot remember at this time")
    p2_before_none: Optional[bool] = Field(default=None, description="None")
    p2_before_pain: Optional[str] = Field(default=None, description="Pain")
    p2_before_inflammation: Optional[str] = Field(default=None, description="Inflammation")
    p2_before_stress: Optional[str] = Field(default=None, description="Stress")
    p2_before_sleep: Optional[str] = Field(default=None, description="Sleep")
    p2_before_gastric_reflux: Optional[str] = Field(default=None, description="Gastric Reflux")
    p2_before_diabetes: Optional[str] = Field(default=None, description="Diabetes")
    p2_before_high_blood_pressure: Optional[str] = Field(default=None, description="High Blood Pressure")
    p2_before_thyroid_problem: Optional[str] = Field(default=None, description="Thyroid Problem")
    p2_before_other: Optional[str] = Field(default=None, description="Other")
class P2MedicationsCurrentlyTaking(BaseModel):
    """
    Medications Currently Taking
    """

    p2_current_cannot_remember: Optional[bool] = Field(default=None, description="The patient cannot remember at this time")
    p2_current_none: Optional[bool] = Field(default=None, description="None")
    p2_current_pain: Optional[str] = Field(default=None, description="Pain")
    p2_current_inflammation: Optional[str] = Field(default=None, description="Inflammation")
    p2_current_stress: Optional[str] = Field(default=None, description="Stress")
    p2_current_sleep: Optional[str] = Field(default=None, description="Sleep")
    p2_current_gastric_reflux: Optional[str] = Field(default=None, description="Gastric Reflux")
    p2_current_diabetes: Optional[str] = Field(default=None, description="Diabetes")
    p2_current_high_blood_pressure: Optional[str] = Field(default=None, description="High Blood Pressure")
    p2_current_thyroid_problem: Optional[str] = Field(default=None, description="Thyroid Problem")
    p2_current_other: Optional[str] = Field(default=None, description="Other")
class P2MedicationsAfterInjury(BaseModel):
    """
    Medications After Work Injury
    Medications taken after the work injury (but no longer taking). How many times per Day? For how long have you taken the medication for?
    """

    p2_after_cannot_remember: Optional[bool] = Field(default=None, description="The patient cannot remember at this time")
    p2_after_none: Optional[bool] = Field(default=None, description="None")
    p2_after_pain: Optional[str] = Field(default=None, description="Pain")
    p2_after_inflammation: Optional[str] = Field(default=None, description="Inflammation")
    p2_after_stress: Optional[str] = Field(default=None, description="Stress")
    p2_after_sleep: Optional[str] = Field(default=None, description="Sleep")
    p2_after_gastric_reflux: Optional[str] = Field(default=None, description="Gastric Reflux")
    p2_after_diabetes: Optional[str] = Field(default=None, description="Diabetes")
    p2_after_high_blood_pressure: Optional[str] = Field(default=None, description="High Blood Pressure")
    p2_after_thyroid_problem: Optional[str] = Field(default=None, description="Thyroid Problem")
    p2_after_other: Optional[str] = Field(default=None, description="Other")
    p2_patient_call_office: Optional[str] = Field(default=None, description="Patient to call the office with the names of the medications they take")
class P3MouthSymptoms(BaseModel):
    """
    Mouth Symptoms (page 3 of the form, top section).
    Each question: YES/NO on the left, 'Sometimes' on the right. Patient circles one.
    """

    p3_dry_mouth: Optional[str] = Field(default=None, description="Do you feel that you have dry mouth?")  # Options: YES, NO, Sometimes
    p3_hoarseness: Optional[str] = Field(default=None, description="Do you have hoarseness?")  # Options: YES, NO, Sometimes
    p3_saliva_too_little: Optional[str] = Field(default=None, description="Does the amount of saliva in your mouth seem to be too little?")  # Options: YES, NO, Sometimes
    p3_difficulty_swallowing: Optional[str] = Field(default=None, description="Do you have any difficulties swallowing?")  # Options: YES, NO, Sometimes
    p3_mouth_dry_eating: Optional[str] = Field(default=None, description="Does your mouth feel dry when eating a meal?")  # Options: YES, NO, Sometimes
    p3_sip_liquids_aid: Optional[str] = Field(default=None, description="Do you sip liquids to aid in swallowing dry food?")  # Options: YES, NO, Sometimes
class P3BadBreath(BaseModel):
    """
    Bad Breath Assessment
    """

    p3_bad_breath_before: Optional[str] = Field(default=None, description="Do you have bad breath? (Before the Injury)")  # Options: YES, NO
    p3_bad_breath_after: Optional[str] = Field(default=None, description="Do you have bad breath? (After the Injury)")  # Options: YES, NO
    p3_bad_breath_percentage_before: Optional[int] = Field(default=None, description="What percentage of time do you have bad breath? (Before) (Format: 0 to 100%)")
    p3_bad_breath_percentage_after: Optional[int] = Field(default=None, description="What percentage of time do you have bad breath? (After) (Format: 0 to 100%)")
    p3_breath_intensity_before: Optional[int] = Field(default=None, description="How intense is your bad breath? (Before)")
    p3_breath_intensity_after: Optional[int] = Field(default=None, description="How intense is your bad breath? (After)")
    p3_people_tell_before: Optional[int] = Field(default=None, description="How often do people tell you that you have bad breath? (Before)")
    p3_people_tell_after: Optional[int] = Field(default=None, description="How often do people tell you that you have bad breath? (After)")
    p3_interfere_others_before: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to interact with other people? (Before)")
    p3_interfere_others_after: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to interact with other people? (After)")
    p3_interfere_family_before: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to interact with your family? (Before)")
    p3_interfere_family_after: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to interact with your family? (After)")
    p3_intimate_kissing_before: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to have intimate kissing with your significant other? (Before)")
    p3_intimate_kissing_after: Optional[int] = Field(default=None, description="Does your bad breath interfere with your ability to have intimate kissing with your significant other? (After)")
    p3_embarrassment_before: Optional[int] = Field(default=None, description="Does your bad breath cause you embarrassment? (Before)")
    p3_embarrassment_after: Optional[int] = Field(default=None, description="Does your bad breath cause you embarrassment? (After)")
    p3_stress_before: Optional[int] = Field(default=None, description="Does your bad breath cause you stress? (Before)")
    p3_stress_after: Optional[int] = Field(default=None, description="Does your bad breath cause you stress? (After)")
class P3HalitosisMeter(BaseModel):
    """
    Halitosis Meter Reading
    """

    p3_halitosis_reading: Optional[str] = Field(default=None, description="Halitosis Meter Reading")  # Options: 1 = No Odor, 2 = Slight Odor, 3 = Moderate Odor, 4 = Strong Odor, 5 = Intense Odor
class P3TasteChanges(BaseModel):
    """
    Taste Changes
    """

    p3_taste_feels_bland: Optional[str] = Field(default=None, description="Since your work injury have you noticed that your taste feels bland?")  # Options: Yes, No
    p3_taste_perception_change: Optional[str] = Field(default=None, description="Has there been a change in your perception of taste of sweet, salty, or sour foods?")  # Options: Yes, No
    p3_taste_change_amount: Optional[int] = Field(default=None, description="If yes, From 0 to 10 how much do you feel your taste has changed?")
    p3_taste_covid_related: Optional[str] = Field(default=None, description="Was your change in taste caused by Covid-19")  # Options: Yes, No
    p3_doctor_covid_diagnosis: Optional[str] = Field(default=None, description="If yes, has a doctor determined that you caught Covid at work?")  # Options: Yes, No
    p3_gerd_work_related: Optional[str] = Field(default=None, description="Has a doctor determined that your GERD is work related?")  # Options: Yes, No
class P3SignatureSection(BaseModel):
    """
    Signature
    """

    p3_patient_signature: str = Field(description="Patient's Signature")
    p3_signature_date: str = Field(description="Date (Format: MM/DD/YYYY)")
class P4P4HandDominance(BaseModel):
    """
    Hand Dominance
    """

    p4_hand_dominance: Optional[str] = Field(default=None, description="Hand Dominance")  # Options: Right, Left
class P4P4WorkInjury(BaseModel):
    """
    Work Injury
    In your work injury, did you injure your:
    """

    p4_right_body_parts_injured: list[str] = Field(default=None, description="Right body parts injured")  # Options: Shoulder, Arm, Elbow, Wrist, Hand...
    p4_left_body_parts_injured: list[str] = Field(default=None, description="Left body parts injured")  # Options: Shoulder, Arm, Elbow, Wrist, Hand...
class P4P4DailyActivities(BaseModel):
    """
    Daily Activities
    """

    p4_difficulty_grip_toothbrush: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to adequately grip a toothbrush and brush your teeth?")
    p4_difficulty_floss_teeth: Optional[str] = Field(default=None, description="Do you have any difficulty using hands/fingers to adequately floss your teeth?")
    p4_shoulder_pain_brushing_flossing: Optional[str] = Field(default=None, description="Does shoulder pain cause you any difficulty brushing and/or flossing your teeth?")
    p4_difficulty_toothpaste_cap: Optional[str] = Field(default=None, description="Do you have any difficulty holding a toothpaste tube with one hand and using the other hand to open the toothpaste cap?")
    p4_difficulty_squeeze_toothpaste: Optional[str] = Field(default=None, description="Do you have any difficulty squeezing toothpaste with one hand and holding the toothbrush with the other hand?")
    p4_difficulty_cut_food: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to cut your food?")
    p4_difficulty_feed_yourself: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to feed yourself?")
    p4_difficulty_raise_arm_comb: Optional[str] = Field(default=None, description="Do you have any difficulty raising up your arm to comb or brush your hair?")
class P4P4SmokingHistory(BaseModel):
    """
    Smoking History
    """

    p4_do_you_smoke: Optional[str] = Field(default=None, description="Do you Smoke?")
    p4_have_you_ever_smoked: Optional[str] = Field(default=None, description="Have you ever smoked?")
    p4_when_stop_smoking_months: Optional[int] = Field(default=None, description="When did you stop smoking (months ago)")
    p4_when_stop_smoking_years: Optional[int] = Field(default=None, description="When did you stop smoking (years ago)")
    p4_cigarettes_per_day: Optional[int] = Field(default=None, description="How much do you smoke? (cigarettes/day)")
    p4_years_smoker: Optional[int] = Field(default=None, description="How many years were you a smoker?")
    p4_smoking_increase_after_injury: Optional[str] = Field(default=None, description="Did your smoking usage increase after the industrial injury?")
    p4_cigarettes_per_day_if_yes: Optional[int] = Field(default=None, description="If yes, cigarettes per day")
class P4P4SubstanceUse(BaseModel):
    """
    Substance Use
    """

    p4_drink_alcohol: Optional[str] = Field(default=None, description="Do You Drink Alcohol?")
    p4_alcohol_how_much: Optional[str] = Field(default=None, description="If yes, How much?")
    p4_use_recreational_drugs: Optional[str] = Field(default=None, description="Do you use recreational drugs?")
    p4_recreational_drugs_describe: Optional[str] = Field(default=None, description="If yes, describe")
    p4_used_amphetamines: Optional[str] = Field(default=None, description="Have you used amphetamines?")
    p4_amphetamines_when: Optional[str] = Field(default=None, description="If yes, When?")
class P5HeaderInfo(BaseModel):
    """
    Header Information
    """

    p5_name: Optional[str] = Field(default=None, description="Name:")
    p5_gender: Optional[str] = Field(default=None, description="M___F___")  # Options: M, F
    p5_date: Optional[date] = Field(default=None, description="Date: (Format: ____/____/202___)")
    p5_interpreter: Optional[str] = Field(default=None, description="Interpreter:")
    p5_date_of_injury: Optional[date] = Field(default=None, description="Date of Injury:")
    p5_ptp_dr: Optional[str] = Field(default=None, description="PTP: DR_")
class P5EmploymentHistory(BaseModel):
    """
    Employment History
    """

    p5_employed_at: Optional[str] = Field(default=None, description="Employed at:")
    p5_employment_duration_years: Optional[int] = Field(default=None, description="for ___ years")
    p5_employment_duration_months: Optional[int] = Field(default=None, description="months")
    p5_job_title: Optional[str] = Field(default=None, description="Job Title:")
    p5_worked_days_per_week: Optional[int] = Field(default=None, description="Worked ___Days per week;")
    p5_worked_hours_per_day: Optional[int] = Field(default=None, description="Worked ___Hours per day")
    p5_hand_dominance: Optional[str] = Field(default=None, description="Right Left Hand Dominant")  # Options: Right, Left
    p5_job_duties: Optional[str] = Field(default=None, description="What did patient do at the job?")
    p5_job_requirements_initial: list[str] = Field(default=None, description="Job Requirements:")  # Options: driving, walking, standing, sitting, squatting...
    p5_lifting_maximum_lbs: Optional[int] = Field(default=None, description="lifting up to maximum of ___lbs.")
    p5_carrying_maximum_lbs: Optional[int] = Field(default=None, description="carrying up to maximum ___lbs.")
    p5_computer_mouse_hand: Optional[str] = Field(default=None, description="using a computer mouse: R L")  # Options: R, L
    p5_workstation_type: list[str] = Field(default=None, description="non-ergonomic: desk chair work station")  # Options: desk, chair, work station
    p5_monitor_location: Optional[str] = Field(default=None, description="computer monitor located in: F R L")  # Options: F, R, L
    p5_phone_cradle_hand: Optional[str] = Field(default=None, description="cradling the phone on: R L")  # Options: R, L
    p5_current_work_status: Optional[str] = Field(default=None, description="Current Work Status:")  # Options: Disabled, Still working at the same company, Not Working/Retired
    p5_date_stopped_working: Optional[date] = Field(default=None, description="Date Stopped working")
    p5_presently_working_company: Optional[str] = Field(default=None, description="Presently working at different company")
    p5_presently_working_as: Optional[str] = Field(default=None, description="as")
    p5_current_job_duties: Optional[str] = Field(default=None, description="Job duties:")
class P6P6TraumaHistory(BaseModel):
    """
    Trauma History Review
    """

    p6_trauma_history_dr_name: Optional[str] = Field(default=None, description="Reviewed History of Trauma with patient as per the report of Dr.")
    p6_trauma_history_date: Optional[str] = Field(default=None, description="Date (Format: ___/___/202___)")
    p6_patient_signature: Optional[str] = Field(default=None, description="Patient's Signature")
    p6_patient_signature_date: Optional[str] = Field(default=None, description="Date (Format: _____/_______/202____)")
class P6P6IndustrialInjury(BaseModel):
    """
    History of Industrial Injury
    """

    p6_patient_poor_historian: Optional[str] = Field(default=None, description="Patient is a Poor Historian (Yes/No)")  # Options: Yes, No
    p6_injury_description_1: Optional[str] = Field(default=None, description="Injury Description 1")
    p6_injury_description_2: Optional[str] = Field(default=None, description="Injury Description 2")
    p6_injury_description_3: Optional[str] = Field(default=None, description="Injury Description 3")
    p6_orthopedic_injuries: list[P6OrthopedicInjuriesRow] = Field(default_factory=list, description="Orthopedic Injuries")
class P6P6MvaDetails(BaseModel):
    """
    Motor Vehicle Accident Details
    """

    p6_mva_role: list = Field(default=None, description="If MVA - Role in Vehicle")  # Options: Driver, Passenger, Right Rear Seat, Left Rear Seat
    p6_vehicle_hit_on: list = Field(default=None, description="Vehicle Hit On")  # Options: R, L, Front, Rear
    p6_wearing_seatbelt: Optional[str] = Field(default=None, description="Wearing a seatbelt?")  # Options: Yes, No
    p6_airbag_deployed: Optional[str] = Field(default=None, description="Airbag Deployed?")  # Options: Yes, No
    p6_thrown_about: Optional[str] = Field(default=None, description="Thrown About?")  # Options: Yes, No
    p6_struck_mouth_face: list = Field(default=None, description="Struck Mouth Face?")  # Options: Steering Wheel, Door, Window
    p6_struck_back_of_head: Optional[str] = Field(default=None, description="Struck back of head on headrest?")  # Options: Yes, No
    p6_direct_trauma_face_jaw: list = Field(default=None, description="Direct Trauma to the Face/Jaw?")  # Options: R, L
    p6_scars: Optional[str] = Field(default=None, description="Scars")
    p6_fractured_jaw: Optional[str] = Field(default=None, description="Fractured Jaw?")  # Options: Yes, No
    p6_fractured_teeth_count: Optional[str] = Field(default=None, description="Fractured Teeth #")
    p6_lost_teeth_count: Optional[str] = Field(default=None, description="Lost Teeth #")
class P7P7PainStressSection(BaseModel):
    """
    Pain and Stress Related Questions
    """

    p7_orthopedic_pain_clenching: Optional[bool] = Field(default=None, description="Orthopedic pain causing clenching/bracing of facial muscles")
    p7_developed_stressors_injury: Optional[bool] = Field(default=None, description="Developed stressors in response to industrial orthopedic injuries")
    p7_stressors_work: list[str] = Field(default=None, description="Stressors at Work")  # Options: Heavy workload, Long or inflexible hours, Tight deadlines, Lack of control, Conflicting or uncertain job expectations...
    p7_clenching_bracing_stress: Optional[str] = Field(default=None, description="Clenching/Bracing of facial muscles in response to stress")  # Options: Yes, No
    p7_clenching_bracing_notes: Optional[str] = Field(default=None, description="Handwritten notes next to the clenching/bracing stress question")
    p7_bruxism_after_work_pain: Optional[str] = Field(default=None, description="Did the bruxism begin after the you started having work related pain/stress?")  # Options: Yes, No
    p7_bruxism_days_after: Optional[int] = Field(default=None, description="Days after")
    p7_bruxism_weeks_after: Optional[int] = Field(default=None, description="Weeks after")
    p7_clenching_day: Optional[bool] = Field(default=None, description="Clenching - Day")
    p7_clenching_night: Optional[bool] = Field(default=None, description="Clenching - Night")
    p7_grinding_day: Optional[bool] = Field(default=None, description="Grinding - Day")
    p7_grinding_night: Optional[bool] = Field(default=None, description="Grinding - Night")
    p7_bracing_facial_day: Optional[bool] = Field(default=None, description="Bracing Facial Musculature - Day")
    p7_bracing_facial_night: Optional[bool] = Field(default=None, description="Bracing Facial Musculature - Night")
    p7_bruxism_percent_time: Optional[float] = Field(default=None, description="Bruxism: % of Time")
    p7_bruxism_vas_intensity: Optional[float] = Field(default=None, description="VAS Intensity", ge=0, le=10)
class P7P7PreexistingConditions(BaseModel):
    """
    Pre-Existing Conditions
    """

    p7_headaches_percent_time: Optional[float] = Field(default=None, description="Headaches % of time")
    p7_headaches_intensity_vas: Optional[float] = Field(default=None, description="intensity of Headache on VAS", ge=0, le=10)
    p7_vertex_location: list[str] = Field(default=None, description="Vertex - Location of headache")  # Options: R, L, Forehead, Temple, Occiput...
    p7_migraine_diagnosis: Optional[bool] = Field(default=None, description="Have you ever been diagnosed with migraines?")
    p7_migraine_details: Optional[str] = Field(default=None, description="if yes, migraine details")
    p7_facial_pain_location: list[str] = Field(default=None, description="Facial Pain location")  # Options: R, L, B
    p7_facial_pain_percent_time: Optional[float] = Field(default=None, description="Facial Pain % of time")
    p7_facial_pain_intensity_vas: Optional[float] = Field(default=None, description="intensity of Facial Pain on VAS", ge=0, le=10)
    p7_tmj_pain_location: list[str] = Field(default=None, description="TMJ Pain location")  # Options: R, L, B
    p7_tmj_pain_percent_time: Optional[float] = Field(default=None, description="TMJ Pain % of time")
    p7_tmj_pain_intensity_vas: Optional[float] = Field(default=None, description="intensity of TMJ Pain on VAS", ge=0, le=10)
    p7_preexisting_bruxism_percent_time: Optional[float] = Field(default=None, description="Bruxism: % of time")
    p7_preexisting_bruxism_intensity_vas: Optional[float] = Field(default=None, description="intensity of Bruxism on VAS", ge=0, le=10)
    p7_nightguard_made: Optional[str] = Field(default=None, description="If a nightguard was made (year made)")
    p7_nightguard_still_uses: Optional[bool] = Field(default=None, description="Still uses a nightguard?")
    p7_nightguard_stop_reason: Optional[str] = Field(default=None, description="Reason stopped using nightguard?")  # Options: Does not fit, Lost, Wore Out, Broken
    p7_eating_hard_chewy_food: Optional[bool] = Field(default=None, description="Did you have any prior problems eating hard or chewy food?")
    p7_speaking_prolonged_periods: Optional[bool] = Field(default=None, description="Did you have any prior problems speaking for prolonged periods of time?")
class P7P7AttestationSignature(BaseModel):
    """
    Attestation and Signature
    """

    p7_patient_signature: str = Field(description="Patient's Signature")
    p7_signature_date: date = Field(description="Date (Format: MM/DD/YYYY)")
class P7P7TreatmentsReceived(BaseModel):
    """
    Treatments Received Due to the Industrial Injury
    """

    p7_surgery_body_parts: list[str] = Field(default=None, description="Surgery to body parts")  # Options: Neck, R Shoulder, L Shoulder, R Arm, L Arm...
    p7_surgery_year: Optional[str] = Field(default=None, description="Year(s) of surgery, handwritten above the body parts")
    p7_surgery_how_many_times: Optional[str] = Field(default=None, description="How many times surgery was performed")
class P8TxReceived(BaseModel):
    """
    Tx Received — treatments circled from the printed list, plus specialist evaluations.
    """

    p8_tx_received: list[str] = Field(default_factory=list, description="Treatments circled: Physical Therapy, Chiropractic Manipulations, Acupuncture, Injections, Steroid, Spinal, Trigger Point")
    p8_psychological_therapy_evaluated_by: Optional[str] = Field(default=None, description="Psychological Therapy: Evaluated by (may overflow multiple lines)")
    p8_neurologist_evaluated_by: Optional[str] = Field(default=None, description="Neurologist: Evaluated by (may overflow multiple lines)")
class P8PriorHistory(BaseModel):
    """
    Prior History
    """

    p8_past_medical_history: Optional[str] = Field(default=None, description="Past Medical History")
    p8_past_surgeries: Optional[str] = Field(default=None, description="Past Surgeries")
    p8_history_prior_industrial_injuries: Optional[str] = Field(default=None, description="History of Prior Industrial Injuries")
    p8_history_non_industrial_injuries: Optional[str] = Field(default=None, description="History of Non-Industrial Injuries")
    p8_mva_rows: Optional[str] = Field(default=None, description="MVA rows — motor vehicle accident fill-in rows below non-industrial injuries")
class P9P9DentalHistory(BaseModel):
    """
    Dental History
    """

    p9_last_dentist_visit: Optional[str] = Field(default=None, description="When was the last time you were seen by a dentist, besides in our office?")  # Options: Years ago, Months ago, Weeks ago, Other, Never
    p9_last_xray: Optional[str] = Field(default=None, description="When was the last time you had Full Mouth X-Ray taken?")
    p9_prior_dentist_info: Optional[str] = Field(default=None, description="To the best of your ability, please list the name(s), addresses and phone numbers of your prior dentist(s):")
class P9P9DentalTreatments(BaseModel):
    """
    Dental Treatments
    """

    p9_checkup_frequency: Optional[str] = Field(default=None, description="Every: 6 months ________ year - Fill in frequency - year option")
    p9_last_teeth_cleaned: Optional[str] = Field(default=None, description="Last time patient had teeth cleaned")
    p9_dentist_1_name: Optional[str] = Field(default=None, description="Name of Dentist:")
    p9_dentist_1_phone: Optional[str] = Field(default=None, description="Phone #:")
    p9_dentist_1_address: Optional[str] = Field(default=None, description="Dentist's Address:")
    p9_dentist_2_name: Optional[str] = Field(default=None, description="Name of Dentist:")
    p9_dentist_2_phone: Optional[str] = Field(default=None, description="Phone #:")
    p9_dentist_2_address: Optional[str] = Field(default=None, description="Dentist's Address:")
class P9P9TreatmentsSinceInjury(BaseModel):
    """
    Dental Treatments Received Since Industrial Injuries
    """

    p9_injury_dentist_name: Optional[str] = Field(default=None, description="If yes, Name of Dentist:")
    p9_injury_dentist_phone: Optional[str] = Field(default=None, description="Phone #:")
    p9_gum_treatments: Optional[bool] = Field(default=None, description="Gum Treatments")
    p9_restorations_location: list[str] = Field(default=None, description="Restorations on teeth in")  # Options: UR, UL, LR, LL
    p9_root_canals_location: list[str] = Field(default=None, description="Root Canals in")  # Options: UR, UL, LR, LL
    p9_crowns_location: list[str] = Field(default=None, description="Crowns in")  # Options: UR, UL, LR, LL
    p9_implants_location: list[str] = Field(default=None, description="Implants in")  # Options: UR, UL, LR, LL
    p9_partial_denture_location: list[str] = Field(default=None, description="Partial Denture")  # Options: Upper, Lower
    p9_complete_denture_location: list[str] = Field(default=None, description="Complete Denture")  # Options: Upper, Lower
    p9_oral_appliance_type: list[str] = Field(default=None, description="Oral Appliance type")  # Options: Upper, Lower, Bruxism Oral Appliance, Oral Sleep Appliance
    p9_extractions_wisdom: Optional[bool] = Field(default=None, description="Extractions: Wisdom teeth")
    p9_extractions_teeth_numbers: Optional[str] = Field(default=None, description="Teeth #")
    p9_missing_teeth_count: Optional[int] = Field(default=None, description="Missing Teeth?")
    p9_missing_prior_injury: Optional[int] = Field(default=None, description="Prior to the industrial injury?#")
    p9_missing_after_injury: Optional[int] = Field(default=None, description="After the Injury?#")
class P10P10PresentSymptoms(BaseModel):
    """
    Present Symptoms
    """

    p10_weight_loss_lbs: Optional[float] = Field(default=None, description="Weight Loss lbs")
    p10_loss_due_to: Optional[str] = Field(default=None, description="Loss due to")
    p10_facial_pain_diet: Optional[str] = Field(default=None, description="Facial Pain Diet")
    p10_present_weight_kg: Optional[float] = Field(default=None, description="Present Weight Kg")
    p10_height_cm: Optional[int] = Field(default=None, description="Height cm")
    p10_frame_size: Optional[str] = Field(default=None, description="Frame")  # Options: Small, Medium, Large
    p10_snores: Optional[str] = Field(default=None, description="Snores")
    p10_snores_condition: Optional[str] = Field(default=None, description="Snores condition")  # Options: Pre-existing, Aggravated, After Work Injury
    p10_gasps_for_air: Optional[str] = Field(default=None, description="Gasps for Air at Night")
    p10_gasps_condition: Optional[str] = Field(default=None, description="Gasps condition")  # Options: Pre-existing, Aggravated, After Work Injury
    p10_palpitations: Optional[str] = Field(default=None, description="Palpitations on Awakening")
    p10_palpitations_condition: Optional[str] = Field(default=None, description="Palpitations condition")  # Options: Pre-existing, Aggravated, After Work Injury
    p10_breathing_cessation: Optional[str] = Field(default=None, description="Breathing Cessation at Night")
    p10_breathing_condition: Optional[str] = Field(default=None, description="Breathing cessation condition")  # Options: Pre-existing, Aggravated, After Work Injury
    p10_sleep_study: Optional[str] = Field(default=None, description="Patient had Sleep Study")
    p10_sleep_study_date: Optional[date] = Field(default=None, description="Date of sleep study")
    p10_sleep_disorder_diagnosed: Optional[str] = Field(default=None, description="Patient diagnosed with a Sleep Disorder")
    p10_patient_knows_results: Optional[str] = Field(default=None, description="Patient does not know results")
    p10_given_mask: Optional[str] = Field(default=None, description="Given mask during Sleep Study")
    p10_used_cpap: Optional[str] = Field(default=None, description="Used CPAP during Sleep Study")
    p10_given_cpap: Optional[str] = Field(default=None, description="Patient given CPAP")
    p10_cpap_times_per_week: Optional[int] = Field(default=None, description="Patient uses CPAP times per week")
    p10_cpap_hours_per_night: Optional[float] = Field(default=None, description="CPAP hours per night")
    p10_cannot_tolerate_cpap: Optional[str] = Field(default=None, description="Patient cannot tolerate CPAP")
class P10P10Headaches(BaseModel):
    """
    Headaches
    """

    p10_headache_locations: list[str] = Field(default=None, description="Headache Locations")  # Options: On Top of Head, Temple R, Temple L, Forehead R, Forehead L...
    p10_headache_frequency: Optional[str] = Field(default=None, description="Headache Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_headache_quality: list[str] = Field(default=None, description="Headache Quality")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_headache_severity: Optional[str] = Field(default=None, description="Headache Severity")  # Options: Minimal, Slight, Moderate, Severe
    p10_headache_percent_time: Optional[int] = Field(default=None, description="Headache % of Time")
    p10_headache_vas: Optional[int] = Field(default=None, description="Headache VAS", ge=0, le=10)
    p10_headache_started_approx: Optional[str] = Field(default=None, description="Headaches Started Approx")
    p10_bruxism_caused_headaches: Optional[str] = Field(default=None, description="Do you think your bruxism may have caused you to have headaches?")
class P10P10FacePain(BaseModel):
    """
    Face Pain
    """

    p10_right_face_pain_frequency: Optional[str] = Field(default=None, description="Right Face Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_right_face_pain_quality: list[str] = Field(default=None, description="Right Face Pain Quality")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_right_face_pain_severity: Optional[str] = Field(default=None, description="Right Face Pain Severity")  # Options: Minimal, Slight, Moderate, Severe
    p10_right_face_pain_percent_time: Optional[int] = Field(default=None, description="Right Face Pain % of Time")
    p10_right_face_pain_vas: Optional[int] = Field(default=None, description="Right Face Pain VAS", ge=0, le=10)
    p10_left_face_pain_frequency: Optional[str] = Field(default=None, description="Left Face Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_left_face_pain_quality: list[str] = Field(default=None, description="Left Face Pain Quality")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_left_face_pain_severity: Optional[str] = Field(default=None, description="Left Face Pain Severity")  # Options: Minimal, Slight, Moderate, Severe
    p10_left_face_pain_percent_time: Optional[int] = Field(default=None, description="Left Face Pain % of Time")
    p10_left_face_pain_vas: Optional[int] = Field(default=None, description="Left Face Pain VAS", ge=0, le=10)
    p10_left_face_pain_started_approx: Optional[str] = Field(default=None, description="Left Face Pain Started Approx")
    p10_bruxism_caused_face_pain: Optional[str] = Field(default=None, description="Do you think your bruxism may have caused you to have face pain?")
class P10P10TmjNoisePain(BaseModel):
    """
    TMJ Noise and Pain
    """

    p10_noises_in_tmj: list[str] = Field(default=None, description="Noises in TMJ")  # Options: R, L, Grinding, Clicking
    p10_tmj_noise_started_approx: Optional[str] = Field(default=None, description="TMJ Noise Started Approx")
    p10_pre_injury_tmj_noise_vas: Optional[int] = Field(default=None, description="Pre-Injury TMJ Noise VAS", ge=0, le=10)
    p10_post_injury_tmj_noise_vas: Optional[int] = Field(default=None, description="Post Injury TMJ Noise VAS", ge=0, le=10)
    p10_right_tmj_pain_frequency: Optional[str] = Field(default=None, description="Right TMJ Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_right_tmj_pain_quality: list[str] = Field(default=None, description="Right TMJ Pain Quality")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_right_tmj_pain_severity: Optional[str] = Field(default=None, description="Right TMJ Pain Severity")  # Options: Minimal, Slight, Moderate, Severe
    p10_right_tmj_pain_percent_time: Optional[int] = Field(default=None, description="Right TMJ Pain % of Time")
    p10_right_tmj_pain_vas: Optional[int] = Field(default=None, description="Right TMJ Pain VAS", ge=0, le=10)
    p10_left_tmj_pain_frequency: Optional[str] = Field(default=None, description="Left TMJ Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_left_tmj_pain_quality: list[str] = Field(default=None, description="Left TMJ Pain Quality")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_left_tmj_pain_severity: Optional[str] = Field(default=None, description="Left TMJ Pain Severity")  # Options: Minimal, Slight, Moderate, Severe
    p10_left_tmj_pain_percent_time: Optional[int] = Field(default=None, description="Left TMJ Pain % of Time")
    p10_left_tmj_pain_vas: Optional[int] = Field(default=None, description="Left TMJ Pain VAS", ge=0, le=10)
    p10_left_tmj_pain_started_approx: Optional[str] = Field(default=None, description="Left TMJ Pain Started Approx")
class P11P11JawMouthSymptoms(BaseModel):
    """
    Jaw and Mouth Symptoms
    """

    p11_limited_opening_mouth: Optional[str] = Field(default=None, description="Limited Opening of the Mouth")
    p11_locking_frequency: Optional[str] = Field(default=None, description="Locking")  # Options: Yes, No, Closed, Open
    p11_locking_closed_times_per: Optional[int] = Field(default=None, description="Closed X per")
    p11_locking_closed_frequency: Optional[str] = Field(default=None, description="Closed frequency unit")  # Options: day, wk, month
    p11_locking_open_times_per: Optional[int] = Field(default=None, description="Open X per")
    p11_locking_open_frequency: Optional[str] = Field(default=None, description="Open frequency unit")  # Options: day, wk, month
    p11_first_locked: Optional[str] = Field(default=None, description="First locked")
    p11_can_self_manipulate_jaw: Optional[str] = Field(default=None, description="Can self-manipulate Jaw to unlock?")
    p11_difficult_painful_chew: Optional[str] = Field(default=None, description="Difficult and painful to chew hard food:")  # Options: Face, TMJ, Teeth, R, L
    p11_bite_feels_off: Optional[str] = Field(default=None, description="Bite feels off")
    p11_facial_pain: Optional[str] = Field(default=None, description="Facial Pain")  # Options: Smiling, Yawning
class P11P11OralSymptoms(BaseModel):
    """
    Oral Symptoms
    """

    p11_soreness_teeth_waking: Optional[str] = Field(default=None, description="Soreness of teeth upon waking up in the morning?")
    p11_soreness_face_jaw_awakening: Optional[str] = Field(default=None, description="Soreness in Face/Jaw Upon Awakening?")  # Options: Yes, No, R, L
    p11_teeth_sensitive_hot_cold: Optional[str] = Field(default=None, description="Teeth are sensitive to hot and cold?")
    p11_bleeding_gums: Optional[str] = Field(default=None, description="Bleeding Gums?")
    p11_speech_dysfunction: Optional[str] = Field(default=None, description="Speech Dysfunction")  # Options: Indistinct Articulation, Hoarseness, Cotton Mouth, Missing Upper Anterior Teeth, Cannot Talk for Long Periods of Time Due to Pain...
    p11_speak_max_time_minutes: Optional[int] = Field(default=None, description="Can Speak Max. Time Minutes")
    p11_voice_changes: Optional[str] = Field(default=None, description="Voice Changes In:")  # Options: Tone, Pitch, Slurring, Drooling, People Asking Patient To Repeat Themselves
class P11P11AdditionalSymptoms(BaseModel):
    """
    Additional Symptoms
    """

    p11_ear_problems: Optional[str] = Field(default=None, description="Ear Problems")  # Options: R, L, Both, Ringing, Pain...
    p11_sleep_disturbances: Optional[str] = Field(default=None, description="Sleep Disturbances")
    p11_fatigue: Optional[str] = Field(default=None, description="Fatigue")
    p11_generalized_tenderness: Optional[str] = Field(default=None, description="Generalized tenderness all over the body?")
    p11_stress_increases_pain: Optional[str] = Field(default=None, description="Stress Increases Pain?")
    p11_prior_injuries_face_jaw: Optional[str] = Field(default=None, description="Prior Injuries to Face / Jaw")
class P12P12FacialPainActivities(BaseModel):
    """
    Activities of Daily Living VAS
    """

    p12_eating_hard_chewy_food_pain: Optional[str] = Field(default=None, description="If your facial pain is aggravated by eating hard or chewy food, what is your pain level?")  # Options: YES, NO
    p12_eating_hard_chewy_food_vas: Optional[int] = Field(default=None, description="VAS score for eating hard or chewy food pain", ge=0, le=10)
    p12_prolonged_speaking_pain: Optional[str] = Field(default=None, description="If your face pain is aggravated by prolonged speaking, what is your pain level?")  # Options: YES, NO
    p12_prolonged_speaking_vas: Optional[int] = Field(default=None, description="VAS score for prolonged speaking pain", ge=0, le=10)
    p12_max_speak_time: Optional[int] = Field(default=None, description="Maximum time able to speak continuously - Time in minutes")
    p12_repeat_not_understood: Optional[str] = Field(default=None, description="People ask you to repeat yourself because they do not understand you?")  # Options: YES, NO
    p12_repeat_not_understood_vas: Optional[int] = Field(default=None, description="VAS score for repeat not understood", ge=0, le=10)
    p12_intense_kissing_pain: Optional[str] = Field(default=None, description="Is your facial pain aggravated by intense kissing?")  # Options: YES, NO
    p12_intense_kissing_vas: Optional[int] = Field(default=None, description="VAS score for intense kissing pain", ge=0, le=10)
    p12_sleep_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to get enough sleep?")  # Options: YES, NO
    p12_sleep_interference_vas: Optional[int] = Field(default=None, description="VAS score for sleep interference", ge=0, le=10)
    p12_sleeping_pressure_pain: Optional[str] = Field(default=None, description="Does the pressure on your face while you are sleeping result in face or jaw pain?")  # Options: YES, NO
    p12_social_activities_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to participate in social activities?")  # Options: YES, NO
    p12_social_activities_vas: Optional[int] = Field(default=None, description="VAS score for social activities interference", ge=0, le=10)
    p12_relationship_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere in your relationship with your family members or significant other?")  # Options: YES, NO
    p12_relationship_vas: Optional[int] = Field(default=None, description="VAS score for relationship interference", ge=0, le=10)
    p12_concentration_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to concentrate?")  # Options: YES, NO
    p12_concentration_vas: Optional[int] = Field(default=None, description="VAS score for concentration interference", ge=0, le=10)
    p12_irritable_angry: Optional[str] = Field(default=None, description="Does your facial pain cause you to be irritable/angry?")  # Options: YES, NO
    p12_irritable_angry_vas: Optional[int] = Field(default=None, description="VAS score for irritable/angry", ge=0, le=10)
    p12_experience_stress: Optional[str] = Field(default=None, description="Does your facial pain cause you to experience stress?")  # Options: YES, NO
    p12_experience_stress_vas: Optional[int] = Field(default=None, description="VAS score for experience stress", ge=0, le=10)
class P12P12CommunicationTalking(BaseModel):
    """
    Communication / Talking
    """

    p12_talking_ability: Optional[str] = Field(default=None, description="Communication / Talking ability level")  # Options: You can talk as much as you want without facial pain, jaw tiredness or discomfort, You can talk as much as you want, but talking causes some facial pain, jaw tiredness or discomfort, You can not talk as much as you want because of facial pain, jaw tiredness or discomfort, You can not talk much at all because of your facial pain, jaw tiredness or discomfort, Your facial pain prevents you from talking at all except for answering yes or no or only some words at a time
class P12P12EatingChewing(BaseModel):
    """
    Eating / Chewing
    """

    p12_eating_ability: Optional[str] = Field(default=None, description="Eating / Chewing ability level")  # Options: You can eat and chew anything you want without facial pain, discomfort or jaw tiredness, You can eat and chew most anything you want, but it sometimes causes facial pain, discomfort or jaw tiredness, You cannot eat hard or chewy foods, because it often causes facial pain, discomfort or jaw tiredness, You must eat only soft foods (consistency of scrambled eggs or less) because of your facial pain, discomfort or jaw tiredness, You must stay on a liquid diet because of your facial pain
    p12_hard_foods_restriction: Optional[str] = Field(default=None, description="Hard Foods: You must stay away from eating hard foods which includes: - Tough meats, hard bread, nuts, apples, carrots, crunchy vegetables, hard candy")  # Options: YES, NO
    p12_chewy_foods_restriction: Optional[str] = Field(default=None, description="Chewy Foods: You must stay away eating chewy foods which includes: - Chewing gum, steak, pizza crusts, and bagels; candies like: taffy, caramel, licorice, gummy bears")  # Options: YES, NO
    p12_soft_foods_only: Optional[str] = Field(default=None, description="Soft Foods: You can only eat soft or liquid type foods with the consistency of scrambled eggs or less")  # Options: YES, NO
class P12P12AttestationSignature(BaseModel):
    """
    Attestation and Signature
    """

    p12_patient_signature: str = Field(description="Patient's Signature")
    p12_signature_date: date = Field(description="Date (Format: MM/DD/YYYY)")
class P13P13SelfCareHygiene(BaseModel):
    """
    Self-Care Hygiene
    """

    p13_brushing_teeth_severity: Optional[str] = Field(default=None, description="Brushing Teeth")  # Options: None, Mild, Moderate, Severe
    p13_flossing_teeth_severity: Optional[str] = Field(default=None, description="Flossing Teeth")  # Options: None, Mild, Moderate, Severe
class P13P13Communication(BaseModel):
    """
    Communication
    """

    p13_speak_extended_period_severity: Optional[str] = Field(default=None, description="Speak for Extended Period of Time")  # Options: None, Mild, Moderate, Severe
    p13_max_time_speak: Optional[str] = Field(default=None, description="Max Time Speak ______Min (Format: Minutes)")
    p13_speaking_difficulty_severity: Optional[str] = Field(default=None, description="Speaking Difficulty")  # Options: None, Mild, Moderate, Severe
    p13_asked_to_repeat_themselves_severity: Optional[str] = Field(default=None, description="Asked to Repeat Themselves")  # Options: None, Mild, Moderate, Severe
class P13P13MotorFunction(BaseModel):
    """
    Motor Function
    """

    p13_mastication_severity: Optional[str] = Field(default=None, description="Mastication")  # Options: None, Mild, Moderate, Severe
    p13_tasting_severity: Optional[str] = Field(default=None, description="Tasting")  # Options: None, Mild, Moderate, Severe
    p13_tasting_vas: Optional[str] = Field(default=None, description="VAS ____")
    p13_taste_change_type: Optional[str] = Field(default=None, description="Due to dryness of the mouth causing a change in taste:")  # Options: Bitter, Metallic, Bland
    p13_swallowing_severity: Optional[str] = Field(default=None, description="Swallowing")  # Options: None, Mild, Moderate, Severe
class P13P13Bruxism(BaseModel):
    """
    Bruxism
    """

    p13_bruxism_severity: Optional[str] = Field(default=None, description="Bruxism")  # Options: None, Mild, Moderate, Severe
class P13P13SexualFunction(BaseModel):
    """
    Sexual Function
    """

    p13_kissing_oral_activities_severity: Optional[str] = Field(default=None, description="Kissing, Oral Activities")  # Options: None, Mild, Moderate, Severe
class P14P14ClinicalExamination(BaseModel):
    """
    Clinical Examination
    """

    p14_unspecified_rheumat: Optional[str] = Field(default=None, description="Unspecified Rheumat.")
    p14_tender_phalanges: Optional[str] = Field(default=None, description="Tender Phalanges")  # Options: R, L
    p14_multiple_tender_points: Optional[bool] = Field(default=None, description="Multiple Tender Points")
    p14_sleep_disturbances: Optional[bool] = Field(default=None, description="Sleep Disturbances")
    p14_fatigue: Optional[bool] = Field(default=None, description="Fatigue")
    p14_facial_palsy: Optional[str] = Field(default=None, description="Facial Palsy")  # Options: Right, Left
    p14_facial_atrophy: Optional[str] = Field(default=None, description="Facial Atrophy")  # Options: Right, Left
    p14_facial_hypertrophy: Optional[str] = Field(default=None, description="Facial Hypertrophy")  # Options: Right, Left
    p14_dyskinesia: Optional[str] = Field(default=None, description="Dyskinesia")
    p14_tongue_protrusion: Optional[str] = Field(default=None, description="Tongue Protrusion")  # Options: Right, Left, Straight
    p14_maximum_interincisal_opening_mm: Optional[int] = Field(default=None, description="Maximum Interincisal Opening (mm)")
    p14_max_opening_pain_location: Optional[str] = Field(default=None, description="Pain location during maximum opening")  # Options: R, L, Face, TMJ
    p14_max_opening_vas: Optional[int] = Field(default=None, description="Maximum Opening VAS", ge=0, le=10)
    p14_right_lateral_mm: Optional[int] = Field(default=None, description="Right Lateral (mm)")
    p14_right_lateral_pain_location: Optional[str] = Field(default=None, description="Right lateral pain location")  # Options: R, L, Face, TMJ
    p14_right_lateral_vas: Optional[int] = Field(default=None, description="Right Lateral VAS", ge=0, le=10)
    p14_left_lateral_mm: Optional[int] = Field(default=None, description="Left Lateral (mm)")
    p14_left_lateral_pain_location: Optional[str] = Field(default=None, description="Left lateral pain location")  # Options: R, L, Face, TMJ
    p14_left_lateral_vas: Optional[int] = Field(default=None, description="Left Lateral VAS", ge=0, le=10)
    p14_protrusion_mm: Optional[int] = Field(default=None, description="Protrusion (mm)")
    p14_protrusion_pain_location: Optional[str] = Field(default=None, description="Protrusion pain location")  # Options: R, L, Face, TMJ
    p14_protrusion_vas: Optional[int] = Field(default=None, description="Protrusion VAS", ge=0, le=10)
    p14_jaw_deviation_deflection: Optional[bool] = Field(default=None, description="Jaw Deviation - Deflection")
    p14_jaw_deviation_opening: Optional[bool] = Field(default=None, description="Jaw Deviation - Opening")
    p14_jaw_deviation_closing: Optional[bool] = Field(default=None, description="Jaw Deviation - Closing")
    p14_jaw_deviation_direction: Optional[str] = Field(default=None, description="Jaw Deviation Direction")  # Options: R, L
    p14_jaw_deviation_mm: Optional[int] = Field(default=None, description="Jaw Deviation (mm)")
    p14_s_form_deviation: Optional[str] = Field(default=None, description="S-Form Deviation")  # Options: R, L
    p14_capsulitis: Optional[str] = Field(default=None, description="Capsulitis")
    p14_right_lateral_pole_pain: Optional[str] = Field(default=None, description="Right Lateral Pole Pain")
    p14_right_lateral_pole_vas: Optional[int] = Field(default=None, description="Right Lateral Pole VAS", ge=0, le=10)
    p14_left_lateral_pole_pain: Optional[str] = Field(default=None, description="Left Lateral Pole Pain")
    p14_left_lateral_pole_vas: Optional[int] = Field(default=None, description="Left Lateral Pole VAS", ge=0, le=10)
    p14_right_via_eam_pain: Optional[str] = Field(default=None, description="Right VIA EAM Pain")
    p14_right_via_eam_vas: Optional[int] = Field(default=None, description="Right VIA EAM VAS", ge=0, le=10)
    p14_left_via_eam_pain: Optional[str] = Field(default=None, description="Left VIA EAM Pain")
    p14_left_via_eam_vas: Optional[int] = Field(default=None, description="Left VIA EAM VAS", ge=0, le=10)
    p14_joint_noises_right: Optional[bool] = Field(default=None, description="Joint Noises (Manual) - Right")
    p14_joint_noises_left: Optional[bool] = Field(default=None, description="Joint Noises (Manual) - Left")
    p14_joint_noises_crepitus: Optional[bool] = Field(default=None, description="Joint Noises - Crepitus")
    p14_joint_noises_clicking: Optional[bool] = Field(default=None, description="Joint Noises - Clicking")
    p14_joint_noises_translational: Optional[bool] = Field(default=None, description="Joint Noises - Translational")
    p14_joint_noises_lateral: Optional[bool] = Field(default=None, description="Joint Noises - Lateral")
    p14_muscle_palpation_table: list[P14MusclePalpationTableRow] = Field(default_factory=list, description="Tenderness: Palpable Taut Bands / Trigger Points")
class P15P15Occlusion(BaseModel):
    """
    Occlusion Assessment
    """

    p15_class_selection: Optional[str] = Field(default=None, description="Class")  # Options: I, II, III
    p15_overbite_mm: Optional[float] = Field(default=None, description="Overbite ______mm")
    p15_overjet_mm: Optional[float] = Field(default=None, description="Overjet______mm")
    p15_midline_deviation: Optional[float] = Field(default=None, description="Midline Deviation ______mm R L")
    p15_crossbite: Optional[str] = Field(default=None, description="Crossbite")  # Options: Ant., R, L
    p15_bite_type: Optional[str] = Field(default=None, description="Bite Type")  # Options: Closed Bite, Collapsed Bite, Unstable Bite
    p15_open_bite: Optional[str] = Field(default=None, description="Open Bite")  # Options: Ant., R, L
    p15_tongue_thrust: Optional[str] = Field(default=None, description="Tongue Thrust")  # Options: Ant., R, L, Both Sides
    p15_tori_location: Optional[str] = Field(default=None, description="Tori")  # Options: Max, Man
class P15P15Periodontal(BaseModel):
    """
    Periodontal Assessment
    """

    p15_scalloping: Optional[str] = Field(default=None, description="Scalloping")  # Options: Right, Left, Minimal, Slight, Moderate...
    p15_buccal_mucosal_ridging: Optional[str] = Field(default=None, description="Buccal Mucosal Ridging")  # Options: Right, Left, Minimal, Slight, Moderate...
    p15_occlusal_wear: Optional[str] = Field(default=None, description="Occlusal Wear")  # Options: None Apparent, Right, Left, Ant., Minimal...
class P15P15PatientConditions(BaseModel):
    """
    Patient Conditions
    """

    p15_patient_has: Optional[str] = Field(default=None, description="Patient Has:")  # Options: FUD, FLD, UPD, LPD
    p15_fractured_dentures: Optional[str] = Field(default=None, description="Fractured Dentures")  # Options: Upper, Lower, Full, Partial
class P15P15DentalFindings(BaseModel):
    """
    Dental Findings
    """

    p15_abfractions_teeth: Optional[str] = Field(default=None, description="Abfractions on Teeth #")  # Options: 2, 3, 4, 5, 6...
    p15_missing_teeth: Optional[str] = Field(default=None, description="Missing Teeth #")  # Options: 2, 3, 4, 5, 6...
    p15_missing_third_molars: Optional[str] = Field(default=None, description="Missing Third Molars #")  # Options: 1, 16, 17, 32
    p15_gum_recession_teeth: Optional[str] = Field(default=None, description="Gum Recession Teeth #")  # Options: 2, 3, 4, 5, 6...
    p15_fractured_teeth: Optional[str] = Field(default=None, description="Fractured Teeth #")
    p15_fractured_bridge_crowns: Optional[str] = Field(default=None, description="Fractured Bridge or Crowns #")
    p15_visually_apparent_decayed_teeth: Optional[str] = Field(default=None, description="Visually Apparent Decayed Teeth #")
    p15_broken_dental_filling: Optional[str] = Field(default=None, description="Broken Dental Filling #")
    p15_teeth_sensitive_percussion: Optional[str] = Field(default=None, description="Teeth Sensitive to Percussion #")
    p15_teeth_sensitive_periapical_palpation: Optional[str] = Field(default=None, description="Teeth sensitive to Periapical Palpation #")
    p15_teeth_mobility: Optional[str] = Field(default=None, description="Teeth with Mobility #")
    p15_bleeding_gums: Optional[str] = Field(default=None, description="Bleeding Gums")
    p15_inflamed_gingiva: Optional[str] = Field(default=None, description="Inflamed Gingiva")
    p15_scars_detail: Optional[str] = Field(default=None, description="Scars? Detail:")
    p15_malampati: Optional[str] = Field(default=None, description="Malampati:")
    p15_friedman: Optional[str] = Field(default=None, description="Friedman:")
class P16DiagnosticTests(BaseModel):
    """
    Diagnostic Tests
    """

    p16_blood_pressure: Optional[str] = Field(default=None, description="Blood Pressure (Format: ___/___)")
    p16_no_clicking_was_auscultated: Optional[str] = Field(default=None, description="No Clicking was Auscultated")
class P16SalivaryDiagnostic(BaseModel):
    """
    Salivary Diagnostic Testing
    """

    pass
class P17OralAnatomyDiagram(BaseModel):
    """
    Oral Anatomy Diagram
    """

    p17_lips_upper: Optional[str] = Field(default=None, description="Upper")
    p17_lips_lower: Optional[str] = Field(default=None, description="Lower")
    p17_lips_vermillion_border: Optional[str] = Field(default=None, description="Vermillion Border")
    p17_lips_commissure: Optional[str] = Field(default=None, description="Commissure")
    p17_cheeks_right: Optional[str] = Field(default=None, description="Right")
    p17_cheeks_left: Optional[str] = Field(default=None, description="Left")
    p17_gingiva_attached_tissue: Optional[str] = Field(default=None, description="Attached Tissue")
    p17_gingiva_free_tissue: Optional[str] = Field(default=None, description="Free Tissue")
    p17_frenal_attachments_right_superior: Optional[str] = Field(default=None, description="Right Superior")
    p17_frenal_attachments_right_anterior: Optional[str] = Field(default=None, description="Right Anterior")
    p17_frenal_attachments_left_anterior: Optional[str] = Field(default=None, description="Left Anterior")
    p17_frenal_attachments_left_superior: Optional[str] = Field(default=None, description="Left Superior")
    p17_palate_hard: Optional[str] = Field(default=None, description="Hard")
    p17_palate_soft: Optional[str] = Field(default=None, description="Soft")
    p17_tongue_dorsum: Optional[str] = Field(default=None, description="Dorsum")
    p17_tongue_right_lateral_border: Optional[str] = Field(default=None, description="Right Lateral Border")
    p17_tongue_left_lateral_border: Optional[str] = Field(default=None, description="Left Lateral Border")
    p17_tongue_ventral: Optional[str] = Field(default=None, description="Ventral")
    p17_floor_vestibular_duct: Optional[str] = Field(default=None, description="Vestibular Duct")
class P17ClinicalImpressions(BaseModel):
    """
    Clinical Impressions
    """

    p17_clinical_impression_1: Optional[str] = Field(default=None, description="Clinical Impression")
    p17_clinical_impression_2: Optional[str] = Field(default=None, description="Clinical Impression")
class P17Diagnosis(BaseModel):
    """
    Diagnosis
    """

    p17_s09_93xa: Optional[str] = Field(default=None, description="S09.93XA Traumatic Injury to Face Mandible Teeth #")
    p17_traumatic_injury_teeth_number: Optional[str] = Field(default=None, description="Teeth #")
    p17_g51_0: Optional[str] = Field(default=None, description="G51.0 Facial Palsy Right Left")
    p17_g50_0: Optional[str] = Field(default=None, description="G50.0 Trigeminal Nerve Neuropathic Pain / Central Sensitization")
    p17_f45_8: Optional[str] = Field(default=None, description="F45.8 Bruxism")
    p17_m79_1: Optional[str] = Field(default=None, description="M79.1 Myalgia of Facial Muscles")
    p17_m65_80: Optional[str] = Field(default=None, description="M65.80 Capsulitis / Inflammation Right Left")
    p17_m26_69_internal_derangement: Optional[str] = Field(default=None, description="M26.69 Internal Derangement Right Left")
    p17_m26_69_osteoarthrosis: Optional[str] = Field(default=None, description="M26.69 Osteoarthrosis Right Left")
    p17_m26_69_osteoarthritis: Optional[str] = Field(default=None, description="M26.69 Osteoarthritis Right Left")
    p17_k11_7: Optional[str] = Field(default=None, description="K11.7 Xerostomia")
    p17_k05_6: Optional[str] = Field(default=None, description="K05.6 Inflammation of the Gums")
    p17_g51_0_halitosis: Optional[str] = Field(default=None, description="G51.0 Halitosis / Oral Malodor")
    p17_r19_6: Optional[str] = Field(default=None, description="R19.6 Suggestions of an Unspecified Rheumatological / Systemic Condition")
    p17_other_diagnosis_1: Optional[str] = Field(default=None, description="Other")
    p17_other_diagnosis_2: Optional[str] = Field(default=None, description="Other")
class P18P18QstSection(BaseModel):
    """
    QST
    """

    p18_qst_table: list[P18QstTableRow] = Field(default_factory=list, description="QST")
class P18P18QstColdSection(BaseModel):
    """
    QST Cold
    """

    p18_qst_cold_table: list[P18QstColdTableRow] = Field(default_factory=list, description="QST Cold")
class P18P18QstBilateralSection(BaseModel):
    """
    QST After Bilateral SPGB, if necessary
    """

    p18_qst_bilateral_table: list[P18QstBilateralTableRow] = Field(default_factory=list, description="QST After Bilateral SPGB, if necessary")
class P19P19LateralBorderTongueScalloping(BaseModel):
    """
    Lateral Border of the Tongue Scalloping
    """

    pass
class P19P19BuccalMucosalRidging(BaseModel):
    """
    Buccal Mucosal Ridging
    """

    p19_buccal_mucosal_ridging: Optional[str] = Field(default=None, description="Buccal Mucosal Ridging")  # Options: Right, Left
class P19P19OcclusalWear(BaseModel):
    """
    Occlusal Wear
    """

    p19_occlusal_wear: Optional[str] = Field(default=None, description="Occlusal Wear")  # Options: Anterior, Generalized
class P19P19BleedingFlossing(BaseModel):
    """
    Bleeding on Flossing
    """

    pass
class P19P19TongueBladesAdhering(BaseModel):
    """
    Tongue Blades adhering to inside of cheeks
    """

    pass
class P19P19Erosion(BaseModel):
    """
    Erosion
    """

    p19_erosion_class: Optional[str] = Field(default=None, description="Erosion Class")  # Options: Class I, II, III, Occlusion
class P19P19ConditionsList(BaseModel):
    """
    Dental/Oral Conditions
    """

    pass
class P19P19Deviations(BaseModel):
    """
    Deviations
    """

    p19_deviation_tongue_protrusion: Optional[str] = Field(default=None, description="Deviation of Tongue on Protrusion")  # Options: Right, Left
    p19_deviation_mandible_opening: Optional[str] = Field(default=None, description="Deviation of Mandible Upon Opening")  # Options: Right, Left
    p19_facial_palsy: Optional[str] = Field(default=None, description="Facial Palsy")  # Options: Right, Left
class P19P19DentalIssues(BaseModel):
    """
    Dental Issues
    """

    p19_missing_broken_teeth: Optional[str] = Field(default=None, description="Missing/Broken Teeth #")
class P19P19BiteConditions(BaseModel):
    """
    Bite Conditions
    """

    p19_open_bite: Optional[str] = Field(default=None, description="Open Bite")  # Options: Anterior, Right, Left
    p19_cross_bite: Optional[str] = Field(default=None, description="Cross Bite")  # Options: Anterior, Right, Left
    p19_collapsed_bite: Optional[str] = Field(default=None, description="Collapsed Bite")  # Options: Unstable Bite, Off Bite
class P19P19FacialConditions(BaseModel):
    """
    Facial Conditions
    """

    pass
class P19P19MuscleConditions(BaseModel):
    """
    Muscle Conditions
    """

    p19_hypertrophy_masseter: Optional[str] = Field(default=None, description="Hypertrophy of Masseter Muscle")  # Options: Right, Left, Bilateral
class P19P19TongueTrust(BaseModel):
    """
    Tongue Trust
    """

    p19_tongue_trust: Optional[str] = Field(default=None, description="Tongue Trust")  # Options: Anterior, Lateral, Right, Left
class P19P19OrthodonticConditions(BaseModel):
    """
    Orthodontic and Oral Conditions
    """

    pass
class P20P20TreatmentPlan(BaseModel):
    """
    Treatment Plan
    """

    p20_treatment_checkboxes: list[str] = Field(default=None, description="Treatment Options")  # Options: Orthotic Appliance / Resilient Orthotic OAOA OSA TRD Diagnostic Splint, Craniofacial Exercises, Trigger Point Injections, Sphenopalatine Ganglion Blocks, Trigeminal Pharyngoplasty...
    p20_consultations_needed: list[str] = Field(default=None, description="Consultations and Studies Needed")  # Options: Sleep Study Report Needed, Polysomnogram Needed, Physical Therapy Treatment Needed, Psychological Consultation Needed, Neurological Care Needed...
    p20_plastic_surgery_reason: Optional[str] = Field(default=None, description="Plastic Surgery Consultation Needed for")
    p20_ent_consultation_ringing: Optional[bool] = Field(default=None, description="ENT Consultation Needed for Ringing in ears")
    p20_ent_consultation_hearing_loss: Optional[bool] = Field(default=None, description="ENT Consultation Needed for Hearing Loss")
    p20_internal_medicine_consults: list[str] = Field(default=None, description="Internal Medicine Consult Needed for")  # Options: HBP, Diabetes, GERD, Kidney, Thyroid
    p20_thyroid_details: Optional[str] = Field(default=None, description="Thyroid details")
    p20_dental_consultations: list[str] = Field(default=None, description="Dental Consultations")  # Options: Referral for Evaluation And Treatment with Prosthodontic/Periodontist Specialist, Oral Surgery Consultation, Orthodontic Consultation
    p20_dental_consultation_reasons: list[str] = Field(default=None, description="Dental Consultation for")  # Options: Treatment for Decay, Fractured Teeth, Xerostomia / Periodontal Disease
    p20_patient_records_tasks: list[str] = Field(default=None, description="Patient Tasks")  # Options: Patient to get Dental Records / FMX, Patient to get Prescriptions from Pharmacy, I NEED ALL MEDICAL AND DENTAL RECORDS
    p20_xray_disclosure: Optional[bool] = Field(default=None, description="Patient informed they must see any dentist for X-rays to determine if any fracture, decay, and / or periodontal disease is present that can be caused or aggravated by their industrially related xerostomia or bruxism conditions")
    p20_dental_treatment_disclosure: Optional[bool] = Field(default=None, description="Patient informed they must see any dentist for the decay and / or periodontal disease that can be caused or aggravated by their industrially related xerostomia")
    p20_treatment_authorization_disclosure: Optional[bool] = Field(default=None, description="Patient informed that if they require dental treatment for decay or fractured of teeth that was caused or aggravated by their industrially related xerostomia, or trauma, or bruxism, that no treatment will be performed by our office for the decay or fractured teeth until authorization and payment is made to our office by the workers compensation insurance company")
    p20_doctor_signature: Optional[str] = Field(default=None, description="Dr. Signature")
    p20_signature_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class Page1Data(BaseModel):
    """
    Page 1: Patient Information Form
    Complexity: 6/10
    """

    p1_header_info: Optional[P1P1HeaderInfo] = Field(default=None, description="Form Header Information")
    p1_patient_demographics: Optional[P1P1PatientDemographics] = Field(default=None, description="Patient Demographics")
    p1_medical_history: Optional[P1P1MedicalHistory] = Field(default=None, description="Medical History Questions")
    p1_allergies: Optional[P1P1Allergies] = Field(default=None, description="History of Allergies")
    p1_medications: Optional[P1P1Medications] = Field(default=None, description="Current Medications")
    p1_doctor_completion_table: list[P1DoctorCompletionTableRow] = Field(default_factory=list, description="BELOW THE LINE TO BE COMPLETED BY THE DOCTOR:")
class Page2Data(BaseModel):
    """
    Page 2: History of Medication Usage
    Complexity: 6/10
    """

    medications_before_injury: Optional[P2MedicationsBeforeInjury] = Field(default=None, description="Medications Before Work Injury")
    medications_currently_taking: Optional[P2MedicationsCurrentlyTaking] = Field(default=None, description="Medications Currently Taking")
    medications_after_injury: Optional[P2MedicationsAfterInjury] = Field(default=None, description="Medications After Work Injury")
class Page3Data(BaseModel):
    """
    Page 3: Orofacial Exam - Page 3
    Complexity: 7/10
    """

    mouth_symptoms: Optional[P3MouthSymptoms] = Field(default=None, description="Mouth Symptoms")
    bad_breath: Optional[P3BadBreath] = Field(default=None, description="Bad Breath Assessment")
    halitosis_meter: Optional[P3HalitosisMeter] = Field(default=None, description="Halitosis Meter Reading")
    taste_changes: Optional[P3TasteChanges] = Field(default=None, description="Taste Changes")
    signature_section: Optional[P3SignatureSection] = Field(default=None, description="Signature")
class Page4Data(BaseModel):
    """
    Page 4: Orofacial Exam - Page 4
    Complexity: 6/10
    """

    p4_hand_dominance: Optional[P4P4HandDominance] = Field(default=None, description="Hand Dominance")
    p4_work_injury: Optional[P4P4WorkInjury] = Field(default=None, description="Work Injury")
    p4_daily_activities: Optional[P4P4DailyActivities] = Field(default=None, description="Daily Activities")
    p4_smoking_history: Optional[P4P4SmokingHistory] = Field(default=None, description="Smoking History")
    p4_substance_use: Optional[P4P4SubstanceUse] = Field(default=None, description="Substance Use")
    p4_patient_signature: Optional[str] = Field(default=None, description="Patient's Signature")
    p4_signature_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class Page5Data(BaseModel):
    """
    Page 5: Employment History
    Complexity: 7/10
    """

    p5_location: Optional[str] = Field(default=None, description="Office location (HAWTHORNE, RESEDA, ANAHEIM, REDLANDS, SACRAMENTO)")
    p5_eval_type: Optional[str] = Field(default=None, description="Evaluation type (PRIVATE, WCAB, QME, PQME, APQME, AME, UNREPRESENTED, PERSONAL INJURY)")
    header_info: Optional[P5HeaderInfo] = Field(default=None, description="Header Information")
    employment_history: Optional[P5EmploymentHistory] = Field(default=None, description="Employment History")
class Page6Data(BaseModel):
    """
    Page 6: History of Industrial Injury
    Complexity: 8/10
    """

    p6_trauma_history: Optional[P6P6TraumaHistory] = Field(default=None, description="Trauma History Review")
    p6_industrial_injury: Optional[P6P6IndustrialInjury] = Field(default=None, description="History of Industrial Injury")
    p6_mva_details: Optional[P6P6MvaDetails] = Field(default=None, description="Motor Vehicle Accident Details")
class Page7Data(BaseModel):
    """
    Page 7: Orofacial Exam - Page 7
    Complexity: 8/10
    """

    p7_pain_stress_section: Optional[P7P7PainStressSection] = Field(default=None, description="Pain and Stress Related Questions")
    p7_preexisting_conditions: Optional[P7P7PreexistingConditions] = Field(default=None, description="Pre-Existing Conditions")
    p7_attestation_signature: Optional[P7P7AttestationSignature] = Field(default=None, description="Attestation and Signature")
    p7_treatments_received: Optional[P7P7TreatmentsReceived] = Field(default=None, description="Treatments Received Due to the Industrial Injury")
class Page8Data(BaseModel):
    """
    Page 8: Orofacial Exam - Page 8
    Complexity: 6/10
    """

    tx_received: Optional[P8TxReceived] = Field(default=None, description="Tx Received")
    prior_history: Optional[P8PriorHistory] = Field(default=None, description="Prior History")
    p8_any_injuries_after_industrial_date: Optional[str] = Field(default=None, description="Any Injuries After the Date of Industrial Injury (Industrial or Non-Industrial)")
    p8_mva_injury_table: list[P8MvaInjuryTableRow] = Field(default_factory=list, description="MVA Injury Details")
class Page9Data(BaseModel):
    """
    Page 9: Dental History
    Complexity: 7/10
    """

    p9_dental_history: Optional[P9P9DentalHistory] = Field(default=None, description="Dental History")
    p9_dental_treatments: Optional[P9P9DentalTreatments] = Field(default=None, description="Dental Treatments")
    p9_treatments_since_injury: Optional[P9P9TreatmentsSinceInjury] = Field(default=None, description="Dental Treatments Received Since Industrial Injuries")
class Page10Data(BaseModel):
    """
    Page 10: Present Symptoms
    Complexity: 8/10
    """

    p10_present_symptoms: Optional[P10P10PresentSymptoms] = Field(default=None, description="Present Symptoms")
    p10_headaches: Optional[P10P10Headaches] = Field(default=None, description="Headaches")
    p10_face_pain: Optional[P10P10FacePain] = Field(default=None, description="Face Pain")
    p10_tmj_noise_pain: Optional[P10P10TmjNoisePain] = Field(default=None, description="TMJ Noise and Pain")
class Page11Data(BaseModel):
    """
    Page 11: Orofacial Exam - Page 11
    Complexity: 8/10
    """

    p11_jaw_mouth_symptoms: Optional[P11P11JawMouthSymptoms] = Field(default=None, description="Jaw and Mouth Symptoms")
    p11_oral_symptoms: Optional[P11P11OralSymptoms] = Field(default=None, description="Oral Symptoms")
    p11_additional_symptoms: Optional[P11P11AdditionalSymptoms] = Field(default=None, description="Additional Symptoms")
    epworth_sleepiness_scale: Optional[P11EpworthSleepinessScale] = Field(default=None, description="Epworth Sleepiness Scale")
class Page12Data(BaseModel):
    """
    Page 12: Activities of Daily Living VAS
    Complexity: 7/10
    """

    p12_facial_pain_activities: Optional[P12P12FacialPainActivities] = Field(default=None, description="Activities of Daily Living VAS")
    p12_communication_talking: Optional[P12P12CommunicationTalking] = Field(default=None, description="Communication / Talking")
    p12_eating_chewing: Optional[P12P12EatingChewing] = Field(default=None, description="Eating / Chewing")
    p12_attestation_signature: Optional[P12P12AttestationSignature] = Field(default=None, description="Attestation and Signature")
class Page13Data(BaseModel):
    """
    Page 13: Activities of Daily Living
    Complexity: 6/10
    """

    p13_self_care_hygiene: Optional[P13P13SelfCareHygiene] = Field(default=None, description="Self-Care Hygiene")
    p13_communication: Optional[P13P13Communication] = Field(default=None, description="Communication")
    p13_motor_function: Optional[P13P13MotorFunction] = Field(default=None, description="Motor Function")
    p13_bruxism: Optional[P13P13Bruxism] = Field(default=None, description="Bruxism")
    p13_sexual_function: Optional[P13P13SexualFunction] = Field(default=None, description="Sexual Function")
class Page14Data(BaseModel):
    """
    Page 14: Clinical Examination
    Complexity: 8/10
    """

    p14_clinical_examination: Optional[P14P14ClinicalExamination] = Field(default=None, description="Clinical Examination")
class Page15Data(BaseModel):
    """
    Page 15: Orofacial Exam - Page 15
    Complexity: 8/10
    """

    p15_occlusion: Optional[P15P15Occlusion] = Field(default=None, description="Occlusion Assessment")
    p15_periodontal: Optional[P15P15Periodontal] = Field(default=None, description="Periodontal Assessment")
    p15_patient_conditions: Optional[P15P15PatientConditions] = Field(default=None, description="Patient Conditions")
    p15_dental_findings: Optional[P15P15DentalFindings] = Field(default=None, description="Dental Findings")
class Page16Data(BaseModel):
    """
    Page 16: Diagnostic Tests
    Complexity: 8/10
    """

    diagnostic_tests: Optional[P16DiagnosticTests] = Field(default=None, description="Diagnostic Tests")
    salivary_diagnostic: Optional[P16SalivaryDiagnostic] = Field(default=None, description="Salivary Diagnostic Testing")
    p16_amylase_test: Optional[str] = Field(default=None, description="Amylase Test")
class Page17Data(BaseModel):
    """
    Page 17: Oral Cancer Screening Form
    Complexity: 6/10
    """

    oral_anatomy_diagram: Optional[P17OralAnatomyDiagram] = Field(default=None, description="Oral Anatomy Diagram")
    clinical_impressions: Optional[P17ClinicalImpressions] = Field(default=None, description="Clinical Impressions")
    diagnosis: Optional[P17Diagnosis] = Field(default=None, description="Diagnosis")
    p17_dfv_signature: Optional[str] = Field(default=None, description="DFV")
class Page18Data(BaseModel):
    """
    Page 18: Trigeminal Nerve Neuropathic QST Testing
    Complexity: 8/10
    """

    p18_qst_section: Optional[P18P18QstSection] = Field(default=None, description="QST")
    p18_qst_cold_section: Optional[P18P18QstColdSection] = Field(default=None, description="QST Cold")
    p18_qst_bilateral_section: Optional[P18P18QstBilateralSection] = Field(default=None, description="QST After Bilateral SPGB, if necessary")
class Page19Data(BaseModel):
    """
    Page 19: Diagnostic Photographs
    Complexity: 4/10
    """

    p19_lateral_border_tongue_scalloping: Optional[P19P19LateralBorderTongueScalloping] = Field(default=None, description="Lateral Border of the Tongue Scalloping")
    p19_buccal_mucosal_ridging: Optional[P19P19BuccalMucosalRidging] = Field(default=None, description="Buccal Mucosal Ridging")
    p19_occlusal_wear: Optional[P19P19OcclusalWear] = Field(default=None, description="Occlusal Wear")
    p19_bleeding_flossing: Optional[P19P19BleedingFlossing] = Field(default=None, description="Bleeding on Flossing")
    p19_tongue_blades_adhering: Optional[P19P19TongueBladesAdhering] = Field(default=None, description="Tongue Blades adhering to inside of cheeks")
    p19_erosion: Optional[P19P19Erosion] = Field(default=None, description="Erosion")
    p19_conditions_list: Optional[P19P19ConditionsList] = Field(default=None, description="Dental/Oral Conditions")
    p19_deviations: Optional[P19P19Deviations] = Field(default=None, description="Deviations")
    p19_dental_issues: Optional[P19P19DentalIssues] = Field(default=None, description="Dental Issues")
    p19_bite_conditions: Optional[P19P19BiteConditions] = Field(default=None, description="Bite Conditions")
    p19_facial_conditions: Optional[P19P19FacialConditions] = Field(default=None, description="Facial Conditions")
    p19_muscle_conditions: Optional[P19P19MuscleConditions] = Field(default=None, description="Muscle Conditions")
    p19_tongue_trust: Optional[P19P19TongueTrust] = Field(default=None, description="Tongue Trust")
    p19_orthodontic_conditions: Optional[P19P19OrthodonticConditions] = Field(default=None, description="Orthodontic and Oral Conditions")
class Page20Data(BaseModel):
    """
    Page 20: Treatment Plan
    Complexity: 7/10
    """

    p20_treatment_plan: Optional[P20P20TreatmentPlan] = Field(default=None, description="Treatment Plan")
# =============================================================================
# MAIN EXTRACTION MODEL
# =============================================================================

class OrofacialExamExtraction(BaseModel):
    """
    Complete extraction model for: orofacial_exam
    
    Use this model with instructor to extract all data from filled forms.
    """

    # Metadata
    extraction_timestamp: Optional[datetime] = Field(default=None, description="When extraction occurred")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    needs_review: bool = Field(default=False, description="Form needs human review")
    review_reasons: list[str] = Field(default_factory=list, description="Why review is needed")

    # Page Data
    page_1: Optional[Page1Data] = Field(default=None, description="Page 1: Patient Information Form")
    page_2: Optional[Page2Data] = Field(default=None, description="Page 2: History of Medication Usage")
    page_3: Optional[Page3Data] = Field(default=None, description="Page 3: Orofacial Exam - Page 3")
    page_4: Optional[Page4Data] = Field(default=None, description="Page 4: Orofacial Exam - Page 4")
    page_5: Optional[Page5Data] = Field(default=None, description="Page 5: Employment History")
    page_6: Optional[Page6Data] = Field(default=None, description="Page 6: History of Industrial Injury")
    page_7: Optional[Page7Data] = Field(default=None, description="Page 7: Orofacial Exam - Page 7")
    page_8: Optional[Page8Data] = Field(default=None, description="Page 8: Orofacial Exam - Page 8")
    page_9: Optional[Page9Data] = Field(default=None, description="Page 9: Dental History")
    page_10: Optional[Page10Data] = Field(default=None, description="Page 10: Present Symptoms")
    page_11: Optional[Page11Data] = Field(default=None, description="Page 11: Orofacial Exam - Page 11")
    page_12: Optional[Page12Data] = Field(default=None, description="Page 12: Activities of Daily Living VAS")
    page_13: Optional[Page13Data] = Field(default=None, description="Page 13: Activities of Daily Living")
    page_14: Optional[Page14Data] = Field(default=None, description="Page 14: Clinical Examination")
    page_15: Optional[Page15Data] = Field(default=None, description="Page 15: Orofacial Exam - Page 15")
    page_16: Optional[Page16Data] = Field(default=None, description="Page 16: Diagnostic Tests")
    page_17: Optional[Page17Data] = Field(default=None, description="Page 17: Oral Cancer Screening Form")
    page_18: Optional[Page18Data] = Field(default=None, description="Page 18: Trigeminal Nerve Neuropathic QST Testing")
    page_19: Optional[Page19Data] = Field(default=None, description="Page 19: Diagnostic Photographs")
    page_20: Optional[Page20Data] = Field(default=None, description="Page 20: Treatment Plan")

    # Field-level evidence (optional, for detailed tracking)
    field_evidence: list[ExtractedFieldValue] = Field(default_factory=list, description="Detailed evidence for each extracted field")
