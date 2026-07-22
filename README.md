# Databricks One — Monthly Close Demo

End-to-end "Monthly Close" reconciliation demo for a finance department. A Lakeview dashboard surfaces a revenue reconciliation gap between CRM and accounting systems, a Genie space lets users investigate root causes in natural language, a Streamlit app (Databricks App) lets a controller upload corrections and trigger remediation, and a Lakeflow Job applies the corrections back to Unity Catalog tables.


## Workflow

1. **Dashboard** — CFO / controller opens the monthly close dashboard and sees a revenue reconciliation gap.
2. **Genie** — user asks the Finance Genie space natural-language questions to investigate root causes (missing invoices, unposted credit notes, pricing mismatches).
3. **App — Upload Corrections** — controller uploads an Excel file with the fixes to a Unity Catalog Volume via the Streamlit app.
4. **Job** — uploading triggers (or the user manually triggers) the reconciliation job, which reads the Excel file and writes corrections to the accounting tables.
5. **Dashboard** — refreshing the dashboard shows the gap resolved.
6. **App — Reporting Pack** — controller downloads a pre-built CFO PowerPoint pack.
7. **App — Reset Demo** — restores the three affected tables from their original CSVs in the Volume, for repeatable demos.

## Repository Structure

```
app/                        Databricks App (Streamlit) source
  main.py                   UI: upload corrections, download reporting pack, reset demo data
  databricks_writer.py      Unity Catalog read/write helpers (Statement Execution API)
  correction_processor.py   Validates and summarizes the uploaded corrections Excel file
  app.yaml                  App command, env vars, and resource bindings
  requirements.txt          Python dependencies
jobs/
  process_corrections       Notebook run by the reconciliation job
README.md
```

## Components

### 1. App — Databricks App (Streamlit)

* **Source:** `app/` (`main.py`, `databricks_writer.py`, `correction_processor.py`, `app.yaml`, `requirements.txt`)
* **Framework:** Streamlit (`streamlit run main.py`)
* **App resource:** a SQL warehouse resource, bound in the Apps UI under the key `sql-warehouse`. Used by the Reset Demo function to rebuild tables and exposed to the app via the `SQL_WAREHOUSE_ID` env var (`valueFrom: sql-warehouse` in `app.yaml`).
* **Environment variables** (`app.yaml`) — update these to match your target environment:
  * `VOLUME_PATH` — UC Volume path for uploaded corrections files, e.g. `/Volumes/<catalog>/<schema>/documents_uploaded`
  * `JOB_ID` — the reconciliation job's ID in your workspace (assigned when you create the job, see below)
  * `SQL_WAREHOUSE_ID` — bound via `valueFrom: sql-warehouse`; no need to hardcode a value
* **Auth:** no PATs or secrets in code — the Databricks SDK `WorkspaceClient()` auto-authenticates as the app's service principal. No app-specific secrets need to be configured.

### 2. Job — Reconciliation Job (Lakeflow Job)

* **Task:** single notebook task running the `jobs/process_corrections` notebook.
* **Compute:** serverless job compute with the `openpyxl` library dependency (required to read the uploaded `.xlsx` corrections file).
* **Trigger:** run on demand — either manually or via the app's "Trigger Reconciliation Job" button (`w.jobs.run_now(job_id=...)`), after the corrections file has been uploaded to the Volume.
* **What it does:** reads the uploaded corrections Excel file from `/Volumes/<catalog>/<schema>/documents_uploaded/`, validates the three correction sheets (Sync Manual Invoices, Post Credit Notes, Fix Pricing), and writes the changes to `accounting_invoices`, `accounting_invoice_lines`, and `journal_entries`.
* Before creating the job, update the `CATALOG` / `SCHEMA` constants at the top of the notebook to point at your target catalog and schema.

### 3. Dashboard — Monthly Close (Lakeview)

A Lakeview dashboard whose datasets query the finance schema tables (`crm_invoices`, `accounting_invoices`, `credit_notes`, `reconciliation_items`, `journal_entries`, `customers`) to surface the CRM-vs-accounting revenue gap, P&L variance, and AR trends. When importing/rebuilding it in a new workspace, point every dataset query at your target catalog and schema.

### 4. Genie Space — Finance Ask Me Anything

A Genie space over the same finance tables, used for natural-language investigation of CRM vs. accounting discrepancies, invoice/payment/journal-entry analysis, and customer segmentation for root-cause analysis of the reconciliation gap.

* **Known limitations:** no detailed payment/adjustment transaction history beyond invoice and credit-note headers; no real-time integration with external systems; no inventory/returns data beyond invoices.

## Data

This demo does not ship a target catalog/schema — you must create one in your workspace and load the data into it before deploying the job, app, dashboard, and Genie space.

* Create a Unity Catalog **catalog** and **schema** (e.g. `<catalog>.<schema>`) to hold the demo data.
* Create a **Volume** in that schema (e.g. `<catalog>.<schema>.documents_uploaded`) and upload:
  * `accounting_invoices.csv`, `accounting_invoice_lines.csv`, `journal_entries.csv` — source-of-truth CSVs used by the app's **Reset Demo** function to rebuild the three tables the job modifies.
  * A reporting pack `.pptx` — served by the app's **Reporting Pack** tab (update `REPORT_PACK_PATH` in `main.py` to match the file name you upload).
* Load the CSVs (and any additional CRM/customer source data) into the following **tables** in your schema: `crm_invoices`, `crm_invoice_lines`, `accounting_invoices`, `accounting_invoice_lines`, `credit_notes`, `reconciliation_items`, `journal_entries`, `customers`.
* The uploaded corrections file (produced by the finance team, consumed by the reconciliation job) is written to the same Volume by the app — no need to pre-create it.

## Setup

1. **Data** — create the catalog/schema/Volume and load the tables described above.
2. **Job** — import the `jobs/process_corrections` notebook, update its `CATALOG` / `SCHEMA` constants, and create a job with a single notebook task on serverless compute with the `openpyxl` dependency. Note the resulting job ID.
3. **App** — deploy the `app/` folder as a Databricks App, attach a SQL warehouse as the `sql-warehouse` resource, and set `VOLUME_PATH` / `JOB_ID` in `app.yaml` to match your catalog/schema and the job ID from step 2.
4. **Dashboard** — import or rebuild the Lakeview dashboard, pointing its dataset queries at your catalog/schema.
5. **Genie space** — create a Genie space over the same tables, with instructions describing the data model above.

## Redeployment Checklist

1. **Job:** confirm the job's notebook task points at the current `jobs/process_corrections` notebook and that the `openpyxl` dependency is present in the serverless environment.
2. **App:** redeploy from `app/`; verify the `sql-warehouse` resource is attached and `VOLUME_PATH` / `JOB_ID` in `app.yaml` match the target catalog/schema and job ID.
3. **Dashboard:** verify the dashboard's dataset queries resolve against your target catalog/schema.
4. **Genie space:** confirm the Genie space's table list matches the schema above and permissions allow the intended audience to query it.
5. **Reset demo data:** use the app's **Reset Demo** tab (requires the `sql-warehouse` resource) to restore `accounting_invoices`, `accounting_invoice_lines`, and `journal_entries` from the Volume CSVs before each demo run.
