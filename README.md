# Medical Form Template Extraction System

A Python CLI tool that:
1. **Phase 1 (scan):** Scans blank PDF forms → Generates Pydantic schemas
2. **Phase 2 (extract):** Extracts data from filled forms using a multi-stage LLM pipeline

## 🎯 Key Features

- **Claude Sonnet 4** by default (cost-efficient), Opus available for complex forms
- **Multi-stage extraction pipeline** (6 stages per page)
- **Handles complex annotations:** brackets, lines, arrows, margin notes
- **Spatial relationship detection:** understands groupings and connections
- **Semantic interpretation:** clinical meaning of annotations
- **Validation & review flagging:** identifies items needing human review
- **Cost optimizations:** image compression, smart prompts, efficient defaults

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd form-extractor
pip install -r requirements.txt
```

**System requirement:** Install poppler for PDF processing:
- **macOS:** `brew install poppler`
- **Ubuntu:** `sudo apt-get install poppler-utils`
- **Windows:** Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows)

### 2. Set API Key

```bash
# Create .env file with your Anthropic API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### 3. Verify Setup

```bash
python main.py check
```

---

## 📋 Commands

### `scan` - Analyze Blank Forms (Phase 1)

Generates schemas from blank forms for field mapping.

```bash
# Scan a blank PDF
python main.py scan ./input/blank_form.pdf --name "exam_form" --output ./templates/

# Preview without saving
python main.py scan ./input/blank_form.pdf --name "test" --preview
```

**Output:**
- `exam_form_schema.json` - Complete form structure
- `exam_form_page_N.json` - Per-page schemas
- `exam_form_models.py` - Pydantic models for extraction
- `exam_form_summary.txt` - Human-readable summary

---

### `extract` - Extract from Filled Forms (Phase 2) 

**NEW:** Multi-stage extraction with full annotation support.

```bash
# Basic extraction (no schema)
python main.py extract ./filled_form.pdf --name "patient_smith"

# With schema for better field mapping
python main.py extract ./filled_form.pdf --name "patient_smith" --schema ./templates/exam_form_schema.json

# From folder of scanned images
python main.py extract ./scanned_pages/ --name "patient_doe" --output ./extractions/
```

**Output:**
- `patient_smith_extraction.json` - Complete extraction with all data
- `patient_smith_page_N.json` - Per-page results
- `patient_smith_summary.txt` - Human-readable summary with review items

---

## 🔬 Multi-Stage Extraction Pipeline

The `extract` command runs 6 stages per page:

| Stage | Purpose | What It Detects |
|-------|---------|-----------------|
| **1. Visual Detection** | Find all elements | Handwriting, marks, brackets, lines, arrows, circles |
| **2. OCR/Transcription** | Extract text | Handwritten text with confidence scores |
| **3. Spatial Analysis** | Detect connections | Brackets grouping items, arrows pointing, lines connecting |
| **4. Field Mapping** | Map to known fields | Match values to form fields, handle corrections |
| **5. Semantic Analysis** | Interpret meaning | What annotations mean clinically, group purposes |
| **6. Validation** | Quality check | Flag ambiguous items, calculate confidence |

### What It Handles

✅ **Standard fields:** Text, dates, yes/no, checkboxes, circled options  
✅ **Brackets & groupings:** `{ medications }` with notes like "stopped taking"  
✅ **Lines & arrows:** Connecting elements with annotations  
✅ **Margin notes:** Free-form text anywhere on page  
✅ **Corrections:** Crossed-out values with new values  
✅ **Cross-references:** "See attached sheet" links  
✅ **Circled selections:** Items circled from printed lists  

---

## 📁 Project Structure

```
form-extractor/
├── input/                  # Put blank/filled PDFs here
├── templates/              # Generated schemas go here
├── extractions/            # Extraction results go here
├── main.py                 # CLI entry point
├── requirements.txt
└── src/
    ├── models/
    │   ├── field_types.py      # Enums
    │   ├── fields.py           # FormFieldSchema, TableSchema
    │   ├── sections.py         # SectionSchema
    │   ├── pages.py            # PageSchema
    │   ├── form.py             # FormSchema
    │   ├── extraction.py       # SourceEvidence, ExtractedFieldValue
    │   └── annotations.py      # 🆕 Visual marks, spatial connections, groups
    ├── services/
    │   ├── analyzer.py         # Blank form analyzer
    │   ├── pdf_processor.py    # PDF → images
    │   └── extraction_pipeline.py  # 🆕 Multi-stage extraction
    └── generators/
        ├── schema_generator.py
        └── pydantic_generator.py
```

