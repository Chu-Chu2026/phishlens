"""Convert a Markdown briefing into a clean printable PDF."""

from __future__ import annotations

import argparse
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
LEFT = 18
RIGHT = 18
USABLE = 210 - LEFT - RIGHT


def _safe(text: str) -> str:
    return (
        text.replace("**", "")
        .replace("`", "")
        .replace("—", "-")
        .replace("–", "-")
        .replace("'", "'")
        .replace("'", "'")
        .replace(""", '"')
        .replace(""", '"')
        .replace("…", "...")
        .replace("→", "->")
        .replace("×", "x")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


class PDF(FPDF):
    def __init__(self, footer_label: str = "PhishLens Report", **kwargs):
        super().__init__(**kwargs)
        self.footer_label = footer_label

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            10,
            f"{self.footer_label}  |  Page {self.page_no()}",
            align="C",
        )


def _reset_x(pdf: PDF) -> None:
    pdf.set_x(LEFT)


def _ensure_space(pdf: PDF, needed: float = 20) -> None:
    if pdf.get_y() > 297 - 18 - needed:
        pdf.add_page()
        _reset_x(pdf)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Markdown briefing to PDF.")
    parser.add_argument(
        "--md",
        default=str(ROOT / "REPORT_WRITING_ARTIFACT.md"),
        help="Input Markdown path",
    )
    parser.add_argument(
        "--pdf",
        default=str(ROOT / "REPORT_WRITING_ARTIFACT.pdf"),
        help="Output PDF path",
    )
    parser.add_argument(
        "--title",
        default="PhishLens - Project Report Writing Artifact",
        help="Cover title",
    )
    parser.add_argument(
        "--subtitle",
        default="Explainable Ensemble Machine Learning (EEML) for Phishing URL Detection",
        help="Cover subtitle",
    )
    parser.add_argument(
        "--footer",
        default="PhishLens Report Writing Artifact",
        help="Footer label",
    )
    args = parser.parse_args()

    md_path = Path(args.md)
    pdf_path = Path(args.pdf)
    lines = md_path.read_text(encoding="utf-8").splitlines()
    pdf = PDF(format="A4", footer_label=args.footer)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_left_margin(LEFT)
    pdf.set_right_margin(RIGHT)

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(USABLE, 8, args.title)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(USABLE, 6, args.subtitle)
    pdf.ln(3)
    pdf.set_draw_color(80, 80, 80)
    pdf.line(LEFT, pdf.get_y(), LEFT + USABLE, pdf.get_y())
    pdf.ln(5)

    i = 0
    first_h1_skipped = False
    while i < len(lines):
        raw = lines[i].rstrip()
        _reset_x(pdf)

        if raw.startswith("# ") and not first_h1_skipped:
            first_h1_skipped = True
            i += 1
            continue

        if raw.startswith("---"):
            pdf.ln(2)
            pdf.line(LEFT, pdf.get_y(), LEFT + USABLE, pdf.get_y())
            pdf.ln(4)
            i += 1
            continue

        if raw.startswith("```"):
            _ensure_space(pdf, 30)
            pdf.set_font("Courier", "", 8)
            pdf.set_fill_color(245, 245, 245)
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                _reset_x(pdf)
                pdf.multi_cell(USABLE, 4.5, _safe(lines[i]), fill=True)
                i += 1
            i += 1
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            continue

        if raw.startswith("|") and "|" in raw[1:]:
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if all(set(c) <= set("-: ") and c for c in cells):
                    i += 1
                    continue
                rows.append([_safe(c) for c in cells])
                i += 1
            if not rows:
                continue
            ncols = max(len(r) for r in rows)
            col_w = USABLE / ncols
            for r_idx, row in enumerate(rows):
                _ensure_space(pdf, 12)
                _reset_x(pdf)
                pdf.set_font("Helvetica", "B" if r_idx == 0 else "", 7)
                while len(row) < ncols:
                    row.append("")
                for cell in row:
                    txt = cell if len(cell) <= 40 else cell[:37] + "..."
                    pdf.cell(col_w, 6, txt, border=1)
                pdf.ln(6)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
            continue

        if raw.startswith("### "):
            _ensure_space(pdf, 16)
            pdf.set_font("Helvetica", "B", 12)
            pdf.ln(2)
            pdf.multi_cell(USABLE, 7, _safe(raw[4:]))
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(1)
        elif raw.startswith("## "):
            _ensure_space(pdf, 24)
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(3)
            pdf.multi_cell(USABLE, 7, _safe(raw[3:]))
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(2)
        elif raw.startswith("> "):
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(USABLE, 5.5, _safe(raw[2:]))
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
            pdf.ln(1)
        elif raw.startswith("- ") or raw.startswith("* "):
            pdf.multi_cell(USABLE, 5.5, _safe("- " + raw[2:]))
        elif len(raw) >= 3 and raw[0].isdigit() and raw[1] == ".":
            pdf.multi_cell(USABLE, 5.5, _safe(raw))
        elif raw.strip() == "":
            pdf.ln(2)
        elif raw.startswith("*End"):
            pdf.ln(4)
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(USABLE, 5, _safe(raw.strip("* ")))
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(USABLE, 5.5, _safe(raw))

        i += 1

    pdf.output(str(pdf_path))
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
