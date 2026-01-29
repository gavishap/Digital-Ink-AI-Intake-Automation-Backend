
"""
Pydantic Models for: orofacial_exam
Form ID: orofacial_exam

Generated on: 2026-01-16T13:06:22.484656
Total Pages: 20
Total Fields: 581

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

class P3DryMouthOptions(str, Enum):
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3HoarsenessOptions(str, Enum):
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3LittleSalivaOptions(str, Enum):
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3SwallowingDifficultiesOptions(str, Enum):
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3DryMouthEatingOptions(str, Enum):
    YES = "YES"
    NO = "NO"
    SOMETIMES = "Sometimes"

class P3SipLiquidsOptions(str, Enum):
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
    VALUE_4__STRONG_ODOR = "4 =Strong Odor"
    VALUE_5___INTENSE_ODOR = "5 = Intense Odor"

class P3TasteFeelsBlandOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3TastePerceptionChangeOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3TasteChangeCovidOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3DoctorCovidWorkOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P3GerdWorkRelatedOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4HandDominanceOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P4DifficultyGripToothbrushOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultyFlossTeethOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4ShoulderPainBrushingOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultyToothpasteTubeOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultySqueezeToothpasteOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultyCutFoodOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultyFeedYourselfOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DifficultyRaiseArmCombOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DoYouSmokeOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4HaveYouSmokedOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4SmokingIncreaseAfterInjuryOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4DrinkAlcoholOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4UseRecreationalDrugsOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P4UsedAmphetaminesOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P5InsuranceTypeOptions(str, Enum):
    PRIVATE = "PRIVATE"
    WCAB = "WCAB"
    QME = "QME"
    PQME = "PQME"
    APQME = "APQME"
    AME = "AME"
    UNREPRESENTED = "UNREPRESENTED"
    PERSONAL_INJURY = "PERSONAL INJURY"

class P5GenderOptions(str, Enum):
    M = "M"
    F = "F"

class P5HandDominantOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P5JobRequirementsActivitiesOptions(str, Enum):
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

class P5ComputerActivitiesOptions(str, Enum):
    TYPING = "typing"
    USING_A_COMPUTER_MOUSE = "using a computer mouse"

class P5MouseHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5WorkstationSetupOptions(str, Enum):
    NON_ERGONOMIC = "non-ergonomic"
    DESK = "desk"
    CHAIR = "chair"
    WORK_STATION = "work station"
    NON_FULLY_ADJUSTABLE_CHAIR_WITH_NON_ADJUSTABLE_ARM_REST = "non-fully adjustable chair with non-adjustable arm rest"

class P5MonitorLocationOptions(str, Enum):
    F = "F"
    R = "R"
    L = "L"

class P5PhoneHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5CurrentWorkStatusOptions(str, Enum):
    DISABLED = "Disabled"
    STILL_WORKING_AT_THE_SAME_COMPANY = "Still working at the same company"
    NOT_WORKING_RETIRED = "Not Working/Retired"

class P5CurrentJobRequirementsActivitiesOptions(str, Enum):
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

class P5CurrentComputerActivitiesOptions(str, Enum):
    TYPING = "typing"
    USING_A_COMPUTER_MOUSE = "using a computer mouse"

class P5CurrentMouseHandOptions(str, Enum):
    R = "R"
    L = "L"

class P5CurrentWorkstationSetupOptions(str, Enum):
    NON_ERGONOMIC = "non-ergonomic"
    DESK = "desk"
    CHAIR = "chair"
    WORK_STATION = "work station"
    NON_FULLY_ADJUSTABLE_CHAIR_WITH_NON_ADJUSTABLE_ARM_REST = "non-fully adjustable chair with non-adjustable arm rest"

class P5CurrentMonitorLocationOptions(str, Enum):
    F = "F"
    R = "R"
    L = "L"

class P5CurrentPhoneHandOptions(str, Enum):
    R = "R"
    L = "L"

class P6PoorHistorianOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P6VehiclePositionOptions(str, Enum):
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

class P7StressorsAtWorkOptions(str, Enum):
    HEAVY_WORKLOAD = "Heavy workload"
    LONG_OR_INFLEXIBLE_HOURS = "Long or inflexible hours"
    TIGHT_DEADLINES = "Tight deadlines"
    LACK_OF_CONTROL = "Lack of control"
    CONFLICTING_OR_UNCERTAIN_JOB_EXPECTATIONS = "Conflicting or uncertain job expectations"
    NIGHT_SHIFTS = "Night shifts"
    LACK_OF_SUPPORT = "Lack of support"
    BULLYING = "Bullying"
    POOR_RELATIONSHIPS = "Poor relationships"

class P7ClenchingDayNightOptions(str, Enum):
    DAY = "Day"
    NIGHT = "Night"

class P7GrindingDayNightOptions(str, Enum):
    DAY = "Day"
    NIGHT = "Night"

class P7BracingDayNightOptions(str, Enum):
    DAY = "Day"
    NIGHT = "Night"

class P7VertexLocationsOptions(str, Enum):
    R_FOREHEAD = "R Forehead"
    L_FOREHEAD = "L Forehead"
    R_TEMPLE = "R Temple"
    L_TEMPLE = "L Temple"
    R_OCCIPUT = "R Occiput"
    L_OCCIPUT = "L Occiput"
    R_BEHIND_EYES = "R Behind Eyes"
    L_BEHIND_EYES = "L Behind Eyes"

class P7FacialPainLocationsOptions(str, Enum):
    R = "R"
    L = "L"
    B = "B"

class P7TmjPainLocationsOptions(str, Enum):
    R = "R"
    L = "L"
    B = "B"

class P7NightguardStopReasonOptions(str, Enum):
    DOES_NOT_FIT = "Does not fit"
    LOST = "Lost"
    WORE_OUT = "Wore Out"
    BROKEN = "Broken"

class P7SurgeryLocationsOptions(str, Enum):
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

class P8TxReceivedOptions(str, Enum):
    PHYSICAL_THERAPY = "Physical Therapy"
    CHIROPRACTIC_MANIPULATIONS = "Chiropractic Manipulations"
    ACUPUNCTURE = "Acupuncture"
    INJECTIONS = "Injections"
    STEROID = "Steroid"
    SPINAL = "Spinal"
    TRIGGER_POINT = "Trigger Point"

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

class P9BruxismApplianceLocationOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"

class P9SleepApplianceLocationOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"

class P10FrameSizeOptions(str, Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"

class P10SnoresOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10GaspsForAirAtNightOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10PalpitationsOnAwakeningOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10BreathingCessationAtNightOptions(str, Enum):
    YES = "Yes"
    NO = "No"
    PRE_EXISTING = "Pre-existing"
    AGGRAVATED = "Aggravated"
    AFTER_WORK_INJURY = "After Work Injury"

class P10HeadacheLocationOptions(str, Enum):
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

class P10HeadacheIntensityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10HeadacheCharacteristicsOptions(str, Enum):
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

class P10RightFacePainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10RightFacePainIntensityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10RightFacePainCharacteristicsOptions(str, Enum):
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

class P10LeftFacePainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10LeftFacePainIntensityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10LeftFacePainCharacteristicsOptions(str, Enum):
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

class P10RightTmjPainIntensityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10RightTmjPainCharacteristicsOptions(str, Enum):
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

class P10LeftTmjPainFrequencyOptions(str, Enum):
    OCCASIONAL = "Occasional"
    INTERMITTENT = "Intermittent"
    FREQUENT = "Frequent"
    CONSTANT = "Constant"

class P10LeftTmjPainIntensityOptions(str, Enum):
    MINIMAL = "Minimal"
    SLIGHT = "Slight"
    MODERATE = "Moderate"
    SEVERE = "Severe"

class P10LeftTmjPainCharacteristicsOptions(str, Enum):
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

class P11ClosedFrequencyUnitOptions(str, Enum):
    DAY = "day"
    WK = "wk"
    MONTH = "month"

class P11OpenFrequencyUnitOptions(str, Enum):
    DAY = "day"
    WK = "wk"
    MONTH = "month"

class P11DifficultChewHardFoodOptions(str, Enum):
    FACE = "Face"
    TMJ = "TMJ"
    TEETH = "Teeth"

class P11DifficultChewSideOptions(str, Enum):
    R = "R"
    L = "L"

class P11FacialPainOptions(str, Enum):
    SMILING = "Smiling"
    YAWNING = "Yawning"

class P11SorenessFaceJawSideOptions(str, Enum):
    R = "R"
    L = "L"

class P11SpeechDysfunctionOptions(str, Enum):
    INDISTINCT_ARTICULATION = "Indistinct Articulation"
    HOARSENESS = "Hoarseness"
    COTTON_MOUTH = "Cotton Mouth"
    MISSING_UPPER_ANTERIOR_TEETH = "Missing Upper Anterior Teeth"
    CANNOT_TALK_FOR_LONG_PERIODS_OF_TIME_DUE_TO_PAIN = "Cannot Talk for Long Periods of Time Due to Pain"
    JAW_TIREDNESS = "Jaw Tiredness"

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

class P12HardChewyFoodPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ProlongedSpeakingPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12RepeatNotUnderstandOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12KissingPainOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SleepInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SleepingPressureOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12SocialActivitiesOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12RelationshipInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ConcentrateInterferenceOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12IrritableAngryOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12StressOptions(str, Enum):
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

class P12HardFoodsAvoidOptions(str, Enum):
    YES = "YES"
    NO = "NO"

class P12ChewyFoodsAvoidOptions(str, Enum):
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

class P13AskedToRepeatSeverityOptions(str, Enum):
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

class P13TastingTasteChangeOptions(str, Enum):
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

class P14UnspecifiedRheumatOptions(str, Enum):
    YES = "Yes"
    NO = "No"

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

class P14DyskinesiaOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P14TongueProtrusionOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"
    STRAIGHT = "Straight"

class P14MaxOpeningPainSideOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14RightLateralPainSideOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14LeftLateralPainSideOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14ProtrusionPainSideOptions(str, Enum):
    R = "R"
    L = "L"
    FACE = "Face"
    TMJ = "TMJ"

class P14DeviationSideOptions(str, Enum):
    R = "R"
    L = "L"

class P14SFormDeviationOptions(str, Enum):
    R = "R"
    L = "L"

class P14CapsulitisOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P15ClassOptions(str, Enum):
    I = "I"
    II = "II"
    III = "III"

class P15CrossbiteOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"

class P15OpenBiteOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"

class P15TongueThrustOptions(str, Enum):
    ANT_ = "Ant."
    R = "R"
    L = "L"
    BOTH_SIDES = "Both Sides"

class P15BiteTypeOptions(str, Enum):
    CLOSED_BITE = "Closed Bite"
    COLLAPSED_BITE = "Collapsed Bite"
    UNSTABLE_BITE = "Unstable Bite"

class P15ToriOptions(str, Enum):
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

class P15AbractionsTeethOptions(str, Enum):
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

class P15BleedingGumsOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P15InflamedGingivaOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P16ElevatedMuscularActivityOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P16IncoordinationAberrantFunctionOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P16TissueAnalysisLipsOptions(str, Enum):
    DRY = "Dry"
    CRACKED = "Cracked"
    WET = "Wet"

class P16TissueAnalysisTongueOptions(str, Enum):
    FISSURING = "Fissuring"
    DRY = "Dry"
    WHITE_PATCHES = "White Patches"

class P16QualityOfSalivaOptions(str, Enum):
    CLOUDY = "Cloudy"
    ROPEY = "Ropey"
    VISCOUS = "Viscous"
    BLOODY = "Bloody"

class P16SalivaPoolingFloorMouthOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P16AdherenceTongueDepressorOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P16SalivaryFlowUnstimulatedOptions(str, Enum):
    LESS_THAN_0_1ML = "Less than 0.1mL"
    GREATER_THAN_0_1ML = "Greater than 0.1mL"

class P16SalivaryFlowStimulatedOptions(str, Enum):
    LESS_THAN_0_5ML = "Less than 0.5mL"
    GREATER_THAN_0_5ML = "Greater than 0.5mL"

class P16GingivalBleedingOptions(str, Enum):
    YES = "Yes"
    NO = "No"

class P17LipsOptions(str, Enum):
    UPPER = "Upper"
    LOWER = "Lower"
    VERMILLION_BORDER = "Vermillion Border"
    COMMISSURE = "Commissure"

class P17CheeksOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P17GingivoperioOptions(str, Enum):
    FREE_GINGIVA = "Free Gingiva"
    ATTACHED_GINGIVA = "Attached Gingiva"

class P17FacialPillarsOptions(str, Enum):
    RIGHT_POSTERIOR = "Right Posterior"
    RIGHT_ANTERIOR = "Right Anterior"
    LEFT_ANTERIOR = "Left Anterior"
    LEFT_POSTERIOR = "Left Posterior"

class P17PalateOptions(str, Enum):
    HARD = "Hard"
    SOFT = "Soft"

class P17TongueOptions(str, Enum):
    DORSUM = "Dorsum"
    RIGHT_LATERAL_BORDER = "Right Lateral Border"
    LEFT_LATERAL_BORDER = "Left Lateral Border"
    VENTRAL = "Ventral"

class P17G510Options(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P17M6580Options(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P17M2669DerangementOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P17M2669OsteoarthrosisOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P17M2669OsteoarthritisOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19LateralBorderTongueScallopingOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19BuccalMucosalRidgingOptions(str, Enum):
    RIGHT = "Right"
    LEFT = "Left"

class P19OcclusalWearOptions(str, Enum):
    ANTERIOR = "Anterior"
    GENERALIZED = "Generalized"

class P19ErosionOptions(str, Enum):
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

class P20TreatmentOptionsOptions(str, Enum):
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
    PLASTIC_SURGERY_CONSULTATION_NEEDED = "Plastic Surgery Consultation Needed"
    ENT_CONSULTATION_NEEDED_FOR__RINGING_IN_EARS_HEARING_LOSS = "ENT Consultation Needed for: Ringing in ears Hearing Loss"
    INTERNAL_MEDICINE_CONSULT_NEEDED_FOR__HBP_DIABETES_GERD_KIDNEY_THYROID = "Internal Medicine Consult Needed for: HBP Diabetes GERD Kidney Thyroid"

class P20DentalReferralsOptions(str, Enum):
    REFERRAL_FOR_EVALUATION_AND_TREATMENT_WITH_PROSTHODONTIC_PERIODONTIST_SPECIALIST = "Referral for Evaluation And Treatment with Prosthodontic/Periodontist Specialist"
    ORAL_SURGERY_CONSULTATION = "Oral Surgery Consultation"
    ORTHODONTIC_CONSULTATION = "Orthodontic Consultation"
    DENTAL_CONSULTATION_FOR__TREATMENT_FOR_DECAY_FRACTURED_TEETH_XEROSTOMIA___PERIODONTAL_DISEASE = "Dental Consultation for: Treatment for Decay Fractured Teeth Xerostomia / Periodontal Disease"
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
    """Row data for BELOW THE LINE TO BE COMPLETED BY THE DOCTOR."""

    condition: Optional[str] = Field(default=None, description="Condition")
    dx_pre_injury: Optional[str] = Field(default=None, description="DX Pre-Injury")
    increased_after_injury: Optional[str] = Field(default=None, description="Increased After Injury")
    dx_post_injury: Optional[str] = Field(default=None, description="DX Post-Injury")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P6OrthopedicInjuriesRow(BaseModel):
    """Row data for Orthopedic Injuries."""

    body_part: Optional[str] = Field(default=None, description="Orthopedic injuries to:")
    frequency: Optional[str] = Field(default=None, description="Freq.-%")
    vas_score: Optional[str] = Field(default=None, description="VAS")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P8MvaHistoryRow(BaseModel):
    """Row data for MVA History."""

    mva_date: Optional[str] = Field(default=None, description="MVA")
    injured: Optional[str] = Field(default=None, description="Injured")
    facial_jaw_problems: Optional[str] = Field(default=None, description="No facial/Jaw problems or pain")
    residual_problems: Optional[str] = Field(default=None, description="Residual Problems: None")
class P11EpworthSleepinessScaleRow(BaseModel):
    """Row data for Epworth Sleepiness Scale."""

    situation: Optional[str] = Field(default=None, description="Situation")
    score_0: Optional[bool] = Field(default=None, description="0")
    score_1: Optional[bool] = Field(default=None, description="1")
    score_2: Optional[bool] = Field(default=None, description="2")
    score_3: Optional[bool] = Field(default=None, description="3")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P14TendernessTableRow(BaseModel):
    """Row data for Tenderness and Palpable Taut Bands / Trigger Points."""

    muscle_name: Optional[str] = Field(default=None, description="Muscle")
    side: Optional[str] = Field(default=None, description="Side")
    vas_score: Optional[str] = Field(default=None, description="VAS")
    y_n_1: Optional[str] = Field(default=None, description="Y/N")
    rptha_rpoha: Optional[str] = Field(default=None, description="RPTHA/RPOHA")
    wrp_to: Optional[str] = Field(default=None, description="WRP To")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstTableRow(BaseModel):
    """Row data for QST."""

    location: Optional[str] = Field(default=None, description="Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    seconds: Optional[float] = Field(default=None, description="Seconds")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstColdTableRow(BaseModel):
    """Row data for QST Cold."""

    location: Optional[str] = Field(default=None, description="Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P18QstBilateralTableRow(BaseModel):
    """Row data for QST After Bilateral SPGB, if necessary."""

    location: Optional[str] = Field(default=None, description="Location")
    vas_score: Optional[float] = Field(default=None, description="VAS")
    seconds: Optional[float] = Field(default=None, description="Seconds")
    sharp: Optional[str] = Field(default=None, description="Sharp")
    electrical: Optional[str] = Field(default=None, description="Electrical")
    burning: Optional[str] = Field(default=None, description="Burning")
    row_label: Optional[str] = Field(default=None, description="Pre-printed row label")
class P1PatientInfo(BaseModel):
    """
    Patient Information
    """

    p1_nurse: Optional[str] = Field(default=None, description="Nurse:")
    p1_intp: Optional[str] = Field(default=None, description="INTP:")
    p1_cert_number: Optional[str] = Field(default=None, description="CERT #:")
    p1_qme_time_started: Optional[str] = Field(default=None, description="IF QME: TIME STARTED:")
    p1_time_ended: Optional[str] = Field(default=None, description="TIME ENDED:")
    p1_name: str = Field(description="NAME:")
    p1_date: Optional[str] = Field(default=None, description="DATE: (Format: MM/DD/YYYY)")
    p1_primary_treating_physician: Optional[str] = Field(default=None, description="Primary Treating Physician: Dr.")
    p1_birth_date: Optional[str] = Field(default=None, description="Birth Date: (Format: MM/DD/YYYY)")
    p1_gender: Optional[str] = Field(default=None, description="Gender")  # Options: MALE, FEMALE
    p1_home_phone: Optional[str] = Field(default=None, description="Home Tel:")
    p1_cell_phone: Optional[str] = Field(default=None, description="Cell:")
    p1_email: Optional[str] = Field(default=None, description="Email:")
    p1_address: Optional[str] = Field(default=None, description="Address:")
    p1_attorney_name: Optional[str] = Field(default=None, description="Attorney's Name:")
    p1_attorney_phone: Optional[str] = Field(default=None, description="Attorney's Phone #:")
class P1MedicalHistory(BaseModel):
    """
    Medical History Questions
    """

    p1_heart_problems: Optional[str] = Field(default=None, description="Do you have any heart problems?")
    p1_metal_joint_replacements: Optional[str] = Field(default=None, description="Do you have any metal joint replacements (NOT DENTAL FILLINGS)")
    p1_high_blood_pressure: Optional[str] = Field(default=None, description="Do you have High Blood Pressure?")
    p1_diabetes: Optional[str] = Field(default=None, description="Do you have Diabetes?")
    p1_stomach_acids: Optional[str] = Field(default=None, description="Do you feel that stomach acids come up into your mouth or throat?")
    p1_kidney_problems: Optional[str] = Field(default=None, description="Do you have any Kidney problems?")
    p1_thyroid_problem: Optional[str] = Field(default=None, description="Do you have a Thyroid problem?")
    p1_hiv_hepatitis: Optional[str] = Field(default=None, description="Do you have or have you had any of the following: HIV, Hepatitis, TB, VD")
    p1_blood_thinners: Optional[str] = Field(default=None, description="Are you taking blood thinners?")
    p1_blood_thinner_type: Optional[str] = Field(default=None, description="Which one:")
    p1_breathing_problems: Optional[str] = Field(default=None, description="Do you have any breathing problems?")
    p1_numbness_pins_needles: Optional[str] = Field(default=None, description="Do you have any numbness or pins / needles feeling anywhere in your body?")
    p1_numbness_location: Optional[str] = Field(default=None, description="Where:")
    p1_liver_problems: Optional[str] = Field(default=None, description="Do you have any Liver problems?")
    p1_urinary_problems: Optional[str] = Field(default=None, description="Do you have any Urinary problems?")
    p1_awakens_urinate: Optional[str] = Field(default=None, description="Awakens at night to urinate: - times per night")
    p1_sleep_study: Optional[str] = Field(default=None, description="Have you ever had a Sleep Study Test?")
    p1_sleep_study_when: Optional[str] = Field(default=None, description="When:")
    p1_sleep_study_results: Optional[str] = Field(default=None, description="Apnea Results?")
    p1_cpap_mask: Optional[str] = Field(default=None, description="Have you ever been given a CPAP mask to use at night to help you breathe?")
    p1_morning_headache: Optional[str] = Field(default=None, description="Do you awaken in the morning with a headache in your temple/forehead areas?")
class P1Allergies(BaseModel):
    """
    History of Allergies
    """

    p1_allergies: Optional[str] = Field(default=None, description="History of Allergies:")  # Options: Penicillin, Sulfa, Erythromycin, Seasonal Allergies
class P1Medications(BaseModel):
    """
    Current Medications
    """

    p1_current_medications: Optional[str] = Field(default=None, description="Please circle medications you are taking?")  # Options: Pristiq, Wellbutrin, Effexor, Celexa, Cymbalta...
    p1_medications_for_conditions: Optional[str] = Field(default=None, description="Medications For: Diabetes Sleep High Blood Pressure Pain Anti-Inflammatory Cholesterol - see attached sheet")
class P2MedicationUsageQuestions(BaseModel):
    """
    History of Medication Usage
    """

    p2_times_per_day: Optional[int] = Field(default=None, description="How many times per Day?")
    p2_medication_duration: Optional[str] = Field(default=None, description="For how long have they taken the Medication?")
    p2_dosage: Optional[str] = Field(default=None, description="Dosage?")
class P2BeforeInjuryMedications(BaseModel):
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
class P2PresentlyTakingMedications(BaseModel):
    """
    Medications Presently Taking
    """

    p2_presently_cannot_remember: Optional[bool] = Field(default=None, description="The patient cannot remember at this time")
    p2_presently_none: Optional[bool] = Field(default=None, description="None")
    p2_presently_pain: Optional[str] = Field(default=None, description="Pain")
    p2_presently_inflammation: Optional[str] = Field(default=None, description="Inflammation")
    p2_presently_stress: Optional[str] = Field(default=None, description="Stress")
    p2_presently_sleep: Optional[str] = Field(default=None, description="Sleep")
    p2_presently_gastric_reflux: Optional[str] = Field(default=None, description="Gastric Reflux")
    p2_presently_diabetes: Optional[str] = Field(default=None, description="Diabetes")
    p2_presently_high_blood_pressure: Optional[str] = Field(default=None, description="High Blood Pressure")
    p2_presently_thyroid_problem: Optional[str] = Field(default=None, description="Thyroid Problem")
    p2_presently_other: Optional[str] = Field(default=None, description="Other")
class P2AfterInjuryMedications(BaseModel):
    """
    Medications After Work Injury
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
class P3P3MouthSymptoms(BaseModel):
    """
    Mouth Symptoms
    """

    p3_dry_mouth: Optional[str] = Field(default=None, description="Do you feel that you have dry mouth?")  # Options: YES, NO, Sometimes
    p3_hoarseness: Optional[str] = Field(default=None, description="Do you have hoarseness?")  # Options: YES, NO, Sometimes
    p3_little_saliva: Optional[str] = Field(default=None, description="Does the amount of saliva in your mouth seem to be too little?")  # Options: YES, NO, Sometimes
    p3_swallowing_difficulties: Optional[str] = Field(default=None, description="Do you have any difficulties swallowing?")  # Options: YES, NO, Sometimes
    p3_dry_mouth_eating: Optional[str] = Field(default=None, description="Does your mouth feel dry when eating a meal?")  # Options: YES, NO, Sometimes
    p3_sip_liquids: Optional[str] = Field(default=None, description="Do you sip liquids to aid in swallowing dry food?")  # Options: YES, NO, Sometimes
