"""
Screener Results PDF Report Generator
Nifty 100 Financial Intelligence Platform
"""

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

from src.analytics.screener.engine import run_screener
from src.config import DB_PATH, OUTPUT_DIR, REPORTS_DIR


def generate_screener_report(preset: str = "QUALITY", db_path: Path = DB_PATH) -> Path:
    """Generate Screener PDF report for a given preset."""
    screened_df = run_screener(preset=preset, db_path=db_path)

    pdf_dir = REPORTS_DIR / "screener"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"Screener_{preset}_Report.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"), alignment=0)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=12)

    story = [
        Paragraph(f"<b>Nifty 100 Screener Report: {preset} Preset</b>", title_style),
        Paragraph(f"Matches: {len(screened_df)} companies | Generated: {datetime.now().strftime('%d %b %Y')}", body_style),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=6, spaceAfter=12),
    ]

    if not screened_df.empty:
        headers = ["Ticker", "Company Name", "ROE %", "OPM %", "D/E", "FCF (Cr)", "Health Score"]
        rows = [headers]
        for _, r in screened_df.head(25).iterrows():
            rows.append([
                str(r.get("company_id")),
                str(r.get("company_name", "")),
                f"{r.get('return_on_equity_pct', 0):.1f}%" if pd.notna(r.get("return_on_equity_pct")) else "N/A",
                f"{r.get('operating_profit_margin_pct', 0):.1f}%" if pd.notna(r.get("operating_profit_margin_pct")) else "N/A",
                f"{r.get('debt_to_equity', 0):.2f}" if pd.notna(r.get("debt_to_equity")) else "N/A",
                f"{r.get('free_cash_flow_cr', 0):,.1f}" if pd.notna(r.get("free_cash_flow_cr")) else "N/A",
                f"{r.get('health_score', 'N/A')}",
            ])
        t = Table(rows, colWidths=[65, 175, 60, 60, 50, 70, 60])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(t)

    doc.build(story)
    print(f"Screener Report generated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    generate_screener_report("QUALITY")
