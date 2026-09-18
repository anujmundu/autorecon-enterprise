"""
Domain models and schema definitions for the AutoRecon-Enterprise system.
"""

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    AMOUNT_DISCREPANCY = "AMOUNT_DISCREPANCY"
    MISSING_IN_BANK = "MISSING_IN_BANK"
    UNMATCHED_BANK_TX = "UNMATCHED_BANK_TX"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"


class InvoiceRecord(BaseModel):
    invoice_id: str = Field(..., description="Unique invoice or bill identifier")
    vendor_name: str = Field(..., description="Entity or vendor name on invoice")
    invoice_date: str = Field(..., description="Date of issuance (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Due date if available")
    subtotal: float = Field(..., ge=0, description="Pre-tax amount")
    tax_amount: float = Field(0.0, ge=0, description="Applicable tax/VAT")
    total_amount: float = Field(..., ge=0, description="Total billed amount")
    currency: str = Field(default="USD", max_length=3)
    category: str = Field(default="General & Administrative")
    status: str = Field(default="PENDING")


class BankTransaction(BaseModel):
    transaction_id: str = Field(..., description="Bank transaction reference code")
    posted_date: str = Field(..., description="Posting date (YYYY-MM-DD)")
    description: str = Field(..., description="Raw bank transaction memo or narrative")
    amount: float = Field(..., description="Debit or credit transaction amount")
    currency: str = Field(default="USD", max_length=3)
    account_number: Optional[str] = Field(None, description="Masked account number")


class ReconciliationMatch(BaseModel):
    invoice_id: Optional[str] = None
    transaction_id: Optional[str] = None
    vendor_name: str
    bank_description: Optional[str] = None
    invoice_amount: Optional[float] = None
    bank_amount: Optional[float] = None
    amount_difference: float = 0.0
    match_status: MatchStatus
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    audit_notes: str = ""


class AuditSummary(BaseModel):
    total_invoices_reviewed: int
    total_bank_transactions: int
    matched_count: int
    discrepancy_count: int
    unmatched_invoices_count: int
    unmatched_bank_tx_count: int
    total_invoiced_value: float
    total_reconciled_value: float
    total_variance_value: float
