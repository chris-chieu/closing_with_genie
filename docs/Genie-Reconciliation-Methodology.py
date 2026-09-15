# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Title & Operating Model
# MAGIC %md
# MAGIC # Genie Reconciliation Methodology
# MAGIC ## Reusable Principles & Verification Prompts
# MAGIC
# MAGIC A practitioner's framework for deploying Databricks Genie as a **read-only monthly reconciliation investigation assistant**. It applies in tax, treasury, insurance claims, intercompany eliminations, subledger-to-general-ledger reconciliation, and other domains that operate recurring close cycles.
# MAGIC
# MAGIC The framework uses **reconciliation scope** as its neutral unit of design. A scope may be a legal entity, account, bank account, currency, portfolio, business unit, product, claims cohort, counterparty, or another stable segment. Legal entity is a common default in tax and statutory close; it is not a universal design rule.
# MAGIC
# MAGIC Each principle includes a Genie Code action script. The script is intended to **CHECK** queryable artifacts available to Genie Code and **BUILD** drafts of missing artifacts such as views, metadata, instructions, join snippets, and deterministic test queries. Review all generated artifacts before applying them.
# MAGIC Copy and paste into Genie Code each of the action script
# MAGIC
# MAGIC ### What a pass criterion means
# MAGIC
# MAGIC A pass criterion is an assertion Genie Code can verify from accessible, governed, queryable artifacts: schema and catalog metadata, table/view definitions, instruction text, persisted run records, test results, or other control evidence. A pass criterion does **not** prove business truth, control effectiveness, timely human review, approval quality, or the adequacy of professional judgment.
# MAGIC
# MAGIC The framework therefore separates four evidence levels:
# MAGIC
# MAGIC | Evidence level | Example | Genie Code can assess? |
# MAGIC |---|---|---|
# MAGIC | Artifact existence | A break-summary view, certification tag, join snippet, or benchmark exists | Usually yes |
# MAGIC | Structural conformance | Required fields are present; a join includes the declared scope and period; an instruction mandates provenance | Usually yes |
# MAGIC | Persisted execution evidence | A refresh, access test, benchmark, or review record has a timestamp and result in a governed table | Yes, if accessible |
# MAGIC | Control effectiveness | A reviewer concluded the analysis was sufficient; a policy was applied correctly; a team acted on a finding | No — practitioner-owned |
# MAGIC
# MAGIC ### How to use this notebook
# MAGIC
# MAGIC 1. Define the reconciliation scope and applicable close period.
# MAGIC 2. Run the principles in the sequence shown below. Within each phase, retain a single Genie Code session where useful so later scripts can reuse discovered context.
# MAGIC 3. Treat a failed structural criterion as a design or data gap. Treat missing human/process evidence as a practitioner action, not as something the assistant can declare complete.
# MAGIC 4. Review and apply any SQL, metadata, instructions, or snippets Genie Code drafts; then rerun the relevant check.
# MAGIC 5. Revisit the recurring principles at every close and revisit setup principles after material changes to data, scope, policy, access, or the Genie space.
# MAGIC
# MAGIC ### Principles at a glance
# MAGIC
# MAGIC | # | Principle | Category | Phase |
# MAGIC |---|---|---|---|
# MAGIC | 1 | Reconciliation Grain and Linkage | Data foundation | 1. Data foundation |
# MAGIC | 2 | Close-Period Readiness, Finality, and Reproducibility | Data foundation | 1. Data foundation |
# MAGIC | 3 | Metadata Curation | Data foundation | 1. Data foundation |
# MAGIC | 4 | Explicit Matching and Variance Logic | Reconciliation model | 2. Reconciliation model |
# MAGIC | 5 | Precompute the Break Summary | Reconciliation model | 2. Reconciliation model |
# MAGIC | 6 | Scope the Genie Space | Agent design | 3. Agent design and access |
# MAGIC | 7 | Security Model: Viewer Run-As | Agent design and access | 3. Agent design and access |
# MAGIC | 8 | Read-Only Investigation Boundary | Agent design and access | 3. Agent design and access |
# MAGIC | 9 | Workflow-Oriented Starter Questions | User experience | 3. Agent design and access |
# MAGIC | 10 | Traceable Answers and Provenance | Controls | 4. Evidence and quality |
# MAGIC | 11 | Benchmark and Improve Each Close Cycle | Controls | 4. Evidence and quality |
# MAGIC | 12 | Independent Evaluation and Assurance | Controls | 4. Evidence and quality |

# COMMAND ----------

