# Medical Form Extraction & Clinical Report Generation

Python backend for AI-powered medical form extraction and clinical report generation.

## What This Does

1. **Extract** — Scans filled medical forms using a 6-stage AI vision pipeline
2. **Generate** — Produces clinical narrative DOCX reports using learned rules + LLM
3. **Serve** — FastAPI backend for the web application

---

## Quick Start

### Prerequisites
- Python 3.10+
- Poppler (for PDF processing): `brew install poppler` / `apt install poppler-utils`
- API keys (Together AI, Fireworks AI, or Anthropic)

### Setup

```bash
cd form-extractor
pip install -r requirements.txt

# Create .env with your API keys
cat > .env << 'EOF'
TOGETHER_API_KEY=your_together_key
FIREWORKS_API_KEY=your_fireworks_key
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
EOF

# Start the API server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

---

## Architecture

### AI Providers (Priority Order)

| Provider | Model | Used For |
|----------|-------|----------|
| Together AI | Llama 4 Maverick 17B | Vision extraction (primary), narrative generation (primary) |
| Fireworks AI | DeepSeek V3 | Narrative generation (fallback) |
| Anthropic | Claude Sonnet 4 | Extraction fallback, correlation/training |

### Extraction Pipeline (6 Stages)

Each page of a filled form goes through:

| Stage | Purpose |
|-------|---------|
| 1. Visual Detection | Find handwriting, circles, marks |
| 2. OCR/Transcription | Extract text with confidence scores |
| 3. Spatial Analysis | Detect groupings, brackets, arrows |
| 4. Field Mapping | Match values to form structure |
| 5. Semantic Analysis | Interpret clinical meaning |
| 6. Validation | Flag items needing review |

**Dual-Image Mode:** Compares blank template vs filled form for differential analysis.

### Clinical Report Generation

The clinical report generator uses a ruleset learned from 31 training reports:

1. Loads `report_learning/outputs/rules/report_rules.json` (25+ sections, 131 field IDs)
2. For each section, determines the content type:
   - **`formatted_fill`** — Template with `{field_id}` placeholders substituted from extraction
   - **`narrative`** — LLM generates clinical text using generation prompt + few-shot examples
   - **`static_text`** — Verbatim content inserted
   - **`list`** / **`table`** / **`conditional_block`** — Structured content
3. A `FIELD_NAME_MAP` (100+ entries) bridges production extraction field names to rule IDs
4. Assembles everything into a DOCX with Arial font, Heading 2 sections, justified text

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | No | Health check |
| `/api/analyze` | POST | Yes | Upload single PDF/image for analysis |
| `/api/analyze-images` | POST | Yes | Upload batch of page images |
| `/api/save-annotated-pdfs` | POST | Yes | Save annotated PDFs to Storage |
| `/api/jobs/{job_id}` | GET | No | Job status polling |
| `/api/results/{job_id}` | GET | No | Full extraction results |
| `/api/results/{job_id}/summary` | GET | No | Results summary |
| `/api/generate-clinical-report` | POST | Yes | Generate clinical narrative DOCX |
| `/api/reports` | POST | Yes | Upload/persist a report |
| `/api/reports/{id}/download` | GET | Yes | Signed download URL |
| `/api/documents` | GET | Yes | List documents |
| `/api/documents/{id}` | GET | Yes | Document detail |
| `/api/documents/{id}/reanalyze` | POST | Yes | Re-analyze existing document |

### Generate Clinical Report

```bash
curl -X POST http://localhost:8000/api/generate-clinical-report \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id"}'

