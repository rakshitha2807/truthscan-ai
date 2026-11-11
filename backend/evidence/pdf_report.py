
import json
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)
from xml.sax.saxutils import escape


# ==========================================
# TRUTHSCAN AI - PDF EVIDENCE REPORT
# ==========================================

project_root = Path(__file__).resolve().parents[2]

report_json = project_root / "reports" / "evidence_report.json"

graph_image = project_root / "reports" / "evidence_graph.png"

output_pdf = project_root / "reports" / "truthscan_evidence_report.pdf"


# ==========================================
# CHECK INPUT FILES
# ==========================================

if not report_json.exists():
    raise FileNotFoundError(
        "evidence_report.json not found. Run graph.py first."
    )


# ==========================================
# LOAD JSON DATA
# ==========================================

with open(report_json, "r", encoding="utf-8") as file:
    data = json.load(file)


summary = data["summary"]
documents = data.get("documents", [])
contradictions = data.get("contradictions", [])


# ==========================================
# CREATE PDF DOCUMENT
# ==========================================

pdf = SimpleDocTemplate(
    str(output_pdf),
    pagesize=A4,
    rightMargin=45,
    leftMargin=45,
    topMargin=45,
    bottomMargin=45
)


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontSize=23,
    textColor=colors.HexColor("#174A3A"),
    alignment=1,
    spaceAfter=12
)

heading_style = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading2"],
    textColor=colors.HexColor("#174A3A"),
    spaceBefore=15,
    spaceAfter=10
)

normal_style = styles["BodyText"]

story = []


# ==========================================
# TITLE
# ==========================================

story.append(
    Paragraph("TRUTHSCAN AI", title_style)
)

story.append(
    Paragraph(
        "DIGITAL EVIDENCE ANALYSIS REPORT",
        styles["Heading2"]
    )
)

story.append(Spacer(1, 15))

story.append(
    Paragraph(
        "Generated on: " + datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        ),
        normal_style
    )
)

story.append(Spacer(1, 20))


# ==========================================
# EXECUTIVE SUMMARY
# ==========================================

story.append(
    Paragraph("1. Executive Summary", heading_style)
)

summary_data = [
    ["Parameter", "Result"],

    ["Total Documents", str(summary.get("total_documents", 0))],

    ["Total Contradictions",
     str(summary.get("total_contradictions", 0))],

    ["OCR Uncertain Documents",
     str(summary.get("ocr_uncertain_documents", 0))],

    ["Overall Status", summary.get("status", "UNKNOWN")]
]

summary_table = Table(
    summary_data,
    colWidths=[240, 220]
)

summary_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0),
     colors.HexColor("#174A3A")),

    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

    ("PADDING", (0, 0), (-1, -1), 9),

    ("BACKGROUND", (0, 1), (-1, -1),
     colors.HexColor("#F0F5F2"))
]))

story.append(summary_table)

story.append(Spacer(1, 20))


# ==========================================
# DOCUMENT ANALYSIS
# ==========================================

story.append(
    Paragraph("2. Document Analysis", heading_style)
)

for index, document in enumerate(documents, start=1):

    story.append(
        Paragraph(
            f"Document {index}: {escape(str(document.get('file', 'Unknown')))}",
            styles["Heading3"]
        )
    )

    fields = document.get("fields", {})

    extracted_data = [
        ["Field", "Extracted Value"],

        ["Amounts", str(fields.get("amounts", []))],

        ["Dates", str(fields.get("dates", []))],

        ["Transaction IDs",
         str(fields.get("transaction_ids", []))],

        ["Payment Status",
         str(fields.get("statuses", []))],

        ["OCR Confidence",
         str(document.get("ocr_confidence", "N/A"))],

        ["OCR Agreement",
         str(document.get("ocr_versions_agree", "N/A"))],

        ["Amount Review Required",
         str(document.get("amount_review_required", False))]
    ]

    table = Table(
        extracted_data,
        colWidths=[180, 280]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#DCEBE3")),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("PADDING", (0, 0), (-1, -1), 7),

        ("VALIGN", (0, 0), (-1, -1), "TOP")
    ]))

    story.append(table)

    story.append(Spacer(1, 15))


# ==========================================
# CONTRADICTION ANALYSIS
# ==========================================

story.append(
    Paragraph("3. Contradiction Analysis", heading_style)
)

if contradictions:

    for index, issue in enumerate(contradictions, start=1):

        story.append(
            Paragraph(
                f"<b>Issue {index}: {escape(str(issue.get('type', 'Unknown')))}</b>",
                normal_style
            )
        )

        issue_data = [
            ["Parameter", "Value"],

            ["Field", str(issue.get("field", "N/A"))],

            ["Document 1", str(issue.get("file1", "N/A"))],

            ["Document 2", str(issue.get("file2", "N/A"))],

            ["Value 1", str(issue.get("value1", "N/A"))],

            ["Value 2", str(issue.get("value2", "N/A"))],

            ["Description", str(issue.get("message", "N/A"))]
        ]

        issue_table = Table(
            issue_data,
            colWidths=[180, 280]
        )

        issue_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#FCE4E4")),

            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

            ("PADDING", (0, 0), (-1, -1), 7)
        ]))

        story.append(issue_table)

        story.append(Spacer(1, 15))

else:

    story.append(
        Paragraph(
            "No contradictions were detected.",
            normal_style
        )
    )


# ==========================================
# EVIDENCE GRAPH
# ==========================================

story.append(
    Paragraph("4. Evidence Graph", heading_style)
)

if graph_image.exists():

    graph = Image(str(graph_image))

    graph.drawWidth = 6.5 * inch
    graph.drawHeight = 4.5 * inch

    story.append(graph)

else:

    story.append(
        Paragraph(
            "Evidence graph image is not available.",
            normal_style
        )
    )


# ==========================================
# FINAL DISCLAIMER
# ==========================================

story.append(Spacer(1, 20))

story.append(
    Paragraph("5. Important Note", heading_style)
)

story.append(
    Paragraph(
        "This report presents automated OCR-based evidence "
        "analysis. Detected inconsistencies and OCR uncertainties "
        "require human verification. A contradiction does not "
        "automatically establish fraud or document manipulation.",
        normal_style
    )
)


# ==========================================
# GENERATE PDF
# ==========================================

pdf.build(story)

print("\n===================================")
print(" TRUTHSCAN AI PDF REPORT GENERATED")
print("===================================")

print("Saved at:", output_pdf)
