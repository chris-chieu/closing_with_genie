"""
Correction Processor for the Monthly Close Reconciliation App.

Handles three types of corrections from the uploaded Excel file:
  1. Sync Manual Invoices  – Create accounting entries for CRM-only invoices
  2. Post Credit Notes     – Post unposted credit notes to accounting
  3. Fix Pricing           – Adjust accounting prices to match CRM promo prices

Each processor validates the input, computes impacts, and returns a summary
of changes to apply.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass
class CorrectionResult:
    """Result of processing one correction sheet."""

    correction_type: str
    items_processed: int
    total_amount: Decimal
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: pd.DataFrame | None = None


@dataclass
class ProcessingReport:
    """Aggregate report for all corrections."""

    results: list[CorrectionResult]
    total_gap_before: Decimal
    total_gap_after: Decimal
    gap_resolved: Decimal

    @property
    def gap_resolved_pct(self) -> float:
        if self.total_gap_before == 0:
            return 0.0
        return float(self.gap_resolved / self.total_gap_before * 100)

    @property
    def residual_pct(self) -> float:
        if self.total_gap_before == 0:
            return 0.0
        # Use the original CRM total for the percentage base
        return 100.0 - self.gap_resolved_pct


def _d(val) -> Decimal:
    """Return a Decimal rounded to 2 places."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Individual processors
# ---------------------------------------------------------------------------

def process_manual_invoices(
    sheet_df: pd.DataFrame,
    crm_invoices: pd.DataFrame,
    accounting_invoices: pd.DataFrame,
) -> CorrectionResult:
    """
    Process 'Sync Manual Invoices' sheet.

    For each CRM invoice marked as not synced, validates it exists in CRM
    but not in accounting, then creates the accounting entry.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if sheet_df.empty:
        return CorrectionResult(
            correction_type="Sync Manual Invoices",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=["Sheet is empty"],
        )

    # Normalize column names
    sheet_df.columns = sheet_df.columns.str.strip()

    required_cols = {"CRM Invoice ID"}
    missing = required_cols - set(sheet_df.columns)
    if missing:
        return CorrectionResult(
            correction_type="Sync Manual Invoices",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=[f"Missing required columns: {missing}"],
        )

    # Get unique invoices from the sheet
    invoice_ids = sheet_df["CRM Invoice ID"].dropna().unique()

    # Validate each invoice
    existing_in_acct = set(accounting_invoices["crm_invoice_id"].values)
    existing_in_crm = set(crm_invoices["crm_invoice_id"].values)

    valid_invoices = []
    total_amount = Decimal("0")

    for inv_id in invoice_ids:
        if inv_id not in existing_in_crm:
            errors.append(f"{inv_id}: Not found in CRM invoices")
            continue
        if inv_id in existing_in_acct:
            warnings.append(f"{inv_id}: Already exists in accounting — skipped")
            continue

        crm_row = crm_invoices[crm_invoices["crm_invoice_id"] == inv_id].iloc[0]
        amount = _d(crm_row["total_amount"])
        total_amount += amount
        valid_invoices.append({
            "CRM Invoice ID": inv_id,
            "Customer ID": crm_row["customer_id"],
            "Invoice Date": crm_row["invoice_date"],
            "Amount": float(amount),
            "Status": "To be created in Accounting",
        })

    details_df = pd.DataFrame(valid_invoices) if valid_invoices else None

    return CorrectionResult(
        correction_type="Sync Manual Invoices",
        items_processed=len(valid_invoices),
        total_amount=total_amount,
        errors=errors,
        warnings=warnings,
        details=details_df,
    )


def process_credit_notes(
    sheet_df: pd.DataFrame,
    credit_notes: pd.DataFrame,
) -> CorrectionResult:
    """
    Process 'Post Credit Notes' sheet.

    Validates each credit note ID exists in the credit_notes table, then
    sums the amounts.  The Excel file IS the decision — if a credit note
    is listed, the team has determined it needs to be posted.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if sheet_df.empty:
        return CorrectionResult(
            correction_type="Post Credit Notes",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=["Sheet is empty"],
        )

    sheet_df.columns = sheet_df.columns.str.strip()

    required_cols = {"Credit Note ID"}
    missing = required_cols - set(sheet_df.columns)
    if missing:
        return CorrectionResult(
            correction_type="Post Credit Notes",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=[f"Missing required columns: {missing}"],
        )

    cn_ids = sheet_df["Credit Note ID"].dropna().unique()
    cn_lookup = credit_notes.set_index("credit_note_id")

    valid_notes = []
    total_amount = Decimal("0")

    for cn_id in cn_ids:
        if cn_id not in cn_lookup.index:
            errors.append(f"{cn_id}: Not found in credit notes")
            continue

        cn_row = cn_lookup.loc[cn_id]
        amount = _d(cn_row["amount"])
        total_amount += amount
        valid_notes.append({
            "Credit Note ID": cn_id,
            "CRM Invoice ID": cn_row["crm_invoice_id"],
            "Amount": float(amount),
            "Reason": cn_row["reason"],
            "Status": "To be posted to Accounting",
        })

    details_df = pd.DataFrame(valid_notes) if valid_notes else None

    return CorrectionResult(
        correction_type="Post Credit Notes",
        items_processed=len(valid_notes),
        total_amount=total_amount,
        errors=errors,
        warnings=warnings,
        details=details_df,
    )


