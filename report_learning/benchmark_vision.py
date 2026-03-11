"""
Vision Model Benchmark for Medical Form Extraction
===================================================
Tests 10 vision model configs against user-verified ground truth
for the AUBRIE VASQUEZ INIT orofacial pain exam form (page 1).

Usage:
    cd form-extractor
    python -m report_learning.benchmark_vision
"""

import base64
import io
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).parent
PDF_PATH = (
    SCRIPT_DIR
    / "training_data"
    / "source_forms"
    / "Matthew Signed Documents"
    / "AUBRIE VASQUEZ INIT.pdf"
)
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "benchmark"
EXAM_PAGE = 3  # 1-indexed PDF page (first exam page after 2 lawyer pages)

# ============================================================
# GROUND TRUTH  (user-verified against the physical form)
# ============================================================

GROUND_TRUTH_YES_NO: dict[int, tuple[str, str]] = {
    1:  ("NO",  "heart problems"),
    2:  ("NO",  "metal joint replacements"),
    3:  ("NO",  "high blood pressure"),
    4:  ("NO",  "diabetes"),
    5:  ("YES", "stomach acids"),
    6:  ("NO",  "kidney problems"),
    7:  ("NO",  "thyroid problem"),
    8:  ("NO",  "HIV/hepatitis/TB/VD"),
    9:  ("NO",  "blood thinners"),
    10: ("YES", "breathing problems"),
    11: ("YES", "numbness/pins and needles"),
    12: ("NO",  "liver problems"),
    13: ("NO",  "urinary problems"),
    14: ("YES", "awakens to urinate"),
    15: ("YES", "sleep study"),
    16: ("NO",  "CPAP mask"),
    17: ("YES", "morning headache"),
}

GROUND_TRUTH_HEADER = {
    "name": "aubrie vasquez",
    "date": "11/18/2025",
    "birth_date": "08/16/1994",
    "sex": "female",
}

GROUND_TRUTH_ALLERGIES = "caphor"
GROUND_TRUTH_DX_MARKS = {"diabetes", "gastric"}

GROUND_TRUTH_FOLLOW_UPS = {
    4:  "pre",
    10: "asthma",
    11: "fingers",
    14: "3",
    15: "2018",
}

# ============================================================
# MODEL CONFIGURATIONS
# ============================================================


@dataclass
class ModelConfig:
    name: str
    provider: str
    model_id: str
    base_url: Optional[str] = None
    api_key_env: str = ""
    price_in: float = 0.0
    price_out: float = 0.0
    prompt_key: str = "standard"
    dpi: int = 150
    max_dim: int = 1568


MODELS = [
    ModelConfig(
        "Qwen3-VL-8B", "together", "Qwen/Qwen3-VL-8B-Instruct",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.08, 0.50,
    ),
    ModelConfig(
        "Qwen3-VL-8B (enh)", "together", "Qwen/Qwen3-VL-8B-Instruct",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.08, 0.50, "enhanced",
    ),
    ModelConfig(
        "Qwen3-VL-8B 300dpi", "together", "Qwen/Qwen3-VL-8B-Instruct",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.08, 0.50, "enhanced", 300, 2048,
    ),
    ModelConfig(
        "Qwen3-VL-32B", "together", "Qwen/Qwen3-VL-32B-Instruct",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.50, 1.50,
    ),
    ModelConfig(
        "Qwen3-VL-235B", "together", "Qwen/Qwen3-VL-235B-A22B-Instruct-FP8",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.20, 6.00,
    ),
    ModelConfig(
        "Qwen2.5-VL-72B", "together", "Qwen/Qwen2.5-VL-72B-Instruct",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 1.95, 8.00,
    ),
    ModelConfig(
        "Llama4 Maverick", "together",
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.27, 0.85,
    ),
    ModelConfig(
        "Kimi K2.5 (TG)", "together", "moonshotai/Kimi-K2.5",
        "https://api.together.xyz/v1", "TOGETHER_API_KEY", 0.50, 2.80,
    ),
    ModelConfig(
        "Kimi K2.5 (FW)", "fireworks", "accounts/fireworks/models/kimi-k2p5",
        "https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY", 0.50, 2.80,
    ),
    ModelConfig(
        "Claude Sonnet 4", "anthropic", "claude-sonnet-4-20250514",
        None, "ANTHROPIC_API_KEY", 3.00, 15.00,
    ),
]

