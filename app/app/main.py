"""
Monthly Close — Finance Controller Portal

A Streamlit app with three workflows:
  1. Upload corrections → trigger reconciliation job
  2. Download the pre-built CFO reporting pack (PPTX)
  3. Reset demo data → restore tables from the CSVs in the UC Volume

Run locally (dev):
    cd app && streamlit run main.py

On Databricks Apps:
    Deployed via app.yaml — the SDK auto-authenticates.
"""

from __future__ import annotations

import io
import os
import time

import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VOLUME_PATH = os.environ.get(
    "VOLUME_PATH",
    "/Volumes/christophe_chieu/demo_finance_department/documents_uploaded",
)
JOB_ID = os.environ.get("JOB_ID", "")
REPORT_PACK_PATH = os.environ.get(
    "REPORT_PACK_PATH",
    "/Volumes/christophe_chieu/demo_finance_department/documents_uploaded/reporting_pack_jan2026.pptx",
)
SQL_WAREHOUSE_ID = os.environ.get("SQL_WAREHOUSE_ID", "")

# Catalog / schema derived from the volume path: /Volumes/<catalog>/<schema>/<volume>
_volume_parts = VOLUME_PATH.strip("/").split("/")
CATALOG, SCHEMA = _volume_parts[1], _volume_parts[2]


