"""
Intelligent Reconciliation & Discrepancy Auditing Engine.
Implements exact matching, fuzzy entity resolution, tolerance thresholds,
and duplicate/ghost transaction detection.
"""

from datetime import datetime
from typing import List, Tuple, Set
from .models import (
    InvoiceRecord,
    BankTransaction,
    ReconciliationMatch,
    MatchStatus,
    AuditSummary,
)

# Optional fuzzy matching fallback
try:
    from thefuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False


class ReconciliationEngine:
    """Core matching algorithm with configurable tolerance thresholds."""

    def __init__(
        self,
        amount_tolerance: float = 0.05,        # Max absolute discrepancy considered a match (e.g. wire fees)
        fuzzy_threshold: float = 75.0,         # Minimum token sort score for vendor fuzzy matching
        date_window_days: int = 14,            # Proximity window for transaction posting
    ):
        self.amount_tolerance = amount_tolerance
        self.fuzzy_threshold = fuzzy_threshold
        self.date_window_days = date_window_days

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculates token similarity between vendor and bank narrative."""
        s1_clean = s1.lower().strip()
        s2_clean = s2.lower().strip()

        if s1_clean in s2_clean or s2_clean in s1_clean:
            return 95.0

        if FUZZY_AVAILABLE:
            return float(fuzz.token_set_ratio(s1_clean, s2_clean))

        # Basic fallback word-overlap coefficient if thefuzz is not yet installed
        words1 = set(s1_clean.split())
        words2 = set(s2_clean.split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1.intersection(words2))
        return (overlap / min(len(words1), len(words2))) * 100.0

    def _days_between(self, d1_str: str, d2_str: str) -> int:
        """Parses dates and returns absolute difference in days."""
        try:
            d1 = datetime.strptime(d1_str[:10], "%Y-%m-%d")
            d2 = datetime.strptime(d2_str[:10], "%Y-%m-%d")
            return abs((d1 - d2).days)
        except Exception:
            return 999

    def reconcile(
        self,
        invoices: List[InvoiceRecord],
        bank_txs: List[BankTransaction],
    ) -> Tuple[List[ReconciliationMatch], AuditSummary]:
        """
        Executes a multi-stage reconciliation pipeline:
        Stage 1: Duplicate invoice detection
        Stage 2: Exact reference/amount matching
        Stage 3: Fuzzy vendor + proximity amount matching
        Stage 4: Residual unmatched tracking (ghost invoices & unbilled bank debits)
        """
        matches: List[ReconciliationMatch] = []
        matched_tx_ids: Set[str] = set()
        matched_inv_ids: Set[str] = set()

        # --- Stage 1: Duplicate Invoice Detection ---
        seen_keys = {}
        for inv in invoices:
            key = (inv.vendor_name.lower(), round(inv.total_amount, 2))
            if key in seen_keys:
                matches.append(
                    ReconciliationMatch(
                        invoice_id=inv.invoice_id,
                        vendor_name=inv.vendor_name,
                        invoice_amount=inv.total_amount,
                        match_status=MatchStatus.DUPLICATE_INVOICE,
                        confidence_score=100.0,
                        audit_notes=f"Potential duplicate billing of previously seen invoice: {seen_keys[key]}",
                    )
                )
                matched_inv_ids.add(inv.invoice_id)
            else:
                seen_keys[key] = inv.invoice_id

        # --- Stage 2: Exact Reference / ID Matching ---
        for inv in invoices:
            if inv.invoice_id in matched_inv_ids:
                continue

            for tx in bank_txs:
                if tx.transaction_id in matched_tx_ids:
                    continue

                # Match by explicit ID contained in memo
                if inv.invoice_id.lower() in tx.description.lower():
                    delta = round(abs(inv.total_amount - tx.amount), 2)
                    status = MatchStatus.EXACT_MATCH if delta <= self.amount_tolerance else MatchStatus.AMOUNT_DISCREPANCY
                    note = "Matched via Invoice ID in bank memo."
                    if status == MatchStatus.AMOUNT_DISCREPANCY:
                        note += f" Discrepancy of ${delta} detected."

                    matches.append(
                        ReconciliationMatch(
                            invoice_id=inv.invoice_id,
                            transaction_id=tx.transaction_id,
                            vendor_name=inv.vendor_name,
                            bank_description=tx.description,
                            invoice_amount=inv.total_amount,
                            bank_amount=tx.amount,
                            amount_difference=delta,
                            match_status=status,
                            confidence_score=99.0 if status == MatchStatus.EXACT_MATCH else 85.0,
                            audit_notes=note,
                        )
                    )
                    matched_inv_ids.add(inv.invoice_id)
                    matched_tx_ids.add(tx.transaction_id)
                    break

        # --- Stage 3: Fuzzy Vendor + Amount Matching ---
        for inv in invoices:
            if inv.invoice_id in matched_inv_ids:
                continue

            best_match: Tuple[BankTransaction, float, float] = None  # (tx, score, delta)

            for tx in bank_txs:
                if tx.transaction_id in matched_tx_ids:
                    continue

                sim = self._string_similarity(inv.vendor_name, tx.description)
                delta = round(abs(inv.total_amount - tx.amount), 2)
                day_diff = self._days_between(inv.invoice_date, tx.posted_date)

                # Viable match if name is similar and dates are within window
                if sim >= self.fuzzy_threshold and day_diff <= self.date_window_days:
                    if delta <= self.amount_tolerance:
                        # High confidence exact amount match
                        best_match = (tx, sim, delta)
                        break
                    elif delta <= (inv.total_amount * 0.15):  # Within 15% variance threshold (taxes/fees)
                        if best_match is None or delta < best_match[2]:
                            best_match = (tx, sim * 0.85, delta)

            if best_match:
                tx, score, delta = best_match
                status = MatchStatus.FUZZY_MATCH if delta <= self.amount_tolerance else MatchStatus.AMOUNT_DISCREPANCY
                note = f"Fuzzy matched vendor '{inv.vendor_name}' with score {score:.1f}%."
                if status == MatchStatus.AMOUNT_DISCREPANCY:
                    note += f" Discrepancy of ${delta} (likely tax or bank fee variance)."

                matches.append(
                    ReconciliationMatch(
                        invoice_id=inv.invoice_id,
                        transaction_id=tx.transaction_id,
                        vendor_name=inv.vendor_name,
                        bank_description=tx.description,
                        invoice_amount=inv.total_amount,
                        bank_amount=tx.amount,
                        amount_difference=delta,
                        match_status=status,
                        confidence_score=score,
                        audit_notes=note,
                    )
                )
                matched_inv_ids.add(inv.invoice_id)
                matched_tx_ids.add(tx.transaction_id)
            else:
                # Invoice has no matching bank record (Missing payment or ghost invoice)
                matches.append(
                    ReconciliationMatch(
                        invoice_id=inv.invoice_id,
                        vendor_name=inv.vendor_name,
                        invoice_amount=inv.total_amount,
                        amount_difference=inv.total_amount,
                        match_status=MatchStatus.MISSING_IN_BANK,
                        confidence_score=0.0,
                        audit_notes="Invoice issued but no corresponding bank debit detected.",
                    )
                )
                matched_inv_ids.add(inv.invoice_id)

        # --- Stage 4: Residual Unmatched Bank Transactions (Unbilled charges) ---
        for tx in bank_txs:
            if tx.transaction_id not in matched_tx_ids:
                matches.append(
                    ReconciliationMatch(
                        transaction_id=tx.transaction_id,
                        vendor_name=tx.description,
                        bank_description=tx.description,
                        bank_amount=tx.amount,
                        amount_difference=tx.amount,
                        match_status=MatchStatus.UNMATCHED_BANK_TX,
                        confidence_score=0.0,
                        audit_notes="Bank debit exists with no associated vendor invoice on record.",
                    )
                )
                matched_tx_ids.add(tx.transaction_id)

        # --- Compute Executive Audit Summary ---
        matched_count = sum(1 for m in matches if m.match_status in [MatchStatus.EXACT_MATCH, MatchStatus.FUZZY_MATCH])
        discrepancy_count = sum(1 for m in matches if m.match_status == MatchStatus.AMOUNT_DISCREPANCY)
        unmatched_inv = sum(1 for m in matches if m.match_status in [MatchStatus.MISSING_IN_BANK, MatchStatus.DUPLICATE_INVOICE])
        unmatched_bank = sum(1 for m in matches if m.match_status == MatchStatus.UNMATCHED_BANK_TX)

        total_inv_val = sum(inv.total_amount for inv in invoices)
        total_recon_val = sum(m.bank_amount for m in matches if m.bank_amount and m.match_status in [MatchStatus.EXACT_MATCH, MatchStatus.FUZZY_MATCH])
        total_variance = sum(m.amount_difference for m in matches if m.match_status == MatchStatus.AMOUNT_DISCREPANCY)

        summary = AuditSummary(
            total_invoices_reviewed=len(invoices),
            total_bank_transactions=len(bank_txs),
            matched_count=matched_count,
            discrepancy_count=discrepancy_count,
            unmatched_invoices_count=unmatched_inv,
            unmatched_bank_tx_count=unmatched_bank,
            total_invoiced_value=round(total_inv_val, 2),
            total_reconciled_value=round(total_recon_val, 2),
            total_variance_value=round(total_variance, 2),
        )

        return matches, summary