# ============================================================
# PROMPTS
# ============================================================

STANDARD_PROMPT = """\
You are analyzing page 1 of a filled-out orofacial pain examination form.
Extract ALL handwritten and circled data visible on this page.

This page contains:
1. HEADER at top: patient name, date, birth date, sex (Male or Female circled)
2. 17 NUMBERED YES/NO medical history questions — the patient CIRCLES either "YES" or "NO"
3. ALLERGIES field with handwritten text
4. MEDICATION TABLE at bottom with a "DX Post-Injury" column where X marks may appear

Return ONLY valid JSON with exactly this structure:
{
  "header": {
    "name": "", "date": "", "birth_date": "", "sex": ""
  },
  "yes_no_questions": [
    {"number": 1, "topic": "brief topic", "answer": "YES or NO", "notes": "any handwritten notes"}
  ],
  "allergies": "",
  "dx_post_injury_marks": ["row name where X appears in DX Post-Injury column"],
  "other_observations": []
}

Include all 17 questions numbered 1 through 17.
For each question report ONLY what is visibly circled on the form."""

ENHANCED_PROMPT = """\
You are analyzing page 1 of a filled-out orofacial pain examination form.
Extract ALL handwritten and circled data visible on this page.

This page contains:
1. HEADER at top: patient name, date, birth date, sex (Male or Female circled)
2. 17 NUMBERED YES/NO medical history questions
3. ALLERGIES field
4. MEDICATION TABLE at bottom with "DX Post-Injury" column

CRITICAL — HOW TO READ YES/NO QUESTIONS:
- Each question has the words "YES" and "NO" printed side by side on the form.
- The patient draws a hand-drawn CIRCLE (oval or ring shape) around ONE of them.
- A circle ENCLOSING "YES" means the answer is YES.
- A circle ENCLOSING "NO" means the answer is NO.
- NOT all answers are the same — some are YES and some are NO.
- You MUST look at each question individually.
- If you see a curved mark surrounding "YES", the answer is YES.
- If you see a curved mark surrounding "NO", the answer is NO.
- SEVERAL questions on this form ARE answered YES — look carefully.

For each question, briefly note what you see in "observation" before giving your answer.

Return ONLY valid JSON:
{
  "header": {
    "name": "", "date": "", "birth_date": "", "sex": ""
  },
  "yes_no_questions": [
    {"number": 1, "topic": "brief topic", "observation": "what you see", "answer": "YES or NO", "notes": "handwritten notes if any"}
  ],
  "allergies": "",
  "dx_post_injury_marks": ["row name where X appears"],
  "other_observations": []
}

Include all 17 questions numbered 1 through 17."""

PROMPTS = {"standard": STANDARD_PROMPT, "enhanced": ENHANCED_PROMPT}

# ============================================================
# IMAGE PREPARATION
# ============================================================


def prepare_image(
    pdf_path: Path, page_num: int, dpi: int = 150, max_dim: int = 1568
) -> tuple[str, str]:
    from pdf2image import convert_from_path

    images = convert_from_path(
        str(pdf_path), dpi=dpi, first_page=page_num, last_page=page_num
    )
    img = images[0].convert("RGB")
    w, h = img.size
    console.print(f"    Raw: {w}x{h} @ {dpi} DPI")

    if w > max_dim or h > max_dim:
        ratio = min(max_dim / w, max_dim / h)
        nw, nh = int(w * ratio), int(h * ratio)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        console.print(f"    Resized: {nw}x{nh}")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    buf.seek(0)
    b64 = base64.standard_b64encode(buf.read()).decode("utf-8")
    console.print(f"    JPEG: {len(b64) * 3 / 4 / 1024:.0f} KB")
    return b64, "image/jpeg"


