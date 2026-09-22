"""
Sector Summary PDF Report Generator
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

from src.config import DB_PATH, SECTOR_REPORTS_DIR


def generate_sector_report(db_path: Path = DB_PATH) -> Path:
    """Generate Sector Analytics PDF report."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM sector_metrics ORDER BY company_count DESC", conn)
    conn.close()

    SECTOR_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = SECTOR_REPORTS_DIR / "Nifty100_Sector_Analytics_Report.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"), alignment=0)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=12)

    story = [
        Paragraph("<b>Nifty 100 Sector Intelligence Report</b>", title_style),
        Paragraph(f"Sector Median KPI Analysis | Generated: {datetime.now().strftime('%d %b %Y')}", body_style),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=6, spaceAfter=12),
    ]

    if not df.empty:
        headers = ["Sector", "Companies", "Median ROE%", "Median ROCE%", "Median OPM%", "Median D/E", "Median FCF(Cr)"]
        rows = [headers]
        for _, r in df.iterrows():
            rows.append([
                str(r.get("broad_sector")),
                str(r.get("company_count")),
                f"{r.get('median_roe', 0):.1f}%" if pd.notna(r.get("median_roe")) else "N/A",
                f"{r.get('median_roce', 0):.1f}%" if pd.notna(r.get("median_roce")) else "N/A",
                f"{r.get('median_opm', 0):.1f}%" if pd.notna(r.get("median_opm")) else "N/A",
                f"{r.get('median_de', 0):.2f}" if pd.notna(r.get("median_de")) else "N/A",
                f"{r.get('median_fcf', 0):,.1f}" if pd.notna(r.get("median_fcf")) else "N/A",
            ])
        t = Table(rows, colWidths=[130, 65, 75, 75, 75, 60, 60])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(t)

    doc.build(story)
    print(f"Sector Report generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_sector_report()
