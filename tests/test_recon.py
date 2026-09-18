"""
Automated unit and integration test suite for AutoRecon-Enterprise.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.models import InvoiceRecord, BankTransaction, MatchStatus
from src.core.matcher import ReconciliationEngine
from src.core.parser import DataIngestionEngine


def test_exact_invoice_id_match():
    invoices = [
        InvoiceRecord(
            invoice_id="INV-101",
            vendor_name="Acme Corp",
            invoice_date="2026-02-01",
            subtotal=100.0,
            tax_amount=10.0,
            total_amount=110.0,
        )
    ]
    bank_txs = [
        BankTransaction(
            transaction_id="TX-501",
            posted_date="2026-02-03",
            description="ACH DEBIT ACME CORP FOR INV-101",
            amount=110.0,
        )
    ]

    engine = ReconciliationEngine()
    matches, summary = engine.reconcile(invoices, bank_txs)

    assert len(matches) == 1
    assert matches[0].match_status == MatchStatus.EXACT_MATCH
    assert matches[0].confidence_score >= 95.0
    assert summary.matched_count == 1
    assert summary.discrepancy_count == 0


def test_amount_discrepancy_detection():
    invoices = [
        InvoiceRecord(
            invoice_id="INV-102",
            vendor_name="Twilio Inc",
            invoice_date="2026-02-01",
            subtotal=200.0,
            tax_amount=0.0,
            total_amount=200.0,
        )
    ]
    bank_txs = [
        BankTransaction(
            transaction_id="TX-502",
            posted_date="2026-02-03",
            description="WIRE TWILIO INC INV-102",
            amount=215.0,  # $15 unexpected variance
        )
    ]

    engine = ReconciliationEngine(amount_tolerance=0.05)
    matches, summary = engine.reconcile(invoices, bank_txs)

    assert len(matches) == 1
    assert matches[0].match_status == MatchStatus.AMOUNT_DISCREPANCY
    assert matches[0].amount_difference == 15.0
    assert summary.discrepancy_count == 1


def test_duplicate_invoice_detection():
    invoices = [
        InvoiceRecord(
            invoice_id="INV-A",
            vendor_name="WeWork",
            invoice_date="2026-02-01",
            subtotal=1000.0,
            tax_amount=0.0,
            total_amount=1000.0,
        ),
        InvoiceRecord(
            invoice_id="INV-B",
            vendor_name="WeWork",
            invoice_date="2026-02-01",
            subtotal=1000.0,
            tax_amount=0.0,
            total_amount=1000.0,
        ),
    ]
    bank_txs = [
        BankTransaction(
            transaction_id="TX-W1",
            posted_date="2026-02-03",
            description="WEWORK RENT",
            amount=1000.0,
        )
    ]

    engine = ReconciliationEngine()
    matches, summary = engine.reconcile(invoices, bank_txs)

    statuses = [m.match_status for m in matches]
    assert MatchStatus.DUPLICATE_INVOICE in statuses