class P3P3BadBreath(BaseModel):
    """
    Bad Breath Assessment
    """

    p3_bad_breath_before: Optional[str] = Field(default=None, description="Do you have bad breath? (Before the Injury)")  # Options: YES, NO
    p3_bad_breath_after: Optional[str] = Field(default=None, description="Do you have bad breath? (After the Injury)")  # Options: YES, NO
    p3_bad_breath_percentage_before: Optional[str] = Field(default=None, description="What percentage of time do you have bad breath? (Before the Injury) (Format: 0 to 100%)")
    p3_bad_breath_percentage_after: Optional[str] = Field(default=None, description="What percentage of time do you have bad breath? (After the Injury) (Format: 0 to 100%)")
    p3_breath_intensity_before: Optional[str] = Field(default=None, description="How intense is your bad breath? (Before the Injury)")
    p3_breath_intensity_after: Optional[str] = Field(default=None, description="How intense is your bad breath? (After the Injury)")
    p3_people_tell_breath_before: Optional[str] = Field(default=None, description="How often do people tell you that you have bad breath? (Before the Injury)")
    p3_people_tell_breath_after: Optional[str] = Field(default=None, description="How often do people tell you that you have bad breath? (After the Injury)")
    p3_breath_interfere_others_before: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to interact with other people? (Before the Injury)")
    p3_breath_interfere_others_after: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to interact with other people? (After the Injury)")
    p3_breath_interfere_family_before: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to interact with your family? (Before the Injury)")
    p3_breath_interfere_family_after: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to interact with your family? (After the Injury)")
    p3_breath_interfere_intimate_before: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to have intimate kissing with your significant other? (Before the Injury)")
    p3_breath_interfere_intimate_after: Optional[str] = Field(default=None, description="Does your bad breath interfere with your ability to have intimate kissing with your significant other? (After the Injury)")
    p3_breath_embarrassment_before: Optional[str] = Field(default=None, description="Does your bad breath cause you embarrassment? (Before the Injury)")
    p3_breath_embarrassment_after: Optional[str] = Field(default=None, description="Does your bad breath cause you embarrassment? (After the Injury)")
    p3_breath_stress_before: Optional[str] = Field(default=None, description="Does your bad breath cause you stress? (Before the Injury)")
    p3_breath_stress_after: Optional[str] = Field(default=None, description="Does your bad breath cause you stress? (After the Injury)")
