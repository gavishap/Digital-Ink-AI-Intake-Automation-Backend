"""
Condense bloated extraction JSONs into clean per-page field summaries.

Two stages:
  1. Deterministic condensation — merge field_values + spatial_connections +
     free_form_annotations, recover YES/NO selections, flag conflicts.
  2. (Optional) AI verification — targeted LLM pass on flagged/critical pages.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

console = Console()

# Pages where extraction accuracy matters most (1-indexed exam page numbers)
CRITICAL_PAGES = {1, 3, 10, 14, 16}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_yes_no_from_connector(connector_id: str) -> tuple[str, str] | None:
    """Parse a connector_element_id like 'do_you_smoke_no' into (field, answer)."""
    for suffix in ("_yes", "_no"):
        if connector_id.endswith(suffix):
            field = connector_id[: -len(suffix)]
            answer = suffix.lstrip("_").upper()
            return field, answer
    return None


def _flatten_field_value(fv: dict[str, Any]) -> dict[str, Any]:
    """Strip metadata from a single field_value dict, keeping only data."""
    out: dict[str, Any] = {}
    val = fv.get("value")
    if val is not None and val != "":
        out["value"] = val

    is_checked = fv.get("is_checked")
    if is_checked is not None:
        out["is_checked"] = is_checked

    circled = fv.get("circled_options")
    if circled:
        out["circled_options"] = circled

    if fv.get("has_correction"):
        out["has_correction"] = True
        orig = fv.get("original_value")
        if orig is not None:
            out["original_value"] = orig

    return out if out else {"value": None}


_VAS_FIELD_HINTS = {"vas", "intensity", "interfere", "embarrass", "stress", "percent_of_time"}


def _is_vas_field(field_id: str) -> bool:
    """Check if a field name suggests a 0-10 VAS scale value."""
    fid_lower = field_id.lower()
    return any(hint in fid_lower for hint in _VAS_FIELD_HINTS)


def _normalise_vas(raw: str, field_id: str = "") -> str:
    """Fix common VAS misreads like '67' -> '6-7' on 0-10 scale fields only."""
    raw = raw.strip()
    if not _is_vas_field(field_id):
        return raw
    if re.fullmatch(r"\d{2}", raw):
        a, b = int(raw[0]), int(raw[1])
        if b > a and a <= 10 and b <= 10:
            return f"{raw[0]}-{raw[1]}"
    return raw


# ---------------------------------------------------------------------------
# Per-page condensation
# ---------------------------------------------------------------------------

def _condense_page(page: dict[str, Any]) -> dict[str, Any]:
    """Condense a single page from the raw extraction into a clean summary."""
    page_num = page.get("page_number", 0)
    fields: dict[str, Any] = {}
    review_flags: list[str] = []

    # 1. Core field_values
    for fid, fv in page.get("field_values", {}).items():
        fields[fid] = _flatten_field_value(fv)

    # 2. Recover YES/NO and selections from spatial_connections
    for conn in page.get("spatial_connections", []):
        if conn.get("relationship_meaning") != "Selection":
            continue
        cid = conn.get("connector_element_id", "")
        source_ids = conn.get("source_element_ids", [])

        parsed = _extract_yes_no_from_connector(cid)
        if parsed:
            field_key, answer = parsed
            sc_key = f"sc_{field_key}"
            if sc_key not in fields and field_key not in fields:
                fields[sc_key] = {"value": answer, "source": "spatial_connection"}
        elif len(source_ids) >= 2:
            group = source_ids[0]
            selection = "_".join(source_ids[1:])
            sc_key = f"sc_{group}_{selection}"
            if sc_key not in fields:
                fields[sc_key] = {"selected": True, "source": "spatial_connection"}

    # 3. Merge free_form_annotations
    for ann in page.get("free_form_annotations", []):
        raw_text = ann.get("raw_text", "")
        normalized = ann.get("normalized_text", "")
        related = ann.get("relates_to_field_ids") or []
        purpose = ann.get("annotation_purpose", "")

        if not raw_text and not normalized:
            continue

        for rel_fid in related:
            matched_key = None
            for fid in fields:
                if rel_fid.lower().replace(" ", "_") in fid.lower():
                    matched_key = fid
                    break

            if matched_key:
                existing = fields[matched_key]
                existing_val = existing.get("value") if isinstance(existing, dict) else existing
                if existing_val and raw_text and str(existing_val) != raw_text:
                    norm_existing = _normalise_vas(str(existing_val))
                    norm_raw = _normalise_vas(raw_text)
                    if norm_existing != norm_raw and norm_existing != normalized:
                        if isinstance(existing, dict):
                            existing["annotation_note"] = normalized or raw_text
                        review_flags.append(
                            f"{matched_key}: field='{existing_val}' vs annotation='{raw_text}'"
                        )
                elif not existing_val and raw_text:
                    if isinstance(existing, dict):
                        existing["value"] = raw_text
            else:
                ann_key = f"ann_{rel_fid.lower().replace(' ', '_')}"
                if ann_key not in fields:
                    fields[ann_key] = {
                        "value": raw_text,
                        "annotation": normalized or None,
                        "purpose": purpose or None,
                    }

    # 4. VAS normalisation pass (only on fields that look like VAS scales)
    for fid, fv in fields.items():
        if isinstance(fv, dict) and isinstance(fv.get("value"), str):
            original = fv["value"]
            fixed = _normalise_vas(original, fid)
            if fixed != original:
                fv["value"] = fixed
                review_flags.append(f"{fid}: normalised '{original}' -> '{fixed}'")

    # 5. Clean up empty fields and source tags
    cleaned: dict[str, Any] = {}
    for fid, fv in fields.items():
        if isinstance(fv, dict):
            fv.pop("source", None)
            if fv.get("purpose"):
                fv.pop("purpose", None)
            if fv.get("annotation") is None:
                fv.pop("annotation", None)
            if fv.get("annotation_note") is None:
                fv.pop("annotation_note", None)
            if len(fv) == 1 and "value" in fv:
                fv = fv["value"]
            elif len(fv) == 1 and "selected" in fv:
                fv = True
        if fv is None:
            continue
        cleaned[fid] = fv

    result: dict[str, Any] = {
        "page_number": page_num,
        "fields": cleaned,
    }
    if review_flags:
        result["review_flags"] = review_flags
    items_needing = page.get("items_needing_review", 0)
    if items_needing:
        result["items_needing_review"] = items_needing
    reasons = page.get("review_reasons", [])
    if reasons:
        result["extraction_review_reasons"] = reasons

    return result


# ---------------------------------------------------------------------------
# Full-document condensation
# ---------------------------------------------------------------------------

def condense_extraction(raw: dict[str, Any]) -> dict[str, Any]:
    """Condense a full raw extraction JSON into a clean summary."""
    pages = [_condense_page(p) for p in raw.get("pages", [])]
    return {
        "form_name": raw.get("form_name", ""),
        "source_file": raw.get("source_file", ""),
        "total_pages": raw.get("total_pages", len(pages)),
        "pages": pages,
    }


def condense_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    """Condense a single extraction JSON file and write the result."""
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    condensed = condense_extraction(raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(condensed, indent=2, ensure_ascii=False), encoding="utf-8")
    return condensed


def condense_all(
    input_dir: Path,
    output_dir: Path,
    skip_existing: bool = True,
) -> list[dict[str, Any]]:
    """Condense all extraction JSONs in a directory."""
    files = sorted(input_dir.glob("*_extraction.json"))
    if not files:
        console.print(f"[red]No extraction JSONs in {input_dir}[/red]")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for f in files:
        stem = f.stem.replace("_extraction", "")
        out_path = output_dir / f"{stem}_condensed.json"

        if skip_existing and out_path.exists():
            console.print(f"  [dim]Skip (exists): {out_path.name}[/dim]")
            condensed = json.loads(out_path.read_text(encoding="utf-8"))
            results.append(condensed)
            continue

        console.print(f"  Condensing [cyan]{f.name}[/cyan]...")
        condensed = condense_file(f, out_path)
        total_fields = sum(len(p.get("fields", {})) for p in condensed["pages"])
        flags = sum(len(p.get("review_flags", [])) for p in condensed["pages"])
        console.print(
            f"    -> {total_fields} fields across {len(condensed['pages'])} pages"
            f"{f', {flags} review flags' if flags else ''}"
        )
        results.append(condensed)

    return results


# ---------------------------------------------------------------------------
# AI verification pass
# ---------------------------------------------------------------------------

def _needs_ai_review(page: dict[str, Any]) -> bool:
    """Decide if a condensed page warrants an AI verification pass."""
    if page.get("review_flags"):
        return True
    if page.get("items_needing_review", 0) > 0:
        return True
    if page.get("page_number") in CRITICAL_PAGES:
        return True
    return False


def _build_verify_prompt(page: dict[str, Any]) -> str:
    """Build a compact LLM prompt for verifying a condensed page."""
    fields_str = json.dumps(page.get("fields", {}), indent=2, ensure_ascii=False)
    flags = page.get("review_flags", [])
    flags_str = "\n".join(f"- {f}" for f in flags) if flags else "(none)"

    return f"""You are a medical form data verification expert. Review this condensed extraction
