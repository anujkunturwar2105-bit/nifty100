"""
Company Financial Tearsheet Generator
Nifty 100 Financial Intelligence Platform

Generates production-grade PDF financial tearsheets for 92 Nifty companies using ReportLab.
Outputs PDFs into `reports/tearsheets/` and logs results to `output/report_generation_log.csv`.
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

from src.config import DB_PATH, OUTPUT_DIR, TEARSHEETS_DIR


def generate_company_tearsheet(ticker: str, db_path: Path = DB_PATH) -> Path | None:
    """Generate a single company PDF tearsheet."""
    conn = sqlite3.connect(db_path)
    comp_df = pd.read_sql_query("SELECT * FROM companies WHERE id = ?", conn, params=(ticker,))

    if comp_df.empty:
        conn.close()
        return None

    company_info = comp_df.iloc[0].to_dict()

    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    cf_df = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios_calc WHERE company_id = ? ORDER BY year ASC", conn, params=(ticker,))
    health_df = pd.read_sql_query("SELECT * FROM health_scores WHERE company_id = ?", conn, params=(ticker,))
    pc_df = pd.read_sql_query("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=(ticker,))
    conn.close()

    TEARSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = TEARSHEETS_DIR / f"{ticker}_Tearsheet.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=20, leading=24, textColor=colors.HexColor("#1e293b"), alignment=0)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#334155"))
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#64748b"))

    story = []

    # Title & Header
    comp_name = company_info.get("company_name") or ticker
    story.append(Paragraph(f"<b>{comp_name} ({ticker})</b>", title_style))
    story.append(Paragraph(f"Nifty 100 Financial Tearsheet | Generated: {datetime.now().strftime('%d %b %Y')}", small_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=6, spaceAfter=10))

    # Company Summary Card
    health_score = health_df.iloc[0]["score"] if not health_df.empty else "N/A"
    health_band = health_df.iloc[0]["band"] if not health_df.empty else "N/A"
    about_text = company_info.get("about_company") or "Financial Analytics Profile"

    summary_data = [
        [Paragraph(f"<b>Ticker:</b> {ticker}", body_style), Paragraph(f"<b>Health Score:</b> {health_score} / 100 ({health_band})", body_style)],
        [Paragraph(f"<b>Face Value:</b> {company_info.get('face_value', 'N/A')}", body_style), Paragraph(f"<b>Book Value:</b> Rs. {company_info.get('book_value', 'N/A')}", body_style)],
    ]
    t_summary = Table(summary_data, colWidths=[270, 270])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 10))

    # Recent Financial Performance Table
    story.append(Paragraph("<b>Recent Financial Performance (P&L Summary)</b>", heading_style))
    if not pnl_df.empty:
        recent_pnl = pnl_df.tail(5)
        headers = ["Year", "Sales (Cr)", "Op. Profit", "OPM %", "Net Profit", "EPS"]
        table_rows = [headers]
        for _, r in recent_pnl.iterrows():
            def _fmt(val, fmt=",.1f"):
                return f"{val:{fmt}}" if pd.notna(val) and val is not None else "0.0"
            table_rows.append([
                str(r.get("year")),
                _fmt(r.get("sales")),
                _fmt(r.get("operating_profit")),
                _fmt(r.get("opm_percentage")) + "%",
                _fmt(r.get("net_profit")),
                _fmt(r.get("eps")),
            ])
        t_pnl = Table(table_rows, colWidths=[70, 95, 95, 80, 95, 105])
        t_pnl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(t_pnl)
    else:
        story.append(Paragraph("Financial statement data unavailable.", body_style))

    story.append(Spacer(1, 10))

    # Key Ratios Table
    story.append(Paragraph("<b>Key Calculated Ratios</b>", heading_style))
    if not ratios_df.empty:
        recent_ratios = ratios_df.tail(5)
        headers_r = ["Year", "ROE %", "ROCE %", "D/E Ratio", "Int Coverage", "FCF (Cr)", "CFO (Cr)"]
        table_r_rows = [headers_r]
        for _, r in recent_ratios.iterrows():
            roe_val = f"{r.get('return_on_equity_pct'):.1f}%" if pd.notna(r.get("return_on_equity_pct")) else "N/A"
            roce_val = f"{r.get('roce_pct'):.1f}%" if pd.notna(r.get("roce_pct")) else "N/A"
            de_val = f"{r.get('debt_to_equity'):.2f}" if pd.notna(r.get("debt_to_equity")) else "N/A"
            ic_val = f"{r.get('interest_coverage'):.1f}x" if pd.notna(r.get("interest_coverage")) else "N/A"
            fcf_val = f"{r.get('free_cash_flow_cr'):,.1f}" if pd.notna(r.get("free_cash_flow_cr")) else "N/A"
            cfo_val = f"{r.get('cash_from_operations_cr'):,.1f}" if pd.notna(r.get("cash_from_operations_cr")) else "N/A"

            table_r_rows.append([str(r.get("year")), roe_val, roce_val, de_val, ic_val, fcf_val, cfo_val])

        t_ratios = Table(table_r_rows, colWidths=[70, 75, 75, 75, 80, 80, 85])
        t_ratios.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(t_ratios)

    story.append(Spacer(1, 10))

    # Pros & Cons Section
    story.append(Paragraph("<b>Quantitative Pros & Cons</b>", heading_style))
    if not pc_df.empty:
        pros_txt = pc_df.iloc[0].get("pros") or "No pros recorded."
        cons_txt = pc_df.iloc[0].get("cons") or "No cons recorded."

        pc_data = [
            [Paragraph("<b>Strengths (Pros):</b>", body_style), Paragraph(pros_txt, body_style)],
            [Paragraph("<b>Concerns (Cons):</b>", body_style), Paragraph(cons_txt, body_style)],
        ]
        t_pc = Table(pc_data, colWidths=[120, 420])
        t_pc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        story.append(t_pc)

    doc.build(story)
    return pdf_path


def batch_generate_tearsheets(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Batch generate PDF tearsheets for all available companies in SQLite database."""
    conn = sqlite3.connect(db_path)
    companies_df = pd.read_sql_query("SELECT id FROM companies", conn)
    conn.close()

    log_records = []
    start_time = datetime.now()

    for idx, row in companies_df.iterrows():
        ticker = row["id"]
        try:
            path = generate_company_tearsheet(ticker, db_path)
            status = "SUCCESS" if path and path.exists() else "FAILED"
            log_records.append({
                "ticker": ticker,
                "report_type": "TEARSHEET",
                "pdf_path": str(path) if path else "",
                "status": status,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            log_records.append({
                "ticker": ticker,
                "report_type": "TEARSHEET",
                "pdf_path": "",
                "status": f"ERROR: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })

    log_df = pd.DataFrame(log_records)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_df.to_csv(OUTPUT_DIR / "report_generation_log.csv", index=False)
    print(f"Batch Tearsheet generation complete: {sum(1 for r in log_records if r['status'] == 'SUCCESS')}/{len(log_records)} PDFs generated.")
    return log_df


if __name__ == "__main__":
    batch_generate_tearsheets()