class P3P3HalitosisTaste(BaseModel):
    """
    Halitosis and Taste Assessment
    """

    p3_halitosis_reading: Optional[str] = Field(default=None, description="Halitosis Meter Reading")  # Options: 1 = No Odor, 2 = Slight Odor, 3 = Moderate Odor, 4 =Strong Odor, 5 = Intense Odor
    p3_taste_feels_bland: Optional[str] = Field(default=None, description="Since your work injury have you noticed that your taste feels bland?")  # Options: Yes, No
    p3_taste_perception_change: Optional[str] = Field(default=None, description="Has there been a change in your perception of taste of sweet, salty, or sour foods?")  # Options: Yes, No
    p3_taste_change_amount: Optional[str] = Field(default=None, description="If yes, From 0 to 10 how much do you feel your taste has changed?")
    p3_taste_change_covid: Optional[str] = Field(default=None, description="Was your change in taste caused by Covid-19")  # Options: Yes, No
    p3_doctor_covid_work: Optional[str] = Field(default=None, description="If yes, has a doctor determined that you caught Covid at work?")  # Options: Yes, No
    p3_gerd_work_related: Optional[str] = Field(default=None, description="Has a doctor determined that your GERD is work related?")  # Options: Yes, No
class P3P3SignatureSection(BaseModel):
    """
    Attestation and Signature
    """

    p3_patient_signature: Optional[str] = Field(default=None, description="Patient's Signature:")
    p3_signature_date: Optional[str] = Field(default=None, description="Date: (Format: MM/DD/YYYY)")
class P4HandDominance(BaseModel):
    """
    Hand Dominance
    """

    p4_hand_dominance: Optional[str] = Field(default=None, description="Hand Dominance")  # Options: Right, Left
class P4WorkInjuryBodyParts(BaseModel):
    """
    In your work injury, did you injure your:
    """

    p4_injury_right_shoulder: Optional[bool] = Field(default=None, description="Right Shoulder")
    p4_injury_right_arm: Optional[bool] = Field(default=None, description="Right Arm")
    p4_injury_right_elbow: Optional[bool] = Field(default=None, description="Right Elbow")
    p4_injury_right_wrist: Optional[bool] = Field(default=None, description="Right Wrist")
    p4_injury_right_hand: Optional[bool] = Field(default=None, description="Right Hand")
    p4_injury_right_fingers: Optional[bool] = Field(default=None, description="Right Fingers")
    p4_injury_left_shoulder: Optional[bool] = Field(default=None, description="Left Shoulder")
    p4_injury_left_arm: Optional[bool] = Field(default=None, description="Left Arm")
    p4_injury_left_elbow: Optional[bool] = Field(default=None, description="Left Elbow")
    p4_injury_left_wrist: Optional[bool] = Field(default=None, description="Left Wrist")
    p4_injury_left_hand: Optional[bool] = Field(default=None, description="Left Hand")
    p4_injury_left_fingers: Optional[bool] = Field(default=None, description="Left Fingers")
class P4HandFunctionDifficulties(BaseModel):
    """
    Hand Function Difficulties
    """

    p4_difficulty_grip_toothbrush: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to adequately grip a toothbrush and brush your teeth?")  # Options: Yes, No
    p4_difficulty_floss_teeth: Optional[str] = Field(default=None, description="Do you have any difficulty using hands/fingers to adequately floss your teeth?")  # Options: Yes, No
    p4_shoulder_pain_brushing: Optional[str] = Field(default=None, description="Does shoulder pain cause you any difficulty brushing and/or flossing your teeth?")  # Options: Yes, No
    p4_difficulty_toothpaste_tube: Optional[str] = Field(default=None, description="Do you have any difficulty holding a toothpaste tube with one hand and using the other hand to open the toothpaste cap?")  # Options: Yes, No
    p4_difficulty_squeeze_toothpaste: Optional[str] = Field(default=None, description="Do you have any difficulty squeezing toothpaste with one hand and holding the toothbrush with the other hand?")  # Options: Yes, No
    p4_difficulty_cut_food: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to cut your food?")  # Options: Yes, No
    p4_difficulty_feed_yourself: Optional[str] = Field(default=None, description="Do you have any difficulty using your hands to feed yourself?")  # Options: Yes, No
    p4_difficulty_raise_arm_comb: Optional[str] = Field(default=None, description="Do you have any difficulty raising up your arm to comb or brush your hair?")  # Options: Yes, No
class P4SubstanceUseHistory(BaseModel):
    """
    Substance Use History
    """

    p4_do_you_smoke: Optional[str] = Field(default=None, description="Do you Smoke?")  # Options: Yes, No
    p4_have_you_smoked: Optional[str] = Field(default=None, description="Have you ever smoked?")  # Options: Yes, No
    p4_when_stop_smoking_months: Optional[int] = Field(default=None, description="When did you stop smoking? (months ago)")
    p4_when_stop_smoking_years: Optional[int] = Field(default=None, description="When did you stop smoking? (years ago)")
    p4_cigarettes_per_day: Optional[int] = Field(default=None, description="How much do you smoke? (cigarettes/day)")
    p4_years_smoker: Optional[int] = Field(default=None, description="How many years were you a smoker?")
    p4_smoking_increase_after_injury: Optional[str] = Field(default=None, description="Did your smoking usage increase after the industrial injury?")  # Options: Yes, No
    p4_cigarettes_per_day_if_yes: Optional[int] = Field(default=None, description="If yes, cigarettes per day")
    p4_drink_alcohol: Optional[str] = Field(default=None, description="Do You Drink Alcohol?")  # Options: Yes, No
    p4_alcohol_how_much: Optional[str] = Field(default=None, description="If yes, How much?")
    p4_use_recreational_drugs: Optional[str] = Field(default=None, description="Do you use recreational drugs?")  # Options: Yes, No
    p4_recreational_drugs_describe: Optional[str] = Field(default=None, description="If yes, describe:")
    p4_used_amphetamines: Optional[str] = Field(default=None, description="Have you used amphetamines?")  # Options: Yes, No
    p4_amphetamines_when: Optional[str] = Field(default=None, description="If yes, When?")
class P4AttestationSignature(BaseModel):
    """
    Attestation and Signature
    """

    p4_patient_signature: str = Field(description="Patient's Signature")
    p4_signature_date: date = Field(description="Date (Format: MM/DD/YYYY)")
class P5P5Header(BaseModel):
    """
    Header Information
    """

    p5_insurance_type: list[str] = Field(default=None, description="Insurance Type")  # Options: PRIVATE, WCAB, QME, PQME, APQME...
    p5_name: Optional[str] = Field(default=None, description="Name")
    p5_gender: Optional[str] = Field(default=None, description="M / F")  # Options: M, F
    p5_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
    p5_interpreter: Optional[str] = Field(default=None, description="Interpreter")
    p5_date_of_injury: Optional[date] = Field(default=None, description="Date of Injury")
    p5_ptp_dr: Optional[str] = Field(default=None, description="PTP: DR")
class P5P5EmploymentHistory(BaseModel):
    """
    Employment History
    """

    p5_employed_at: Optional[str] = Field(default=None, description="Employed at")
    p5_employment_duration_years: Optional[int] = Field(default=None, description="for ___ years")
    p5_employment_duration_months: Optional[int] = Field(default=None, description="months")
    p5_job_title: Optional[str] = Field(default=None, description="Job Title")
    p5_days_per_week: Optional[int] = Field(default=None, description="Worked ___ Days per week")
    p5_hours_per_day: Optional[int] = Field(default=None, description="Worked ___ Hours per day")
    p5_hand_dominant: Optional[str] = Field(default=None, description="Right / Left Hand Dominant")  # Options: Right, Left
    p5_job_duties: Optional[str] = Field(default=None, description="What did patient do at the job?")
    p5_job_requirements_activities: list[str] = Field(default=None, description="Job Requirements - Activities")  # Options: driving, walking, standing, sitting, squatting...
    p5_lifting_maximum: Optional[int] = Field(default=None, description="lifting up to maximum of ___ lbs")
    p5_carrying_maximum: Optional[int] = Field(default=None, description="carrying up to maximum ___ lbs")
    p5_computer_activities: list[str] = Field(default=None, description="Computer Activities")  # Options: typing, using a computer mouse
    p5_mouse_hand: Optional[str] = Field(default=None, description="Mouse Hand (R/L)")  # Options: R, L
    p5_workstation_setup: list[str] = Field(default=None, description="Workstation Setup")  # Options: non-ergonomic, desk, chair, work station, non-fully adjustable chair with non-adjustable arm rest
    p5_monitor_location: Optional[str] = Field(default=None, description="computer monitor located in (F/R/L)")  # Options: F, R, L
    p5_phone_hand: Optional[str] = Field(default=None, description="cradling the phone on (R/L)")  # Options: R, L
    p5_writing_activity: Optional[bool] = Field(default=None, description="writing")
    p5_current_work_status: Optional[str] = Field(default=None, description="Current Work Status")  # Options: Disabled, Still working at the same company, Not Working/Retired
    p5_date_stopped_working: Optional[date] = Field(default=None, description="Date Stopped working")
    p5_current_company: Optional[str] = Field(default=None, description="Presently working at different company")
    p5_current_position: Optional[str] = Field(default=None, description="as")
    p5_current_job_duties: Optional[str] = Field(default=None, description="Job duties")
    p5_current_job_requirements_activities: list[str] = Field(default=None, description="Current Job Requirements - Activities")  # Options: driving, walking, standing, sitting, squatting...
    p5_current_lifting_maximum: Optional[int] = Field(default=None, description="lifting up to maximum of ___ lbs")
    p5_current_carrying_maximum: Optional[int] = Field(default=None, description="carrying up to maximum ___ lbs")
    p5_current_computer_activities: list[str] = Field(default=None, description="Current Computer Activities")  # Options: typing, using a computer mouse
    p5_current_mouse_hand: Optional[str] = Field(default=None, description="Current Mouse Hand (R/L)")  # Options: R, L
    p5_current_workstation_setup: list[str] = Field(default=None, description="Current Workstation Setup")  # Options: non-ergonomic, desk, chair, work station, non-fully adjustable chair with non-adjustable arm rest
    p5_current_monitor_location: Optional[str] = Field(default=None, description="current computer monitor located in (F/R/L)")  # Options: F, R, L
    p5_current_phone_hand: Optional[str] = Field(default=None, description="current cradling the phone on (R/L)")  # Options: R, L
    p5_current_writing_activity: Optional[bool] = Field(default=None, description="current writing")
class P6P6TraumaHistory(BaseModel):
    """
    Trauma History
    """

    p6_doctor_name: Optional[str] = Field(default=None, description="Reviewed History of Trauma with patient as per the report of Dr.")
    p6_report_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class P6P6PatientSignature(BaseModel):
    """
    Patient's Signature
    """

    p6_patient_signature: Optional[str] = Field(default=None, description="Patient's Signature")
    p6_signature_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class P6P6IndustrialInjury(BaseModel):
    """
    History of Industrial Injury
    """

    p6_poor_historian: Optional[str] = Field(default=None, description="(Patient is a Poor Historian: Yes No)")  # Options: Yes, No
    p6_orthopedic_injuries: list[P6OrthopedicInjuriesRow] = Field(default_factory=list, description="Orthopedic Injuries")