def process_pricing_fixes(
    sheet_df: pd.DataFrame,
    reconciliation_items: pd.DataFrame,
) -> CorrectionResult:
    """
    Process 'Fix Pricing' sheet.

    For each invoice with a pricing discrepancy, calculates the adjustment
    needed to align accounting prices with CRM promotional prices.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if sheet_df.empty:
        return CorrectionResult(
            correction_type="Fix Pricing",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=["Sheet is empty"],
        )

    sheet_df.columns = sheet_df.columns.str.strip()

    required_cols = {"CRM Invoice ID"}
    missing = required_cols - set(sheet_df.columns)
    if missing:
        return CorrectionResult(
            correction_type="Fix Pricing",
            items_processed=0,
            total_amount=Decimal("0"),
            errors=[f"Missing required columns: {missing}"],
        )

    invoice_ids = sheet_df["CRM Invoice ID"].dropna().unique()
    recon_lookup = reconciliation_items.set_index("crm_invoice_id")

    valid_fixes = []
    total_amount = Decimal("0")

    for inv_id in invoice_ids:
        if inv_id not in recon_lookup.index:
            errors.append(f"{inv_id}: Not found in reconciliation items")
            continue

        recon_row = recon_lookup.loc[inv_id]
        # Handle case where there could be multiple rows (shouldn't happen)
        if isinstance(recon_row, pd.DataFrame):
            recon_row = recon_row.iloc[0]

        variance = _d(abs(float(recon_row["variance_amount"])))
        if variance == 0:
            warnings.append(f"{inv_id}: No pricing variance found — skipped")
            continue

        total_amount += variance
        valid_fixes.append({
            "CRM Invoice ID": inv_id,
            "Acct Invoice ID": recon_row.get("acct_invoice_id", ""),
            "CRM Amount": float(recon_row["crm_amount"]),
            "Acct Amount": float(recon_row["acct_amount"]),
            "Variance": float(variance),
            "Status": "Adjust accounting to promo price",
        })

    details_df = pd.DataFrame(valid_fixes) if valid_fixes else None

    return CorrectionResult(
        correction_type="Fix Pricing",
        items_processed=len(valid_fixes),
        total_amount=total_amount,
        errors=errors,
        warnings=warnings,
        details=details_df,
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def process_corrections(
    excel_file,
    crm_invoices: pd.DataFrame,
    accounting_invoices: pd.DataFrame,
    credit_notes: pd.DataFrame,
    reconciliation_items: pd.DataFrame,
) -> ProcessingReport:
    """
    Process an uploaded Excel corrections file with up to 3 sheets.

    Returns a ProcessingReport with the results for each sheet and
    the overall impact on the reconciliation gap.
    """
    # Read all sheets
    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names

    results: list[CorrectionResult] = []

    # --- Sheet 1: Sync Manual Invoices ---
    if "Sync Manual Invoices" in sheet_names:
        df = pd.read_excel(xls, sheet_name="Sync Manual Invoices")
        result = process_manual_invoices(df, crm_invoices, accounting_invoices)
        results.append(result)

    # --- Sheet 2: Post Credit Notes ---
    if "Post Credit Notes" in sheet_names:
        df = pd.read_excel(xls, sheet_name="Post Credit Notes")
        result = process_credit_notes(df, credit_notes)
        results.append(result)

    # --- Sheet 3: Fix Pricing ---
    if "Fix Pricing" in sheet_names:
        df = pd.read_excel(xls, sheet_name="Fix Pricing")
        result = process_pricing_fixes(df, reconciliation_items)
        results.append(result)

    # --- Compute gap impact ---
    # Current gap: sum of all unmatched / variance / credit-note-issue items
    # in the reconciliation view.  The credit note gap is already captured
    # as invoice-level variance (accounting header > CRM header).
    gap_before = Decimal("0")
    for _, row in reconciliation_items.iterrows():
        status = row["match_status"]
        if status in ("Unmatched-CRM Only", "Variance", "Credit Note Issue"):
            gap_before += _d(abs(float(row["variance_amount"])))

    gap_resolved = sum(r.total_amount for r in results)
    gap_after = max(gap_before - gap_resolved, Decimal("0"))

    return ProcessingReport(
        results=results,
        total_gap_before=gap_before,
        total_gap_after=gap_after,
        gap_resolved=gap_resolved,
    )
