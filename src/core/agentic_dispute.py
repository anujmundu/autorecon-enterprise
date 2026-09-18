"""
Agentic Vendor Dispute & Escalation Generator.
Autonomous communication engine that drafts legally grounded, detail-precise
vendor dispute letters and emails for identified financial anomalies.
"""

from typing import Dict, Any
from datetime import datetime
from .models import ReconciliationMatch, MatchStatus


class AgenticDisputeGenerator:
    """Generates professional, context-aware dispute packages for vendor reconciliation anomalies."""

    TONE_TEMPLATES = {
        "inquiry": {
            "subject": "Inquiry Regarding Recent Statement Variance: Invoice {inv_id}",
            "salutation": "Dear Accounts Receivable Team at {vendor},",
            "body": (
                "We are in the process of routine monthly ledger reconciliation and noticed a variance "
                "concerning Invoice {inv_id} (issued on our records). Our banking records indicate a settled "
                "debit of ${bank_amt:,.2f}, whereas our original approved invoice total reflects ${inv_amt:,.2f}, "
                "leaving an unresolved variance delta of ${delta:,.2f}.\n\n"
                "Audit Observation: {notes}\n\n"
                "Could your billing team please provide an itemized breakdown or fee clarification to help us "
                "balance this entry promptly?"
            ),
            "closing": "Thank you for your prompt assistance,\nFinance Operations Team",
        },
        "correction": {
            "subject": "Adjustment Required: Discrepancy on Invoice {inv_id} / Transaction Ref {tx_id}",
            "salutation": "Attention: Billing & Finance Department — {vendor},",
            "body": (
                "Our automated reconciliation audit has flagged a billing discrepancy requiring immediate adjustment.\n\n"
                "• Invoice Reference: {inv_id}\n"
                "• Billed Amount on Record: ${inv_amt:,.2f}\n"
                "• Cleared Bank Debit: ${bank_amt:,.2f}\n"
                "• Net Overcharge / Variance: ${delta:,.2f}\n"
                "• Discrepancy Classification: {status}\n\n"
                "Details: {notes}\n\n"
                "Please issue a formal credit memo or initiate a refund for the excess amount of ${delta:,.2f} "
                "within 5 business days to keep our vendor accounts in good standing."
            ),
            "closing": "Sincerely,\nSenior Controller & Accounts Payable",
        },
        "escalation": {
            "subject": "FORMAL ESCALATION: Unauthorized Charge / Duplicate Invoice Notice — {vendor}",
            "salutation": "Urgent: Formal Notice to Billing Leadership at {vendor},",
            "body": (
                "This is a formal notice regarding an unresolved billing anomaly identified during our financial audit.\n\n"
                "Discrepancy Breakdown:\n"
                "- Primary Document: {inv_id}\n"
                "- Bank Debit Reference: {tx_id}\n"
                "- Variance Exposure: ${delta:,.2f}\n"
                "- Audit Finding: {notes}\n\n"
                "In accordance with our commercial agreement terms, unauthorized variances and duplicate charges "
                "must be resolved within 3 business days. Please freeze further automatic debits on this account and "
                "remit credit confirmation immediately."
            ),
            "closing": "Regards,\nLegal & Financial Compliance Department",
        },
    }

    @classmethod
    def generate_dispute_notice(
        cls,
        match: ReconciliationMatch,
        tone: str = "correction",
    ) -> Dict[str, str]:
        """
        Synthesizes a structured dispute communication packet.
        """
        tone_key = tone.lower() if tone.lower() in cls.TONE_TEMPLATES else "correction"
        tpl = cls.TONE_TEMPLATES[tone_key]

        inv_id = match.invoice_id or "N/A"
        tx_id = match.transaction_id or "N/A"
        vendor = match.vendor_name or "Vendor"
        inv_amt = match.invoice_amount or 0.0
        bank_amt = match.bank_amount or 0.0
        delta = match.amount_difference or abs(inv_amt - bank_amt)
        notes = match.audit_notes or "Discrepancy identified between ledger and settlement debit."

        subject = tpl["subject"].format(inv_id=inv_id, tx_id=tx_id, vendor=vendor)
        salutation = tpl["salutation"].format(vendor=vendor)
        body = tpl["body"].format(
            inv_id=inv_id,
            tx_id=tx_id,
            vendor=vendor,
            inv_amt=inv_amt,
            bank_amt=bank_amt,
            delta=delta,
            status=match.match_status.value,
            notes=notes,
        )
        closing = tpl["closing"]

        full_message = f"{salutation}\n\n{body}\n\n{closing}"

        return {
            "tone": tone_key.capitalize(),
            "subject": subject,
            "recipient_vendor": vendor,
            "invoice_id": inv_id,
            "transaction_id": tx_id,
            "disputed_amount": delta,
            "formatted_letter": full_message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