class P6P6MvaDetails(BaseModel):
    """
    MVA Details
    If MVA
    """

    p6_vehicle_position: Optional[str] = Field(default=None, description="Driver Passenger Right Rear Seat Left Rear Seat")  # Options: Driver, Passenger, Right Rear Seat, Left Rear Seat
    p6_vehicle_hit_on: Optional[str] = Field(default=None, description="Vehicle Hit On:")  # Options: R, L, Front, Rear
    p6_wearing_seatbelt: Optional[str] = Field(default=None, description="Wearing a seatbelt?")  # Options: Yes, No
    p6_airbag_deployed: Optional[str] = Field(default=None, description="Airbag Deployed?")  # Options: Yes, No
    p6_thrown_about: Optional[str] = Field(default=None, description="Thrown About?")  # Options: Yes, No
    p6_struck_mouth_face: Optional[str] = Field(default=None, description="Struck Mouth Face?")  # Options: Steering Wheel, Door, Window
    p6_struck_back_of_head: Optional[str] = Field(default=None, description="Struck back of head on headrest?")  # Options: Yes, No
    p6_direct_trauma_face_jaw: Optional[str] = Field(default=None, description="Direct Trauma to the Face/Jaw?")  # Options: R, L
    p6_scars: Optional[str] = Field(default=None, description="Scars?")
    p6_fractured_jaw: Optional[str] = Field(default=None, description="Fractured Jaw?")  # Options: Yes, No
    p6_fractured_teeth_count: Optional[int] = Field(default=None, description="Fractured Teeth? #")
    p6_lost_teeth_count: Optional[int] = Field(default=None, description="Lost Teeth? #")
class P7P7WorkRelatedSymptoms(BaseModel):
    """
    Work-Related Symptoms and Stress
    """

    p7_orthopedic_pain_clenching: Optional[bool] = Field(default=None, description="Orthopedic pain causing clenching/bracing of facial muscles")
    p7_stressors_industrial_injuries: Optional[bool] = Field(default=None, description="Developed stressors in response to industrial orthopedic injuries")
    p7_stressors_at_work: list[str] = Field(default=None, description="Stressors at Work")  # Options: Heavy workload, Long or inflexible hours, Tight deadlines, Lack of control, Conflicting or uncertain job expectations...
    p7_clenching_bracing_stress: Optional[bool] = Field(default=None, description="Clenching/Bracing of facial muscles in response to stress")
    p7_bruxism_after_work_pain: Optional[bool] = Field(default=None, description="Did the bruxism begin after the you started having work related pain/stress?")
    p7_days_after: Optional[int] = Field(default=None, description="Days after")
    p7_weeks_after: Optional[int] = Field(default=None, description="Weeks after")
    p7_clenching_day_night: list[str] = Field(default=None, description="Clenching")  # Options: Day, Night
    p7_grinding_day_night: list[str] = Field(default=None, description="Grinding")  # Options: Day, Night
    p7_bracing_day_night: list[str] = Field(default=None, description="Bracing Facial Musculature")  # Options: Day, Night
    p7_bruxism_percent_time: Optional[float] = Field(default=None, description="Bruxism: % of Time")
    p7_bruxism_vas_intensity: Optional[float] = Field(default=None, description="VAS Intensity", ge=0, le=10)
class P7P7PreExistingConditions(BaseModel):
    """
    Pre-Existing Conditions
    """

    p7_headaches_percent_time: Optional[float] = Field(default=None, description="Headaches % of time")
    p7_headaches_intensity_vas: Optional[float] = Field(default=None, description="intensity of Headache on VAS", ge=0, le=10)
    p7_vertex_locations: list[str] = Field(default=None, description="Vertex")  # Options: R Forehead, L Forehead, R Temple, L Temple, R Occiput...
    p7_migraine_diagnosis: Optional[bool] = Field(default=None, description="Have you ever been diagnosed with migraines?")
    p7_migraine_details: Optional[str] = Field(default=None, description="if yes, details")
    p7_facial_pain_locations: list[str] = Field(default=None, description="Facial Pain")  # Options: R, L, B
    p7_facial_pain_percent_time: Optional[float] = Field(default=None, description="% of time")
    p7_facial_pain_intensity_vas: Optional[float] = Field(default=None, description="intensity of Facial Pain on VAS", ge=0, le=10)
    p7_tmj_pain_locations: list[str] = Field(default=None, description="TMJ Pain")  # Options: R, L, B
    p7_tmj_pain_percent_time: Optional[float] = Field(default=None, description="% of time")
    p7_tmj_pain_intensity_vas: Optional[float] = Field(default=None, description="intensity of TMJ Pain on VAS", ge=0, le=10)
    p7_bruxism_percent_time_preexisting: Optional[float] = Field(default=None, description="Bruxism: % of time")
    p7_bruxism_intensity_vas_preexisting: Optional[float] = Field(default=None, description="intensity of Bruxism on VAS", ge=0, le=10)
    p7_nightguard_made: Optional[str] = Field(default=None, description="If a nightguard was made (year made)")
    p7_still_uses_nightguard: Optional[bool] = Field(default=None, description="Still uses a nightguard?")
    p7_nightguard_stop_reason: list[str] = Field(default=None, description="Reason stopped using nightguard?")  # Options: Does not fit, Lost, Wore Out, Broken
    p7_eating_hard_chewy_food: Optional[bool] = Field(default=None, description="Did you have any prior problems eating hard or chewy food?")
    p7_speaking_prolonged_periods: Optional[bool] = Field(default=None, description="Did you have any prior problems speaking for prolonged periods of time?")
class P7P7Attestation(BaseModel):
    """
    Patient Attestation
    """

    p7_patient_signature: Optional[str] = Field(description="Patient's Signature:")
    p7_signature_date: Optional[str] = Field(default=None, description="Date: (Format: MM/DD/YYYY)")
class P7P7TreatmentsReceived(BaseModel):
    """
    Treatments Received Due to the Industrial Injury
    """

    p7_surgery_locations: list[str] = Field(default=None, description="Surgery to:")  # Options: Neck, R Shoulder, L Shoulder, R Arm, L Arm...
    p7_surgery_times: Optional[int] = Field(default=None, description="How many times?")
class P8TxReceived(BaseModel):
    """
    Tx Received
    """

    p8_tx_received: list[str] = Field(default=None, description="Tx Received")  # Options: Physical Therapy, Chiropractic Manipulations, Acupuncture, Injections, Steroid...
    p8_psychological_therapy_evaluated_by: Optional[str] = Field(default=None, description="Psychological Therapy: Evaluated by")
    p8_neurologist_evaluated_by: Optional[str] = Field(default=None, description="Neurologist: Evaluated by")
class P8PriorHistory(BaseModel):
    """
    Prior History
    """

    p8_injuries_after_industrial_date: Optional[str] = Field(default=None, description="Any Injuries After the Date of Industrial Injury (Industrial or Non-Industrial)")
    p8_mva_history: list[P8MvaHistoryRow] = Field(default_factory=list, description="MVA History")
class P9DentalHistory(BaseModel):
    """
    Dental History
    """

    p9_last_dentist_visit: Optional[str] = Field(default=None, description="When was the last time you were seen by a dentist, besides in our office?")  # Options: Years ago, Months ago, Weeks ago, Other, Never
    p9_last_full_mouth_xray: Optional[str] = Field(default=None, description="When was the last time you had Full Mouth X-Ray taken?")
    p9_prior_dentist_names: Optional[str] = Field(default=None, description="To the best of your ability, please list the name(s), addresses and phone numbers of your prior dentist(s):")
    p9_dental_checkup_frequency: Optional[str] = Field(default=None, description="Every: 6 months _______ year")
    p9_last_teeth_cleaning: Optional[str] = Field(default=None, description="Last time patient had teeth cleaned")
    p9_current_dentist_name: Optional[str] = Field(default=None, description="Name of Dentist:")
    p9_current_dentist_phone: Optional[str] = Field(default=None, description="Phone #: (Format: (XXX) XXX-XXXX)")
    p9_current_dentist_address: Optional[str] = Field(default=None, description="Dentist's Address:")
    p9_second_dentist_name: Optional[str] = Field(default=None, description="Name of Dentist:")
    p9_second_dentist_phone: Optional[str] = Field(default=None, description="Phone #: (Format: (XXX) XXX-XXXX)")
    p9_second_dentist_address: Optional[str] = Field(default=None, description="Dentist's Address:")
    p9_post_injury_dentist_name: Optional[str] = Field(default=None, description="If yes, Name of Dentist:")
    p9_post_injury_dentist_phone: Optional[str] = Field(default=None, description="Phone #: (Format: (XXX) XXX-XXXX)")
    p9_dental_treatments_received: Optional[bool] = Field(default=None, description="Dental Treatments Received Since Industrial Injuries:")
    p9_gum_treatments: Optional[bool] = Field(default=None, description="Gum Treatments")
    p9_restorations_location: list[str] = Field(default=None, description="Restorations on teeth in")  # Options: UR, UL, LR, LL
    p9_root_canals_location: list[str] = Field(default=None, description="Root Canals in")  # Options: UR, UL, LR, LL
    p9_crowns_location: list[str] = Field(default=None, description="Crowns in")  # Options: UR, UL, LR, LL
    p9_implants_location: list[str] = Field(default=None, description="Implants in")  # Options: UR, UL, LR, LL
    p9_partial_denture_location: list[str] = Field(default=None, description="Partial Denture")  # Options: Upper, Lower
    p9_complete_denture_location: list[str] = Field(default=None, description="Complete Denture")  # Options: Upper, Lower
    p9_bruxism_appliance_location: list[str] = Field(default=None, description="Bruxism Oral Appliance")  # Options: Upper, Lower
    p9_sleep_appliance_location: list[str] = Field(default=None, description="Oral Sleep Appliance")  # Options: Upper, Lower
    p9_wisdom_teeth_extracted: Optional[bool] = Field(default=None, description="Wisdom teeth")
    p9_other_teeth_extracted: Optional[str] = Field(default=None, description="Teeth #")
    p9_missing_teeth: Optional[str] = Field(default=None, description="Missing Teeth?")
    p9_missing_before_injury: Optional[str] = Field(default=None, description="Prior to the industrial injury?#")
    p9_missing_after_injury: Optional[str] = Field(default=None, description="After the Injury?#")
class P10WeightPhysical(BaseModel):
    """
    Weight and Physical Information
    """

    p10_weight_gain_loss: Optional[float] = Field(default=None, description="Weight Gain Loss (Format: lbs)")
    p10_loss_due_to: Optional[str] = Field(default=None, description="Loss due to")
    p10_facial_pain_diet: Optional[str] = Field(default=None, description="Facial Pain Diet")
    p10_present_weight: Optional[float] = Field(default=None, description="Present Weight (Format: Kg)")
    p10_height: Optional[float] = Field(default=None, description="Height (Format: cm)")
    p10_frame_size: Optional[str] = Field(default=None, description="Frame")  # Options: Small, Medium, Large
class P10SleepSymptoms(BaseModel):
    """
    Sleep Related Symptoms
    """

    p10_snores: Optional[str] = Field(default=None, description="Snores")  # Options: Yes, No, Pre-existing, Aggravated, After Work Injury
    p10_gasps_for_air_at_night: Optional[str] = Field(default=None, description="Gasps for Air at Night")  # Options: Yes, No, Pre-existing, Aggravated, After Work Injury
    p10_palpitations_on_awakening: Optional[str] = Field(default=None, description="Palpitations on Awakening")  # Options: Yes, No, Pre-existing, Aggravated, After Work Injury
    p10_breathing_cessation_at_night: Optional[str] = Field(default=None, description="Breathing Cessation at Night")  # Options: Yes, No, Pre-existing, Aggravated, After Work Injury
    p10_patient_had_sleep_study: Optional[str] = Field(default=None, description="Patient had Sleep Study")
    p10_sleep_study_date: Optional[str] = Field(default=None, description="If yes for sleep study: Date of study")
    p10_patient_diagnosed_sleep_disorder: Optional[str] = Field(default=None, description="Patient diagnosed with a Sleep Disorder")
    p10_patient_does_not_know_results: Optional[str] = Field(default=None, description="Patient does not know results")
    p10_given_mask_during_sleep_study: Optional[str] = Field(default=None, description="Given mask during Sleep Study")
    p10_used_cpap_during_sleep_study: Optional[str] = Field(default=None, description="Used CPAP during Sleep Study")
    p10_patient_given_cpap: Optional[str] = Field(default=None, description="Patient given CPAP")
    p10_patient_uses_cpap_times_per_week: Optional[str] = Field(default=None, description="Patient uses CPAP ___ times per week at night for ___ hours")
    p10_patient_cannot_tolerate_cpap: Optional[str] = Field(default=None, description="Patient cannot tolerate CPAP. X ____")