# Response: { "report_id": "...", "storage_path": "...", "filename": "..." }
```

---

## Project Structure

```
form-extractor/
├── api/
│   └── server.py                          # FastAPI backend (all endpoints)
│
├── src/
│   ├── models/
│   │   ├── annotations.py                 # VisualMark, SpatialConnection, AnnotationGroup
│   │   ├── extraction.py                  # FormExtractionResult, PageExtractionResult
│   │   ├── field_types.py                 # Enums (FieldType, MarkType)
│   │   ├── fields.py                      # FormFieldSchema, TableSchema
│   │   ├── form.py                        # FormSchema
│   │   ├── pages.py                       # PageSchema
│   │   └── sections.py                    # SectionSchema
│   ├── services/
│   │   ├── extraction_pipeline.py         # 6-stage AI pipeline (Together AI + Claude)
│   │   ├── pdf_processor.py              # PDF → images (pdf2image/poppler)
│   │   ├── analyzer.py                    # Blank form structure analysis
│   │   ├── supabase_client.py            # Supabase client singleton
│   │   ├── job_manager.py                # DB CRUD for jobs, documents, results, reports
│   │   └── storage_manager.py            # Supabase Storage upload/download (upsert)
│   └── generators/
│       ├── clinical_report_generator.py   # Rules + LLM → clinical DOCX
│       ├── schema_generator.py            # JSON schema output
│       └── pydantic_generator.py          # Pydantic model generation
│
├── report_learning/                       # Training module (ran offline)
│   ├── cli.py                             # Click CLI for training pipeline
│   ├── scanner/                           # Phase 1: DOCX report parsing
│   │   ├── docx_parser.py                # Mechanical DOCX structure extraction
│   │   ├── llm_content_analyzer.py       # LLM element classification
│   │   └── models.py                     # ScannedReport, ReportSection, ReportElement
│   ├── correlator/                        # Phase 2-3: Field mapping + patterns
│   │   ├── condenser.py                  # Extraction JSON condensation
│   │   ├── field_mapper.py               # Per-pair LLM correlation (Claude)
│   │   ├── pattern_analyzer.py           # Cross-report pattern discovery
│   │   └── models.py                     # PairCorrelation, CrossReportPatterns
│   ├── rules/                             # Phase 4-5: Rule generation + validation
│   │   ├── rule_generator.py             # Section rule synthesis
│   │   ├── rule_validator.py             # Validation + refinement
│   │   └── models.py                     # SectionRule, ReportRules
│   ├── training_data/
│   │   ├── completed_reports/            # 31 DOCX clinical reports (input)
│   │   └── source_forms/                 # 31 signed patient PDFs (input)
│   └── outputs/
│       ├── rules/
│       │   └── report_rules.json         # *** Master ruleset ***
│       ├── scanned/                      # 31 parsed report JSONs
│       ├── correlations/                 # 31 field mapping JSONs
│       ├── extractions_v2/               # 31 extraction JSONs
│       └── generated_reports/            # Test-generated clinical reports
│
├── templates/                             # Generated form schemas + blank images
├── Dockerfile                             # Python 3.11-slim + poppler-utils
├── requirements.txt
└── main.py                                # CLI entry point (scan, extract, info, check)
```

---

## Report Learning Pipeline (How Rules Were Built)

The report learning engine was trained on 31 completed clinical reports:

| Phase | Command | LLM | Output |
|-------|---------|-----|--------|
| 1. Report Scanning | `cli.py scan` | python-docx + Claude | `outputs/scanned/` |
| 2. Form Extraction | `cli.py extract` | Together AI (Llama 4 Maverick) | `outputs/extractions_v2/exam/` |
| 3. Condensation | `cli.py condense` | Rule-based | `outputs/extractions_v2/condensed/` |
| 4. Correlation | `cli.py correlate` | Claude Sonnet 4 | `outputs/correlations/` |
| 5. Pattern Analysis | (part of correlate) | Claude Sonnet 4 | `outputs/rules/cross_report_patterns.json` |
| 6. Rule Generation | `cli.py generate-rules` | Claude Sonnet 4 | `outputs/rules/report_rules.json` |
| 7. Validation | `cli.py validate` | Claude Sonnet 4 | `outputs/rules/validation_scores.json` |

To re-train with new reports, add DOCX + PDF pairs to `training_data/` and re-run the pipeline.

---

## CLI Commands

```bash
# System check
python main.py check

# Scan blank form → generate schema
python main.py scan ./input/blank_form.pdf --name "exam" --output ./templates/

# Extract from filled form
python main.py extract ./input/filled_form.pdf --name "patient_name"

# Extract with schema for better field mapping
python main.py extract ./input/filled.pdf --name "smith" --schema ./templates/exam_schema.json

# Report learning pipeline
python -m report_learning.cli scan
python -m report_learning.cli extract
python -m report_learning.cli condense
python -m report_learning.cli correlate
python -m report_learning.cli generate-rules
python -m report_learning.cli validate
```

---

## Dependencies

Key packages (`requirements.txt`):

| Package | Purpose |
|---------|---------|
| instructor | Structured LLM outputs with Pydantic |
| anthropic | Claude API client |
| openai | Together AI / Fireworks AI client (OpenAI-compatible) |
| python-docx | DOCX parsing and generation |
| pydantic | Data validation |
| pdf2image | PDF to image conversion |
| Pillow | Image processing |
| fastapi + uvicorn | API framework |
| supabase | Supabase client for DB + Storage |

---

*Last Updated: 2026-03-10*
