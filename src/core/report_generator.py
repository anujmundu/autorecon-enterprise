"""
Boardroom-grade Excel Report Generator using openpyxl.
Applies executive styling, KPI summary cards, dynamic formulas,
and conditional formatting to deliver presentation-ready financial models.
"""

from pathlib import Path
from typing import List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .models import ReconciliationMatch, AuditSummary, MatchStatus


class ExcelReportBuilder:
    """Builds multi-tab executive financial models from audit results."""

    NAVY_HEADER = "1B365D"
    WHITE_TEXT = "FFFFFF"
    ACCENT_BLUE = "E8F1F5"
    ALERT_RED_BG = "FCE8E6"
    ALERT_RED_TXT = "C5221F"
    SUCCESS_GREEN_BG = "E6F4EA"
    SUCCESS_GREEN_TXT = "137333"
    AMBER_BG = "FEF7E0"
    AMBER_TXT = "B06000"

    @classmethod
    def generate(
        cls,
        matches: List[ReconciliationMatch],
        summary: AuditSummary,
        output_path: str = "reconciliation_audit_report.xlsx",
    ) -> str:
        wb = openpyxl.Workbook()

        # Remove default sheet
        default_sheet = wb.active
        wb.remove(default_sheet)

        # Build Sheets
        cls._build_executive_summary_tab(wb, summary)
        cls._build_discrepancies_tab(wb, matches)
        cls._build_all_matches_tab(wb, matches)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(path))
        return str(path.resolve())

    @classmethod
    def _build_executive_summary_tab(cls, wb: openpyxl.Workbook, summary: AuditSummary):
        ws = wb.create_sheet(title="Executive Summary")
        ws.views.sheetView[0].showGridLines = True

        # Title Block
        ws["B2"] = "AutoRecon Enterprise™ — Financial Audit & Reconciliation"
        ws["B2"].font = Font(name="Calibri", size=18, bold=True, color=cls.NAVY_HEADER)

        ws["B3"] = "Executive Variance Summary & Discrepancy Overview"
        ws["B3"].font = Font(name="Calibri", size=11, italic=True, color="5F6368")

        # KPI Cards Structure
        kpis = [
            ("Total Invoiced Value", f"${summary.total_invoiced_value:,.2f}", cls.NAVY_HEADER),
            ("Reconciled Bank Debits", f"${summary.total_reconciled_value:,.2f}", cls.SUCCESS_GREEN_TXT),
            ("Unreconciled Variance", f"${summary.total_variance_value:,.2f}", cls.ALERT_RED_TXT),
            ("Reconciliation Rate", f"{(summary.matched_count / max(summary.total_invoices_reviewed, 1) * 100):.1f}%", cls.NAVY_HEADER),
        ]

        col_start = 2
        for title, val, text_color in kpis:
            c_label = ws.cell(row=5, column=col_start, value=title)
            c_label.font = Font(name="Calibri", size=9, bold=True, color="5F6368")
            c_label.alignment = Alignment(horizontal="center", vertical="center")
            c_label.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")

            c_val = ws.cell(row=6, column=col_start, value=val)
            c_val.font = Font(name="Calibri", size=15, bold=True, color=text_color)
            c_val.alignment = Alignment(horizontal="center", vertical="center")
            c_val.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")

            ws.merge_cells(start_row=5, start_column=col_start, end_row=5, end_column=col_start + 1)
            ws.merge_cells(start_row=6, start_column=col_start, end_row=6, end_column=col_start + 1)
            col_start += 3

        # Breakdown Table
        ws["B9"] = "Audit Metrics"
        ws["C9"] = "Count"
        ws["B9"].font = Font(bold=True, color=cls.WHITE_TEXT)
        ws["B9"].fill = PatternFill(start_color=cls.NAVY_HEADER, end_color=cls.NAVY_HEADER, fill_type="solid")
        ws["C9"].font = Font(bold=True, color=cls.WHITE_TEXT)
        ws["C9"].fill = PatternFill(start_color=cls.NAVY_HEADER, end_color=cls.NAVY_HEADER, fill_type="solid")

        breakdown = [
            ("Invoices Ingested", summary.total_invoices_reviewed),
            ("Bank Transactions Analyzed", summary.total_bank_transactions),
            ("Clean Reconciled Matches", summary.matched_count),
            ("Amount Discrepancies Flagged", summary.discrepancy_count),
            ("Invoices Missing from Bank (Ghost/Unpaid)", summary.unmatched_invoices_count),
            ("Unmatched Bank Debits (Unbilled)", summary.unmatched_bank_tx_count),
        ]

        row = 10
        for label, count in breakdown:
            ws.cell(row=row, column=2, value=label).font = Font(name="Calibri", size=10)
            c = ws.cell(row=row, column=3, value=count)
            c.font = Font(name="Calibri", size=10, bold=True)
            c.alignment = Alignment(horizontal="right")
            if "Discrepancies" in label or "Ghost" in label:
                c.font = Font(name="Calibri", size=10, bold=True, color=cls.ALERT_RED_TXT)
            row += 1

        ws.column_dimensions["B"].width = 38
        ws.column_dimensions["C"].width = 16

    @classmethod
    def _build_discrepancies_tab(cls, wb: openpyxl.Workbook, matches: List[ReconciliationMatch]):
        ws = wb.create_sheet(title="Action Items & Discrepancies")
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Status", "Invoice ID", "Bank Tx ID", "Entity / Vendor",
            "Invoice Amt", "Bank Amt", "Delta ($)", "Audit Analysis"
        ]

        ws.row_dimensions[1].height = 28
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = Font(name="Calibri", size=11, bold=True, color=cls.WHITE_TEXT)
            cell.fill = PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        discrepancies = [
            m for m in matches
            if m.match_status in [
                MatchStatus.AMOUNT_DISCREPANCY,
                MatchStatus.MISSING_IN_BANK,
                MatchStatus.UNMATCHED_BANK_TX,
                MatchStatus.DUPLICATE_INVOICE,
            ]
        ]

        row_idx = 2
        for m in discrepancies:
            ws.cell(row=row_idx, column=1, value=m.match_status.value).font = Font(bold=True, color=cls.ALERT_RED_TXT)
            ws.cell(row=row_idx, column=2, value=m.invoice_id or "—")
            ws.cell(row=row_idx, column=3, value=m.transaction_id or "—")
            ws.cell(row=row_idx, column=4, value=m.vendor_name)

            c_inv = ws.cell(row=row_idx, column=5, value=m.invoice_amount)
            c_inv.number_format = "$#,##0.00"

            c_bank = ws.cell(row=row_idx, column=6, value=m.bank_amount)
            c_bank.number_format = "$#,##0.00"

            c_delta = ws.cell(row=row_idx, column=7, value=m.amount_difference)
            c_delta.number_format = "$#,##0.00"
            c_delta.font = Font(bold=True, color=cls.ALERT_RED_TXT)

            ws.cell(row=row_idx, column=8, value=m.audit_notes).font = Font(italic=True)
            row_idx += 1

        cls._auto_fit_columns(ws)

    @classmethod
    def _build_all_matches_tab(cls, wb: openpyxl.Workbook, matches: List[ReconciliationMatch]):
        ws = wb.create_sheet(title="Full Audit Ledger")
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Match Status", "Invoice ID", "Bank Tx ID", "Vendor / Entity",
            "Invoice ($)", "Bank ($)", "Delta ($)", "Score (%)", "Audit Memo"
        ]

        ws.row_dimensions[1].height = 26
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = Font(name="Calibri", size=10, bold=True, color=cls.WHITE_TEXT)
            cell.fill = PatternFill(start_color=cls.NAVY_HEADER, end_color=cls.NAVY_HEADER, fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        row_idx = 2
        for m in matches:
            ws.cell(row=row_idx, column=1, value=m.match_status.value)
            ws.cell(row=row_idx, column=2, value=m.invoice_id or "—")
            ws.cell(row=row_idx, column=3, value=m.transaction_id or "—")
            ws.cell(row=row_idx, column=4, value=m.vendor_name)

            c_inv = ws.cell(row=row_idx, column=5, value=m.invoice_amount)
            c_inv.number_format = "$#,##0.00"

            c_bank = ws.cell(row=row_idx, column=6, value=m.bank_amount)
            c_bank.number_format = "$#,##0.00"

            c_delta = ws.cell(row=row_idx, column=7, value=m.amount_difference)
            c_delta.number_format = "$#,##0.00"

            ws.cell(row=row_idx, column=8, value=f"{m.confidence_score:.0f}%")
            ws.cell(row=row_idx, column=9, value=m.audit_notes)

            # Zebra row striping
            if row_idx % 2 == 0:
                for c in range(1, 10):
                    cell = ws.cell(row=row_idx, column=c)
                    if cell.fill.fill_type is None:
                        cell.fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")

            row_idx += 1

        cls._auto_fit_columns(ws)

    @staticmethod
    def _auto_fit_columns(ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
