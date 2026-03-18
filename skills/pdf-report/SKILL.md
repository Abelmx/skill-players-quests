---
name: pdf-report
description: Generate PDF reports and documents from data or text. Use when the user asks to create PDF files, reports, or documents.
---

# PDF Report

Generate PDF reports and documents from data or text.

## Usage

```bash
python scripts/generate_pdf.py --title "Report Title" --content "Content text..." --output report.pdf
```

- `--title`: Document title (required)
- `--content`: Content text (required)
- `--output`: Output file path (default: report.pdf)
- `--table`: Optional path to CSV/JSON for table data

## Notes

- Uses reportlab (pip install if needed)
- Creates a simple PDF with title, content paragraphs, and optional table data
