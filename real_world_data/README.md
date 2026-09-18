# Authentic Real-World Data Directory: AutoRecon Enterprise™

This directory contains **authentic, real-world regulatory tax filings, contractor nonemployee compensation records, and vendor settlement documents** downloaded directly from official federal repositories and open standard sources.

---

### Downloaded Benchmark Files & Direct URLs

| # | File Name | File Size | Document Type & Description | Direct Download URL / Source |
|---|---|---|---|---|
| **1** | `01_irs_w9_vendor_identification.pdf` | 137.5 KB | Official IRS Form W-9: Request for Taxpayer Identification Number & Certification (Vendor Onboarding) | [IRS.gov Official PDF](https://www.irs.gov/pub/irs-pdf/fw9.pdf) |
| **2** | `02_irs_1099nec_contractor_nonemployee_compensation.pdf` | 524.9 KB | Official IRS Form 1099-NEC: Nonemployee Compensation (Contractor Payouts & B2B Invoicing) | [IRS.gov Official PDF](https://www.irs.gov/pub/irs-pdf/f1099nec.pdf) |
| **3** | `03_irs_1120_corporate_income_tax_return.pdf` | 332.1 KB | Official IRS Form 1120: U.S. Corporation Income Tax Return (Corporate Audit & Reconciliation) | [IRS.gov Official PDF](https://www.irs.gov/pub/irs-pdf/f1120.pdf) |
| **4** | `04_irs_1040_individual_income_tax_filing.pdf` | 215.1 KB | Official IRS Form 1040: U.S. Individual Income Tax Return (Personal Tax & 1099 Reconciliation) | [IRS.gov Official PDF](https://www.irs.gov/pub/irs-pdf/f1040.pdf) |
| **5** | `05_irs_941_employer_quarterly_federal_tax_return.pdf` | 821.9 KB | Official IRS Form 941: Employer's Quarterly Federal Tax Return (Payroll & Withholding Audit) | [IRS.gov Official PDF](https://www.irs.gov/pub/irs-pdf/f941.pdf) |

---

### How to Test in the Browser UI
1. Open the **AutoRecon Cockpit** at `http://localhost:8501`.
2. In the left sidebar under **File Upload**:
   - Upload any of the PDFs above into the **Invoice Upload** dropzone.
   - The ingestion engine uses `pypdf` + regex extraction to parse document numbers, dates, and amounts into structured `InvoiceRecord` entities.
3. In the **Reconciliation Cockpit**:
   - Run the automated matching engine to cross-reference against bank transactions.
   - Inspect the **Audit Copilot** tab and ask questions like *"What is the total balance?"* or *"List any discrepancies"*.
4. In the **Dispute Notice Generator**:
   - Auto-generate an audit dispute letter complete with statutory interest calculation.