from page {page.get('page_number', '?')} of an orofacial pain examination form.

EXTRACTED FIELDS:
{fields_str}

REVIEW FLAGS:
{flags_str}

Your tasks:
1. Fix obvious OCR/handwriting misreads (e.g. "67" should be "6-7" on a 0-10 VAS scale)
2. Normalise medication names to standard spellings
3. Flag any internally inconsistent data (e.g. YES answer but no detail where expected)
4. Do NOT add new fields — only correct existing values

Return the corrected fields as a JSON object with the same keys. Only include fields you changed.
If nothing needs correction, return an empty object {{}}.
Output ONLY valid JSON, no commentary."""


def verify_page_with_llm(
    page: dict[str, Any],
    client: Any,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, Any]:
    """Send a condensed page to the LLM for verification, return corrections."""
    import anthropic as _anthropic

    prompt = _build_verify_prompt(page)
    resp = client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def verify_condensed(
    condensed: dict[str, Any],
    client: Any | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict[str, Any]:
    """Run AI verification on flagged/critical pages of a condensed extraction."""
    if client is None:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[yellow]No ANTHROPIC_API_KEY — skipping AI verify[/yellow]")
            return condensed
        client = anthropic.Anthropic(api_key=api_key)

    pages_verified = 0
    for page in condensed.get("pages", []):
        if not _needs_ai_review(page):
            continue

        corrections = verify_page_with_llm(page, client, model)
        if corrections:
            for fid, new_val in corrections.items():
                if fid in page.get("fields", {}):
                    old = page["fields"][fid]
                    page["fields"][fid] = new_val
                    page.setdefault("ai_corrections", []).append({
                        "field": fid,
                        "old": old,
                        "new": new_val,
                    })
            pages_verified += 1

    if pages_verified:
        condensed["ai_verified_pages"] = pages_verified
    return condensed


def verify_all(
    condensed_dir: Path,
    output_dir: Path | None = None,
) -> int:
    """Run AI verification on all condensed JSONs. Overwrites in place or to output_dir."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]ANTHROPIC_API_KEY not set[/red]")
        return 0

    client = anthropic.Anthropic(api_key=api_key)
    dest = output_dir or condensed_dir
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(condensed_dir.glob("*_condensed.json"))
    total_verified = 0

    for f in files:
        condensed = json.loads(f.read_text(encoding="utf-8"))
        pages_needing = sum(1 for p in condensed.get("pages", []) if _needs_ai_review(p))
        if not pages_needing:
            console.print(f"  [dim]Skip (no flags): {f.name}[/dim]")
            continue

        console.print(f"  Verifying [cyan]{f.name}[/cyan] ({pages_needing} pages)...")
        verified = verify_condensed(condensed, client)
        n = verified.get("ai_verified_pages", 0)
        total_verified += n

        out_path = dest / f.name
        out_path.write_text(json.dumps(verified, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"    -> {n} pages corrected")

    return total_verified
