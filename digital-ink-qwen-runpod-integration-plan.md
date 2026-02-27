# Digital Ink — Qwen3-VL + RunPod Integration Plan

## Overview

We are replacing Claude API calls for vision/OCR tasks with a self-hosted **Qwen3-VL-32B-Instruct-FP8** model running on **RunPod Serverless**. This model handles both image understanding (reading handwritten medical forms) AND text structuring (outputting structured JSON) in a single call. Claude is retained only as a fallback for low-confidence extractions.

---

## Architecture

```
Patient Form Image
        │
        ▼
  Digital Ink Backend
        │
        ▼
  RunPod Serverless Endpoint (Qwen3-VL-32B)
   - Reads handwritten text from form image
   - Structures extracted data into JSON
   - Returns structured patient data
        │
        ▼
  Confidence Check
   ├── confidence >= 0.85 → Use Qwen result
   └── confidence < 0.85  → Fallback to Claude API
```

---

## Model Details

| Property | Value |
|----------|-------|
| Model | Qwen/Qwen3-VL-32B-Instruct-FP8 |
| Type | Vision-Language Model (reads images + generates text) |
| Parameters | 32 billion |
| Quantization | FP8 (8-bit floating point) |
| VRAM Required | ~32GB |
| Context Window | 16,384 tokens (configured) |
| License | Apache 2.0 (fully commercial) |
| Multi-image | Yes, up to 4 images per request |

