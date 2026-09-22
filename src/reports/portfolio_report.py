"""
Portfolio Summary PDF Report Generator
Nifty 100 Financial Intelligence Platform
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DB_PATH, PORTFOLIO_REPORTS_DIR


def generate_portfolio_report(db_path: Path = DB_PATH) -> Path:
    """Generate Portfolio Summary PDF report."""
    conn = sqlite3.connect(db_path)
    comp_df = pd.read_sql_query("SELECT id FROM companies", conn)
    hs_df = pd.read_sql_query("SELECT score, band FROM health_scores", conn)
    conn.close()

    PORTFOLIO_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = PORTFOLIO_REPORTS_DIR / "Nifty100_Portfolio_Summary.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"), alignment=0)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story = [
        Paragraph("<b>Nifty 100 Universe Portfolio Summary Report</b>", title_style),
        Paragraph(f"Financial Intelligence & Analytics | Generated: {datetime.now().strftime('%d %b %Y')}", body_style),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=6, spaceAfter=12),
    ]

    total_companies = len(comp_df)
    avg_score = round(float(hs_df["score"].mean()), 1) if not hs_df.empty else 0.0
    excellent_count = sum(1 for b in hs_df["band"] if b == "EXCELLENT")
    good_count = sum(1 for b in hs_df["band"] if b == "GOOD")

    summary_rows = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Total Analytical Companies", body_style), Paragraph(str(total_companies), body_style)],
        [Paragraph("Average Financial Health Score", body_style), Paragraph(f"{avg_score} / 100", body_style)],
        [Paragraph("Companies with Excellent Health (>=80)", body_style), Paragraph(str(excellent_count), body_style)],
        [Paragraph("Companies with Good Health (65-79)", body_style), Paragraph(str(good_count), body_style)],
    ]

    t = Table(summary_rows, colWidths=[300, 240])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t)

    doc.build(story)
    print(f"Portfolio Report generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_portfolio_report()
