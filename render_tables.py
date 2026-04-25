"""
Render HTML table snippets from llms.json and asrs.json.

Usage:
  python render_tables.py
  python render_tables.py --llm-json llm/llms.json --asr-json asr/asrs.json
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def fmt_pct(value) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def fmt_params(row) -> str:
    params_b = row.get("params_b")
    memory_gb = row.get("memory_gb")
    if params_b is None:
        return "—"
    mem = f"{memory_gb:.1f}GB" if memory_gb is not None else "?"
    return f"{params_b:.0f}B ({mem})"


def render(json_path: Path, template_path: Path, out: Path) -> None:
    data = json.loads(json_path.read_text())
    col_labels = data["text"]
    rows = data["data"]
    cols = [k for k in col_labels if k != "model" and k not in ("cloud", "params_b", "memory_gb")]

    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    env.filters["fmt"] = fmt
    env.filters["fmt_pct"] = fmt_pct
    env.filters["fmt_params"] = fmt_params
    template = env.get_template(template_path.name)

    html = template.render(rows=rows, cols=cols, col_labels=col_labels)
    out.write_text(html, encoding="utf-8")
    print(f"Saved to {out}")


def main():
    parser = argparse.ArgumentParser(description="Render table HTML from JSON")
    parser.add_argument("--llm-json", default="llm/llms.json")
    parser.add_argument("--asr-json", default="asr/asrs.json")
    parser.add_argument("--llm-out", default="llm/llms_table.html")
    parser.add_argument("--asr-out", default="asr/asrs_table.html")
    args = parser.parse_args()

    render(Path(args.llm_json), Path("llm/table_template.jinja"), Path(args.llm_out))
    render(Path(args.asr_json), Path("asr/table_template.jinja"), Path(args.asr_out))


if __name__ == "__main__":
    main()