### What Qwen3-VL Can Do
- **Read handwritten text** from scanned/photographed medical forms
- **Read printed text** from any document
- **Understand form layout** — knows which field a handwritten entry belongs to
- **Output structured JSON** — extracts and formats data in one shot
- **Process multiple images** — can compare blank template vs filled form
- **General text tasks** — summarization, formatting, Q&A (it's a full LLM, not just OCR)

### What It Cannot Do
- No web browsing or tool use
- No real-time knowledge (training data cutoff)
- Slightly slower than Claude on pure text reasoning tasks
- May struggle with extremely messy handwriting (fallback to Claude)

---

## RunPod Serverless Endpoint

| Property | Value |
|----------|-------|
| Endpoint ID | `524sp0tkjw1t3u` |
| Base URL | `https://api.runpod.ai/v2/524sp0tkjw1t3u/openai/v1` |
| API Format | OpenAI-compatible (`/v1/chat/completions`) |
| GPU | A100 80GB PCIe (auto-assigned) |
| Scaling | 0 to 1 workers (scales to zero when idle) |
| Cold Start | ~15 min first time, ~2-3 min with network volume |
| Cost When Idle | $0.00 |
| Cost When Active | ~$0.00076/sec (~$2.74/hr) |
| Authentication | RunPod API Key (Bearer token) |

---

## Environment Variables

Add these to your `.env`:

```env
# RunPod Qwen3-VL (primary — vision + text extraction)
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_URL=https://api.runpod.ai/v2/524sp0tkjw1t3u/openai/v1

# Claude (fallback only)
ANTHROPIC_API_KEY=your_anthropic_api_key
```

---

## API Integration Code

### Client Setup

```python
from openai import OpenAI
import anthropic
import os

# Primary: Qwen3-VL on RunPod
qwen_client = OpenAI(
    api_key=os.getenv("RUNPOD_API_KEY"),
    base_url=os.getenv("RUNPOD_ENDPOINT_URL")
)

# Fallback: Claude
claude_client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
```

### Single Image Extraction (Most Common)

```python
import base64

def extract_form_data(image_path: str) -> dict:
    """Extract structured data from a medical form image using Qwen3-VL."""
    
    # Read and encode image
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # Detect media type
    if image_path.lower().endswith(".png"):
        media_type = "image/png"
    elif image_path.lower().endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    else:
        media_type = "image/png"  # default
    
    response = qwen_client.chat.completions.create(
        model="Qwen/Qwen3-VL-32B-Instruct-FP8",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{img_b64}"
                    }
                },
                {
                    "type": "text",
                    "text": """Extract all handwritten and printed field data from this medical form.
Return ONLY valid JSON with this structure:
{
    "patient_name": "",
    "date_of_birth": "",
    "date_signed": "",
    "address": "",
    "phone": "",
    "email": "",
    "insurance_provider": "",
    "policy_number": "",
    "group_number": "",
    "emergency_contact_name": "",
    "emergency_contact_phone": "",
    "allergies": [],
    "medications": [],
    "medical_conditions": [],
    "signature_present": true/false,
    "confidence": 0.0-1.0,
    "notes": "any fields that were unclear or partially readable"
}
Fill in only fields that are visible on the form. Set confidence to your overall certainty level."""
                }
            ]
        }],
        max_tokens=2048,
        temperature=0.1
    )
    
    return response.choices[0].message.content
```

### Dual Image Extraction (Blank Template + Filled Form)

```python
def extract_with_template(template_path: str, filled_path: str) -> dict:
    """Compare blank template with filled form for better field mapping."""
    
    with open(template_path, "rb") as f:
        template_b64 = base64.b64encode(f.read()).decode()
    with open(filled_path, "rb") as f:
        filled_b64 = base64.b64encode(f.read()).decode()
    
    response = qwen_client.chat.completions.create(
        model="Qwen/Qwen3-VL-32B-Instruct-FP8",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{template_b64}"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{filled_b64}"}
                },
                {
                    "type": "text",
                    "text": """Image 1 is a blank medical form template. Image 2 is the same form filled out by a patient.
Compare both images to identify each field label from the template and extract the handwritten value from the filled form.
Return ONLY valid JSON mapping field names to their handwritten values.
Include a "confidence" field (0.0-1.0) for overall extraction certainty.
Include a "low_confidence_fields" array listing any fields where the handwriting was hard to read."""
                }
            ]
        }],
        max_tokens=2048,
        temperature=0.1
    )
    
    return response.choices[0].message.content
```

### Extraction with Claude Fallback

```python
import json

def extract_with_fallback(image_path: str) -> dict:
    """Try Qwen first, fall back to Claude if confidence is low."""
    
    # Try Qwen3-VL first
    try:
        raw_result = extract_form_data(image_path)
        result = json.loads(raw_result)
        
        if result.get("confidence", 0) >= 0.85:
            result["model_used"] = "qwen3-vl"
            return result
        else:
            # Low confidence — fall back to Claude
            return extract_with_claude(image_path)
    
    except Exception as e:
        # Qwen failed (cold start timeout, parsing error, etc.)
        print(f"Qwen extraction failed: {e}, falling back to Claude")
        return extract_with_claude(image_path)


def extract_with_claude(image_path: str) -> dict:
    """Fallback extraction using Claude."""
    
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    media_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
    
    response = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": img_b64
                    }
                },
                {
                    "type": "text",
                    "text": "Extract all handwritten and printed field data from this medical form. Return ONLY valid JSON with field names as keys and extracted values as values. Include a 'confidence' field (0.0-1.0)."
                }
            ]
        }]
    )
    
    result = json.loads(response.content[0].text)
    result["model_used"] = "claude-fallback"
    return result
```

---

## Important API Notes

### RunPod Serverless Behavior
- **Cold start:** First request after idle spins up a worker (~15 min without network volume, ~2-3 min with). The request will queue and wait — it does NOT timeout immediately.
- **Idle timeout:** Worker shuts down 5 seconds after last request completes.
- **Concurrent requests:** Max 30 concurrent requests per worker.
- **Request timeout:** 600 seconds (10 min) execution timeout per request.

### Request Format
The API is **OpenAI-compatible**. Use the standard OpenAI Python SDK with a custom `base_url`. The model name in requests must be exactly: `Qwen/Qwen3-VL-32B-Instruct-FP8`

### Image Handling
- Images must be sent as **base64-encoded data URIs** in the format: `data:{media_type};base64,{base64_string}`
- Supported formats: JPEG, PNG, WebP
- Max 4 images per request (configured via `--limit-mm-per-prompt`)
- Larger images = more tokens consumed = slower inference

### Error Handling
- If the endpoint has no active workers, the first request triggers a cold start. Your HTTP client should have a timeout of at least **300 seconds** (5 min) to account for this.
- If RunPod returns a queue/job response instead of a direct completion, you may need to poll the job status endpoint. The OpenAI-compatible route (`/openai/v1/chat/completions`) should handle this transparently.

---

## Cost Comparison

| Scenario | Qwen on RunPod | Claude API |
|----------|---------------|------------|
| Per form (est.) | ~$0.01-0.03 | ~$0.05-0.15 |
| 100 forms/day | ~$3-5/day | ~$10-15/day |
| Idle cost | $0.00 | $0.00 |
| Monthly (500 forms) | ~$50-75 | ~$150-250 |

---

## Migration Checklist

1. [ ] Add `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_URL` to `.env`
2. [ ] Install/update OpenAI SDK: `pip install openai`
3. [ ] Replace all vision/OCR Claude calls with Qwen client calls
4. [ ] Keep Claude client initialized for fallback only
5. [ ] Update image encoding to use base64 data URIs
6. [ ] Set HTTP client timeout to 300+ seconds for cold starts
7. [ ] Add confidence-based fallback logic
8. [ ] Test with real medical forms
9. [ ] Monitor RunPod dashboard for cost and error tracking
