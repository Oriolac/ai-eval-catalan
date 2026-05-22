"""
Render ranked-bar-chart HTML from llms.json (CLAM%) and asrs.json (WER).

Usage:
  python render_bar_charts.py
  python render_bar_charts.py --llm-json llm/llms.json --asr-json asr/asrs.json --out bar_charts.html
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


# Color thresholds for CLAM% (higher = better)
def clam_color(pct: float) -> str:
    if pct >= 50:
        return "#388e3c"   # green
    if pct >= 40:
        return "#f9a825"   # amber
    return "#c62828"       # red


# Color thresholds for WER (lower = better)
def wer_color(wer: float) -> str:
    if wer <= 0.10:
        return "#388e3c"   # green
    if wer <= 0.20:
        return "#f9a825"   # amber
    return "#c62828"       # red


def shorten_asr_label(model: str) -> str:
    """Keep the last component, trim long paths like 'projecte-aina/whisper-...'."""
    name = model.split("/")[-1]
    # Abbreviate long names
    if len(name) > 30:
        name = name[:28] + "…"
    return name


def shorten_llm_label(model: str) -> str:
    """Clean up llm model names for display."""
    # Strip org prefix (e.g. 'google_gemma-3-12b-it' → 'gemma-3-12b-it')
    if "_" in model and not model.startswith("gpt") and not model.startswith("gemini"):
        model = model.split("_", 1)[-1]
    # Strip '-it' suffix
    import re
    model = re.sub(r"-it$", "", model)
    return model


def build_clam_chart(data: list[dict]) -> dict:
    max_val = max(r["clam_pct"] for r in data if r["clam_pct"] is not None)
    threshold = 50.0          # "usable for Catalan tasks"
    threshold_pct = (threshold / max_val) * 100

    rows = []
    for r in data:
        if r["clam_pct"] is None:
            continue
        pct = r["clam_pct"]
        rows.append({
            "label": shorten_llm_label(r["model"]),
            "bar_pct": (pct / max_val) * 100,
            "color": clam_color(pct),
            "display": f"{pct:.1f}%",
        })

    return {
        "title": "CLAM % — LLMs en català",
        "subtitle": "50% usable",
        "threshold_pct": threshold_pct,
        "threshold_label": "> 50% el considerem usable",
        "caption": "Línia discontínua al 50% = \"usable per a tasques en català\"",
        "rows": rows,
    }


def build_wer_chart(data: list[dict]) -> dict:
    # Exclude VibeVoice outlier (WER=1.0) from scaling
    valid = [r for r in data if r["wer"] is not None and r["wer"] < 1.0]
    max_val = max(r["wer"] for r in valid)
    threshold = 0.10          # "near-human transcription"
    threshold_pct = (threshold / max_val) * 100

    rows = []
    for r in valid:
        wer = r["wer"]
        rows.append({
            "label": shorten_asr_label(r["model"]),
            "bar_pct": (wer / max_val) * 100,
            "color": wer_color(wer),
            "display": f"{wer*100:.2f}%",
            "cloud": r.get("cloud", False),
        })

    return {
        "title": "WER — Models ASR en català (menor = millor)",
        "subtitle": "10% habilitat d'un humà",
        "threshold_pct": threshold_pct,
        "threshold_label": "10% habilitat d'un humà",
        "caption": "Línia discontínua al 10% ≈ \"habilitat d'un humà\"",
        "rows": rows,
    }


def render(template, charts: list[dict], out: Path) -> None:
    html = template.render(charts=charts)
    out.write_text(html, encoding="utf-8")
    print(f"Saved to {out}")


def main():
    parser = argparse.ArgumentParser(description="Render bar charts HTML")
    parser.add_argument("--llm-json", default="llm/llms.json")
    parser.add_argument("--asr-json", default="asr/asrs.json")
    parser.add_argument("--llm-out", default="llm/llms_bar.html")
    parser.add_argument("--asr-out", default="asr/asrs_bar.html")
    args = parser.parse_args()

    template_path = Path(__file__).parent / "bar_chart_template.jinja"
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)

    llm_data = json.loads(Path(args.llm_json).read_text())["data"]
    render(template, [build_clam_chart(llm_data)], Path(args.llm_out))

    asr_data = json.loads(Path(args.asr_json).read_text())["data"]
    render(template, [build_wer_chart(asr_data)], Path(args.asr_out))


if __name__ == "__main__":
    main()