# DBTITLE 1,Principle 1 — Reconciliation Grain and Linkage
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 1: Reconciliation Grain and Linkage
# MAGIC **Category:** Data foundation
# MAGIC
# MAGIC **Statement:** *"If the available data cannot isolate and explain a reconciliation break, Genie cannot do so either."*
# MAGIC
# MAGIC Reconciliation begins with a model that supports investigation at the appropriate level of detail. The relevant source, target, and reference datasets need a documented grain, a way to associate contributing records across datasets, and a field for scoping to the close period. A summary-only table may support reporting, but not dependable drill-down unless a declared detail path exists.
# MAGIC
# MAGIC Do not require Genie to infer business keys from similarly named columns. Declare the reconciliation keys, expected linkage pattern, and drill-down route from an exception summary to supporting records.
# MAGIC
# MAGIC **Pass criteria — queryable structural evidence:**
# MAGIC * Reconciliation-relevant datasets are identified and each has a documented grain
# MAGIC * Each relevant dataset contains a declared close-period field or is linked through a documented period-scoping rule
# MAGIC * Declared reconciliation keys and relationship/join artifacts exist for the relevant source, target, and supporting datasets
# MAGIC * Sample queries can trace a selected break or variance from the exception level to contributing supporting records
# MAGIC * Profiling queries exist or can be generated for null keys, duplicate keys, and unmatched-key rates by close period
# MAGIC
# MAGIC **Practitioner guidance — adequacy of the data model:**
# MAGIC * A domain owner determines whether the documented grain and linkage genuinely support the reconciliation objective; field presence alone does not prove semantic adequacy.
# MAGIC * The close team decides which aggregation level is appropriate for the reconciliation and whether exception drill-down is sufficiently complete for review.
# MAGIC * Resolve structural data-model gaps before treating the Genie space as a close investigation capability.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 1
# MAGIC %md
# MAGIC ```text
# MAGIC Assess reconciliation grain and linkage.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog: <your_catalog>
# MAGIC - Schema: <your_schema>
# MAGIC - Close period: <YYYY-MM or other period identifier>
# MAGIC - Reconciliation scope field(s): <for example entity_code, bank_account, portfolio>
# MAGIC
# MAGIC STEP 1 — DISCOVER:
# MAGIC 1. List tables and views in the catalog/schema using information_schema.
# MAGIC 2. Identify candidate reconciliation datasets and assign a role: source, target, supporting detail, reference, readiness/control, or break summary.
# MAGIC 3. For each candidate, list documented table grain, period field, scope field(s), primary/business key candidates, and descriptions.
# MAGIC
# MAGIC STEP 2 — CHECK:
# MAGIC 4. Identify datasets with no documented grain, no usable period-scoping field, or no declared linkage to another relevant dataset.
# MAGIC 5. For each declared linkage, profile the selected close period for null keys, duplicate keys, unmatched keys, and cardinality risks.
# MAGIC 6. Identify summary-only datasets lacking a documented supporting-detail drill-down route.
# MAGIC 7. Draft a sample trace query that starts from one selected break/variance and returns its contributing records.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 8. Draft table/column comments for missing grain, period, scope, and key documentation.
# MAGIC 9. Draft reusable profiling SQL for key completeness and match-rate checks by close period.
# MAGIC 10. Draft a reconciliation-key and drill-down mapping artifact using actual table and column names.
# MAGIC
# MAGIC Output: a table-role and linkage inventory; gaps classified as MISSING_GRAIN,
# MAGIC MISSING_PERIOD_SCOPE, UNDECLARED_LINKAGE, KEY_QUALITY_RISK, or NO_DRILLDOWN_PATH.
# MAGIC Flag structural gaps for practitioner resolution; do not claim that semantic adequacy
# MAGIC has been proven.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 2 — Close-Period Readiness, Finality, and Reproducibility
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 2: Close-Period Readiness, Finality, and Reproducibility
# MAGIC **Category:** Data foundation
# MAGIC
# MAGIC **Statement:** *"An agent may investigate a close period only when its inputs are identifiable, status-labelled, and reproducible for that period."*
# MAGIC
# MAGIC A generally trusted table is not automatically a valid source for a particular close. The reconciliation needs to identify which source versions were used, whether the data is preliminary or approved/final, when it was available, and whether the break summary and supporting detail use consistent inputs. Without this, the same question may produce different results during a review, or a preparer may inadvertently investigate a mixed-as-of population.
# MAGIC
# MAGIC This principle separates **queryable evidence of readiness** from the business decision that a source is complete or final. Genie Code can inspect fields, control records, timestamps, run identifiers, and consistency. It cannot determine whether an upstream system’s completion declaration is substantively correct.
# MAGIC
# MAGIC **Pass criteria — queryable structural evidence:**
# MAGIC * Each reconciliation-relevant dataset exposes a close-period identifier (e.g., fiscal_period, close_month) or is linked through a documented period-scoping rule
# MAGIC * Where a data-status field exists (e.g., preliminary, final, approved), Genie Code can inspect its value for the selected scope and period
# MAGIC
# MAGIC **Graduated evidence — where readiness infrastructure exists:**
# MAGIC The following checks become possible when the organization has built the supporting infrastructure. Genie Code can assess them if the artifacts are accessible, but their absence is a maturity gap, not a structural blocker:
# MAGIC * As-of timestamps, snapshot identifiers, or pipeline-run identifiers are present on reconciliation-relevant datasets and are consistent across the inputs used for a given close period
# MAGIC * A readiness/control record identifies the required upstream inputs for a reconciliation scope and close period, enabling a query to flag missing, stale, non-final, or mixed-as-of inputs
# MAGIC * The break summary records or can be linked to the source snapshot/run identifiers used to compute it
# MAGIC * Re-running a defined deterministic reconciliation query against the recorded snapshot/run identifiers is technically possible (e.g., via Delta time travel or explicit snapshot tables)
# MAGIC
# MAGIC **Practitioner guidance — close authority and cutover:**
# MAGIC * The close team defines the cutoff calendar, finality definitions, late-adjustment policy, restatement handling, and authority to declare data ready.
# MAGIC * A designated owner confirms the operational completeness of upstream feeds and decides when a preliminary result may be used.
# MAGIC * Preserve the approved close snapshot and supporting evidence according to the organization’s retention and audit policy.
# MAGIC
# MAGIC **Practitioner guidance — mid-cycle data changes and restatement:**
# MAGIC Source data can change during a live investigation — an upstream rerun, corrected extract, late-arriving feed, revised mapping, or restated break summary. The close team should define:
# MAGIC * What constitutes a mid-cycle change that requires preparer notification (e.g., any source refresh after the investigation baseline is established)
# MAGIC * Whether and how prior snapshot/run versions are retained so earlier investigation results remain reproducible
# MAGIC * How Genie instructions should handle data-basis context: instruct Genie to include snapshot/version/timestamp references in answers so preparers can identify when the data basis differs from their earlier investigation. Whether a change is material, whether analysis must be repeated, or whether sign-off remains valid are close-team decisions.
# MAGIC * Where snapshot infrastructure exists (graduated evidence above), instruct Genie to include the snapshot/run context in answers and to reference a single consistent snapshot set when comparing populations.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 2
# MAGIC %md
# MAGIC ```text
# MAGIC Assess close-period readiness, finality, and reproducibility.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog: <your_catalog>
# MAGIC - Schema: <your_schema>
# MAGIC - Close period: <YYYY-MM or other period identifier>
# MAGIC - Reconciliation scope: <selected scope value>
# MAGIC - Expected input domains: <source, target, reference, etc.>
# MAGIC
# MAGIC STEP 1 — DISCOVER:
# MAGIC 1. For each reconciliation-relevant dataset, identify close-period
# MAGIC    field, data-status field (if any), as-of timestamp, snapshot ID,
# MAGIC    version, or run-ID fields (if any).
# MAGIC 2. Identify any readiness/control tables, snapshot tables, or
# MAGIC    pipeline-run logs that exist in the schema.
# MAGIC
# MAGIC STEP 2 — CHECK (baseline):
# MAGIC 3. Does every reconciliation-relevant dataset have a usable
# MAGIC    close-period identifier?
# MAGIC 4. Where a data-status field exists, what is its value for the
# MAGIC    selected scope and close period?
# MAGIC
# MAGIC STEP 3 — CHECK (graduated — where infrastructure exists):
# MAGIC 5. Are as-of timestamps, snapshot IDs, or run IDs present and
# MAGIC    consistent across the inputs for this close period?
# MAGIC 6. Does a readiness/control record exist? If so, flag missing,
# MAGIC    stale, non-final, or mixed-as-of inputs.
# MAGIC 7. Can the break summary be tied to a consistent source
# MAGIC    snapshot/run set?
# MAGIC
# MAGIC STEP 4 — BUILD:
# MAGIC 8. If no readiness infrastructure exists, draft a generic schema
# MAGIC    for an organization-governed readiness record (reconciliation_scope,
# MAGIC    close_period, input_domain, data_status, as_of_timestamp,
# MAGIC    snapshot_or_run_id, recorded_at, evidence_reference).
# MAGIC    Flag this as a maturity recommendation, not a blocker.
# MAGIC 9. Draft Genie instructions requiring official close responses to
# MAGIC    state the close period and data status where available.
# MAGIC
# MAGIC Output: a readiness inventory per dataset. Classify gaps as
# MAGIC MISSING_PERIOD (structural blocker) or MISSING_STATUS,
# MAGIC MISSING_SNAPSHOT_LINK, NO_READINESS_RECORD (maturity gaps).
# MAGIC Do not declare an input complete or final; report only the
# MAGIC recorded evidence.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 3 — Metadata Curation
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 3: Metadata Curation
# MAGIC **Category:** Data foundation
# MAGIC
# MAGIC **Statement:** *"Genie needs curated business context for the datasets and fields it is expected to use in reconciliation."*
# MAGIC
# MAGIC Focus curation on reconciliation-relevant datasets, not every object in the schema. Table descriptions should identify the business content, documented grain, originating system/process, and expected role. Column descriptions should explain business meaning. For coded fields, document valid values and their meaning. This minimizes unsupported inference from names alone.
# MAGIC
# MAGIC **Pass criteria — queryable structural evidence:**
# MAGIC * Reconciliation-relevant datasets are identified as source, target, supporting detail, break summary, reference, readiness/control, or other declared role
# MAGIC * Each relevant dataset has a non-empty description documenting its business content, data origin, and grain
# MAGIC * Required reconciliation columns—including period, scope, keys, measures, status, and diagnostic fields—have non-empty descriptions
# MAGIC * Coded or enumerated fields used in reconciliation have documented values/meanings in metadata or an accessible reference artifact
# MAGIC
# MAGIC **Practitioner guidance — semantic quality:**
# MAGIC * A domain owner validates that descriptions accurately reflect the business definition; a non-empty comment is not proof of correctness.
# MAGIC * Maintain glossary ownership for terms whose meaning varies by scope, such as balance, exposure, settled, approved, final, exception, or variance.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 3
# MAGIC %md
# MAGIC ```text
# MAGIC Audit and improve metadata for reconciliation-relevant datasets.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog: <your_catalog>
# MAGIC - Schema: <your_schema>
# MAGIC
# MAGIC STEP 1 — DISCOVER:
# MAGIC 1. List tables and views and inspect descriptions, columns, and column comments.
# MAGIC 2. Identify reconciliation-relevant datasets and assign their roles.
# MAGIC
# MAGIC STEP 2 — CHECK:
# MAGIC 3. List relevant datasets without a usable table description.
# MAGIC 4. List required reconciliation fields without descriptions: scope, period, business/reconciliation keys, amounts/measures, status, data status, as-of/snapshot/run ID, and diagnostic fields where present.
# MAGIC 5. Identify coded fields used in reconciliation and compare sampled distinct values with available descriptions or reference data.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 6. Draft table comments that identify business content, data origin, documented grain, and role.
# MAGIC 7. Draft ALTER TABLE ... ALTER COLUMN ... SET COMMENT statements for missing or weak required-field comments.
# MAGIC 8. Draft a compact reference-table specification for undocumented code values if metadata comments are insufficient.
# MAGIC
# MAGIC Output a prioritized report: object_name | field_name | role | issue_type |
# MAGIC current_documentation | proposed_documentation. Mark semantic validation as practitioner-owned.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 4 — Explicit Matching and Variance Logic
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 4: Explicit Matching and Variance Logic
# MAGIC **Category:** Reconciliation model
# MAGIC
# MAGIC **Statement:** *"Where reconciliation compares two or more populations, maintain one authoritative definition of matching, variance, timing, and unmatched-item treatment."*
# MAGIC
# MAGIC Intercompany reconciliation is one instance of a wider pattern: legal-entity-to-legal-entity, bank-to-book, subledger-to-GL, custodian-to-book, claims-to-reserve, or system-to-system reconciliation. The same business event can have different identifiers, dates, signs, currencies, formats, or timing on each side. The assistant must not infer the matching rule.
# MAGIC
# MAGIC Declare the participating datasets, reconciliation scope, period-scoping rule, join keys, cardinality expectation, sign/currency logic, tolerance policy reference, treatment of timing differences, and definition of matched/unmatched. For complex or fuzzy matching, define the deterministic logic and the exception cases rather than describing it only in prose.
# MAGIC
# MAGIC **Pass criteria — queryable structural evidence:**
# MAGIC * An accessible matching/variance artifact identifies participating datasets, reconciliation scope field(s), close-period rule, and declared business or composite join keys
# MAGIC * At least one executable SQL example implements the matching/variance pattern using actual tables and columns
# MAGIC * The artifact defines matched, unmatched, partial-match, timing-difference, and duplicate-match treatment where applicable
# MAGIC * Matching logic references a queryable tolerance/policy artifact when tolerances apply, rather than relying only on hard-coded instruction text
# MAGIC * Profiling or test queries calculate match rates, unmatched counts/amounts, and duplicate/many-to-many risks by close period and scope
# MAGIC
# MAGIC **Practitioner guidance — policy and semantic approval:**
# MAGIC * Domain owners approve the economic meaning of a match, tolerance policy, timing window, sign convention, FX treatment, and exception treatment.
# MAGIC * Where intercompany applies, both counterparties align on the authoritative matching logic and escalation path.
# MAGIC * A table or snippet can document a rule; it cannot prove that the rule is suitable for the business purpose.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 4
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and build explicit matching and variance logic.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog: <your_catalog>
# MAGIC - Schema: <your_schema>
# MAGIC - Reconciliation scope: <scope type and selected value>
# MAGIC - Close period: <period identifier>
# MAGIC - Reconciliation type: <for example bank-to-book, intercompany, subledger-to-GL>
# MAGIC
# MAGIC STEP 1 — DISCOVER:
# MAGIC 1. Identify the participating source/target datasets and any existing join snippets, SQL examples, tolerance tables, and matching documentation.
# MAGIC 2. Identify scope fields, period fields, candidate business keys, amount/currency fields, status fields, and counterparty fields where relevant.
# MAGIC
# MAGIC STEP 2 — CHECK:
# MAGIC 3. Does an accessible artifact explicitly define the participating datasets, scope filter, period rule, join keys, match definition, unmatched treatment, and tolerance reference where applicable?
# MAGIC 4. Does an executable SQL example apply those rules with actual tables and columns?
# MAGIC 5. Profile the selected period for null join keys, duplicate keys, one-to-many/many-to-many matches, unmatched items, and amount variance.
# MAGIC 6. For intercompany, verify that both reporting and counterparty scope are explicit and the close period is applied consistently.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 7. Draft a reusable matching SQL snippet, scoped to the selected period and reconciliation scope.
# MAGIC 8. Draft a variance/unmatched SQL query that records a clear match status and reason.
# MAGIC 9. Draft profiling SQL for match rate, duplicate-match risk, and unmatched variance.
# MAGIC 10. Draft generic effective-dated tolerance-reference-table fields if policy values are currently embedded in instructions.
# MAGIC
# MAGIC Output the authoritative logic inventory and flags: MISSING_MATCH_RULE,
# MAGIC NO_PERIOD_SCOPE, UNDECLARED_CARDINALITY, MISSING_TOLERANCE_REFERENCE,
# MAGIC DUPLICATE_MATCH_RISK, or UNMATCHED_POPULATION.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 5 — Precompute the Break Summary
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 5: Precompute the Break Summary
# MAGIC **Category:** Reconciliation model
# MAGIC
# MAGIC **Statement:** *"Precompute a period-specific break summary so preparers begin with an authoritative investigation queue, not ad hoc reconstruction from raw data."*
# MAGIC
# MAGIC The break summary is the operational center of the close workflow. It makes the current exception population visible and supports common questions without repeatedly rebuilding the reconciliation from raw sources. For each organization-defined reconciliation key and close period, it should expose the variance, break state, diagnostic/classification information where available, aging/carry-forward status, and a route to supporting detail.
# MAGIC
# MAGIC Define the matching and variance logic first. For a two-sided reconciliation—including intercompany—Principle 4 is a prerequisite to the final break-summary definition.
# MAGIC
# MAGIC **Pass criteria — queryable structural and execution evidence:**
# MAGIC * A table or view exists that materializes or reliably exposes a break summary by declared reconciliation scope/key and close period
# MAGIC * The summary contains current-period variance/break state and a declared drill-down identifier or route to supporting detail
# MAGIC * The summary distinguishes current-period exceptions from carry-forward/aged items and exposes originating period, age, or equivalent history where applicable
# MAGIC * The summary includes or can be joined to a comparable prior-period measure when prior-period comparison is in scope
# MAGIC * The summary carries or links to data-status and as-of/snapshot/run evidence required by Principle 2
# MAGIC * Agent instructions designate the summary as the default source for open-break questions, and benchmark cases test that convention
# MAGIC
# MAGIC **Practitioner guidance — workflow and ownership:**
# MAGIC * Decide whether and how the close process records owner, lifecycle status, evidence reference, resolution/action reference, reviewer, and approval details.
# MAGIC * If workflow evidence is persisted, Genie can report it; the adequacy of investigation, review, approval, and resolution remains human-owned.
# MAGIC * Do not prescribe universal workflow values. Use the organization’s lifecycle and evidence model.
# MAGIC
# MAGIC **Practitioner guidance — mid-cycle refresh of the break summary:**
# MAGIC When the break summary is refreshed during an active investigation (e.g., after a source correction or late-arriving feed), preparers lose the population they were working from unless the prior version is retained or the refresh is recorded.
# MAGIC * Record the refresh timestamp and, where snapshot infrastructure exists, the source snapshot/run identifiers used to compute each version of the summary.
# MAGIC * Retain or version the prior break summary so earlier investigation references remain reproducible for the close period.
# MAGIC * Where a refresh timestamp or version column exists, instruct Genie to include it in open-break answers so the preparer can identify which population they are viewing.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 5
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and build the precomputed break summary.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog: <your_catalog>
# MAGIC - Schema: <your_schema>
# MAGIC - Close period: <period identifier>
# MAGIC - Reconciliation scope field(s): <scope fields>
# MAGIC - Reconciliation type: <type>
# MAGIC
# MAGIC PREREQUISITE:
# MAGIC Confirm that matching/variance logic is defined under Principle 4 where this reconciliation compares two or more populations.
# MAGIC
# MAGIC STEP 1 — CHECK:
# MAGIC 1. Identify existing break-summary tables/views for the scope and reconciliation type.
# MAGIC 2. Inspect whether they expose: close period, reconciliation scope/key, variance, break state, supporting-detail identifier/route, current-versus-aged indicator, originating period/age, and prior-period comparison where applicable.
# MAGIC 3. Inspect whether each summary row can be tied to the data status and as-of/snapshot/run evidence of its inputs.
# MAGIC 4. Confirm that a selected summary item can be traced to supporting records using the declared logic.
# MAGIC 5. Identify optional persisted workflow evidence fields if present: owner, lifecycle status, evidence reference, reviewer, approver, approval timestamp.
# MAGIC
# MAGIC STEP 2 — BUILD:
# MAGIC 6. If missing, draft a CREATE VIEW statement for a break summary using the declared matching/variance logic and actual schema names.
# MAGIC 7. Include generic fields for scope, close period, reconciliation key, source amount, target amount, variance, match/break status, age/origin period, diagnostic dimension where available, and source snapshot/run evidence.
# MAGIC 8. Draft an optional companion workflow-evidence specification only if the organization elects to persist workflow information.
# MAGIC 9. Draft a concise Genie instruction: "Use the break summary as the default source for open-break questions. Drill into supporting detail only to investigate a selected item."
# MAGIC
# MAGIC Output a gap assessment using: NO_BREAK_SUMMARY, NO_DRILLDOWN_KEY,
# MAGIC NO_AGE_HISTORY, NO_PRIOR_PERIOD_COMPARISON, or NO_SNAPSHOT_LINEAGE.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 6 — Scope the Genie Space
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 6: Scope the Genie Space
# MAGIC **Category:** Agent design
# MAGIC
# MAGIC **Statement:** *"Scope each Genie space to the smallest stable reconciliation context that shares access rules, data model, policy, vocabulary, and investigation workflow."*
# MAGIC
# MAGIC A narrowly curated scope reduces ambiguity, table-selection errors, and conflicting instructions. In a tax close, the stable context is often one legal entity. In other domains it may be a bank account, portfolio, business unit, claims cohort, product, or another controlled operational segment.
# MAGIC
# MAGIC Group scopes only when they genuinely share their access model, data model, relevant policies/tolerances, vocabulary, and investigation flow. If instructions need repeated conditional branches such as “if scope X, then …,” separate spaces or a more explicit configuration model are usually safer.
# MAGIC
# MAGIC **Pass criteria — queryable structural evidence:**
# MAGIC * The space description identifies the reconciliation scope or an explicitly declared homogeneous scope group, the covered reconciliation types, and relevant contextual attributes
# MAGIC * A queryable or documented scope-configuration artifact identifies the datasets, policies/reference artifacts, and vocabulary applicable to the space
# MAGIC * Included tables and instructions are limited to the declared reconciliation scope; unrelated scopes are identified and excluded
# MAGIC * Instructions direct Genie to use the break summary for open-break questions and to state uncertainty or ask for clarification when scope is ambiguous
# MAGIC * If multiple scopes share a space, a declared comparison matrix records the shared access model, data model, policy/tolerance references, vocabulary, and investigation flow
# MAGIC
# MAGIC **Practitioner guidance — fit of grouping:**
# MAGIC * A close/process owner decides whether grouping is operationally appropriate; a matrix can document similarity but cannot prove it.
# MAGIC * Keep instructions lean. Put changing policy values and detailed mappings in governed reference artifacts rather than embedding values in free-text instructions.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 6
# MAGIC %md
# MAGIC ```text
# MAGIC Define and assess the Genie space scope.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Reconciliation scope type: <entity, account, bank account, portfolio, etc.>
# MAGIC - Scope value(s): <one value or a proposed group>
# MAGIC - Covered reconciliation types: <types>
# MAGIC - Catalog.Schema: <catalog.schema>
# MAGIC
# MAGIC STEP 1 — CHECK GROUPING:
# MAGIC 1. If more than one scope value is proposed, identify whether each shares the same access model, relevant data model, policy/tolerance references, vocabulary, and investigation workflow.
# MAGIC 2. Identify conditional instructions or scope-specific tables that would make the group heterogeneous.
# MAGIC 3. Draft a scope-comparison matrix using only declared, queryable/documented attributes; flag attributes that require practitioner judgment.
# MAGIC
# MAGIC STEP 2 — DISCOVER AND MAP:
# MAGIC 4. List tables/views in the stated catalog/schema and assign reconciliation roles.
# MAGIC 5. Identify tables relevant to the declared scope and flag apparently unrelated scope data.
# MAGIC 6. Identify available break summaries, policy/tolerance references, readiness artifacts, and matching snippets.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 7. Draft a space description naming the reconciliation scope, covered reconciliation types, and relevant context.
# MAGIC 8. Draft lean instructions covering scope boundaries, vocabulary, default break-summary usage, provenance expectations, and safe handling of ambiguity.
# MAGIC 9. Draft a natural-language investigation flow for the declared scope.
# MAGIC
# MAGIC Output the table-role map, scope-comparison matrix where applicable, and proposed space instructions.
# MAGIC Flag HETEROGENEOUS_SCOPE_GROUP or OUT_OF_SCOPE_TABLES; do not claim that grouping is operationally approved.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 7 — Security Model: Viewer Run-As
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 7: Security Model: Viewer Run-As
# MAGIC **Category:** Agent design and access
# MAGIC
# MAGIC **Statement:** *"Enforce reconciliation-scope access in Unity Catalog and run the space under the viewer’s identity; never rely on instructions to enforce segregation."*
# MAGIC
# MAGIC Different preparers, reviewers, and approvers may legitimately have different access. Access restrictions must be enforced through Unity Catalog object permissions, row filters, column masks, and other applicable platform controls. Agent wording is not a security control.
# MAGIC
# MAGIC **Pass criteria — queryable configuration and execution evidence:**
# MAGIC * Reconciliation-relevant tables have inspectable Unity Catalog permissions and, where required, row filters and column masks aligned to the scope model
# MAGIC * A documented access-expectation table exists listing: each role (e.g., Preparer-DE01), the scopes it should be able to query, and the scopes it should be denied
# MAGIC * Where the organization periodically tests these expectations and stores the results, the test-result table records: role tested, scope queried, expected outcome (allow/deny), actual outcome, and test date
# MAGIC
# MAGIC **Practitioner guidance — configuration and access review:**
# MAGIC * Verify the Genie space is configured for viewer run-as in the space settings UI.
# MAGIC
# MAGIC * Security and close-control owners approve the segregation-of-duties design, representative test identities, privileged-access treatment, and periodic access-review cadence.
# MAGIC * Configuration inspection and recorded tests do not prove that every real-world access path is appropriate; investigate test failures and exceptions through the organization’s control process.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 7
# MAGIC %md
# MAGIC ```text
# MAGIC Assess security configuration and available access-test evidence.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Genie space: <space name/identifier>
# MAGIC - Catalog.Schema: <catalog.schema>
# MAGIC - Reconciliation scope type: <scope type>
# MAGIC
# MAGIC STEP 1 — CHECK CONFIGURATION:
# MAGIC 1. List Unity Catalog grants for reconciliation-relevant objects.
# MAGIC 2. Identify row filters and column masks applied to those objects and map them to scope fields.
# MAGIC
# MAGIC STEP 2 — CHECK EVIDENCE:
# MAGIC 3. Identify whether a table documents which roles should
# MAGIC    access which scopes and which should be denied.
# MAGIC 4. If a test-result table exists, summarize the latest
# MAGIC    results: role tested, scope queried, expected outcome
# MAGIC    (allow/deny), actual outcome, and test date.
# MAGIC 5. Flag missing test coverage, stale tests, or mismatches
# MAGIC    between expected and actual outcomes.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 6. Draft a simple access-expectation table listing: role,
# MAGIC    scope, expected outcome (allow/deny).
# MAGIC 7. Draft a companion test-result table: role tested, scope
# MAGIC    queried, expected outcome, actual outcome, test date.
# MAGIC 8. Draft queries to inspect UC grants and applicable
# MAGIC    filters/masks for reconciliation-relevant objects.
# MAGIC
# MAGIC Output configuration observations and persisted-evidence gaps. Do not alter access grants,
# MAGIC filters, masks, or run-as settings; security changes require authorized human review.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 8 — Read-Only Investigation Boundary
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 8: Read-Only Investigation Boundary
# MAGIC **Category:** Agent design and access
# MAGIC
# MAGIC **Statement:** *"Genie investigates and explains reconciliation exceptions; people authorize, record, remediate, and sign off outside the agent."*
# MAGIC
# MAGIC Separate investigation from remediation. Genie may quantify an exception, compare periods, surface supporting evidence, propose a hypothesis, and draft a corrective-action specification for a preparer to consider. It must not post journal entries, amend source records, change workflow status, approve a resolution, or perform sign-off.
# MAGIC
# MAGIC Root-cause classifications and recommendations are hypotheses unless an approved deterministic business rule supports a conclusion. They should be phrased as evidence-backed possibilities and next investigation steps, not as authoritative diagnoses or binding instructions.
# MAGIC
# MAGIC **Pass criteria — queryable configuration evidence:**
# MAGIC * Included data sources and supported query patterns are read-only for the assistant’s intended workflow
# MAGIC * Space instructions explicitly prohibit the agent from presenting itself as an automated reconciliation, remediation, approval, or sign-off capability
# MAGIC * Space instructions require recommendations to be framed as hypotheses or options unless a named deterministic rule supports the conclusion
# MAGIC
# MAGIC **Practitioner guidance — accountable decision-making:**
# MAGIC * The organization defines who may investigate, propose, approve, post, resolve, and sign off.
# MAGIC * A preparer and reviewer determine whether proposed explanations and actions are correct and sufficiently evidenced.
# MAGIC * If write-capable integrations are later introduced, redesign this control boundary, permissions, testing, and approvals before enabling them.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 8
# MAGIC %md
# MAGIC ```text
# MAGIC Assess the read-only investigation boundary.
# MAGIC
# MAGIC STEP 1 — CHECK:
# MAGIC 1. Inspect instructions for explicit read-only language and for wording that distinguishes investigation from remediation and sign-off.
# MAGIC 2. Inspect whether recommendation language requires hypotheses/options and human validation unless a deterministic rule is named.
# MAGIC
# MAGIC STEP 2 — BUILD:
# MAGIC 3. Draft instructions stating:
# MAGIC    - "Use this space for read-only investigation and explanation."
# MAGIC    - "Do not post, amend, approve, resolve, or sign off reconciliation items."
# MAGIC    - "Frame root-cause labels and recommended actions as hypotheses or options unless a named deterministic rule supports them."
# MAGIC    - "State when preparer or reviewer validation is required."
# MAGIC 4. If any write-capable integrations are identified during
# MAGIC    instruction review, list them for authorized human review.
# MAGIC
# MAGIC Output READ_ONLY_CONFIGURED, MISSING_READ_ONLY_INSTRUCTION, or WRITE_ROUTE_DETECTED.
# MAGIC Do not create, modify, or enable integrations.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 9 — Workflow-Oriented Starter Questions
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 9: Workflow-Oriented Starter Questions
# MAGIC **Category:** User experience
# MAGIC
# MAGIC **Statement:** *"Starter questions should give every preparer a safe summary-level entry point and cover the core paths of monthly investigation."*
# MAGIC
# MAGIC A new preparer should be able to start from the break summary, then navigate the principal investigation paths: quantify, decompose, explain or classify, compare with prior periods, identify aged items, and identify the next accountable action where persisted workflow evidence exists. These are paths, not a mandatory linear sequence—experienced users may move directly to trend, aging, a particular counterparty, or a selected exception.
# MAGIC
# MAGIC Use organization-specific terminology, but avoid assuming that every close has a formal root-cause taxonomy or identical workflow columns.
# MAGIC
# MAGIC **Pass criteria — queryable configuration evidence:**
# MAGIC * At least three starter/common questions are configured or available in a documented space artifact
# MAGIC * At least one question starts at a summary level using the break summary for the selected close period
# MAGIC * The collective set covers the applicable investigation paths: quantify, decompose, explain/classify, compare, age, and next action/workflow evidence
# MAGIC * Questions include or prompt for close period and reconciliation scope when those are not fixed by the space context
# MAGIC * Questions do not imply that Genie can approve, remediate, or sign off
# MAGIC
# MAGIC **Practitioner guidance — onboarding and usability:**
# MAGIC * Test starter questions with new and experienced preparers. Whether a user understands where to start is a usability finding, not a machine-verifiable fact.
# MAGIC * Adapt language to the organization’s reconciliation lifecycle, taxonomy, and escalation model.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 9
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and draft starter questions for the monthly investigation workflow.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Reconciliation scope type: <scope type>
# MAGIC - Reconciliation type: <type>
# MAGIC - Close period example: <period>
# MAGIC
# MAGIC STEP 1 — CHECK:
# MAGIC 1. List configured starter/common questions and identify their intended source tables/views.
# MAGIC 2. Identify whether at least one starts from summary-level open breaks/total variance for a close period.
# MAGIC 3. Map the question set to these applicable paths: quantify, decompose, explain/classify, compare prior period, aged/carry-forward, and next action/workflow evidence.
# MAGIC 4. Flag questions that require data fields not present in the break summary or imply approval/remediation authority.
# MAGIC
# MAGIC STEP 2 — BUILD:
# MAGIC 5. Draft questions using actual available scope and diagnostic fields. Include, where applicable:
# MAGIC    - "What are the open breaks and total variance for <scope> in <period>?"
# MAGIC    - "Which reconciliation segments contribute most to the variance?"
# MAGIC    - "What available diagnostic dimensions explain the largest exceptions?"
# MAGIC    - "How does the current period compare with the prior comparable period?"
# MAGIC    - "Which open exceptions are carried forward or aged?"
# MAGIC    - "What recorded owner, status, evidence, or next action is available for the largest exceptions?"
# MAGIC 6. Draft a short onboarding note directing users to begin with the break summary and drill into selected exceptions.
# MAGIC
# MAGIC Output a coverage matrix and flags: NO_SUMMARY_ENTRY_POINT, MISSING_INVESTIGATION_PATH,
# MAGIC UNSUPPORTED_DATA_DEPENDENCY, or CONTROL_BOUNDARY_CONFLICT.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 10 — Traceable Answers and Provenance
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 10: Traceable Answers and Provenance
# MAGIC **Category:** Controls
# MAGIC
# MAGIC **Statement:** *"Answers used in close investigation must be traceable to their source data, close period, data status, snapshot context, and generated query or retained interaction record."*
# MAGIC
# MAGIC An answer is evidence only when a reviewer can identify what was queried, which period and scope were used, the data’s recorded status and as-of/snapshot context, and the calculation or interaction trail. Native platform monitoring, audit logs, conversation retention, or other observability tools may supply parts of that trail, but the methodology does not depend on a single product feature.
# MAGIC
# MAGIC Certification identifies approved sources. It does not replace period readiness or finality; pair certification with Principle 2’s period-specific status and snapshot evidence.
# MAGIC
# MAGIC **Pass criteria — queryable configuration and persisted-evidence criteria:**
# MAGIC * Space instructions require answers that present official close figures to state the source dataset(s), close period, reconciliation scope, recorded data status, and as-of/snapshot/run context where available
# MAGIC * Reconciliation-relevant datasets carry inspectable certification/controlled-source metadata or are represented in an accessible controlled-source registry
# MAGIC * Instructions restrict official close figures to declared controlled/certified sources and require caveats when the data is preliminary, stale, incomplete, or outside scope
# MAGIC * A retained, accessible interaction/query/audit mechanism exists that can associate a sampled answer with generated SQL or query information and source objects, subject to platform capabilities and retention settings
# MAGIC * A queryable or sampleable evidence record can show whether the defined provenance fields were present in retained answers/interactions
# MAGIC
# MAGIC **Practitioner guidance — evidence sufficiency and retention:**
# MAGIC * The close-control owner decides whether the investigation evidence is sufficient for review and sign-off, and which exports or retained records belong in the evidence package.
# MAGIC * Configure retention, privacy, data-access, and audit policies appropriate to the organization and jurisdiction.
# MAGIC * Sampled provenance presence is not proof that every answer is accurate or review-ready; use Principles 11 and 12 for quality assurance.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 10
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and build traceability and provenance controls.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Genie space: <space name/identifier>
# MAGIC - Catalog.Schema: <catalog.schema>
# MAGIC - Close period: <period identifier>
# MAGIC
# MAGIC STEP 1 — CHECK CONFIGURATION:
# MAGIC 1. Inspect available space instructions for requirements to state source dataset, close period, reconciliation scope, data status, as-of/snapshot/run context, caveats, and human-validation boundary.
# MAGIC 2. Identify certification tags, controlled-source registry entries, or equivalent metadata for reconciliation-relevant datasets.
# MAGIC 3. Identify accessible query, conversation, usage, audit, or trace records and the fields they retain.
# MAGIC
# MAGIC STEP 2 — CHECK PERSISTED EVIDENCE:
# MAGIC 4. If retained interactions are accessible, sample recent relevant records and identify whether source, period, scope, data status, snapshot context, and query/SQL reference are available.
# MAGIC 5. Flag unavailable, incomplete, or inaccessible provenance fields without claiming that sign-off evidence is sufficient or insufficient.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 6. Draft concise instructions requiring the defined provenance fields for official close figures.
# MAGIC 7. Draft ALTER TABLE tag statements or a controlled-source registry specification only for datasets identified as reconciliation-relevant.
# MAGIC 8. Draft a generic provenance-sampling query/report specification using fields: interaction_id, timestamp, scope, close_period, source_objects, data_status, snapshot_or_run_id, query_reference, and provenance_complete_flag.
# MAGIC
# MAGIC Output configuration and evidence observations using: MISSING_PROVENANCE_INSTRUCTION,
# MAGIC UNCONTROLLED_SOURCE, NO_RETAINED_QUERY_TRAIL, or INCOMPLETE_RETAINED_PROVENANCE.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 11 — Benchmark and Improve Each Close Cycle
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 11: Benchmark and Improve Each Close Cycle
# MAGIC **Category:** Controls
# MAGIC
# MAGIC **Statement:** *"Operate the agent as a recurring close-cycle improvement loop: benchmark intended behavior, investigate failures, change the underlying artifact, and retest."*
# MAGIC
# MAGIC A close cycle is a natural improvement boundary. Maintain benchmarks that reflect the investigation paths users actually need, execute them before go-live and after material changes, analyze underlying failures, and improve the data, metadata, matching logic, summary, instructions, or knowledge artifact rather than merely polishing a response.
# MAGIC
# MAGIC Benchmarks should cover four dimensions:
# MAGIC
# MAGIC 1. **Calculation correctness** — the result agrees with an independently reproducible trusted calculation for a defined case.
# MAGIC 2. **Provenance** — the answer identifies the required source, scope, period, status, and snapshot context.
# MAGIC 3. **Controlled-source use** — official close figures use only declared controlled/certified sources, or appropriately flag limitations.
# MAGIC 4. **Safe ambiguity handling** — ambiguous, incomplete, preliminary, stale, or out-of-scope requests are clarified, caveated, or declined rather than answered with unsupported certainty.
# MAGIC
# MAGIC **Pass criteria — queryable artifacts and execution evidence:**
# MAGIC * A benchmark suite exists and maps benchmark cases to applicable investigation paths: quantify, decompose, explain/classify, compare, age, and next action/workflow evidence
# MAGIC * Each case identifies one or more acceptance dimensions, expected answer pattern, applicable close period/scope, and trusted expected result or validation method
# MAGIC * The suite collectively covers calculation correctness, provenance, controlled-source use, and safe ambiguity handling
# MAGIC * Where benchmark runs are persisted, records identify suite/version, case ID, tested space/version, execution timestamp, result, and evidence or failure reference
# MAGIC
# MAGIC **Practitioner guidance — cadence and improvement accountability:**
# MAGIC * Define material-change triggers, benchmark cadence, release authority, pass thresholds, and escalation expectations.
# MAGIC * Run the suite before go-live and after material changes; review failures and feedback after each close.
# MAGIC * Track trends only where the organization has a meaningful baseline and retained evidence. A pass-rate trend does not substitute for professional review of high-impact failures.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 11
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and build the recurring benchmark suite.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Genie space: <space name/identifier>
# MAGIC - Close period example: <period>
# MAGIC - Reconciliation scope example: <scope>
# MAGIC
# MAGIC STEP 1 — CHECK:
# MAGIC 1. Identify accessible benchmark questions/cases, expected-results artifacts, and persisted benchmark-run evidence.
# MAGIC 2. Map each case to the applicable investigation path and acceptance dimension(s): calculation correctness, provenance, controlled-source use, safe ambiguity handling.
# MAGIC 3. Flag missing paths/dimensions, cases without an expected result/validation method, and missing run/version evidence where a run log is expected.
# MAGIC
# MAGIC STEP 2 — BUILD:
# MAGIC 4. Draft benchmark cases using real available tables, columns, scope values, and close periods.
# MAGIC 5. For each case, specify: case_id, user question, scope/period context, expected answer pattern, trusted result or validation method, acceptance dimensions, and evidence reference.
# MAGIC 6. Include at least one ambiguity/incomplete-data/out-of-scope case and one preliminary-or-stale-data case.
# MAGIC 7. Draft a generic governed benchmark-run table specification: run_id, suite_version, case_id, space_version, executed_at, result, evidence_reference, failure_category, and remediation_reference.
# MAGIC
# MAGIC Output a coverage matrix and flags: NO_BENCHMARK_SUITE, MISSING_ACCEPTANCE_DIMENSION,
# MAGIC NO_TRUSTED_VALIDATION_METHOD, or NO_PERSISTED_RUN_EVIDENCE.
# MAGIC Do not claim that a benchmark was run unless a retained execution record is available.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Principle 12 — Independent Evaluation and Assurance
# MAGIC %md
# MAGIC ---
# MAGIC ## Principle 12: Independent Evaluation and Assurance
# MAGIC **Category:** Controls
# MAGIC
# MAGIC **Statement:** *"Establish an independent assurance layer that evaluates whether outputs are correct, traceable, and safe; start with deterministic checks and sampled human review."*
# MAGIC
# MAGIC Monitoring tells the team what the assistant did. Assurance evaluates whether defined outputs met their acceptance criteria. It should compare the assistant’s output with trusted references or independently reproducible calculations, retain the result, and distinguish deterministic validation from human judgment.
# MAGIC
# MAGIC Start with deterministic SQL checks that independently reproduce defined variances from controlled source/target datasets and compare them with the break summary. Then add sampled human review for questions involving terminology, interpretation, scope, or contextual judgment. LLM-as-judge may be added later for triage at higher volume, but it is not a prerequisite for a mature close control.
# MAGIC
# MAGIC **Pass criteria — queryable artifacts and execution evidence:**
# MAGIC * Deterministic SQL test queries exist that independently calculate defined reconciliation measures from declared controlled sources and compare them to the break summary or trusted reference
# MAGIC * Each deterministic check states its close period, scope, source snapshot/run context, expected tolerance/reference, and mismatch treatment
# MAGIC * Where execution results are persisted, deterministic-test records identify test/version, timestamp, result, comparison values, source snapshot/run identifiers, and evidence reference
# MAGIC * A trace/evaluation record design exists that can associate question or benchmark case, deterministic result, and human-review result where those artifacts are retained
# MAGIC
# MAGIC **Practitioner guidance — assurance judgment:**
# MAGIC * Domain experts determine sampling methods, reviewer qualifications, acceptance thresholds, and the appropriate response to material failures.
# MAGIC * Human reviewers assess interpretation, ambiguity, and evidence sufficiency; a completed review field does not prove the quality of judgment.
# MAGIC * Add LLM-as-judge only when its intended use, limitations, calibration, oversight, and failure handling are defined. It should support triage, not replace deterministic controls or accountable review.

