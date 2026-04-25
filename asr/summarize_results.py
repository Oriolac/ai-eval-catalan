"""
Reads all ASR result JSONs and generates a summary table.

Usage:
  python summarize_results.py
  python summarize_results.py --results-dir evals
  python summarize_results.py --json-out asrs.json --table-out asrs_table.html
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


COLUMN_LABELS = {
    "model": "Model",
    "wer": "WER",
    "cer": "CER",
    "rtf": "RTF",
}

METRICS = ["wer", "cer", "rtf"]


def load_results(results_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(results_dir.glob("results_*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            fleurs = data.get("benchmarks", {}).get("fleurs_ca", {})
            rows.append({
                "model": data.get("model", path.stem),
                "wer": fleurs.get("wer"),
                "cer": fleurs.get("cer"),
                "rtf": fleurs.get("rtf"),
                "n": fleurs.get("n"),
            })
        except Exception:
            pass
    return rows


def fmt(value, digits=4) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def render_table(rows: list, template_path: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    env.filters["fmt"] = fmt
    template = env.get_template(template_path.name)
    return template.render(rows=rows, cols=METRICS, col_labels=COLUMN_LABELS)


def main():
    parser = argparse.ArgumentParser(description="Summarize ASR eval results")
    parser.add_argument("--results-dir", default="evals")
    parser.add_argument("--table-out", "--html", default="asrs_table.html", dest="table_out")
    parser.add_argument("--json-out", default="asrs.json")
    args = parser.parse_args()

    rows = load_results(Path(args.results_dir))
    if not rows:
        print("No result files found.")
        return

    rows.sort(key=lambda r: r["wer"] if r["wer"] is not None else 9999)

    # ── Console table ─────────────────────────────────────────────────────────
    label_w = max(len(r["model"]) for r in rows) + 2
    header = f"{'Model':<{label_w}}{'WER':>10}{'CER':>10}{'RTF':>10}{'Real-time':>12}{'N':>6}"
    sep = "-" * len(header)

    print(f"\nASR Results — FLEURS Catalan ({len(rows)} model(s))")
    print(sep)
    print(header)
    print(sep)
    for r in rows:
        rt = f"{1/r['rtf']:.1f}x" if r["rtf"] else "—"
        n = str(r["n"]) if r["n"] else "—"
        print(f"{r['model']:<{label_w}}{fmt(r['wer']):>10}{fmt(r['cer']):>10}{fmt(r['rtf']):>10}{rt:>12}{n:>6}")
    print(sep)

    # ── HTML table snippet ────────────────────────────────────────────────────
    template_path = Path(__file__).parent / "table_template.jinja"
    if template_path.exists():
        table_out = Path(args.table_out)
        table_out.write_text(render_table(rows, template_path), encoding="utf-8")
        print(f"Table snippet saved to {table_out}")
    else:
        print(f"Table template {template_path} not found, skipping.")

    # ── JSON export ───────────────────────────────────────────────────────────
    json_text = {k: COLUMN_LABELS.get(k, k) for k in ["model"] + METRICS}
    json_rows = [
        {
            "model": r["model"],
            **{k: round(r[k], 4) if r.get(k) is not None else None for k in METRICS},
        }
        for r in rows
    ]
    json_path = Path(args.json_out)
    json_path.write_text(
        json.dumps({"text": json_text, "data": json_rows}, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"JSON saved to {json_path}")


if __name__ == "__main__":
    main()
