"""
AutoRecon Enterprise™ — Client Demonstration Web Cockpit (Streamlit).
Allows non-technical clients and auditors to upload ledgers, inspect variances,
and export executive Excel audit packages in 1 click.
"""

import sys
from pathlib import Path
import io
import pandas as pd
import streamlit as st

# Path resolution: ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.core.parser import DataIngestionEngine
from src.core.matcher import ReconciliationEngine
from src.core.report_generator import ExcelReportBuilder
from src.core.models import MatchStatus
from src.core.agentic_dispute import AgenticDisputeGenerator
from src.core.audit_copilot import AuditCopilotEngine


st.set_page_config(
    page_title="AutoRecon Enterprise™ | Financial Audit Cockpit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for executive styling
st.markdown("""
<style>
    .main { background-color: #0E1117; color: #FFFFFF; }
    .kpi-card {
        background: linear-gradient(135deg, #1E2638 0%, #151A28 100%);
        border: 1px solid #2E384D;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .kpi-title { font-size: 0.85rem; color: #8F9CAE; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-val { font-size: 1.8rem; font-weight: 700; margin-top: 5px; color: #FFFFFF; }
    .badge-exact { color: #00E676; font-weight: 600; }
    .badge-warn { color: #FF5252; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


st.title("⚡ AutoRecon Enterprise™")
st.caption("Autonomous Financial & Operational Audit Engine • Built by Anuj (Senior Python & AI Automation Specialist)")

# Sidebar Settings
st.sidebar.header("⚙️ Audit Configuration")
tolerance = st.sidebar.slider("Variance Tolerance ($ USD)", min_value=0.0, max_value=5.0, value=0.05, step=0.01)
fuzzy_threshold = st.sidebar.slider("Fuzzy Matching Confidence (%)", min_value=50, max_value=100, value=75, step=5)
date_window = st.sidebar.slider("Posting Date Window (Days)", min_value=1, max_value=30, value=14)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💼 Portfolio Demonstration")
st.sidebar.info("This system automates 25+ hours of weekly manual bookkeeping and invoice-to-bank verification with zero human error.")

# File Ingestion Options
col1, col2 = st.columns(2)

default_inv_path = root_dir / "data" / "invoices.csv"
default_bank_path = root_dir / "data" / "bank_statement.csv"

with col1:
    st.subheader("1. Invoices / ERP Ledger")
    uploaded_invoices = st.file_uploader("Upload Invoices (CSV/Excel)", type=["csv", "xlsx", "json"], key="inv")

with col2:
    st.subheader("2. Bank Statement / Settlement Feed")
    uploaded_bank = st.file_uploader("Upload Bank Feed (CSV/Excel)", type=["csv", "xlsx", "json"], key="bank")

use_sample = False
if not uploaded_invoices or not uploaded_bank:
    if default_inv_path.exists() and default_bank_path.exists():
        if st.button("🚀 Load Enterprise Sample Datasets (AWS, Google, Twilio, WeWork)", use_container_width=True):
            use_sample = True

if uploaded_invoices and uploaded_bank:
    inv_source = uploaded_invoices
    bank_source = uploaded_bank
    can_run = True
elif use_sample or (default_inv_path.exists() and default_bank_path.exists()):
    inv_source = default_inv_path
    bank_source = default_bank_path
    can_run = True
else:
    can_run = False

if can_run:
    try:
        invoices = DataIngestionEngine.parse_invoices(inv_source)
        bank_txs = DataIngestionEngine.parse_bank_transactions(bank_source)

        engine = ReconciliationEngine(
            amount_tolerance=tolerance,
            fuzzy_threshold=float(fuzzy_threshold),
            date_window_days=date_window,
        )
        matches, summary = engine.reconcile(invoices, bank_txs)

        st.markdown("---")
        st.subheader("📊 Executive Variance & Health Dashboard")

        # KPI Metrics Row
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Gross Invoiced Exposure</div>
                <div class="kpi-val">${summary.total_invoiced_value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Settled Capital</div>
                <div class="kpi-val" style="color:#00E676;">${summary.total_reconciled_value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Unreconciled Variance</div>
                <div class="kpi-val" style="color:#FF5252;">${summary.total_variance_value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            rate = (summary.matched_count / max(summary.total_invoices_reviewed, 1)) * 100
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Reconciliation Rate</div>
                <div class="kpi-val" style="color:#29B6F6;">{rate:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # Discrepancy & Match Drill-Down
        t1, t2, t3, t4 = st.tabs([
            "⚠️ Flagged Anomalies & Action Items",
            "📋 Complete Audit Ledger",
            "⚖️ Agentic Dispute Center (2026)",
            "💬 Conversational Audit Copilot (2026)",
        ])

        with t1:
            disc_records = [
                {
                    "Status": m.match_status.value,
                    "Invoice ID": m.invoice_id or "—",
                    "Bank Ref": m.transaction_id or "—",
                    "Vendor / Entity": m.vendor_name,
                    "Invoice ($)": f"${m.invoice_amount:,.2f}" if m.invoice_amount else "—",
                    "Bank ($)": f"${m.bank_amount:,.2f}" if m.bank_amount else "—",
                    "Discrepancy ($)": f"${m.amount_difference:,.2f}",
                    "Audit Analysis": m.audit_notes,
                }
                for m in matches
                if m.match_status not in [MatchStatus.EXACT_MATCH, MatchStatus.FUZZY_MATCH]
            ]
            if disc_records:
                st.dataframe(pd.DataFrame(disc_records), use_container_width=True)
            else:
                st.success("🎉 Zero discrepancies found! Ledgers balance 100%.")

        with t2:
            all_records = [
                {
                    "Status": m.match_status.value,
                    "Invoice ID": m.invoice_id or "—",
                    "Bank Ref": m.transaction_id or "—",
                    "Vendor": m.vendor_name,
                    "Invoice ($)": m.invoice_amount,
                    "Bank ($)": m.bank_amount,
                    "Delta ($)": m.amount_difference,
                    "Score": f"{m.confidence_score:.0f}%",
                    "Notes": m.audit_notes,
                }
                for m in matches
            ]
            st.dataframe(pd.DataFrame(all_records), use_container_width=True)

        with t3:
            st.subheader("⚖️ Agentic Dispute & Escalation Studio")
            st.caption("Autonomously drafts legally precise, detail-backed vendor dispute communications.")

            discrepant_matches = [m for m in matches if m.match_status not in [MatchStatus.EXACT_MATCH, MatchStatus.FUZZY_MATCH]]
            if discrepant_matches:
                disp_options = {
                    f"{m.vendor_name} ({m.match_status.value} - Delta ${m.amount_difference:,.2f})": m
                    for m in discrepant_matches
                }
                selected_anomaly_label = st.selectbox("Select Anomaly to Dispute", list(disp_options.keys()))
                selected_match = disp_options[selected_anomaly_label]

                col_t1, col_t2 = st.columns([1, 2])
                with col_t1:
                    tone = st.radio("Dispute Tone", ["Inquiry", "Correction", "Escalation"], index=1)
                    if st.button("⚡ Generate Autonomous Dispute Notice", use_container_width=True):
                        st.session_state["active_notice"] = AgenticDisputeGenerator.generate_dispute_notice(selected_match, tone=tone.lower())

                with col_t2:
                    if "active_notice" in st.session_state:
                        notice = st.session_state["active_notice"]
                        st.success(f"Dispute Notice Ready for: {notice['recipient_vendor']}")
                        st.text_input("Subject Line", value=notice["subject"])
                        st.text_area("Letter / Email Body", value=notice["formatted_letter"], height=250)
                        st.download_button(
                            "📥 Download Dispute Notice (.txt)",
                            data=f"Subject: {notice['subject']}\n\n{notice['formatted_letter']}",
                            file_name=f"Dispute_{notice['recipient_vendor'].replace(' ', '_')}.txt",
                            use_container_width=True,
                        )
            else:
                st.info("No discrepancies found to dispute.")

        with t4:
            st.subheader("💬 Conversational Audit Copilot")
            st.caption("Ask questions about this audit ledger in plain English (e.g., 'What is our match rate?', 'Show duplicate invoices', 'Variances over $40').")

            copilot = AuditCopilotEngine(matches, summary)
            user_q = st.text_input("Ask Copilot a question...", placeholder="e.g. Show all variances over $30")
            if user_q:
                res = copilot.query(user_q)
                st.markdown(f"**Copilot:** {res['answer']}")
                if res["records"]:
                    st.dataframe(pd.DataFrame(res["records"]), use_container_width=True)

        # Excel Export
        st.markdown("---")
        temp_excel = root_dir / "data" / "temp_audit.xlsx"
        ExcelReportBuilder.generate(matches, summary, str(temp_excel))
        with open(temp_excel, "rb") as f:
            excel_bytes = f.read()

        st.download_button(
            label="📥 Download Boardroom Executive Excel Model (.xlsx)",
            data=excel_bytes,
            file_name="Executive_Reconciliation_Audit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"Error during audit execution: {e}")
