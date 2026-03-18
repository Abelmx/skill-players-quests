#!/usr/bin/env python3
"""Generate PDF reports from title, content, and optional table data."""
import argparse
import csv
import json
import sys


def ensure_reportlab():
    """Install reportlab if needed."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def load_table_data(path: str) -> list:
    """Load table data from CSV or JSON."""
    with open(path) as f:
        if path.endswith(".json"):
            data = json.load(f)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
                rows = [headers] + [[row.get(h, "") for h in headers] for row in data]
            else:
                rows = data
        else:
            reader = csv.reader(f)
            rows = list(reader)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate PDF report")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("--content", required=True, help="Content text (paragraphs separated by newlines)")
    parser.add_argument("--output", default="report.pdf", help="Output file path")
    parser.add_argument("--table", help="Path to CSV or JSON for table data")
    args = parser.parse_args()

    ensure_reportlab()

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(args.output, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(args.title, styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    for para in args.content.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

    if args.table:
        try:
            rows = load_table_data(args.table)
            if rows:
                t = Table(rows)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), "#eeeeee"),
                    ("TEXTCOLOR", (0, 0), (-1, 0), "#000000"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), "#ffffff"),
                    ("GRID", (0, 0), (-1, -1), 0.5, "#cccccc"),
                ]))
                story.append(Spacer(1, 0.3 * inch))
                story.append(t)
        except OSError as e:
            print(f"Warning: Could not load table: {e}", file=sys.stderr)

    doc.build(story)
    print(f"PDF saved to {args.output}")


if __name__ == "__main__":
    main()
