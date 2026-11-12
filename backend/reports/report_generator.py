"""Generate a PDF summary from stress_results.json."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def generate_pdf(results_json, pdf_path, trust_result=None):
    rows = json.loads(Path(results_json).read_text(encoding="utf-8"))
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("TruthScan AI - Image Stress Test Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Purpose: measure how common image transformations affect image similarity and basic image characteristics.", styles["BodyText"]),
        Spacer(1, 10),
        Paragraph("Important: stress-test metrics measure changes caused by transformations. They do not, by themselves, establish whether an image is authentic or manipulated.", styles["BodyText"]),
        Spacer(1, 14),
    ]
    data = [["Test", "Setting", "PSNR (dB)", "SSIM", "File size (bytes)"]]
    for row in rows:
        m = row["metrics"]
        data.append([
            row["test"], row["setting"], f'{m["psnr_db"]:.2f}',
            f'{m["ssim"]:.4f}', str(m["altered_bytes"])
        ])
    table = Table(data, repeatRows=1, colWidths=[75, 115, 75, 65, 110])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    story.extend([table, Spacer(1, 16)])
    if trust_result:
        story.append(Paragraph("Evidence Trust Ladder", styles["Heading2"]))
        story.append(Paragraph(
            f'Score: {trust_result.get("score")} / 100 | {trust_result.get("level")}',
            styles["BodyText"]))
        story.append(Paragraph(trust_result.get("note", ""), styles["Italic"]))
    story.extend([
        Spacer(1, 12),
        Paragraph("Limitations", styles["Heading2"]),
        Paragraph("Results depend on the input image, transformation settings, and comparison method. Cropping removes information; resizing and blur can change similarity scores. Interpret these results alongside the forensic analyzer and independent corroborating evidence.", styles["BodyText"])
    ])
    doc.build(story)
    return Path(pdf_path)
