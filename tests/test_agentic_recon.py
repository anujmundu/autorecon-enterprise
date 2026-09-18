"""
Unit tests for AutoRecon-Agentic 2026 upgrades: dispute generator and audit copilot.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.models import ReconciliationMatch, MatchStatus, AuditSummary
from src.core.agentic_dispute import AgenticDisputeGenerator
from src.core.audit_copilot import AuditCopilotEngine


@pytest.fixture
def sample_match():
    return ReconciliationMatch(
        invoice_id="INV-9901",
        transaction_id="TX-BK-110",
        vendor_name="Acme Cloud Technologies",
        bank_description="ACH DEBIT ACME CLOUD",
        invoice_amount=500.0,
        bank_amount=545.0,
        amount_difference=45.0,
        match_status=MatchStatus.AMOUNT_DISCREPANCY,
        confidence_score=92.0,
        audit_notes="Discrepancy of $45.00 detected between invoice and bank debit.",
    )


@pytest.fixture
def sample_summary():
    return AuditSummary(
        total_invoices_reviewed=10,
        total_bank_transactions=10,
        matched_count=7,
        discrepancy_count=2,
        unmatched_invoices_count=1,
        unmatched_bank_tx_count=0,
        total_invoiced_value=5000.0,
        total_reconciled_value=4500.0,
        total_variance_value=500.0,
    )


def test_agentic_dispute_generation_tones(sample_match):
    # Test Inquiry Tone
    inquiry = AgenticDisputeGenerator.generate_dispute_notice(sample_match, tone="inquiry")
    assert inquiry["tone"] == "Inquiry"
    assert "INV-9901" in inquiry["subject"]
    assert "Acme Cloud Technologies" in inquiry["recipient_vendor"]
    assert inquiry["disputed_amount"] == 45.0

    # Test Escalation Tone
    escalation = AgenticDisputeGenerator.generate_dispute_notice(sample_match, tone="escalation")
    assert escalation["tone"] == "Escalation"
    assert "FORMAL ESCALATION" in escalation["subject"]
    assert "$45.00" in escalation["formatted_letter"]


def test_audit_copilot_queries(sample_match, sample_summary):
    copilot = AuditCopilotEngine([sample_match], sample_summary)

    # Test Match Rate Query
    res1 = copilot.query("What is the overall match rate?")
    assert "70.0%" in res1["answer"]

    # Test Threshold Query
    res2 = copilot.query("Show variances over $30")
    assert len(res2["records"]) == 1
    assert res2["records"][0]["invoice_id"] == "INV-9901"

    # Test Non-matching Threshold Query
    res3 = copilot.query("Show variances over $100")
    assert len(res3["records"]) == 0
