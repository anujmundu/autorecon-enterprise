"""
Conversational Audit Copilot Engine.
Interrogates reconciliation audit ledgers using natural language semantic parsing.
"""

from typing import List, Dict, Any
import re
from .models import ReconciliationMatch, AuditSummary, MatchStatus


class AuditCopilotEngine:
    """Answers conversational audit inquiries over reconciliation ledger records."""

    def __init__(self, matches: List[ReconciliationMatch], summary: AuditSummary):
        self.matches = matches
        self.summary = summary

    def query(self, user_prompt: str) -> Dict[str, Any]:
        p = user_prompt.lower().strip()

        # 1. Match Rate & Executive Status
        if any(kw in p for kw in ["match rate", "accuracy", "overall status", "how well", "summary"]):
            rate = (self.summary.matched_count / max(self.summary.total_invoices_reviewed, 1)) * 100
            answer = (
                f"Overall reconciliation rate is **{rate:.1f}%**. Out of {self.summary.total_invoices_reviewed} invoices reviewed, "
                f"**{self.summary.matched_count}** matched cleanly, **{self.summary.discrepancy_count}** have amount variances, and "
                f"**{self.summary.unmatched_invoices_count}** are missing settlement. Net variance exposure: **${self.summary.total_variance_value:,.2f}**."
            )
            return {"answer": answer, "records": []}

        # 2. Duplicate Invoices
        if "duplicate" in p:
            dups = [m for m in self.matches if m.match_status == MatchStatus.DUPLICATE_INVOICE]
            if dups:
                answer = f"Found **{len(dups)}** duplicate invoice anomalies. These indicate repeated billings for identical amounts."
            else:
                answer = "No duplicate invoices detected in this ledger."
            return {"answer": answer, "records": [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in dups]}

        # 3. Unbilled Bank Debits
        if any(kw in p for kw in ["unbilled", "unmatched bank", "ghost debit", "unauthorized"]):
            unbilled = [m for m in self.matches if m.match_status == MatchStatus.UNMATCHED_BANK_TX]
            tot = sum(m.bank_amount or 0.0 for m in unbilled)
            answer = f"Identified **{len(unbilled)}** bank debits totaling **${tot:,.2f}** that have no matching vendor invoice on file."
            return {"answer": answer, "records": [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in unbilled]}

        # 4. Filter by dollar threshold (e.g. "variances over $50" or "greater than 100")
        threshold_match = re.search(r"(?:over|above|greater than|>)\s*\$?(\d+(?:\.\d+)?)", p)
        if threshold_match:
            threshold = float(threshold_match.group(1))
            filtered = [
                m for m in self.matches
                if m.amount_difference >= threshold and m.match_status != MatchStatus.EXACT_MATCH
            ]
            answer = f"Found **{len(filtered)}** discrepancy records with variance greater than or equal to **${threshold:,.2f}**."
            return {"answer": answer, "records": [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in filtered]}

        # 5. Search by specific vendor name
        matched_by_vendor = []
        for m in self.matches:
            if m.vendor_name and m.vendor_name.lower() in p:
                matched_by_vendor.append(m)
        if matched_by_vendor:
            answer = f"Found **{len(matched_by_vendor)}** record(s) matching vendor mentioned in your query."
            return {"answer": answer, "records": [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in matched_by_vendor]}

        # 6. Default general discrepancy overview
        discs = [m for m in self.matches if m.match_status not in [MatchStatus.EXACT_MATCH, MatchStatus.FUZZY_MATCH]]
        answer = (
            f"There are currently **{len(discs)}** open action items requiring attention, "
            f"representing **${self.summary.total_variance_value:,.2f}** in total unresolved variance."
        )
        return {"answer": answer, "records": [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in discs]}