# ============================================================
# API CALLERS
# ============================================================


def _call_openai_compat(
    cfg: ModelConfig, b64: str, mtype: str, prompt: str
) -> dict:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv(cfg.api_key_env),
        base_url=cfg.base_url,
        timeout=180.0,
    )
    kwargs: dict = dict(
        model=cfg.model_id,
        max_tokens=4096,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mtype};base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    start = time.time()
    try:
        kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
    except Exception:
        kwargs.pop("response_format", None)
        resp = client.chat.completions.create(**kwargs)

    elapsed = time.time() - start
    text = resp.choices[0].message.content or ""
    usage = {}
    if resp.usage:
        usage = {
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    return {"text": text, "elapsed": elapsed, "usage": usage}


def _call_anthropic(
    cfg: ModelConfig, b64: str, mtype: str, prompt: str
) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv(cfg.api_key_env))
    start = time.time()
    resp = client.messages.create(
        model=cfg.model_id,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mtype,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    elapsed = time.time() - start
    text = resp.content[0].text
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return {"text": text, "elapsed": elapsed, "usage": usage}


def call_model(cfg: ModelConfig, b64: str, mtype: str, prompt: str) -> dict:
    if cfg.provider == "anthropic":
        return _call_anthropic(cfg, b64, mtype, prompt)
    return _call_openai_compat(cfg, b64, mtype, prompt)


# ============================================================
# PARSING & SCORING
# ============================================================


def extract_json(text: str) -> Optional[dict]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if 0 <= start < end:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                return None
    return None


def _find_questions(data: dict) -> list:
    for key in (
        "yes_no_questions",
        "questions",
        "medical_questions",
        "medical_history_questions",
    ):
        if key in data and isinstance(data[key], list):
            return data[key]
    for val in data.values():
        if isinstance(val, list) and val and isinstance(val[0], dict):
            if any(k in val[0] for k in ("answer", "response", "number")):
                return val
    return []


def _get_answer(q: dict) -> tuple[Optional[int], Optional[str], str]:
    num = None
    for k in ("number", "num", "question_number", "q"):
        if k in q:
            try:
                num = int(q[k])
            except (ValueError, TypeError):
                pass
            break

    answer = None
    for k in ("answer", "response", "circled", "value"):
        if k in q and q[k]:
            raw = str(q[k]).strip().upper()
            if raw in ("YES", "NO"):
                answer = raw
            elif "YES" in raw:
                answer = "YES"
            elif "NO" in raw:
                answer = "NO"
            break

    notes = str(
        q.get("notes") or q.get("observation") or q.get("details") or ""
    )
    return num, answer, notes


def score_result(data: dict) -> dict:
    scores: dict = {
        "yn_correct": 0,
        "yn_total": 17,
        "yes_hit": 0,
        "yes_total": 6,
        "no_hit": 0,
        "no_total": 11,
        "hdr_hit": 0,
        "hdr_total": 4,
        "allergy_ok": False,
        "dx_hit": 0,
        "dx_total": 2,
        "followup_hit": 0,
        "followup_total": len(GROUND_TRUTH_FOLLOW_UPS),
        "per_q": {},
    }

    questions = _find_questions(data)
    q_map: dict[int, tuple[Optional[str], str]] = {}
    for q in questions:
        num, answer, notes = _get_answer(q)
        if num:
            q_map[num] = (answer, notes)

    for qn, (gt_ans, _topic) in GROUND_TRUTH_YES_NO.items():
        model_ans, model_notes = q_map.get(qn, (None, ""))
        ok = model_ans == gt_ans
        if ok:
            scores["yn_correct"] += 1
            if gt_ans == "YES":
                scores["yes_hit"] += 1
            else:
                scores["no_hit"] += 1
        scores["per_q"][qn] = {
            "expected": gt_ans,
            "got": model_ans or "MISS",
            "ok": ok,
            "notes": model_notes,
        }

    for qn, kw in GROUND_TRUTH_FOLLOW_UPS.items():
        _, notes = q_map.get(qn, (None, ""))
        if notes and kw in notes.lower():
            scores["followup_hit"] += 1

    header = data.get("header", {})
    for field_name in ("name", "date", "birth_date", "sex"):
        mv = str(header.get(field_name, "")).lower().strip()
        gv = GROUND_TRUTH_HEADER[field_name]
        if gv in mv or mv in gv:
            scores["hdr_hit"] += 1

    allergy_val = str(data.get("allergies", "")).lower().strip()
    scores["allergy_ok"] = GROUND_TRUTH_ALLERGIES in allergy_val

    marks = [str(m).lower() for m in data.get("dx_post_injury_marks", [])]
    for expected in GROUND_TRUTH_DX_MARKS:
        if any(expected in m for m in marks):
            scores["dx_hit"] += 1

    return scores


# ============================================================
# DISPLAY
# ============================================================


def print_results(results: list[dict]):
    table = Table(title="Vision Model Benchmark — AUBRIE VASQUEZ Page 1", show_lines=True)
    table.add_column("Model", style="bold", width=20)
    table.add_column("Y/N\n/17", justify="center", width=6)
    table.add_column("YES\n/6", justify="center", width=5)
    table.add_column("NO\n/11", justify="center", width=5)
    table.add_column("Hdr\n/4", justify="center", width=5)
    table.add_column("Alrg", justify="center", width=5)
    table.add_column("DX\n/2", justify="center", width=4)
    table.add_column("Nts\n/5", justify="center", width=4)
    table.add_column("Time", justify="right", width=6)
    table.add_column("Cost", justify="right", width=8)
    table.add_column("", width=8)

    for r in results:
        if r["status"] != "ok":
            err = r.get("error", "?")[:18]
            table.add_row(
                r["model"], *(["-"] * 8), f"[red]{err}[/red]",
            )
            continue

        s = r["scores"]
        yn_pct = s["yn_correct"] / s["yn_total"]
        yes_pct = s["yes_hit"] / s["yes_total"]
        yn_c = "green" if yn_pct >= 0.9 else "yellow" if yn_pct >= 0.7 else "red"
        yes_c = "green" if yes_pct >= 0.8 else "yellow" if yes_pct >= 0.5 else "red"

        cost = 0.0
        u = r.get("usage", {})
        if u:
            cost = (
                u.get("input_tokens", 0) / 1_000_000 * r["price_in"]
                + u.get("output_tokens", 0) / 1_000_000 * r["price_out"]
            )

        table.add_row(
            r["model"],
            f"[{yn_c}]{s['yn_correct']}/{s['yn_total']}[/{yn_c}]",
            f"[{yes_c}]{s['yes_hit']}/{s['yes_total']}[/{yes_c}]",
            f"{s['no_hit']}/{s['no_total']}",
            f"{s['hdr_hit']}/{s['hdr_total']}",
            "[green]Y[/green]" if s["allergy_ok"] else "[red]N[/red]",
            f"{s['dx_hit']}/{s['dx_total']}",
            f"{s['followup_hit']}/{s['followup_total']}",
            f"{r['elapsed']:.1f}s",
            f"${cost:.4f}",
            "[green]OK[/green]",
        )

    console.print(table)

    console.print("\n[bold]Wrong Answers Detail:[/bold]")
    for r in results:
        if r["status"] != "ok":
            continue
        s = r["scores"]
        wrong = [
            f"Q{qn}({d['expected']}->{d['got']})"
            for qn, d in sorted(s["per_q"].items())
            if not d["ok"]
        ]
        if wrong:
            console.print(f"  {r['model']}: [red]{', '.join(wrong)}[/red]")
        else:
            console.print(f"  {r['model']}: [green]ALL CORRECT[/green]")


# ============================================================
# MAIN
# ============================================================


def main():
    load_dotenv(SCRIPT_DIR.parent / ".env")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not PDF_PATH.exists():
        console.print(f"[red]PDF not found: {PDF_PATH}[/red]")
        sys.exit(1)

    console.print(
        Panel(
            "[bold]Vision Model Benchmark[/bold]\n"
            f"File: AUBRIE VASQUEZ INIT.pdf — Exam Page 1 (PDF page {EXAM_PAGE})\n"
            f"Models: {len(MODELS)} configs\n"
            f"Ground truth: 17 YES/NO, 4 header fields, allergies, 2 DX marks"
        )
    )

    console.print("\n[bold]Preparing images...[/bold]")
    images: dict[str, tuple[str, str]] = {}
    for dpi, max_dim in {(cfg.dpi, cfg.max_dim) for cfg in MODELS}:
        key = f"{dpi}_{max_dim}"
        console.print(f"  [{key}] page {EXAM_PAGE} @ {dpi} DPI, max {max_dim}px")
        images[key] = prepare_image(PDF_PATH, EXAM_PAGE, dpi, max_dim)

    results: list[dict] = []
    total = len(MODELS)
    t0 = time.time()

    for i, cfg in enumerate(MODELS):
        tag = f"({i + 1}/{total})"
        console.print(f"\n[bold cyan]{tag} {cfg.name}[/bold cyan]  [{cfg.model_id}]")

        if not os.getenv(cfg.api_key_env):
            console.print(f"  [yellow]SKIP — {cfg.api_key_env} not set[/yellow]")
            results.append({"model": cfg.name, "status": "error", "error": "no API key"})
            continue

        img_key = f"{cfg.dpi}_{cfg.max_dim}"
        b64, mtype = images[img_key]
        prompt = PROMPTS[cfg.prompt_key]

        try:
            raw = call_model(cfg, b64, mtype, prompt)
            parsed = extract_json(raw["text"])

            if not parsed:
                console.print("  [red]JSON parse failed[/red]")
                (OUTPUT_DIR / f"{_safe(cfg.name)}_RAW.txt").write_text(
                    raw["text"], encoding="utf-8"
                )
                results.append({
                    "model": cfg.name, "status": "error",
                    "error": "JSON parse", "elapsed": raw["elapsed"],
                })
                continue

            scores = score_result(parsed)

            out = {
                "model": cfg.name,
                "model_id": cfg.model_id,
                "prompt": cfg.prompt_key,
                "dpi": cfg.dpi,
                "parsed_response": parsed,
                "scores": scores,
                "usage": raw.get("usage", {}),
                "elapsed_s": raw["elapsed"],
            }
            (OUTPUT_DIR / f"{_safe(cfg.name)}.json").write_text(
                json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            console.print(
                f"  [green]OK[/green]  Y/N={scores['yn_correct']}/17  "
                f"YES={scores['yes_hit']}/6  "
                f"{raw['elapsed']:.1f}s"
            )

            results.append({
                "model": cfg.name,
                "status": "ok",
                "scores": scores,
                "usage": raw.get("usage", {}),
                "elapsed": raw["elapsed"],
                "price_in": cfg.price_in,
                "price_out": cfg.price_out,
            })

        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/red]")
            results.append({
                "model": cfg.name, "status": "error",
                "error": str(e)[:120], "elapsed": 0,
            })

        time.sleep(1)

    wall = time.time() - t0
    console.print(f"\n[dim]Total wall time: {wall:.0f}s[/dim]\n")
    print_results(results)

    summary_path = OUTPUT_DIR / "summary.json"
    summary_path.write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    console.print(f"\n[dim]All results saved to {OUTPUT_DIR}[/dim]")


def _safe(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")


if __name__ == "__main__":
    main()