# COMMAND ----------

# DBTITLE 1,Action Script — Principle 12
# MAGIC %md
# MAGIC ```text
# MAGIC Assess and build the independent evaluation and assurance layer.
# MAGIC
# MAGIC PARAMETERS:
# MAGIC - Catalog.Schema: <catalog.schema>
# MAGIC - Reconciliation type: <type>
# MAGIC - Close period: <period>
# MAGIC - Reconciliation scope: <scope>
# MAGIC
# MAGIC STEP 1 — DISCOVER:
# MAGIC 1. Identify controlled/certified source and target datasets, the break summary, trusted reference metrics, deterministic test SQL, evaluation traces, and persisted result tables.
# MAGIC 2. Identify whether source snapshot/run context can be recorded in test results.
# MAGIC
# MAGIC STEP 2 — CHECK:
# MAGIC 3. Determine whether deterministic SQL independently calculates the defined variance/measure from controlled source data and compares it with the break summary or trusted reference.
# MAGIC 4. Inspect whether each test states scope, period, source snapshot/run context, comparison/tolerance, and mismatch treatment.
# MAGIC 5. Identify persisted execution evidence and whether it includes test version, timestamp, results, comparison values, source context, and evidence reference.
# MAGIC 6. Identify the available structure for recording human-review outcomes without claiming reviews occurred.
# MAGIC
# MAGIC STEP 3 — BUILD:
# MAGIC 7. Draft independent deterministic SQL for the selected reconciliation using actual tables and declared matching/variance logic.
# MAGIC 8. Draft a governed evaluation-result table specification with generic fields: evaluation_id, test_or_case_id, version, scope, close_period, snapshot_or_run_id, deterministic_result, expected_result, comparison_status, reviewer_id, review_outcome, reviewed_at, and evidence_reference.
# MAGIC 9. Draft a human-review sampling-plan template and, only if requested, an optional post-hoc LLM-as-judge triage flow.
# MAGIC
# MAGIC Output: available assurance artifacts and flags: NO_INDEPENDENT_DETERMINISTIC_CHECK,
# MAGIC NO_SNAPSHOT_CONTEXT, NO_PERSISTED_EVALUATION_EVIDENCE, or NO_REVIEW_RECORD_STRUCTURE.
# MAGIC Do not assert that human review occurred or that controls are effective unless retained evidence supports that narrower statement.
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Implementation Sequence and Cadence
# MAGIC %md
# MAGIC ---
# MAGIC ## Implementation Sequence and Close Cadence
# MAGIC
# MAGIC ### Initial implementation sequence
# MAGIC
# MAGIC | Phase | Principles | Dependency rationale |
# MAGIC |---|---|---|
# MAGIC | 1. Data foundation | 1, 2, 3 | Establish investigable grain and linkage, period readiness/snapshot evidence, then the semantic metadata used by the agent and tests |
# MAGIC | 2. Reconciliation model | 4, 5 | Define matching/variance logic before materializing the break summary; Principle 4 is conditional but required for two-sided reconciliations |
# MAGIC | 3. Agent design and access | 6, 7, 8, 9 | Define stable scope, enforce access, establish read-only boundaries, then create questions tested in the final user context |
# MAGIC | 4. Evidence and quality | 10, 11, 12 | Configure answer traceability, define recurring benchmarks, then build independent deterministic and human assurance |
# MAGIC
# MAGIC ### Recurring close-cycle checks
# MAGIC
# MAGIC | Close timing | Principles to revisit | Focus |
# MAGIC |---|---|---|
# MAGIC | Before investigation begins | 2, 5, 7, 10 | Recorded input readiness/finality and snapshot consistency; refreshed break summary; applicable access; provenance/trail availability |
# MAGIC | During close | 8, 9, 10 | Read-only boundary, safe investigation paths, and traceable/caveated responses |
# MAGIC | Before close release or sign-off | 11, 12 | Benchmark/evaluation evidence, deterministic variance checks, and practitioner review of material results |
# MAGIC | After close | 11, 12 | Analyze failures, feedback, evidence gaps, changes, and follow-up tests before the next cycle |
# MAGIC
# MAGIC ### Maturity model
# MAGIC
# MAGIC | Level | Capability state | Minimum capabilities |
# MAGIC |---|---|---|
# MAGIC | **L1 — Investigable** | The organization can isolate and trace exceptions at the appropriate grain | 1 and documented scope basics from 6 |
# MAGIC | **L2 — Operational** | A ready, period-specific, reproducible exception queue exists | 2, 3, 4, 5 |
# MAGIC | **L3 — Controlled** | The agent operates in a defined scope with enforced access, read-only boundaries, and traceable evidence | 6, 7, 8, 9, 10 |
# MAGIC | **L4 — Assured and improving** | Independent deterministic checks, benchmarks, retained evidence, and accountable improvement operate through recurring cycles | 11, 12 |
# MAGIC
# MAGIC LLM-as-judge is optional at every maturity level. An L4 implementation can rely on deterministic validation and sampled accountable human review.