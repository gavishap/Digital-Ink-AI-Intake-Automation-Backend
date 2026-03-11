# Claude Validation Prompt

Upload the full PDF to Claude and paste this prompt. Claude will extract every value from every page in a JSON format that matches our extraction output, making it easy to compare.

---

## PROMPT (copy everything below this line)

You are a medical form data extraction expert. I am uploading a scanned, filled-out orofacial pain examination form (PDF). Your job is to extract ALL data from EVERY page — both printed labels and handwritten entries.

**IMPORTANT RULES:**
- Go page by page, in order
- For each page, list every field you can identify with its value
- For YES/NO questions, look carefully at which option is CIRCLED (not just printed)
- For checkboxes, report whether they are checked or not
- If a field is blank/empty, report it as `""` (empty string)
- If handwriting is hard to read, give your best reading
- For circled selections from a printed list (e.g., medications, conditions), list exactly which items are circled
- Note any crossed-out or corrected values
- The first 1-3 pages may be lawyer/case demographic pages (NOT the orofacial exam). Extract those too but label them as "lawyer_page"

**OUTPUT FORMAT — return valid JSON matching this exact structure:**

```json
{
  "patient_name": "...",
  "form_date": "...",
  "total_pages_in_pdf": 0,
  "lawyer_pages": [
    {
      "pdf_page_number": 1,
      "page_type": "lawyer_page",
      "fields": {
        "field_label": {
          "value": "extracted value",
          "is_checked": null,
          "circled_options": []
        }
      }
    }
  ],
  "exam_pages": [
    {
      "pdf_page_number": 2,
      "exam_page_number": 1,
      "page_title": "Patient Information Form / YES-NO Questions",
      "fields": {
        "patient_name": {
          "value": "...",
          "is_checked": null,
          "circled_options": []
        },
        "date": {
          "value": "MM/DD/YYYY",
          "is_checked": null,
          "circled_options": []
        },
        "birth_date": {
          "value": "MM/DD/YYYY",
          "is_checked": null,
          "circled_options": []
        },
        "gender": {
          "value": "MALE or FEMALE",
          "is_checked": true,
          "circled_options": ["FEMALE"]
        },
        "q1_heart_problems": {
          "value": "YES or NO",
          "is_checked": true,
          "circled_options": ["YES"]
        },
        "q1_heart_problems_subtypes": {
          "value": null,
          "is_checked": null,
          "circled_options": ["Murmur", "Stent"]
        }
      }
    }
  ]
}
```

**FIELD VALUE RULES:**

| Field Type | How to Report |
|---|---|
| YES/NO question | `"value": "YES"` or `"value": "NO"` based on which is CIRCLED |
| Checkbox | `"is_checked": true/false` |
| Written text | `"value": "exact text as written"` |
| Circled selection from list | `"circled_options": ["Item1", "Item2"]` |
| Numeric (VAS scale 0-10) | `"value": "7"` |
| Date | `"value": "MM/DD/YYYY"` |
| Empty/blank field | `"value": ""` |
| Crossed out then rewritten | `"value": "new value", "has_correction": true, "original_value": "old value"` |

**PAGE-BY-PAGE GUIDE (standard 20-page orofacial exam):**

- **Page 1**: Patient info header, 17 YES/NO medical questions, history of allergies, medications list, DX table
- **Page 2**: History of Medication Usage (before/presently/after injury)
- **Page 3**: Chief Complaint, VAS scales, injury circumstances
- **Page 4**: Detailed medical history (multiple conditions with checkboxes)
- **Pages 5-20**: Various examination sections (TMJ, dental, cranial nerves, range of motion, palpation, etc.)

For EVERY page, extract EVERY visible piece of handwritten or marked data. Do not skip any pages. Do not summarize — give exact values.

If there are extra pages beyond the standard 20 exam pages (older form versions may have additional sheets), extract those too and label them as `"extra_page"`.

Return ONLY the JSON. No commentary before or after.
