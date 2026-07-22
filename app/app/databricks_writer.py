"""
Databricks Unity Catalog connector — reads and writes.

Uses the Databricks SDK's Statement Execution API to query and modify
Unity Catalog tables directly.  When running as a Databricks App, the
SDK auto-authenticates via the app's service principal — no tokens,
connection strings, or HTTP paths are needed.

Environment variables:
  WAREHOUSE_ID   – SQL warehouse ID (required)
  CATALOG_SCHEMA – Fully qualified catalog.schema (e.g. christophe_chieu.demo_finance_department)
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SDK client
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    """Return a cached WorkspaceClient instance."""
    global _client
    if _client is None:
        from databricks.sdk import WorkspaceClient
        _client = WorkspaceClient()
    return _client


def _warehouse_id() -> str:
    return os.environ.get("WAREHOUSE_ID", "")


def _fq(table: str) -> str:
    """Return the fully-qualified table name using CATALOG_SCHEMA."""
    schema = os.environ.get("CATALOG_SCHEMA", "")
    if schema:
        return f"{schema}.{table}"
    return table


def _catalog_and_schema() -> tuple[str, str]:
    """Split CATALOG_SCHEMA into (catalog, schema)."""
    cs = os.environ.get("CATALOG_SCHEMA", "")
    if "." in cs:
        parts = cs.split(".", 1)
        return parts[0], parts[1]
    return cs, ""


# ---------------------------------------------------------------------------
# SQL execution
# ---------------------------------------------------------------------------

def execute_sql(statement: str) -> pd.DataFrame:
    """Execute a SQL statement and return results as a DataFrame.

    For DML statements (INSERT/UPDATE/DELETE) the returned DataFrame
    will be empty but the statement is still executed.
    """
    w = _get_client()
    wid = _warehouse_id()
    catalog, schema = _catalog_and_schema()

    if not wid:
        raise RuntimeError(
            "WAREHOUSE_ID environment variable is not set. "
            "Cannot execute SQL against Unity Catalog."
        )

    result = w.statement_execution.execute_statement(
        warehouse_id=wid,
        catalog=catalog,
        schema=schema,
        statement=statement,
        wait_timeout="50s",
    )

    # Check for errors
    if result.status and result.status.error:
        raise RuntimeError(
            f"SQL error: {result.status.error.message}"
        )

    # Extract columns and rows
    if result.manifest and result.manifest.schema and result.manifest.schema.columns:
        columns = [col.name for col in result.manifest.schema.columns]
    else:
        return pd.DataFrame()

    rows = []
    if result.result and result.result.data_array:
        rows = result.result.data_array

    return pd.DataFrame(rows, columns=columns)


def is_available() -> bool:
    """Return True if the Databricks SDK and WAREHOUSE_ID are configured."""
    if not _warehouse_id():
        return False
    try:
        _get_client()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Read functions
# ---------------------------------------------------------------------------

def load_table(table_name: str) -> pd.DataFrame:
    """Read an entire Unity Catalog table into a DataFrame."""
    return execute_sql(f"SELECT * FROM {_fq(table_name)}")


def load_all_tables() -> dict[str, pd.DataFrame]:
    """Load all tables required by the app from Unity Catalog."""
    tables = [
        "crm_invoices",
        "accounting_invoices",
        "credit_notes",
        "reconciliation_items",
        "crm_invoice_lines",
        "accounting_invoice_lines",
        "customers",
    ]
    data = {}
    for t in tables:
        logger.info(f"Loading {_fq(t)} ...")
        data[t] = load_table(t)
    return data


# ---------------------------------------------------------------------------
# Write-back functions
# ---------------------------------------------------------------------------

def apply_manual_invoices(
    crm_invoices: pd.DataFrame,
    crm_invoice_lines: pd.DataFrame,
    invoice_ids: list[str],
) -> int:
    """INSERT missing CRM invoices into accounting tables."""
    crm_inv_lookup = crm_invoices.set_index("crm_invoice_id")
    crm_lines_by_inv = crm_invoice_lines.groupby("crm_invoice_id")
    synced = 0

    for inv_id in invoice_ids:
        if inv_id not in crm_inv_lookup.index:
            continue

        inv = crm_inv_lookup.loc[inv_id]
        acct_inv_id = inv_id.replace("CRM-INV", "ACCT-INV")

        # INSERT accounting_invoices
        execute_sql(
            f"""
            INSERT INTO {_fq('accounting_invoices')}
                (acct_invoice_id, customer_id, crm_invoice_id,
                 invoice_date, total_amount, status)
            VALUES ('{acct_inv_id}', '{inv['customer_id']}', '{inv_id}',
                    '{inv['invoice_date']}',
                    CAST('{inv['total_amount']}' AS DECIMAL(18,2)),
                    'Posted')
            """
        )

        # INSERT accounting_invoice_lines
        if inv_id in crm_lines_by_inv.groups:
            lines = crm_lines_by_inv.get_group(inv_id)
            for idx, (_, ln) in enumerate(lines.iterrows(), start=1):
                acct_line_id = f"ACCT-LN-SYNC-{inv_id}-{idx:02d}"
                execute_sql(
                    f"""
                    INSERT INTO {_fq('accounting_invoice_lines')}
                        (line_id, acct_invoice_id, product_id,
                         quantity, unit_price, line_total)
                    VALUES ('{acct_line_id}', '{acct_inv_id}',
                            '{ln['product_id']}', {int(ln['quantity'])},
                            CAST('{ln['unit_price']}' AS DECIMAL(18,2)),
                            CAST('{ln['line_total']}' AS DECIMAL(18,2)))
                    """
                )

        # INSERT journal entries (Revenue credit + AR debit)
        amount = Decimal(str(inv["total_amount"]))
        rev_amount = (amount * Decimal("0.82")).quantize(Decimal("0.01"))

        execute_sql(
            f"""
            INSERT INTO {_fq('journal_entries')}
                (journal_entry_id, gl_account, gl_account_name,
                 posting_date, amount, entry_type, source,
                 description, reference)
            VALUES ('JE-SYNC-{inv_id}-REV', '4000', 'Revenue - Products',
                    '{inv['invoice_date']}',
                    CAST('{rev_amount}' AS DECIMAL(18,2)),
                    'Credit', 'Automated',
                    'Revenue recognition - {acct_inv_id}',
                    '{acct_inv_id}')
            """
        )
        execute_sql(
            f"""
            INSERT INTO {_fq('journal_entries')}
                (journal_entry_id, gl_account, gl_account_name,
                 posting_date, amount, entry_type, source,
                 description, reference)
            VALUES ('JE-SYNC-{inv_id}-AR', '1100', 'Accounts Receivable',
                    '{inv['invoice_date']}',
                    CAST('{amount}' AS DECIMAL(18,2)),
                    'Debit', 'Automated',
                    'AR posting - {acct_inv_id}',
                    '{acct_inv_id}')
            """
        )

        synced += 1

    return synced


def apply_credit_notes(credit_notes_to_post: pd.DataFrame) -> int:
    """UPDATE accounting_invoices to reduce totals for credit note corrections."""
    posted = 0

    for _, cn in credit_notes_to_post.iterrows():
        crm_inv_id = cn["CRM Invoice ID"]
        amount = Decimal(str(cn["Amount"]))

        execute_sql(
            f"""
            UPDATE {_fq('accounting_invoices')}
            SET total_amount = CAST(total_amount AS DECIMAL(18,2))
                               - CAST('{amount}' AS DECIMAL(18,2))
            WHERE crm_invoice_id = '{crm_inv_id}'
            """
        )
        posted += 1

    return posted


def apply_pricing_fixes(
    crm_invoice_lines: pd.DataFrame,
    pricing_fixes: pd.DataFrame,
) -> int:
    """UPDATE accounting line items and invoice headers for pricing corrections."""
    crm_lines_by_inv = crm_invoice_lines.groupby("crm_invoice_id")
    fixed = 0

    for _, fix in pricing_fixes.iterrows():
        crm_inv_id = fix["CRM Invoice ID"]
        acct_inv_id = fix.get("Acct Invoice ID", "")

        if not acct_inv_id:
            continue

        # Update each line item to match CRM pricing
        if crm_inv_id in crm_lines_by_inv.groups:
            lines = crm_lines_by_inv.get_group(crm_inv_id)
            for _, ln in lines.iterrows():
                execute_sql(
                    f"""
                    UPDATE {_fq('accounting_invoice_lines')}
                    SET unit_price = CAST('{ln['unit_price']}' AS DECIMAL(18,2)),
                        line_total = CAST('{ln['line_total']}' AS DECIMAL(18,2))
                    WHERE acct_invoice_id = '{acct_inv_id}'
                      AND product_id = '{ln['product_id']}'
                    """
                )

        # Recalculate invoice header total from corrected lines
        execute_sql(
            f"""
            UPDATE {_fq('accounting_invoices')}
            SET total_amount = (
                SELECT SUM(CAST(line_total AS DECIMAL(18,2)))
                FROM {_fq('accounting_invoice_lines')}
                WHERE acct_invoice_id = '{acct_inv_id}'
            )
            WHERE acct_invoice_id = '{acct_inv_id}'
            """
        )
        fixed += 1

    return fixed


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

def write_corrections(
    report,
    crm_invoices: pd.DataFrame,
    crm_invoice_lines: pd.DataFrame,
) -> dict:
    """Apply all validated corrections to Unity Catalog tables.

    Returns a summary dict, or ``{"enabled": False}`` if
    the SDK / warehouse is not available.
    """
    if not is_available():
        return {"enabled": False}

    summary = {"enabled": True, "results": []}

    for result in report.results:
        if result.items_processed == 0 or result.details is None:
            continue

        if result.correction_type == "Sync Manual Invoices":
            inv_ids = result.details["CRM Invoice ID"].tolist()
            count = apply_manual_invoices(
                crm_invoices, crm_invoice_lines, inv_ids
            )
            summary["results"].append({
                "type": "Sync Manual Invoices",
                "written": count,
            })

        elif result.correction_type == "Post Credit Notes":
            count = apply_credit_notes(result.details)
            summary["results"].append({
                "type": "Post Credit Notes",
                "written": count,
            })

        elif result.correction_type == "Fix Pricing":
            count = apply_pricing_fixes(
                crm_invoice_lines, result.details
            )
            summary["results"].append({
                "type": "Fix Pricing",
                "written": count,
            })

    return summary