class P10Headaches(BaseModel):
    """
    Headaches
    """

    p10_headache_location: Optional[str] = Field(default=None, description="Headache Location")  # Options: On Top of Head, Temple R, Temple L, Forehead R, Forehead L...
    p10_headache_frequency: Optional[str] = Field(default=None, description="Headache Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_headache_intensity: Optional[str] = Field(default=None, description="Headache Intensity")  # Options: Minimal, Slight, Moderate, Severe
    p10_headache_characteristics: Optional[str] = Field(default=None, description="Headache Characteristics")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_headache_percent_time: Optional[float] = Field(default=None, description="Headache % of Time (Format: percentage)")
    p10_headache_vas: Optional[int] = Field(default=None, description="Headache VAS")
    p10_headache_started_approx: Optional[str] = Field(default=None, description="Started Approx.")
    p10_bruxism_caused_headaches: Optional[str] = Field(default=None, description="Do you think your bruxism may have caused you to have headaches?")
class P10FacePain(BaseModel):
    """
    Face Pain
    """

    p10_right_face_pain_frequency: Optional[str] = Field(default=None, description="Right Face Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_right_face_pain_intensity: Optional[str] = Field(default=None, description="Right Face Pain Intensity")  # Options: Minimal, Slight, Moderate, Severe
    p10_right_face_pain_characteristics: Optional[str] = Field(default=None, description="Right Face Pain Characteristics")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_right_face_pain_percent_time: Optional[float] = Field(default=None, description="Right Face Pain % of Time (Format: percentage)")
    p10_right_face_pain_vas: Optional[int] = Field(default=None, description="Right Face Pain VAS")
    p10_left_face_pain_frequency: Optional[str] = Field(default=None, description="Left Face Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_left_face_pain_intensity: Optional[str] = Field(default=None, description="Left Face Pain Intensity")  # Options: Minimal, Slight, Moderate, Severe
    p10_left_face_pain_characteristics: Optional[str] = Field(default=None, description="Left Face Pain Characteristics")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_left_face_pain_percent_time: Optional[float] = Field(default=None, description="Left Face Pain % of Time (Format: percentage)")
    p10_left_face_pain_vas: Optional[int] = Field(default=None, description="Left Face Pain VAS")
    p10_left_face_pain_started_approx: Optional[str] = Field(default=None, description="Left Face Pain Started Approx.")
    p10_bruxism_caused_face_pain: Optional[str] = Field(default=None, description="Do you think your bruxism may have caused you to have face pain?")
class P10TmjSymptoms(BaseModel):
    """
    TMJ Symptoms
    """

    p10_noises_in_tmj: Optional[str] = Field(default=None, description="Noises in TMJ")  # Options: R, L, Grinding, Clicking
    p10_tmj_noise_started_approx: Optional[str] = Field(default=None, description="TMJ Noise Started Approx.")
    p10_pre_injury_tmj_noise_vas: Optional[int] = Field(default=None, description="Pre-Injury / TMJ Noise VAS")
    p10_post_injury_tmj_noise_vas: Optional[int] = Field(default=None, description="Post Injury / TMJ Noise VAS")
    p10_right_tmj_pain_frequency: Optional[str] = Field(default=None, description="Right TMJ Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_right_tmj_pain_intensity: Optional[str] = Field(default=None, description="Right TMJ Pain Intensity")  # Options: Minimal, Slight, Moderate, Severe
    p10_right_tmj_pain_characteristics: Optional[str] = Field(default=None, description="Right TMJ Pain Characteristics")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_right_tmj_pain_percent_time: Optional[float] = Field(default=None, description="Right TMJ Pain % of Time (Format: percentage)")
    p10_right_tmj_pain_vas: Optional[int] = Field(default=None, description="Right TMJ Pain VAS")
    p10_left_tmj_pain_frequency: Optional[str] = Field(default=None, description="Left TMJ Pain Frequency")  # Options: Occasional, Intermittent, Frequent, Constant
    p10_left_tmj_pain_intensity: Optional[str] = Field(default=None, description="Left TMJ Pain Intensity")  # Options: Minimal, Slight, Moderate, Severe
    p10_left_tmj_pain_characteristics: Optional[str] = Field(default=None, description="Left TMJ Pain Characteristics")  # Options: Dull, Aching, Burning, Stabbing, Electrical...
    p10_left_tmj_pain_percent_time: Optional[float] = Field(default=None, description="Left TMJ Pain % of Time (Format: percentage)")
    p10_left_tmj_pain_vas: Optional[int] = Field(default=None, description="Left TMJ Pain VAS")
    p10_left_tmj_pain_started_approx: Optional[str] = Field(default=None, description="Left TMJ Pain Started Approx.")
class P11P11MouthJawSymptoms(BaseModel):
    """
    Mouth and Jaw Symptoms
    """

    p11_limited_opening_mouth: Optional[str] = Field(default=None, description="Limited Opening of the Mouth")
    p11_locking: Optional[str] = Field(default=None, description="Locking")
    p11_closed_times_per_day: Optional[str] = Field(default=None, description="Closed _____ X per day")
    p11_closed_frequency_unit: Optional[str] = Field(default=None, description="Closed frequency unit")  # Options: day, wk, month
    p11_open_times_per_day: Optional[str] = Field(default=None, description="Open _____ X per day")
    p11_open_frequency_unit: Optional[str] = Field(default=None, description="Open frequency unit")  # Options: day, wk, month
    p11_first_locked: Optional[str] = Field(default=None, description="First locked")
    p11_can_self_manipulate_jaw: Optional[str] = Field(default=None, description="Can self-manipulate Jaw to unlock?")
    p11_difficult_chew_hard_food: Optional[str] = Field(default=None, description="Difficult and painful to chew hard food:")  # Options: Face, TMJ, Teeth
    p11_difficult_chew_side: Optional[str] = Field(default=None, description="Difficult and painful to chew hard food side")  # Options: R, L
    p11_bite_feels_off: Optional[str] = Field(default=None, description="Bite feels off")
    p11_facial_pain: Optional[str] = Field(default=None, description="Facial Pain")  # Options: Smiling, Yawning
    p11_soreness_teeth_morning: Optional[str] = Field(default=None, description="Soreness of teeth upon waking up in the morning?")
    p11_soreness_face_jaw_awakening: Optional[str] = Field(default=None, description="Soreness in Face/Jaw Upon Awakening?")
    p11_soreness_face_jaw_side: Optional[str] = Field(default=None, description="Soreness in Face/Jaw side")  # Options: R, L
    p11_teeth_sensitive_hot_cold: Optional[str] = Field(default=None, description="Teeth are sensitive to hot and cold?")
    p11_bleeding_gums: Optional[str] = Field(default=None, description="Bleeding Gums?")
class P11P11SpeechHearing(BaseModel):
    """
    Speech and Hearing Issues
    """

    p11_speech_dysfunction: Optional[str] = Field(default=None, description="Speech Dysfunction")  # Options: Indistinct Articulation, Hoarseness, Cotton Mouth, Missing Upper Anterior Teeth, Cannot Talk for Long Periods of Time Due to Pain...
    p11_can_speak_max_time: Optional[str] = Field(default=None, description="Can Speak Max. Time ___ Minutes")
    p11_voice_changes: Optional[str] = Field(default=None, description="Voice Changes In:")  # Options: Tone, Pitch, Slurring, Drooling, People Asking Patient To Repeat Themselves
    p11_ear_problems: Optional[str] = Field(default=None, description="Ear Problems")  # Options: R, L, Both, Ringing, Pain...
class P11P11GeneralSymptoms(BaseModel):
    """
    General Symptoms
    """

    p11_sleep_disturbances: Optional[str] = Field(default=None, description="Sleep Disturbances")
    p11_fatigue: Optional[str] = Field(default=None, description="Fatigue")
    p11_generalized_tenderness: Optional[str] = Field(default=None, description="Generalized tenderness all over the body?")
    p11_stress_increases_pain: Optional[str] = Field(default=None, description="Stress Increases Pain?")
    p11_prior_injuries_face_jaw: Optional[str] = Field(default=None, description="Prior Injuries to Face / Jaw")
class P12P12FacialPainActivities(BaseModel):
    """
    Activities of Daily Living VAS
    """

    p12_hard_chewy_food_pain: Optional[str] = Field(default=None, description="If your facial pain is aggravated by eating hard or chewy food, what is your pain level?")  # Options: YES, NO
    p12_hard_chewy_food_vas: Optional[int] = Field(default=None, description="VAS pain level for hard or chewy food", ge=0, le=100)
    p12_prolonged_speaking_pain: Optional[str] = Field(default=None, description="If your face pain is aggravated by prolonged speaking, what is your pain level?")  # Options: YES, NO
    p12_prolonged_speaking_vas: Optional[int] = Field(default=None, description="VAS pain level for prolonged speaking", ge=0, le=100)
    p12_max_speak_time: Optional[int] = Field(default=None, description="Maximum time able to speak continuously - Min")
    p12_repeat_not_understand: Optional[str] = Field(default=None, description="People ask you to repeat yourself because they do not understand you?")  # Options: YES, NO
    p12_repeat_not_understand_vas: Optional[int] = Field(default=None, description="VAS level for people not understanding", ge=0, le=100)
    p12_kissing_pain: Optional[str] = Field(default=None, description="Is your facial pain aggravated by intense kissing?")  # Options: YES, NO
    p12_kissing_vas: Optional[int] = Field(default=None, description="VAS pain level for kissing", ge=0, le=100)
    p12_sleep_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to get enough sleep?")  # Options: YES, NO
    p12_sleep_interference_vas: Optional[int] = Field(default=None, description="VAS level for sleep interference", ge=0, le=100)
    p12_sleeping_pressure: Optional[str] = Field(default=None, description="Does the pressure on your face while you are sleeping result in face or jaw pain?")  # Options: YES, NO
    p12_social_activities: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to participate in social activities?")  # Options: YES, NO
    p12_social_activities_vas: Optional[int] = Field(default=None, description="VAS level for social activities interference", ge=0, le=100)
    p12_relationship_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere in your relationship with your family members or significant other?")  # Options: YES, NO
    p12_relationship_vas: Optional[int] = Field(default=None, description="VAS level for relationship interference", ge=0, le=100)
    p12_concentrate_interference: Optional[str] = Field(default=None, description="Does your facial pain interfere with your ability to concentrate?")  # Options: YES, NO
    p12_concentrate_vas: Optional[int] = Field(default=None, description="VAS level for concentration interference", ge=0, le=100)
    p12_irritable_angry: Optional[str] = Field(default=None, description="Does your facial pain cause you to be irritable/angry?")  # Options: YES, NO
    p12_irritable_angry_vas: Optional[int] = Field(default=None, description="VAS level for irritability/anger", ge=0, le=100)
    p12_stress: Optional[str] = Field(default=None, description="Does your facial pain cause you to experience stress?")  # Options: YES, NO
    p12_stress_vas: Optional[int] = Field(default=None, description="VAS level for stress", ge=0, le=100)
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
    p12_hard_foods_avoid: Optional[str] = Field(default=None, description="Hard Foods: You must stay away from eating hard foods which includes: - Tough meats, hard bread, nuts, apples, carrots, crunchy vegetables, hard candy")  # Options: YES, NO
    p12_chewy_foods_avoid: Optional[str] = Field(default=None, description="Chewy Foods: You must stay away eating chewy foods which includes: - Chewing gum, steak, pizza crusts, and bagels; candies like: taffy, caramel, licorice, gummy bears")  # Options: YES, NO
    p12_soft_foods_only: Optional[str] = Field(default=None, description="Soft Foods: You can only eat soft or liquid type foods with the consistency of scrambled eggs or less.")  # Options: YES, NO
class P13SelfCareHygiene(BaseModel):
    """
    Self-Care Hygiene
    """

    p13_brushing_teeth_severity: Optional[str] = Field(default=None, description="Brushing Teeth")  # Options: None, Mild, Moderate, Severe
    p13_flossing_teeth_severity: Optional[str] = Field(default=None, description="Flossing Teeth")  # Options: None, Mild, Moderate, Severe
class P13Communication(BaseModel):
    """
    Communication
    """

    p13_speak_extended_period_severity: Optional[str] = Field(default=None, description="Speak for Extended Period of Time")  # Options: None, Mild, Moderate, Severe
    p13_max_time_speak: Optional[int] = Field(default=None, description="Max Time Speak ______Min (Format: Minutes)")
    p13_speaking_difficulty_severity: Optional[str] = Field(default=None, description="Speaking Difficulty")  # Options: None, Mild, Moderate, Severe
    p13_asked_to_repeat_severity: Optional[str] = Field(default=None, description="Asked to Repeat Themselves")  # Options: None, Mild, Moderate, Severe
class P13MotorFunction(BaseModel):
    """
    Motor Function
    """

    p13_mastication_severity: Optional[str] = Field(default=None, description="Mastication")  # Options: None, Mild, Moderate, Severe
    p13_tasting_severity: Optional[str] = Field(default=None, description="Tasting")  # Options: None, Mild, Moderate, Severe
    p13_tasting_vas: Optional[int] = Field(default=None, description="VAS ____", ge=0, le=100)
    p13_tasting_taste_change: Optional[str] = Field(default=None, description="Due to dryness of the mouth causing a change in taste")  # Options: Bitter, Metallic, Bland
    p13_swallowing_severity: Optional[str] = Field(default=None, description="Swallowing")  # Options: None, Mild, Moderate, Severe
class P13Bruxism(BaseModel):
    """
    Bruxism
    """

    p13_bruxism_severity: Optional[str] = Field(default=None, description="Bruxism")  # Options: None, Mild, Moderate, Severe
class P13SexualFunction(BaseModel):
    """
    Sexual Function
    """

    p13_kissing_oral_activities_severity: Optional[str] = Field(default=None, description="Kissing, Oral Activities")  # Options: None, Mild, Moderate, Severe
class P14P14ClinicalExam(BaseModel):
    """
    Clinical Examination
    """

    p14_unspecified_rheumat: Optional[str] = Field(default=None, description="Unspecified Rheumat.")  # Options: Yes, No
    p14_tender_phalanges: list[str] = Field(default=None, description="Tender Phalanges")  # Options: R, L
    p14_multiple_tender_points: Optional[bool] = Field(default=None, description="Multiple Tender Points")
    p14_sleep_disturbances: Optional[bool] = Field(default=None, description="Sleep Disturbances")
    p14_fatigue: Optional[bool] = Field(default=None, description="Fatigue")
    p14_facial_palsy: list[str] = Field(default=None, description="Facial Palsy")  # Options: Right, Left
    p14_facial_atrophy: list[str] = Field(default=None, description="Facial Atrophy")  # Options: Right, Left
    p14_facial_hypertrophy: list[str] = Field(default=None, description="Facial Hypertrophy")  # Options: Right, Left
    p14_dyskinesia: Optional[str] = Field(default=None, description="Dyskinesia")  # Options: Yes, No
    p14_tongue_protrusion: list[str] = Field(default=None, description="Tongue Protrusion")  # Options: Right, Left, Straight
class P14P14RangeOfMotion(BaseModel):
    """
    Range of Motion
    """

    p14_max_interincisal_opening: Optional[float] = Field(default=None, description="Maximum Interincisal Opening (Format: number in mm)")
    p14_max_opening_pain_side: list[str] = Field(default=None, description="Maximum Opening Pain Side")  # Options: R, L, Face, TMJ
    p14_max_opening_vas: Optional[int] = Field(default=None, description="Maximum Opening VAS", ge=0, le=10)
    p14_right_lateral: Optional[float] = Field(default=None, description="Right Lateral (Format: number in mm)")
    p14_right_lateral_pain_side: list[str] = Field(default=None, description="Right Lateral Pain Side")  # Options: R, L, Face, TMJ
    p14_right_lateral_vas: Optional[int] = Field(default=None, description="Right Lateral VAS", ge=0, le=10)
    p14_left_lateral: Optional[float] = Field(default=None, description="Left Lateral (Format: number in mm)")
    p14_left_lateral_pain_side: list[str] = Field(default=None, description="Left Lateral Pain Side")  # Options: R, L, Face, TMJ
    p14_left_lateral_vas: Optional[int] = Field(default=None, description="Left Lateral VAS", ge=0, le=10)
    p14_protrusion: Optional[float] = Field(default=None, description="Protrusion (Format: number in mm)")
    p14_protrusion_pain_side: list[str] = Field(default=None, description="Protrusion Pain Side")  # Options: R, L, Face, TMJ
    p14_protrusion_vas: Optional[int] = Field(default=None, description="Protrusion VAS", ge=0, le=10)
class P14P14JawDeviation(BaseModel):
    """
    Jaw Deviation
    """

    p14_deflection: Optional[bool] = Field(default=None, description="Deflection")
    p14_opening: Optional[bool] = Field(default=None, description="Opening")
    p14_closing: Optional[bool] = Field(default=None, description="Closing")
    p14_deviation_side: list[str] = Field(default=None, description="Deviation Side")  # Options: R, L
    p14_deviation_mm: Optional[float] = Field(default=None, description="Deviation in mm (Format: number in mm)")
    p14_s_form_deviation: list[str] = Field(default=None, description="S-Form Deviation")  # Options: R, L
class P14P14Capsulitis(BaseModel):
    """
    Capsulitis
    """

    p14_capsulitis: Optional[str] = Field(default=None, description="Capsulitis")  # Options: Yes, No
    p14_right_lateral_pole_pain: Optional[float] = Field(default=None, description="Right Lateral Pole Pain")
    p14_right_lateral_pole_vas: Optional[int] = Field(default=None, description="Right Lateral Pole VAS", ge=0, le=10)
    p14_left_lateral_pole_pain: Optional[float] = Field(default=None, description="Left Lateral Pole Pain")
    p14_left_lateral_pole_vas: Optional[int] = Field(default=None, description="Left Lateral Pole VAS", ge=0, le=10)
    p14_right_via_eam_pain: Optional[float] = Field(default=None, description="Right VIA EAM Pain")
    p14_right_via_eam_vas: Optional[int] = Field(default=None, description="Right VIA EAM VAS", ge=0, le=10)
    p14_left_via_eam_pain: Optional[float] = Field(default=None, description="Left VIA EAM Pain")
    p14_left_via_eam_vas: Optional[int] = Field(default=None, description="Left VIA EAM VAS", ge=0, le=10)
class P14P14JointNoises(BaseModel):
    """
    Joint Noises (Manual)
    """

    p14_joint_noises_right: Optional[bool] = Field(default=None, description="Joint Noises Right")
    p14_joint_noises_left: Optional[bool] = Field(default=None, description="Joint Noises Left")
    p14_crepitus: Optional[bool] = Field(default=None, description="Crepitus")
    p14_clicking: Optional[bool] = Field(default=None, description="Clicking")
    p14_translational: Optional[bool] = Field(default=None, description="Translational")
    p14_lateral: Optional[bool] = Field(default=None, description="Lateral")
class P15P15DentalClassification(BaseModel):
    """
    Dental Classification
    """

    p15_class: Optional[str] = Field(default=None, description="Class I II III")  # Options: I, II, III
    p15_overbite: Optional[float] = Field(default=None, description="Overbite _____ mm")
    p15_overjet: Optional[float] = Field(default=None, description="Overjet _____ mm")
    p15_midline_deviation: Optional[str] = Field(default=None, description="Midline Deviation _____ mm R L")
class P15P15BiteOcclusion(BaseModel):
    """
    Bite and Occlusion
    """

    p15_crossbite: Optional[str] = Field(default=None, description="Crossbite Ant. R L")  # Options: Ant., R, L
    p15_open_bite: Optional[str] = Field(default=None, description="Open Bite Ant. R L")  # Options: Ant., R, L
    p15_tongue_thrust: Optional[str] = Field(default=None, description="Tongue Thrust Ant. R L Both Sides")  # Options: Ant., R, L, Both Sides
    p15_bite_type: Optional[str] = Field(default=None, description="Closed Bite Collapsed Bite Unstable Bite")  # Options: Closed Bite, Collapsed Bite, Unstable Bite
    p15_tori: Optional[str] = Field(default=None, description="Tori Max Man")  # Options: Max, Man
class P15P15OralConditions(BaseModel):
    """
    Oral Conditions
    """

    p15_scalloping: Optional[str] = Field(default=None, description="Scalloping Right Left Minimal Slight Moderate Significant")  # Options: Right, Left, Minimal, Slight, Moderate...
    p15_buccal_mucosal_ridging: Optional[str] = Field(default=None, description="Buccal Mucosal Ridging Right Left Minimal Slight Moderate Significant")  # Options: Right, Left, Minimal, Slight, Moderate...
    p15_occlusal_wear: Optional[str] = Field(default=None, description="Occlusal Wear None Apparent Right Left Ant. Minimal Slight Moderate Significant")  # Options: None Apparent, Right, Left, Ant., Minimal...
class P15P15PatientHistory(BaseModel):
    """
    Patient History
    """

    p15_patient_has: Optional[str] = Field(default=None, description="Patient Has: FUD FLD UPD LPD")  # Options: FUD, FLD, UPD, LPD
    p15_fractured_dentures: Optional[str] = Field(default=None, description="Fractured Dentures Upper Lower Full Partial")  # Options: Upper, Lower, Full, Partial
class P15P15ToothConditions(BaseModel):
    """
    Tooth Conditions
    """

    p15_abractions_teeth: list[str] = Field(default=None, description="Abractions on Teeth # 2 3 4 5 6 7 8 9 10 11 12 13 14 15 18 19 20 21 22 23 24 25 26 27 28 29 30 31")  # Options: 2, 3, 4, 5, 6...
    p15_missing_teeth: list[str] = Field(default=None, description="Missing Teeth # 2 3 4 5 6 7 8 9 10 11 12 13 14 15 18 19 20 21 22 23 24 25 26 27 28 29 30 31")  # Options: 2, 3, 4, 5, 6...
    p15_missing_third_molars: list[str] = Field(default=None, description="Missing Third Molars #1 16 17 32")  # Options: 1, 16, 17, 32
    p15_gum_recession_teeth: list[str] = Field(default=None, description="Gum Recession Teeth # 2 3 4 5 6 7 8 9 10 11 12 13 14 15 18 19 20 21 22 23 24 25 26 27 28 29 30 31")  # Options: 2, 3, 4, 5, 6...
    p15_fractured_teeth: Optional[str] = Field(default=None, description="Fractured Teeth #")
    p15_fractured_bridge_crowns: Optional[str] = Field(default=None, description="Fractured Bridge or Crowns #")
    p15_visually_apparent_decayed_teeth: Optional[str] = Field(default=None, description="Visually Apparent Decayed Teeth #")
    p15_broken_dental_filling: Optional[str] = Field(default=None, description="Broken Dental Filling #")
    p15_teeth_sensitive_percussion: Optional[str] = Field(default=None, description="Teeth Sensitive to Percussion #")
    p15_teeth_sensitive_palpation: Optional[str] = Field(default=None, description="Teeth sensitive to Periapical Palpation #")
    p15_teeth_with_mobility: Optional[str] = Field(default=None, description="Teeth with Mobility #")
class P15P15GumConditions(BaseModel):
    """
    Gum Conditions
    """

    p15_bleeding_gums: Optional[str] = Field(default=None, description="Bleeding Gums")  # Options: Yes, No
    p15_inflamed_gingiva: Optional[str] = Field(default=None, description="Inflamed Gingiva")  # Options: Yes, No
    p15_scars_detail: Optional[str] = Field(default=None, description="Scars? Detail:")
class P15P15MalampatiFriedman(BaseModel):
    """
    Classifications
    """

    p15_malampati: Optional[str] = Field(default=None, description="Malampati:")
    p15_friedman: Optional[str] = Field(default=None, description="Friedman:")
class P16DiagnosticTests(BaseModel):
    """
    Diagnostic Tests
    """

    p16_blood_pressure_systolic: Optional[int] = Field(default=None, description="Blood Pressure (systolic)")
    p16_blood_pressure_diastolic: Optional[int] = Field(default=None, description="Blood Pressure (diastolic)")
    p16_click_opening_r: Optional[str] = Field(default=None, description="Click Opening R")
    p16_click_opening_l: Optional[str] = Field(default=None, description="Click Opening L")
    p16_click_opening_rrl: Optional[str] = Field(default=None, description="Click Opening RRL")
    p16_click_opening_rll: Optional[str] = Field(default=None, description="Click Opening RLL")
    p16_click_closing_r: Optional[str] = Field(default=None, description="Click Closing R")
    p16_click_closing_l: Optional[str] = Field(default=None, description="Click Closing L")
    p16_click_closing_lrl: Optional[str] = Field(default=None, description="Click Closing LRL")
    p16_click_closing_lll: Optional[str] = Field(default=None, description="Click Closing LLL")
    p16_no_clicking_auscultated: Optional[bool] = Field(default=None, description="No Clicking was Auscultated")
    p16_damage_translation_r: Optional[str] = Field(default=None, description="Damage Translation R")
    p16_damage_translation_l: Optional[str] = Field(default=None, description="Damage Translation L")
    p16_damage_lateral_r: Optional[str] = Field(default=None, description="Damage Lateral R")
    p16_damage_lateral_l: Optional[str] = Field(default=None, description="Damage Lateral L")
    p16_r_temporalis_temp: Optional[float] = Field(default=None, description="R Temporalis Temperature")
    p16_l_temporalis_temp: Optional[float] = Field(default=None, description="L Temporalis Temperature")
    p16_r_masseter_temp: Optional[float] = Field(default=None, description="R Masseter Temperature")
    p16_l_masseter_temp: Optional[float] = Field(default=None, description="L Masseter Temperature")
    p16_r_scm_temp: Optional[float] = Field(default=None, description="R SCM Temperature")
    p16_l_scm_temp: Optional[float] = Field(default=None, description="L SCM Temperature")
    p16_r_trapezius_temp: Optional[float] = Field(default=None, description="R Trapezius Temperature")
    p16_l_trapezius_temp: Optional[float] = Field(default=None, description="L Trapezius Temperature")
    p16_bite_force_right: Optional[float] = Field(default=None, description="Diagnostic Bite Force Analysis Right (Format: Newtons)")
    p16_bite_force_left: Optional[float] = Field(default=None, description="Diagnostic Bite Force Analysis Left (Format: Newtons)")
    p16_right_masseter_v_rest: Optional[float] = Field(default=None, description="Right Masseter μV Rest")
    p16_left_masseter_v_rest: Optional[float] = Field(default=None, description="Left Masseter μV Rest")
    p16_right_masseter_v_contraction: Optional[float] = Field(default=None, description="Right Masseter μV Contraction")
    p16_left_masseter_v_contraction: Optional[float] = Field(default=None, description="Left Masseter μV Contraction")
    p16_right_masseter_v_peak: Optional[float] = Field(default=None, description="Right Masseter μV Peak")
    p16_left_masseter_v_peak: Optional[float] = Field(default=None, description="Left Masseter μV Peak")
    p16_right_temporalis_v_rest: Optional[float] = Field(default=None, description="Right Temporalis μV Rest")
    p16_left_temporalis_v_rest: Optional[float] = Field(default=None, description="Left Temporalis μV Rest")
    p16_right_temporalis_v_contraction: Optional[float] = Field(default=None, description="Right Temporalis μV Contraction")
    p16_left_temporalis_v_contraction: Optional[float] = Field(default=None, description="Left Temporalis μV Contraction")
    p16_right_temporalis_v_peak: Optional[float] = Field(default=None, description="Right Temporalis μV Peak")
    p16_left_temporalis_v_peak: Optional[float] = Field(default=None, description="Left Temporalis μV Peak")
    p16_elevated_muscular_activity: Optional[str] = Field(default=None, description="Elevated Muscular Activity")  # Options: Yes, No
    p16_incoordination_aberrant_function: Optional[str] = Field(default=None, description="Incoordination/Aberrant Function")  # Options: Yes, No
    p16_before_o2: Optional[str] = Field(default=None, description="Before O2")
    p16_before_pulse: Optional[int] = Field(default=None, description="Before Pulse")
    p16_after_o2: Optional[str] = Field(default=None, description="After O2")
    p16_after_pulse: Optional[int] = Field(default=None, description="After Pulse")
    p16_amylase_test: Optional[str] = Field(default=None, description="Amylase Test")
class P16SalivaryDiagnostic(BaseModel):
    """
    Salivary Diagnostic Testing
    """

    p16_tissue_analysis_lips: Optional[str] = Field(default=None, description="Tissue Analysis of Lips")  # Options: Dry, Cracked, Wet
    p16_tissue_analysis_tongue: Optional[str] = Field(default=None, description="Tissue Analysis of Tongue")  # Options: Fissuring, Dry, White Patches
    p16_quality_of_saliva: Optional[str] = Field(default=None, description="Quality of Saliva")  # Options: Cloudy, Ropey, Viscous, Bloody
    p16_saliva_pooling_floor_mouth: Optional[str] = Field(default=None, description="Saliva Pooling at Floor of Mouth")  # Options: Yes, No
    p16_adherence_tongue_depressor: Optional[str] = Field(default=None, description="Adherence of Tongue Depressor on inside of cheek")  # Options: Yes, No
    p16_salivary_flow_unstimulated: Optional[str] = Field(default=None, description="Salivary Flow Unstimulated")  # Options: Less than 0.1mL, Greater than 0.1mL
    p16_salivary_flow_stimulated: Optional[str] = Field(default=None, description="Salivary Flow Stimulated")  # Options: Less than 0.5mL, Greater than 0.5mL
    p16_salivary_ph_analysis: Optional[str] = Field(default=None, description="Salivary pH Analysis")
    p16_gingival_bleeding: Optional[str] = Field(default=None, description="Gingival Bleeding")  # Options: Yes, No
class P17P17AnatomicalFindings(BaseModel):
    """
    Anatomical Findings
    """

    p17_lips: Optional[str] = Field(default=None, description="LIPS")  # Options: Upper, Lower, Vermillion Border, Commissure
    p17_cheeks: Optional[str] = Field(default=None, description="CHEEKS")  # Options: Right, Left
    p17_gingivoperio: Optional[str] = Field(default=None, description="GINGIVOPERIO")  # Options: Free Gingiva, Attached Gingiva
    p17_facial_pillars: Optional[str] = Field(default=None, description="FACIAL PILLARS")  # Options: Right Posterior, Right Anterior, Left Anterior, Left Posterior
    p17_palate: Optional[str] = Field(default=None, description="PALATE")  # Options: Hard, Soft
    p17_tongue: Optional[str] = Field(default=None, description="TONGUE")  # Options: Dorsum, Right Lateral Border, Left Lateral Border, Ventral
    p17_floor: Optional[str] = Field(default=None, description="FLOOR")  # Options: Wharton's Duct
    p17_clinical_impression: Optional[str] = Field(default=None, description="Clinical Impression")
class P17P17Diagnosis(BaseModel):
    """
    Diagnosis
    """

    p17_s09_93xa: Optional[str] = Field(default=None, description="S09.93XA Traumatic Injury to Face Mandible Teeth #")
    p17_g51_0: Optional[str] = Field(default=None, description="G51.0 Facial Palsy Right Left")  # Options: Right, Left
    p17_g50_0: Optional[str] = Field(default=None, description="G50.0 Trigeminal Nerve Neuropathic Pain / Central Sensitization")
    p17_f45_8: Optional[str] = Field(default=None, description="F45.8 Bruxism")
    p17_m79_1: Optional[str] = Field(default=None, description="M79.1 Myalgia of Facial Muscles")
    p17_m65_80: Optional[str] = Field(default=None, description="M65.80 Capsulitis / Inflammation Right Left")  # Options: Right, Left
    p17_m26_69_derangement: Optional[str] = Field(default=None, description="M26.69 Internal Derangement Right Left")  # Options: Right, Left
    p17_m26_69_osteoarthrosis: Optional[str] = Field(default=None, description="M26.69 Osteoarthrosis Right Left")  # Options: Right, Left
    p17_m26_69_osteoarthritis: Optional[str] = Field(default=None, description="M26.69 Osteoarthritis Right Left")  # Options: Right, Left
    p17_k11_7: Optional[str] = Field(default=None, description="K11.7 Xerostomia")
    p17_k05_6: Optional[str] = Field(default=None, description="K05.6 Inflammation of the Gums")
    p17_g51_0_halitosis: Optional[str] = Field(default=None, description="G51.0 Halitosis / Oral Malodor")
    p17_r19_6: Optional[str] = Field(default=None, description="R19.6 Suggestions of an Unspecified Rheumatological / Systemic Condition")
    p17_other_line1: Optional[str] = Field(default=None, description="Other:")
    p17_other_line2: Optional[str] = Field(default=None, description="Other (continued)")
    p17_dfv: Optional[str] = Field(default=None, description="DFV")
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
class P19P19LateralBorderTongue(BaseModel):
    """
    Lateral Border of the Tongue Scalloping
    """

    p19_lateral_border_tongue_scalloping: list[str] = Field(default=None, description="Lateral Border of the Tongue Scalloping")  # Options: Right, Left
class P19P19BuccalMucosal(BaseModel):
    """
    Buccal Mucosal Ridging
    """

    p19_buccal_mucosal_ridging: list[str] = Field(default=None, description="Buccal Mucosal Ridging")  # Options: Right, Left
class P19P19OcclusalWear(BaseModel):
    """
    Occlusal Wear
    """

    p19_occlusal_wear: list[str] = Field(default=None, description="Occlusal Wear")  # Options: Anterior, Generalized
class P19P19OralFindings(BaseModel):
    """
    Oral Findings
    """

    p19_bleeding_on_flossing: Optional[str] = Field(default=None, description="Bleeding on Flossing")
    p19_tongue_blades_adhering: Optional[str] = Field(default=None, description="Tongue Blades adhering to inside of cheeks")
    p19_erosion: Optional[str] = Field(default=None, description="Erosion")  # Options: Class I, II, III, Occlusion
    p19_abfractions: Optional[str] = Field(default=None, description="Abfractions")
    p19_cervical_decay: Optional[str] = Field(default=None, description="Cervical Decay")
    p19_generalized_decay: Optional[str] = Field(default=None, description="Generalized Decay")
    p19_biofilm_on_teeth: Optional[str] = Field(default=None, description="Biofilm on Teeth")
    p19_biofilm_on_gums: Optional[str] = Field(default=None, description="Biofilm on Gums")
    p19_swollen_gums: Optional[str] = Field(default=None, description="Swollen Gums")
    p19_gum_recession: Optional[str] = Field(default=None, description="Gum Recession")
    p19_maxillary_torus: Optional[str] = Field(default=None, description="Maxillary Torus")
    p19_mandibular_tori: Optional[str] = Field(default=None, description="Mandibular Tori")
class P19P19Asymmetries(BaseModel):
    """
    Asymmetries and Deviations
    """

    p19_deviation_tongue_protrusion: list[str] = Field(default=None, description="Deviation of Tongue on Protrusion")  # Options: Right, Left
    p19_deviation_mandible_opening: list[str] = Field(default=None, description="Deviation of Mandible Upon Opening")  # Options: Right, Left
    p19_facial_palsy: list[str] = Field(default=None, description="Facial Palsy")  # Options: Right, Left
class P19P19DentalConditions(BaseModel):
    """
    Dental and Prosthetic Conditions
    """

    p19_broken_porcelain_bridge: Optional[str] = Field(default=None, description="Broken Porcelain on Bridge")
    p19_broken_denture: Optional[str] = Field(default=None, description="Broken Denture")
    p19_missing_broken_teeth: Optional[str] = Field(default=None, description="Missing / Broken Teeth #")
class P19P19BiteConditions(BaseModel):
    """
    Bite Conditions
    """

    p19_open_bite: list[str] = Field(default=None, description="Open Bite")  # Options: Anterior, Right, Left
    p19_cross_bite: list[str] = Field(default=None, description="Cross Bite")  # Options: Anterior, Right, Left
    p19_collapsed_bite: list[str] = Field(default=None, description="Collapsed Bite")  # Options: Unstable Bite, Off Bite
    p19_facial_scarring: Optional[str] = Field(default=None, description="Facial Scarring")
class P19P19MuscleConditions(BaseModel):
    """
    Muscle and Tongue Conditions
    """

    p19_hypertrophy_masseter: list[str] = Field(default=None, description="Hypertrophy of Masseter Muscle")  # Options: Right, Left, Bilateral
    p19_tongue_trust: list[str] = Field(default=None, description="Tongue Trust")  # Options: Anterior, Lateral, Right, Left
class P19P19OtherConditions(BaseModel):
    """
    Other Conditions
    """

    p19_orthodontic_brackets: Optional[str] = Field(default=None, description="Orthodontic Brackets")
    p19_fibroma: Optional[str] = Field(default=None, description="Fibroma")
    p19_leukoplakia: Optional[str] = Field(default=None, description="Leukoplakia")
class P20TreatmentPlanSection(BaseModel):
    """
    Treatment Plan
    """

    p20_treatment_options: list[str] = Field(default=None, description="Treatment Plan Options")  # Options: Orthotic Appliance / Resilient Orthotic OAOA OSA TRD Diagnostic Splint, Craniofacial Exercises, Trigger Point Injections, Sphenopalatine Ganglion Blocks, Trigeminal Pharyngoplasty...
    p20_consultations_needed: list[str] = Field(default=None, description="Consultations and Studies Needed")  # Options: Sleep Study Report Needed, Polysomnogram Needed, Physical Therapy Treatment Needed, Psychological Consultation Needed, Neurological Care Needed...
    p20_plastic_surgery_detail: Optional[str] = Field(default=None, description="Plastic Surgery Consultation Needed for")
    p20_dental_referrals: list[str] = Field(default=None, description="Dental Referrals and Services")  # Options: Referral for Evaluation And Treatment with Prosthodontic/Periodontist Specialist, Oral Surgery Consultation, Orthodontic Consultation, Dental Consultation for: Treatment for Decay Fractured Teeth Xerostomia / Periodontal Disease, Patient to get Dental Records / FMX...
    p20_patient_informed_xrays: Optional[bool] = Field(default=None, description="Patient informed they must see any dentist for X-rays to determine if any fracture, decay, and / or periodontal disease is present that can be caused or aggravated by their industrially related xerostomia or bruxism conditions")
    p20_patient_informed_decay: Optional[bool] = Field(default=None, description="Patient informed they must see any dentist for the decay and / or periodontal disease that can be caused or aggravated by their industrially related xerostomia")
    p20_patient_informed_treatment: Optional[bool] = Field(default=None, description="Patient informed that if they require dental treatment for decay or fractured of teeth that was caused or aggravated by their industrially related xerostomia, or trauma, or bruxism, that no treatment will be performed by our office for the decay or fractured teeth until authorization and payment is made to our office by the workers compensation insurance company; and therefore they must seek the required treatment at any dental office to be paid for by the patient them self")
    p20_doctor_signature: Optional[str] = Field(default=None, description="Dr. Signature")
    p20_signature_date: Optional[date] = Field(default=None, description="Date (Format: MM/DD/YYYY)")
class Page1Data(BaseModel):
    """
    Page 1: Medical History Form
    Complexity: 6/10
    """

    patient_info: Optional[P1PatientInfo] = Field(default=None, description="Patient Information")
    medical_history: Optional[P1MedicalHistory] = Field(default=None, description="Medical History Questions")
    allergies: Optional[P1Allergies] = Field(default=None, description="History of Allergies")
    medications: Optional[P1Medications] = Field(default=None, description="Current Medications")
    p1_doctor_completion_table: list[P1DoctorCompletionTableRow] = Field(default_factory=list, description="BELOW THE LINE TO BE COMPLETED BY THE DOCTOR")
class Page2Data(BaseModel):
    """
    Page 2: History of Medication Usage
    Complexity: 6/10
    """

    medication_usage_questions: Optional[P2MedicationUsageQuestions] = Field(default=None, description="History of Medication Usage")
    before_injury_medications: Optional[P2BeforeInjuryMedications] = Field(default=None, description="Medications Before Work Injury")
    presently_taking_medications: Optional[P2PresentlyTakingMedications] = Field(default=None, description="Medications Presently Taking")
    after_injury_medications: Optional[P2AfterInjuryMedications] = Field(default=None, description="Medications After Work Injury")
class Page3Data(BaseModel):
    """
    Page 3: Orofacial Examination - Page 3
    Complexity: 7/10
    """

    p3_mouth_symptoms: Optional[P3P3MouthSymptoms] = Field(default=None, description="Mouth Symptoms")
    p3_bad_breath: Optional[P3P3BadBreath] = Field(default=None, description="Bad Breath Assessment")
    p3_halitosis_taste: Optional[P3P3HalitosisTaste] = Field(default=None, description="Halitosis and Taste Assessment")
    p3_signature_section: Optional[P3P3SignatureSection] = Field(default=None, description="Attestation and Signature")
class Page4Data(BaseModel):
    """
    Page 4: Orofacial Examination - Page 4
    Complexity: 6/10
    """

    hand_dominance: Optional[P4HandDominance] = Field(default=None, description="Hand Dominance")
    work_injury_body_parts: Optional[P4WorkInjuryBodyParts] = Field(default=None, description="In your work injury, did you injure your:")
    hand_function_difficulties: Optional[P4HandFunctionDifficulties] = Field(default=None, description="Hand Function Difficulties")
    substance_use_history: Optional[P4SubstanceUseHistory] = Field(default=None, description="Substance Use History")
    attestation_signature: Optional[P4AttestationSignature] = Field(default=None, description="Attestation and Signature")
class Page5Data(BaseModel):
    """
    Page 5: Employment History
    Complexity: 6/10
    """

    p5_header: Optional[P5P5Header] = Field(default=None, description="Header Information")
    p5_employment_history: Optional[P5P5EmploymentHistory] = Field(default=None, description="Employment History")
class Page6Data(BaseModel):
    """
    Page 6: History of Industrial Injury
    Complexity: 7/10
    """

    p6_trauma_history: Optional[P6P6TraumaHistory] = Field(default=None, description="Trauma History")
    p6_patient_signature: Optional[P6P6PatientSignature] = Field(default=None, description="Patient's Signature")
    p6_industrial_injury: Optional[P6P6IndustrialInjury] = Field(default=None, description="History of Industrial Injury")
    p6_mva_details: Optional[P6P6MvaDetails] = Field(default=None, description="MVA Details")
class Page7Data(BaseModel):
    """
    Page 7: Orofacial Examination - Page 7
    Complexity: 7/10
    """

    p7_work_related_symptoms: Optional[P7P7WorkRelatedSymptoms] = Field(default=None, description="Work-Related Symptoms and Stress")
    p7_pre_existing_conditions: Optional[P7P7PreExistingConditions] = Field(default=None, description="Pre-Existing Conditions")
    p7_attestation: Optional[P7P7Attestation] = Field(default=None, description="Patient Attestation")
    p7_treatments_received: Optional[P7P7TreatmentsReceived] = Field(default=None, description="Treatments Received Due to the Industrial Injury")
class Page8Data(BaseModel):
    """
    Page 8: Prior History - Page 8
    Complexity: 6/10
    """

    tx_received: Optional[P8TxReceived] = Field(default=None, description="Tx Received")
    prior_history: Optional[P8PriorHistory] = Field(default=None, description="Prior History")
class Page9Data(BaseModel):
    """
    Page 9: Dental History
    Complexity: 7/10
    """

    dental_history: Optional[P9DentalHistory] = Field(default=None, description="Dental History")
class Page10Data(BaseModel):
    """
    Page 10: Present Symptoms
    Complexity: 8/10
    """

    weight_physical: Optional[P10WeightPhysical] = Field(default=None, description="Weight and Physical Information")
    sleep_symptoms: Optional[P10SleepSymptoms] = Field(default=None, description="Sleep Related Symptoms")
    headaches: Optional[P10Headaches] = Field(default=None, description="Headaches")
    face_pain: Optional[P10FacePain] = Field(default=None, description="Face Pain")
    tmj_symptoms: Optional[P10TmjSymptoms] = Field(default=None, description="TMJ Symptoms")
class Page11Data(BaseModel):
    """
    Page 11: Orofacial Examination - Page 11
    Complexity: 7/10
    """

    p11_mouth_jaw_symptoms: Optional[P11P11MouthJawSymptoms] = Field(default=None, description="Mouth and Jaw Symptoms")
    p11_speech_hearing: Optional[P11P11SpeechHearing] = Field(default=None, description="Speech and Hearing Issues")
    p11_general_symptoms: Optional[P11P11GeneralSymptoms] = Field(default=None, description="General Symptoms")
    p11_total_score: Optional[str] = Field(default=None, description="Total Score:")
    p11_epworth_sleepiness_scale: list[P11EpworthSleepinessScaleRow] = Field(default_factory=list, description="Epworth Sleepiness Scale")
class Page12Data(BaseModel):
    """
    Page 12: Activities of Daily Living VAS
    Complexity: 7/10
    """

    p12_facial_pain_activities: Optional[P12P12FacialPainActivities] = Field(default=None, description="Activities of Daily Living VAS")
    p12_communication_talking: Optional[P12P12CommunicationTalking] = Field(default=None, description="Communication / Talking")
    p12_eating_chewing: Optional[P12P12EatingChewing] = Field(default=None, description="Eating / Chewing")
    p12_attestation: Optional[bool] = Field(default=None, description="I attest that all of the above is true.")
    p12_patient_signature: Optional[str] = Field(default=None, description="Patient's Signature:")
    p12_signature_date: Optional[date] = Field(default=None, description="Date: (Format: MM/DD/YYYY)")
class Page13Data(BaseModel):
    """
    Page 13: Activities of Daily Living
    Complexity: 4/10
    """

    self_care_hygiene: Optional[P13SelfCareHygiene] = Field(default=None, description="Self-Care Hygiene")
    communication: Optional[P13Communication] = Field(default=None, description="Communication")
    motor_function: Optional[P13MotorFunction] = Field(default=None, description="Motor Function")
    bruxism: Optional[P13Bruxism] = Field(default=None, description="Bruxism")
    sexual_function: Optional[P13SexualFunction] = Field(default=None, description="Sexual Function")
class Page14Data(BaseModel):
    """
    Page 14: Clinical Examination
    Complexity: 8/10
    """

    p14_clinical_exam: Optional[P14P14ClinicalExam] = Field(default=None, description="Clinical Examination")
    p14_range_of_motion: Optional[P14P14RangeOfMotion] = Field(default=None, description="Range of Motion")
    p14_jaw_deviation: Optional[P14P14JawDeviation] = Field(default=None, description="Jaw Deviation")
    p14_capsulitis: Optional[P14P14Capsulitis] = Field(default=None, description="Capsulitis")
    p14_joint_noises: Optional[P14P14JointNoises] = Field(default=None, description="Joint Noises (Manual)")
    p14_tenderness_table: list[P14TendernessTableRow] = Field(default_factory=list, description="Tenderness and Palpable Taut Bands / Trigger Points")
class Page15Data(BaseModel):
    """
    Page 15: Orofacial Examination - Page 15
    Complexity: 8/10
    """

    p15_dental_classification: Optional[P15P15DentalClassification] = Field(default=None, description="Dental Classification")
    p15_bite_occlusion: Optional[P15P15BiteOcclusion] = Field(default=None, description="Bite and Occlusion")
    p15_oral_conditions: Optional[P15P15OralConditions] = Field(default=None, description="Oral Conditions")
    p15_patient_history: Optional[P15P15PatientHistory] = Field(default=None, description="Patient History")
    p15_tooth_conditions: Optional[P15P15ToothConditions] = Field(default=None, description="Tooth Conditions")
    p15_gum_conditions: Optional[P15P15GumConditions] = Field(default=None, description="Gum Conditions")
    p15_malampati_friedman: Optional[P15P15MalampatiFriedman] = Field(default=None, description="Classifications")
class Page16Data(BaseModel):
    """
    Page 16: Diagnostic Tests
    Complexity: 8/10
    """

    diagnostic_tests: Optional[P16DiagnosticTests] = Field(default=None, description="Diagnostic Tests")
    salivary_diagnostic: Optional[P16SalivaryDiagnostic] = Field(default=None, description="Salivary Diagnostic Testing")
class Page17Data(BaseModel):
    """
    Page 17: Oral Cancer Screening Form
    Complexity: 7/10
    """

    p17_anatomical_findings: Optional[P17P17AnatomicalFindings] = Field(default=None, description="Anatomical Findings")
    p17_diagnosis: Optional[P17P17Diagnosis] = Field(default=None, description="Diagnosis")
class Page18Data(BaseModel):
    """
    Page 18: Trigeminal Nerve Neuropathic QST Testing
    Complexity: 6/10
    """

    p18_qst_section: Optional[P18P18QstSection] = Field(default=None, description="QST")
    p18_qst_cold_section: Optional[P18P18QstColdSection] = Field(default=None, description="QST Cold")
    p18_qst_bilateral_section: Optional[P18P18QstBilateralSection] = Field(default=None, description="QST After Bilateral SPGB, if necessary")
class Page19Data(BaseModel):
    """
    Page 19: Diagnostic Photographs
    Complexity: 6/10
    """

    p19_lateral_border_tongue: Optional[P19P19LateralBorderTongue] = Field(default=None, description="Lateral Border of the Tongue Scalloping")
    p19_buccal_mucosal: Optional[P19P19BuccalMucosal] = Field(default=None, description="Buccal Mucosal Ridging")
    p19_occlusal_wear: Optional[P19P19OcclusalWear] = Field(default=None, description="Occlusal Wear")
    p19_oral_findings: Optional[P19P19OralFindings] = Field(default=None, description="Oral Findings")
    p19_asymmetries: Optional[P19P19Asymmetries] = Field(default=None, description="Asymmetries and Deviations")
    p19_dental_conditions: Optional[P19P19DentalConditions] = Field(default=None, description="Dental and Prosthetic Conditions")
    p19_bite_conditions: Optional[P19P19BiteConditions] = Field(default=None, description="Bite Conditions")
    p19_muscle_conditions: Optional[P19P19MuscleConditions] = Field(default=None, description="Muscle and Tongue Conditions")
    p19_other_conditions: Optional[P19P19OtherConditions] = Field(default=None, description="Other Conditions")
class Page20Data(BaseModel):
    """
    Page 20: Treatment Plan
    Complexity: 6/10
    """

    treatment_plan_section: Optional[P20TreatmentPlanSection] = Field(default=None, description="Treatment Plan")
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
    page_1: Optional[Page1Data] = Field(default=None, description="Page 1: Medical History Form")
    page_2: Optional[Page2Data] = Field(default=None, description="Page 2: History of Medication Usage")
    page_3: Optional[Page3Data] = Field(default=None, description="Page 3: Orofacial Examination - Page 3")
    page_4: Optional[Page4Data] = Field(default=None, description="Page 4: Orofacial Examination - Page 4")
    page_5: Optional[Page5Data] = Field(default=None, description="Page 5: Employment History")
    page_6: Optional[Page6Data] = Field(default=None, description="Page 6: History of Industrial Injury")
    page_7: Optional[Page7Data] = Field(default=None, description="Page 7: Orofacial Examination - Page 7")
    page_8: Optional[Page8Data] = Field(default=None, description="Page 8: Prior History - Page 8")
    page_9: Optional[Page9Data] = Field(default=None, description="Page 9: Dental History")
    page_10: Optional[Page10Data] = Field(default=None, description="Page 10: Present Symptoms")
    page_11: Optional[Page11Data] = Field(default=None, description="Page 11: Orofacial Examination - Page 11")
    page_12: Optional[Page12Data] = Field(default=None, description="Page 12: Activities of Daily Living VAS")
    page_13: Optional[Page13Data] = Field(default=None, description="Page 13: Activities of Daily Living")
    page_14: Optional[Page14Data] = Field(default=None, description="Page 14: Clinical Examination")
    page_15: Optional[Page15Data] = Field(default=None, description="Page 15: Orofacial Examination - Page 15")
    page_16: Optional[Page16Data] = Field(default=None, description="Page 16: Diagnostic Tests")
    page_17: Optional[Page17Data] = Field(default=None, description="Page 17: Oral Cancer Screening Form")
    page_18: Optional[Page18Data] = Field(default=None, description="Page 18: Trigeminal Nerve Neuropathic QST Testing")
    page_19: Optional[Page19Data] = Field(default=None, description="Page 19: Diagnostic Photographs")
    page_20: Optional[Page20Data] = Field(default=None, description="Page 20: Treatment Plan")

    # Field-level evidence (optional, for detailed tracking)
    field_evidence: list[ExtractedFieldValue] = Field(default_factory=list, description="Detailed evidence for each extracted field")