---

## 📊 Extraction Output Format

```json
{
  "form_id": "patient_smith",
  "patient_name": "Martha Aguilar",
  "patient_dob": "9/21/70",
  "form_date": "10/23/25",
  "overall_confidence": 0.87,
  "total_items_needing_review": 3,
  "pages": [
    {
      "page_number": 1,
      "field_values": {
        "p1_name": {"value": "Martha Aguilar", "confidence": 0.95},
        "p1_heart_problems": {"is_checked": false, "circled_options": ["NO"]}
      },
      "annotation_groups": [
        {
          "group_id": "med_group_1",
          "member_elements": ["Tramadol", "Ibuprofen", "Hydrocodone"],
          "annotation_text": "Stopped taking but began after injury",
          "interpretation": "These medications were stopped but resumed after the work injury"
        }
      ],
      "free_form_annotations": [
        {
          "raw_text": "See Sheet",
          "relates_to_fields": ["medications_list"],
          "semantic_meaning": "Medication list continues on attached sheet"
        }
      ],
      "cross_page_references": [
        {
          "reference_text": "See Sheet",
          "target_page": 2,
          "is_resolved": true
        }
      ]
    }
  ]
}
```

---

## 💰 Cost Optimization

The system is optimized for cost efficiency:

| Optimization | Impact | Default Setting |
|-------------|--------|-----------------|
| **Claude Sonnet 4** | 5x cheaper than Opus | Default model |
| **Image compression** | ~60% smaller payloads | JPEG quality 85 |
| **Lower DPI** | ~50% fewer input tokens | 150 DPI (sufficient for forms) |
| **Max dimension** | Optimal for Claude vision | 1568px |
| **Reduced max_tokens** | Less output overhead | 4096 |
| **Concise prompts** | Fewer input tokens | Optimized |

### Model Cost Comparison (per 1M tokens)

| Model | Input | Output | Use When |
|-------|-------|--------|----------|
| claude-sonnet-4-20250514 | $3 | $15 | **Default** - Most forms |
| claude-opus-4-5-20251101 | $15 | $75 | Very dense/complex forms |

### Use Opus for Complex Forms

```bash
# When forms have very dense text or complex layouts:
python main.py scan ./complex_form.pdf --name "test" --model claude-opus-4-5-20251101
```

---

## 🔧 Configuration

Environment variables (in `.env`):

```bash
ANTHROPIC_API_KEY=your_key_here
```

CLI options:

```bash
python main.py scan --help

Options:
  -n, --name       Name for this form (required)
  -o, --output     Output directory [default: ./templates]
  --preview        Preview without saving
  --model          Claude model [default: claude-sonnet-4-20250514]
  --dpi            DPI for PDF conversion [default: 150]
  --max-tokens     Max response tokens [default: 4096]
```

```bash
python main.py extract --help

Options:
  -n, --name     Name for extraction output (required)
  -s, --schema   Path to form schema JSON (optional)
  -o, --output   Output directory [default: ./extractions]
  --model        Claude model [default: claude-sonnet-4-20250514]
```

---

## 🎯 Workflow Example

```bash
# 1. First, scan the blank form to generate schema
python main.py scan "./input/blank_exam_form.pdf" --name "dental_exam" --output ./templates/

# 2. Then extract data from filled forms using the schema
python main.py extract "./input/filled_smith.pdf" --name "smith_john" --schema ./templates/dental_exam_schema.json

# 3. Review the extraction
cat ./extractions/smith_john_summary.txt
```

---

## 📝 Handling Complex Annotations

### Brackets Grouping Medications

When patients draw brackets like:
```
  Tramadol    |
  Ibuprofen   } "Stopped taking but began after injury"
  Hydrocodone |
```

The pipeline:
1. Detects the bracket as a spatial connector
2. Identifies which items it groups
3. Extracts the annotation text
4. Interprets the clinical meaning
5. Links it all in a structured `AnnotationGroup`

### Cross-Page References

When a field says "See attached sheet":
1. Detected as a `CrossPageReference`
2. Target page identified
3. Content from target page linked
4. Resolution status tracked

### Corrections

When something is crossed out:
1. Original value captured
2. New value extracted
3. `has_correction: true` flagged
4. Both values preserved for audit

---

## 📄 License

Internal use only - Digital Ink Project
