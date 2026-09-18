"""
High-definition Terminal CLI for AutoRecon-Enterprise using Rich.
Provides styled progress, audit summaries, and instant report generation.
"""

import sys
from pathlib import Path
import argparse

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Support local execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.parser import DataIngestionEngine
from src.core.matcher import ReconciliationEngine
from src.core.report_generator import ExcelReportBuilder
from src.core.models import MatchStatus


console = Console(force_terminal=True, legacy_windows=False)


def run_audit(invoice_file: str, bank_file: str, output_excel: str, tolerance: float):
    console.print(
        Panel.fit(
            "[bold cyan]AutoRecon Enterprise™[/bold cyan] | [bold white]Financial Reconciliation & Anomaly Engine[/bold white]\n"
            "[dim]Author: Anuj | AI Automation Architect & Python Data Specialist[/dim]",
            border_style="cyan",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # Ingestion Task
        t1 = progress.add_task("[yellow]Ingesting multi-source ledgers...", total=None)
        invoices = DataIngestionEngine.parse_invoices(invoice_file)
        bank_txs = DataIngestionEngine.parse_bank_transactions(bank_file)
        progress.update(t1, completed=True)

        # Reconciliation Task
        t2 = progress.add_task("[cyan]Executing multi-stage fuzzy audit algorithm...", total=None)
        engine = ReconciliationEngine(amount_tolerance=tolerance)
        matches, summary = engine.reconcile(invoices, bank_txs)
        progress.update(t2, completed=True)

        # Excel Generation
        t3 = progress.add_task("[green]Compiling boardroom Excel workbook...", total=None)
        saved_path = ExcelReportBuilder.generate(matches, summary, output_excel)
        progress.update(t3, completed=True)

    # Output Summary Table
    summary_table = Table(title="📊 Executive Audit Metrics", show_header=True, header_style="bold blue")
    summary_table.add_column("Audit Metric", style="dim", width=38)
    summary_table.add_column("Value / Count", justify="right", style="bold")

    summary_table.add_row("Total Invoices Ingested", str(summary.total_invoices_reviewed))
    summary_table.add_row("Total Bank Debits Processed", str(summary.total_bank_transactions))
    summary_table.add_row("Clean Reconciled Matches", f"[green]{summary.matched_count}[/green]")
    summary_table.add_row("Amount Discrepancies Flagged", f"[red]{summary.discrepancy_count}[/red]")
    summary_table.add_row("Missing from Bank (Ghost/Unpaid)", f"[yellow]{summary.unmatched_invoices_count}[/yellow]")
    summary_table.add_row("Unmatched Bank Charges (Unbilled)", f"[magenta]{summary.unmatched_bank_tx_count}[/magenta]")
    summary_table.add_section()
    summary_table.add_row("Gross Invoiced Exposure", f"${summary.total_invoiced_value:,.2f}")
    summary_table.add_row("Reconciled Capital Settled", f"[green]${summary.total_reconciled_value:,.2f}[/green]")
    summary_table.add_row("Net Variance Delta", f"[bold red]${summary.total_variance_value:,.2f}[/bold red]")

    console.print(summary_table)

    # Discrepancy Action Items Table
    discrepancies = [m for m in matches if m.match_status != MatchStatus.EXACT_MATCH and m.match_status != MatchStatus.FUZZY_MATCH]
    if discrepancies:
        disc_table = Table(title="⚠️ Action Required: Flagged Discrepancies & Anomaly Log", show_header=True, header_style="bold red")
        disc_table.add_column("Flag Type", style="bold red", width=22)
        disc_table.add_column("Entity / Narrative", width=30)
        disc_table.add_column("Invoice ($)", justify="right")
        disc_table.add_column("Bank ($)", justify="right")
        disc_table.add_column("Delta ($)", justify="right", style="bold red")
        disc_table.add_column("Audit Finding")

        for d in discrepancies:
            disc_table.add_row(
                d.match_status.value,
                d.vendor_name[:28],
                f"${d.invoice_amount:,.2f}" if d.invoice_amount else "—",
                f"${d.bank_amount:,.2f}" if d.bank_amount else "—",
                f"${d.amount_difference:,.2f}",
                d.audit_notes,
            )

        console.print(disc_table)

    console.print(f"\n[bold green]✓ Audit Completed Successfully![/bold green] Boardroom model exported to: [bold underline]{saved_path}[/bold underline]\n")


def main():
    parser = argparse.ArgumentParser(description="AutoRecon Enterprise — Autonomous Reconciliation CLI")
    parser.add_argument("--invoices", default="data/invoices.csv", help="Path to invoices CSV/Excel/JSON")
    parser.add_argument("--bank", default="data/bank_statement.csv", help="Path to bank statement CSV/Excel/JSON")
    parser.add_argument("--output", default="reconciliation_audit_report.xlsx", help="Path for output Excel report")
    parser.add_argument("--tolerance", type=float, default=0.05, help="Tolerance threshold in dollars")

    args = parser.parse_args()
    run_audit(args.invoices, args.bank, args.output, args.tolerance)


if __name__ == "__main__":
    main()