def fq(table: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{table}"


# ---------------------------------------------------------------------------
# Reset definitions — tables touched by the reconciliation job, restored from
# the CSV files stored in the UC Volume. Each entry defines the source CSV,
# typed SELECT expressions, and the table / column comments to regenerate.
# ---------------------------------------------------------------------------
RESET_TABLES = [
    {
        "table": "accounting_invoices",
        "csv": "accounting_invoices.csv",
        "select": [
            "CAST(acct_invoice_id AS STRING) AS acct_invoice_id",
            "CAST(customer_id AS STRING) AS customer_id",
            "CAST(crm_invoice_id AS STRING) AS crm_invoice_id",
            "CAST(invoice_date AS DATE) AS invoice_date",
            "CAST(total_amount AS DOUBLE) AS total_amount",
            "CAST(status AS STRING) AS status",
        ],
        "comment": (
            "Invoices recorded in the accounting (ERP) system. One row per "
            "invoice. Reconciled against CRM invoices during the monthly "
            "close to detect missing invoices, unposted credit notes and "
            "pricing mismatches."
        ),
        "columns": {
            "acct_invoice_id": "Unique identifier of the invoice in the accounting system (primary key).",
            "customer_id": "Customer identifier; foreign key to the customers table.",
            "crm_invoice_id": "Identifier of the matching invoice in the CRM system; used for reconciliation.",
            "invoice_date": "Date the invoice was issued.",
            "total_amount": "Total invoice amount in USD, net of any posted credit notes.",
            "status": "Posting status of the invoice in the accounting system (e.g. Posted).",
        },
    },
    {
        "table": "accounting_invoice_lines",
        "csv": "accounting_invoice_lines.csv",
        "select": [
            "CAST(line_id AS STRING) AS line_id",
            "CAST(acct_invoice_id AS STRING) AS acct_invoice_id",
            "CAST(product_id AS STRING) AS product_id",
            "CAST(quantity AS BIGINT) AS quantity",
            "CAST(unit_price AS DOUBLE) AS unit_price",
            "CAST(line_total AS DOUBLE) AS line_total",
        ],
        "comment": (
            "Line items for invoices in the accounting (ERP) system. One row "
            "per product line. Compared against CRM invoice lines to detect "
            "promotional pricing mismatches during the monthly close."
        ),
        "columns": {
            "line_id": "Unique identifier of the invoice line (primary key).",
            "acct_invoice_id": "Parent invoice identifier; foreign key to accounting_invoices.",
            "product_id": "Product identifier; foreign key to the products table.",
            "quantity": "Number of units billed on this line.",
            "unit_price": "Price per unit in USD as recorded in the accounting system.",
            "line_total": "Line amount in USD (quantity x unit price).",
        },
    },
    {
        "table": "journal_entries",
        "csv": "journal_entries.csv",
        "select": [
            "CAST(journal_entry_id AS STRING) AS journal_entry_id",
            "CAST(gl_account AS BIGINT) AS gl_account",
            "CAST(gl_account_name AS STRING) AS gl_account_name",
            "CAST(posting_date AS DATE) AS posting_date",
            "CAST(amount AS DOUBLE) AS amount",
            "CAST(entry_type AS STRING) AS entry_type",
            "CAST(source AS STRING) AS source",
            "CAST(description AS STRING) AS description",
            "CAST(reference AS STRING) AS reference",
        ],
        "comment": (
            "General ledger journal entries. One row per debit or credit "
            "posting. Powers the P&L and balance-sheet views used in the "
            "monthly close reporting."
        ),
        "columns": {
            "journal_entry_id": "Unique identifier of the journal entry (primary key).",
            "gl_account": "General ledger account code the entry is posted to.",
            "gl_account_name": "Human-readable name of the general ledger account.",
            "posting_date": "Date the entry was posted to the general ledger.",
            "amount": "Entry amount in USD.",
            "entry_type": "Whether the entry is a Debit or a Credit.",
            "source": "Origin of the entry: Automated (system-generated) or Manual.",
            "description": "Free-text description of what the entry records.",
            "reference": "Reference to the related document, typically an accounting invoice ID.",
        },
    },
]

st.set_page_config(
    page_title="Monthly Close — Finance Controller Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# SDK helper
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _get_client() -> WorkspaceClient:
    return WorkspaceClient()


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #f8f9fb; }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        div[data-testid="stMetric"] label {
            color: #64748b; font-size: 0.85rem; font-weight: 500;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-size: 1.6rem; font-weight: 700;
        }

        h1, h2, h3 { color: #1e293b; }

        [data-testid="stFileUploader"] {
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 20px;
            background: white;
        }

        .success-banner {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white; padding: 20px 28px; border-radius: 12px;
            margin: 16px 0; font-size: 1.1rem; font-weight: 600;
        }
        .info-card {
            background: white; border: 1px solid #e2e8f0;
            border-radius: 12px; padding: 20px 24px; margin: 8px 0;
        }
        .info-card h4 { margin: 0 0 8px 0; color: #1e293b; }
        .info-card p  { margin: 0; color: #64748b; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# UI components
# ---------------------------------------------------------------------------
def render_header():
    col1, col2 = st.columns([5, 2])
    with col1:
        st.title("Monthly Close — Finance Controller Portal")
        st.caption("January 2026  |  Databricks One")
    with col2:
        st.markdown(
            """
            <div style="text-align: right; padding-top: 16px;">
                <span style="background: #dbeafe; color: #1d4ed8; padding: 6px 16px;
                       border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
                    Finance Controller View
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar():
    with st.sidebar:
        st.markdown("### About This App")
        st.markdown(
            """
            This app is part of the **Databricks One Monthly Close** demo.

            **Workflow:**
            1. Dashboard identifies the gap
            2. Genie investigates root causes
            3. **Upload Corrections** — apply fixes
            4. A Databricks Job processes them
            5. **Reporting Pack** — download CFO report
            6. Dashboard confirms resolution
            """
        )

        st.markdown("---")
        st.markdown("### Volume Path")
        st.code(VOLUME_PATH, language=None)

        if JOB_ID:
            st.markdown("### Job ID")
            st.code(JOB_ID, language=None)

        st.markdown("---")
        st.markdown("### Corrections — Expected Sheets")
        st.markdown(
            """
            | Sheet | Purpose |
            |-------|---------|
            | Sync Manual Invoices | CRM invoices missing from accounting |
            | Post Credit Notes | Unposted credit notes |
            | Fix Pricing | Promo price mismatches |
            """
        )


def render_upload_section():
    st.markdown("---")
    st.subheader("Upload Corrections File")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            <div class="info-card">
                <h4>Expected Excel Format</h4>
                <p>Upload an Excel file (.xlsx) with up to three sheets:</p>
                <ul style="color: #64748b; font-size: 0.9rem; margin-top: 8px;">
                    <li><strong>Sync Manual Invoices</strong> — CRM invoices to post in accounting</li>
                    <li><strong>Post Credit Notes</strong> — Credit notes to apply</li>
                    <li><strong>Fix Pricing</strong> — Invoices with promotional price adjustments</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="info-card">
                <h4>What happens next?</h4>
                <p>
                    The file is uploaded to a Unity Catalog Volume.
                    You can then trigger a Databricks Job that reads the file,
                    validates corrections, and updates the source tables.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=["xlsx", "xls"],
        help="Upload the corrections spreadsheet.",
    )
    return uploaded_file


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------
def upload_to_volume(uploaded_file) -> str:
    """Upload the file to the Unity Catalog Volume. Returns the full path."""
    w = _get_client()
    file_name = uploaded_file.name
    dest_path = f"{VOLUME_PATH}/{file_name}"

    uploaded_file.seek(0)
    w.files.upload(dest_path, uploaded_file, overwrite=True)
    return dest_path


def trigger_job() -> int | None:
    """Trigger the reconciliation job. Returns the run_id."""
    if not JOB_ID:
        return None
    w = _get_client()
    run = w.jobs.run_now(job_id=int(JOB_ID))
    return run.run_id


def run_sql(statement: str) -> None:
    """Execute a SQL statement on the configured warehouse and wait for it."""
    w = _get_client()
    resp = w.statement_execution.execute_statement(
        warehouse_id=SQL_WAREHOUSE_ID,
        statement=statement,
        wait_timeout="50s",
    )
    while resp.status and resp.status.state in (
        StatementState.PENDING,
        StatementState.RUNNING,
    ):
        time.sleep(2)
        resp = w.statement_execution.get_statement(resp.statement_id)

    if not resp.status or resp.status.state != StatementState.SUCCEEDED:
        error = resp.status.error if resp.status else None
        message = error.message if error else str(resp.status.state if resp.status else "unknown")
        raise RuntimeError(f"SQL statement failed: {message}")


def _sq(text: str) -> str:
    """Escape single quotes for embedding in a SQL string literal."""
    return text.replace("'", "''")


def reset_table(spec: dict) -> None:
    """Overwrite one table from its CSV in the Volume, then regenerate the
    table description and column comments."""
    table = fq(spec["table"])
    csv_path = f"{VOLUME_PATH}/{spec['csv']}"
    select_list = ",\n        ".join(spec["select"])

    # 1. Overwrite the table with the CSV contents
    run_sql(f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT
        {select_list}
        FROM read_files(
            '{csv_path}',
            format => 'csv',
            header => true
        )
    """)

    # 2. Regenerate the table description
    run_sql(f"COMMENT ON TABLE {table} IS '{_sq(spec['comment'])}'")

    # 3. Regenerate the column comments
    for column, comment in spec["columns"].items():
        run_sql(
            f"ALTER TABLE {table} ALTER COLUMN {column} COMMENT '{_sq(comment)}'"
        )


# ---------------------------------------------------------------------------
# Reporting pack section
# ---------------------------------------------------------------------------
def render_reporting_section():
    """Download the pre-built month-end reporting pack."""
    st.markdown("---")
    st.subheader("Month-End Reporting Pack")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            <div class="info-card">
                <h4>CFO Reporting Pack — January 2026</h4>
                <p>A pre-built PowerPoint deck with:</p>
                <ul style="color: #64748b; font-size: 0.9rem; margin-top: 8px;">
                    <li><strong>Executive Summary</strong> — top-line KPIs and key highlights</li>
                    <li><strong>P&L Analysis</strong> — revenue and margin variance vs budget</li>
                    <li><strong>Balance Sheet</strong> — working capital, AR/AP trends, key ratios</li>
                    <li><strong>Recommendations</strong> — AI-generated commentary and February outlook</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="info-card">
                <h4>How it works</h4>
                <p>
                    The reporting pack is generated from the same data that powers
                    the AI/BI Dashboard. AI-written variance commentary is included
                    for each section — ready to share with the CFO and leadership.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        download_btn = st.button(
            "📥  Prepare Reporting Pack",
            type="primary",
            use_container_width=True,
            key="prepare_report",
        )

    if download_btn:
        with st.spinner("Fetching reporting pack from Unity Catalog Volume..."):
            try:
                w = _get_client()
                resp = w.files.download(REPORT_PACK_PATH)
                data = resp.contents.read()
                st.session_state["report_bytes"] = data
                st.session_state["report_ready"] = True
            except Exception as e:
                st.error(f"Could not fetch reporting pack: {e}")
                st.info(
                    "Make sure the reporting pack has been uploaded to:\n\n"
                    f"`{REPORT_PACK_PATH}`"
                )

    if st.session_state.get("report_ready"):
        st.markdown(
            """
            <div class="success-banner">
                ✓ Reporting pack ready for download
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button(
                "⬇  Download Reporting Pack (.pptx)",
                data=st.session_state["report_bytes"],
                file_name="reporting_pack_jan2026.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Reset demo data section
# ---------------------------------------------------------------------------
def render_reset_section():
    """Reset the tables affected by the reconciliation job back to their
    original state, from the CSV files stored in the UC Volume."""
    st.markdown("---")
    st.subheader("Reset Demo Data")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            f"""
            <div class="info-card">
                <h4>What gets reset?</h4>
                <p>The three tables modified by the reconciliation job are
                   overwritten with the original CSV files stored in the
                   Unity Catalog Volume:</p>
                <ul style="color: #64748b; font-size: 0.9rem; margin-top: 8px;">
                    <li><code>{fq('accounting_invoices')}</code> ← accounting_invoices.csv</li>
                    <li><code>{fq('accounting_invoice_lines')}</code> ← accounting_invoice_lines.csv</li>
                    <li><code>{fq('journal_entries')}</code> ← journal_entries.csv</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="info-card">
                <h4>How it works</h4>
                <p>
                    Each table is rebuilt from its CSV file in the Volume, then
                    its table description and column comments are regenerated —
                    so the dashboard and Genie space work exactly as before the
                    corrections were applied.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not SQL_WAREHOUSE_ID:
        st.warning(
            "No `SQL_WAREHOUSE_ID` configured. Set it in the app environment "
            "to enable the reset function."
        )
        return

    st.markdown("")
    confirm = st.checkbox(
        "I understand this will overwrite the current tables and undo all "
        "applied corrections.",
        key="reset_confirm",
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        reset_btn = st.button(
            "🔄  Reset Demo Data",
            type="primary",
            use_container_width=True,
            disabled=not confirm,
            key="reset_demo",
        )

    if reset_btn:
        st.session_state.pop("reset_done", None)
        progress = st.progress(0.0, text="Starting reset...")
        try:
            for i, spec in enumerate(RESET_TABLES):
                progress.progress(
                    i / len(RESET_TABLES),
                    text=f"Restoring {spec['table']} from {spec['csv']}...",
                )
                reset_table(spec)
            progress.progress(1.0, text="Reset complete.")
            st.session_state["reset_done"] = True
        except Exception as e:
            progress.empty()
            st.error(f"Reset failed: {e}")
            return

    if st.session_state.get("reset_done"):
        st.markdown(
            """
            <div class="success-banner">
                ✓ Demo data reset — tables restored from the Volume CSVs,
                descriptions and column comments regenerated.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "Refresh the Lakeview dashboard to see the reconciliation gap "
            "back in its original (unresolved) state."
        )


# ---------------------------------------------------------------------------
# Corrections upload flow (refactored from old main)
# ---------------------------------------------------------------------------
def render_corrections_flow():
    """Full corrections upload + job trigger flow."""
    uploaded_file = render_upload_section()

    if uploaded_file is None:
        st.info("Upload an Excel corrections file to get started.")
        return

    # Preview the file
    try:
        import pandas as pd

        xls = pd.ExcelFile(uploaded_file)
        sheets = xls.sheet_names

        st.markdown("---")
        st.subheader("File Preview")
        st.success(f"**{uploaded_file.name}** — {len(sheets)} sheet(s): {', '.join(sheets)}")

        file_tabs = st.tabs(sheets)
        for file_tab, sheet_name in zip(file_tabs, sheets):
            with file_tab:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
                st.dataframe(df, use_container_width=True, hide_index=True, height=300)
    except Exception as e:
        st.error(f"Could not preview file: {e}")

    # Upload button
    st.markdown("---")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        upload_btn = st.button(
            "Upload to Databricks",
            type="primary",
            use_container_width=True,
        )

    if upload_btn:
        with st.spinner("Uploading file to Unity Catalog Volume..."):
            try:
                dest = upload_to_volume(uploaded_file)
                st.session_state["uploaded_path"] = dest
                st.session_state["upload_done"] = True
            except Exception as e:
                st.error(f"Upload failed: {e}")
                return

    # Post-upload UI
    if st.session_state.get("upload_done"):
        dest = st.session_state.get("uploaded_path", "")
        st.markdown(
            f"""
            <div class="success-banner">
                File uploaded successfully to<br>
                <code style="color: #a7f3d0;">{dest}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Trigger job
        if JOB_ID:
            st.markdown("---")
            st.subheader("Process Corrections")
            st.markdown(
                "The file is now in the volume. "
                "Click below to trigger the reconciliation job that will "
                "read the file, validate corrections, and update the source tables."
            )

            col_job, _ = st.columns([1, 3])
            with col_job:
                trigger_btn = st.button(
                    "Trigger Reconciliation Job",
                    type="primary",
                    use_container_width=True,
                )

            if trigger_btn:
                with st.spinner("Triggering job..."):
                    try:
                        run_id = trigger_job()
                        st.session_state["run_id"] = run_id
                    except Exception as e:
                        st.error(f"Failed to trigger job: {e}")

            if "run_id" in st.session_state:
                run_id = st.session_state["run_id"]
                st.success(f"Job triggered successfully!  Run ID: **{run_id}**")
                st.info(
                    "The job is now processing corrections. "
                    "Once complete, refresh the Lakeview dashboard to see "
                    "the updated reconciliation status."
                )
        else:
            st.info(
                "No `JOB_ID` configured. Trigger the reconciliation job "
                "manually from the Databricks Workflows page."
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    inject_css()
    render_header()
    render_sidebar()

    tab_corrections, tab_report, tab_reset = st.tabs([
        "📤  Upload Corrections",
        "📊  Reporting Pack",
        "🔄  Reset Demo",
    ])

    with tab_corrections:
        render_corrections_flow()

    with tab_report:
        render_reporting_section()

    with tab_reset:
        render_reset_section()


if __name__ == "__main__":
    main()
