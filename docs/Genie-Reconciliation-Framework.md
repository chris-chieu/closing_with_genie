# Genie Reconciliation Framework
## Reusable principles and verification prompts for Databricks Genie

> **Purpose:** A practitioner framework for deploying Databricks Genie as a read-only monthly reconciliation investigation assistant.

This document is designed for GitHub. It describes a domain-agnostic methodology for deploying a reconciliation assistant in tax, treasury, insurance claims, intercompany eliminations, bank-to-book, subledger-to-general-ledger, and similar monthly close processes.

The framework is not a source-data migration method. It defines the **metadata, reconciliation context, and control layer around existing close data** so that Genie can safely help preparers investigate exceptions, surface evidence, compare periods, and identify the next question to ask.

Each principle includes a natural-language **Genie Code action script**. The script is intended to **CHECK** accessible, governed, queryable artifacts and **BUILD** drafts of missing artifacts, such as views, metadata, instructions, join snippets, readiness records, and deterministic test queries. Review all generated artifacts before applying them.

## Core idea

Your source data stays where it is. The context is what you add.

A reconciliation agent cannot safely infer:

- Which dataset is authoritative for open breaks
- How source and target records should match
- What constitutes an exception or variance
- Which close-period snapshot is valid
- Whether a figure is preliminary, final, corrected, or later restated

The methodology creates a governed reconciliation layer around the data the close team already uses: curated metadata, declared joins, matching rules, precomputed break summaries, period and snapshot context, provenance rules, benchmarks, and assurance evidence.

## Evidence and judgment

A central design rule is to separate **evidence** from **judgment**.

Genie Code can check whether the reconciliation context is in place: curated metadata that explains the data, a break summary, documented matching logic, controlled-source indicators, a close-period snapshot, and retained test or execution evidence.

Genie helps the close team investigate exceptions, surface relevant evidence, compare periods, and identify the next question to ask. The close team applies judgment: deciding whether a restatement is material, a break is resolved, evidence is sufficient, or sign-off is justified.

### What a pass criterion means

A pass criterion is an assertion Genie Code can verify from accessible, governed, queryable artifacts: schema and catalog metadata, table/view definitions, instruction text, persisted run records, test results, or other control evidence.

A pass criterion does **not** prove business truth, control effectiveness, timely human review, approval quality, or the adequacy of professional judgment.

| Evidence level | Example | Genie Code can assess? |
|---|---|---|
| Artifact existence | A break-summary view, certification tag, join snippet, or benchmark exists | Usually yes |
| Structural conformance | Required fields are present; a join includes declared scope and period; an instruction mandates provenance | Usually yes |
| Persisted execution evidence | A refresh, access test, benchmark, or review record has a timestamp and result in a governed table | Yes, if accessible |
| Control effectiveness | A reviewer concluded analysis was sufficient; a policy was applied correctly; a team acted on a finding | No — practitioner-owned |

## How to use this methodology

1. Define the reconciliation scope and the applicable close period.
2. Run the principles in the implementation sequence shown below.
3. Treat a failed structural criterion as a design or data-context gap.
4. Treat missing process evidence or judgment as a practitioner action, not something the assistant can declare complete.
5. Review and apply any generated SQL, metadata, instructions, or snippets; then rerun the relevant check.
6. Revisit recurring controls each close cycle and revisit setup controls after material changes to data, scope, policy, access, logic, or the Genie space.

The framework uses **reconciliation scope** as its neutral design unit. A scope may be a legal entity, account, bank account, currency, portfolio, business unit, product, claims cohort, counterparty, or another stable segment. Legal entity is a common default in tax and statutory close; it is not a universal design rule.

## Principles at a glance

| # | Principle | Category | Phase |
|---|---|---|---|
| 1 | Reconciliation Grain and Linkage | Data foundation | 1. Data foundation |
| 2 | Close-Period Readiness, Finality, and Reproducibility | Data foundation | 1. Data foundation |
| 3 | Mid-Cycle Change and Restatement Alerting | Data foundation / recurring close control | 1. Data foundation |
| 4 | Metadata Curation | Data foundation | 1. Data foundation |
| 5 | Explicit Matching and Variance Logic | Reconciliation model | 2. Reconciliation model |
| 6 | Precompute the Break Summary | Reconciliation model | 2. Reconciliation model |
| 7 | Scope the Genie Space | Agent design | 3. Agent design and access |
| 8 | Security Model: Viewer Run-As | Agent design and access | 3. Agent design and access |
| 9 | Read-Only Investigation Boundary | Agent design and access | 3. Agent design and access |
| 10 | Workflow-Oriented Starter Questions | User experience | 3. Agent design and access |
| 11 | Traceable Answers and Provenance | Controls | 4. Evidence and quality |
| 12 | Benchmark and Improve Each Close Cycle | Controls | 4. Evidence and quality |
| 13 | Independent Evaluation and Assurance | Controls | 4. Evidence and quality |

---

## Principle 1: Reconciliation Grain and Linkage

**Category:** Data foundation

**Statement:** *If the available data cannot isolate and explain a reconciliation break, Genie cannot do so either.*

Reconciliation begins with a model that supports investigation at the appropriate level of detail. Relevant source, target, and reference datasets need a documented grain, a way to associate contributing records across datasets, and a field for scoping to the close period. A summary-only table may support reporting, but not dependable drill-down unless a declared detail path exists.

Do not require Genie to infer business keys from similarly named columns. Declare the reconciliation keys, expected linkage pattern, and drill-down route from an exception summary to supporting records.

### Pass criteria

- Reconciliation-relevant datasets are identified and each has a documented grain
- Each relevant dataset contains a declared close-period field or is linked through a documented period-scoping rule
- Declared reconciliation keys and relationship/join artifacts exist for the relevant source, target, and supporting datasets
- Sample queries can trace a selected break or variance from the exception level to contributing supporting records
- Profiling queries exist or can be generated for null keys, duplicate keys, and unmatched-key rates by close period

### Practitioner guidance

- A domain owner determines whether the documented grain and linkage genuinely support the reconciliation objective; field presence alone does not prove semantic adequacy.
- The close team decides which aggregation level is appropriate and whether exception drill-down is sufficiently complete for review.
- Resolve structural gaps before treating the Genie space as a close investigation capability.

### Genie Code action script

```text
Assess reconciliation grain and linkage.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>
- Close period: <YYYY-MM or other period identifier>
- Reconciliation scope field(s): <for example entity_code, bank_account, portfolio>

STEP 1 — DISCOVER:
1. List tables and views in the catalog/schema using information_schema.
2. Identify candidate reconciliation datasets and assign a role: source, target, supporting detail,
   reference, readiness/control, or break summary.
3. For each candidate, list documented table grain, period field, scope field(s), primary/business key
   candidates, and descriptions.

STEP 2 — CHECK:
4. Identify datasets with no documented grain, no usable period-scoping field, or no declared linkage
   to another relevant dataset.
5. For each declared linkage, profile the selected close period for null keys, duplicate keys,
   unmatched keys, and cardinality risks.
6. Identify summary-only datasets lacking a documented supporting-detail drill-down route.
7. Draft a sample trace query that starts from one selected break/variance and returns its
   contributing records.

STEP 3 — BUILD:
8. Draft table/column comments for missing grain, period, scope, and key documentation.
9. Draft reusable profiling SQL for key completeness and match-rate checks by close period.
10. Draft a reconciliation-key and drill-down mapping artifact using actual table and column names.

Output a table-role and linkage inventory. Flag MISSING_GRAIN, MISSING_PERIOD_SCOPE,
UNDECLARED_LINKAGE, KEY_QUALITY_RISK, or NO_DRILLDOWN_PATH. Do not claim that semantic
adequacy has been proven.
```

---

## Principle 2: Close-Period Readiness, Finality, and Reproducibility

**Category:** Data foundation

**Statement:** *An agent may investigate a close period only when its inputs are identifiable, status-labelled, and reproducible for that period.*

A generally trusted table is not automatically a valid source for a particular close. The reconciliation needs to identify which source versions were used, whether data is preliminary or approved/final, when it was available, and whether the break summary and supporting detail use consistent inputs. Otherwise, the same question may produce different results during review, or a preparer may investigate a mixed-as-of population.

This principle separates queryable readiness evidence from the business decision that a source is complete or final. Genie Code can inspect fields, control records, timestamps, run identifiers, and consistency. It cannot determine whether an upstream completion declaration is substantively correct.

### Pass criteria

- Each relevant source and summary dataset exposes, or is linked to, a close-period identifier, data-status value, and as-of timestamp, snapshot identifier, or pipeline-run identifier
- A queryable readiness/control record identifies the required upstream inputs for a reconciliation scope and close period
- The break summary records or can be linked to the source snapshot/run identifiers used to compute it
- A query can identify missing, stale, non-final, or mixed-as-of required inputs for a selected scope and close period
- Re-running a defined deterministic reconciliation query against the recorded snapshot/run identifiers is technically possible

### Practitioner guidance

- The close team defines the cutoff calendar, finality definitions, late-adjustment policy, restatement handling, and authority to declare data ready.
- A designated owner confirms the operational completeness of upstream feeds and decides when a preliminary result may be used.
- Preserve the approved close snapshot and supporting evidence according to organizational retention and audit policy.

### Genie Code action script

```text
Assess close-period readiness, finality, and reproducibility.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>
- Close period: <YYYY-MM or other period identifier>
- Reconciliation scope: <selected scope value>
- Expected input domains: <source, target, reference, etc.>

STEP 1 — DISCOVER:
1. Identify readiness/control tables, snapshot tables, pipeline-run logs, and relevant metadata fields.
2. For each reconciliation-relevant dataset, identify close-period, data-status, as-of timestamp,
   snapshot ID, version, or run-ID fields.
3. Identify whether the break summary records the source snapshot/run IDs used in its calculation.

STEP 2 — CHECK:
4. For the selected scope and close period, list every required input domain and its latest recorded
   status, as-of timestamp, and snapshot/run ID.
5. Flag required inputs that are absent, empty, stale, preliminary when a final status is expected,
   or inconsistent in as-of/snapshot identifiers.
6. Check whether the break summary can be tied to a consistent source snapshot/run set.
7. Draft a reproducibility query that filters to the recorded close-period and snapshot/run identifiers.

STEP 3 — BUILD:
8. If no readiness/control artifact exists, draft a schema for an organization-governed readiness record.
   Use generic fields: reconciliation_scope, close_period, input_domain, data_status,
   as_of_timestamp, snapshot_or_run_id, recorded_at, and evidence_reference.
9. Draft a view or query that returns a readiness matrix by scope and close period.
10. Draft Genie instructions requiring official close responses to state close period, data status,
    and as-of/snapshot reference.

Output a readiness matrix and flags: MISSING_STATUS, MISSING_SNAPSHOT_LINK, STALE_INPUT,
NONFINAL_INPUT, or MIXED_AS_OF. Do not declare an input complete or final; report recorded evidence.
```

---

## Principle 3: Mid-Cycle Change and Restatement Alerting

**Category:** Data foundation / recurring close control

**Statement:** *When a reconciliation input changes after investigation begins, make the change, affected population, and resulting evidence boundary explicit; never allow Genie to silently mix analysis across input versions.*

Principle 2 establishes the readiness baseline at the beginning of a close investigation. It does not by itself define how the agent and close team should respond if an upstream table is refreshed, re-run, corrected, restated, or recalculated while an investigation is underway. A legitimate change can still invalidate comparisons with earlier analysis, evidence, or break-summary results.

The agent must not present a newer result as directly comparable with a prior answer unless both use the same declared close period, reconciliation scope, logic version, and source snapshot/run context. When it detects a relevant change, it should identify the version boundary, state that earlier findings may need revalidation, and direct the preparer to the updated break summary and evidence.

A controlled change artifact may be implemented through pipeline-run records, Delta Change Data Feed, governed data-quality/event tables, change tickets, or another controlled mechanism. The framework does not prescribe a technology or materiality threshold.

### Pass criteria

- Relevant source and break-summary datasets expose, or can be linked to, snapshot/run identifiers and a refresh or effective timestamp
- A queryable change/restatement artifact records post-baseline changes to relevant inputs, including reconciliation scope, close period, affected object, change timestamp, prior snapshot/run identifier, replacement snapshot/run identifier, change type, and evidence/reference
- A query can identify whether the currently available source snapshot/run differs from the snapshot/run recorded for the break summary or prior persisted investigation/evaluation evidence
- A query can identify the available affected scope-period population using keys, record counts, amounts, or break-summary differences
- Space instructions require Genie to disclose a detected version mismatch or post-baseline change before presenting a figure, comparison, or conclusion as an official close result
- Where an investigation/evidence register is persisted, it can record that prior work was superseded, requires revalidation, or was re-performed against a replacement snapshot/run

### Practitioner guidance

- The close-control owner defines what counts as a restatement or material data change, the investigation-start baseline, and thresholds for notification, escalation, or re-performance.
- Data owners determine the substantive correctness of the change and approve revised data status.
- Preparers and reviewers decide whether prior analysis, approval, benchmark evidence, or sign-off support must be repeated.
- The organization defines communication, ticketing, evidence, retention, and distinctions between routine refreshes, late-arriving data, corrected data, revised matching logic, mapping changes, and approved restatements.

### Genie Code action script

```text
Assess and build mid-cycle change and restatement alerting.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>
- Reconciliation scope type: <entity, account, bank account, portfolio, etc.>
- Reconciliation scope: <selected scope value>
- Close period: <period identifier>
- Investigation-start/readiness baseline: <timestamp, snapshot ID, or pipeline run ID>

STEP 1 — DISCOVER:
1. Identify source datasets, the break summary, readiness/control records, pipeline-run logs,
   snapshot/version fields, change logs, change-data-feed artifacts where available, and persisted
   investigation/evaluation evidence.
2. For each relevant dataset, identify refresh/effective timestamp, source snapshot ID, pipeline run ID,
   data status, and logic/version fields.
3. Identify whether a governed change/restatement artifact records post-baseline changes.

STEP 2 — CHECK:
4. Determine the snapshot/run context at the readiness baseline and the currently available source
   and break-summary context for the selected scope and period.
5. Identify datasets whose current context differs from the recorded baseline or break-summary context.
6. Identify recorded post-baseline changes, including type, time, affected object, prior/replacement
   version, and available evidence reference.
7. Where possible, quantify affected population by comparing counts, amounts, and/or break-summary
   results between prior and replacement versions.
8. Identify persisted investigation, benchmark, or evaluation records using a superseded context.
9. Inspect instructions for a requirement to disclose version mismatches and direct revalidation to
   the practitioner.

STEP 3 — BUILD:
10. If no governed change artifact exists, draft a generic table specification with fields:
    change_id, reconciliation_scope_type, reconciliation_scope, close_period, affected_object,
    change_type, detected_at, prior_snapshot_or_run_id, replacement_snapshot_or_run_id,
    prior_logic_version, replacement_logic_version, data_status, impact_reference,
    change_reason_reference, recorded_by, and evidence_reference.
11. Draft a baseline-versus-current view that flags VERSION_MISMATCH or POST_BASELINE_CHANGE.
12. Draft a version-to-version impact query using available keys, counts, amounts, and break status.
13. Draft instructions requiring explicit restatement/version-mismatch disclosure.
14. Draft an optional investigation-evidence-register extension using fields such as investigation_id,
    snapshot_or_run_id, superseded_by_change_id, revalidation_status, revalidated_at,
    and evidence_reference.

Output: a baseline-versus-current version matrix, recorded change log, available impact comparison,
affected evidence records, and flags: NO_CHANGE_ARTIFACT, NO_BASELINE_CONTEXT, VERSION_MISMATCH,
POST_BASELINE_CHANGE, NO_IMPACT_COMPARISON, or MISSING_AGENT_DISCLOSURE_INSTRUCTION.

Do not decide whether a change is material, whether investigation must be repeated, or whether sign-off
remains valid. Report available evidence and route those decisions to the accountable close team.
```

---

## Principle 4: Metadata Curation

**Category:** Data foundation

**Statement:** *Genie needs curated business context for the datasets and fields it is expected to use in reconciliation.*

Focus curation on reconciliation-relevant datasets, not every object in the schema. Table descriptions should identify business content, documented grain, originating system/process, and expected role. Column descriptions should explain business meaning. For coded fields, document valid values and their meaning. This minimizes unsupported inference from names alone.

### Pass criteria

- Reconciliation-relevant datasets are identified as source, target, supporting detail, break summary, reference, readiness/control, or another declared role
- Each relevant dataset has a non-empty description documenting business content, data origin, and grain
- Required reconciliation columns—including period, scope, keys, measures, status, data status, as-of/snapshot/run ID, and diagnostic fields—have non-empty descriptions
- Coded or enumerated fields used in reconciliation have documented values/meanings in metadata or an accessible reference artifact

### Practitioner guidance

- A domain owner validates that descriptions accurately reflect the business definition; a non-empty comment is not proof of correctness.
- Maintain ownership for terms whose meaning varies by scope, such as balance, exposure, settled, approved, final, exception, or variance.

### Genie Code action script

```text
Audit and improve metadata for reconciliation-relevant datasets.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>

STEP 1 — DISCOVER:
1. List tables and views and inspect descriptions, columns, and column comments.
2. Identify reconciliation-relevant datasets and assign their roles.

STEP 2 — CHECK:
3. List relevant datasets without a usable table description.
4. List required reconciliation fields without descriptions: scope, period, business/reconciliation keys,
   amounts/measures, status, data status, as-of/snapshot/run ID, and diagnostic fields where present.
5. Identify coded fields used in reconciliation and compare sampled distinct values with available
   descriptions or reference data.

STEP 3 — BUILD:
6. Draft table comments that identify business content, data origin, documented grain, and role.
7. Draft ALTER TABLE ... ALTER COLUMN ... SET COMMENT statements for missing or weak required-field comments.
8. Draft a compact reference-table specification for undocumented code values if metadata comments are insufficient.

Output a prioritized report: object_name | field_name | role | issue_type |
current_documentation | proposed_documentation. Mark semantic validation as practitioner-owned.
```

---

## Principle 5: Explicit Matching and Variance Logic

**Category:** Reconciliation model

**Statement:** *Where reconciliation compares two or more populations, maintain one authoritative definition of matching, variance, timing, and unmatched-item treatment.*

Intercompany reconciliation is one instance of a wider pattern: legal-entity-to-legal-entity, bank-to-book, subledger-to-GL, custodian-to-book, claims-to-reserve, or system-to-system reconciliation. The same business event can have different identifiers, dates, signs, currencies, formats, or timing on each side. The assistant must not infer the matching rule.

Declare participating datasets, reconciliation scope, period-scoping rule, join keys, cardinality expectation, sign/currency logic, tolerance policy reference, timing-difference treatment, and definitions of matched/unmatched. For complex or fuzzy matching, define deterministic logic and exception cases rather than describing them only in prose.

### Pass criteria

- An accessible matching/variance artifact identifies participating datasets, reconciliation scope fields, close-period rule, and declared business or composite join keys
- At least one executable SQL example implements the matching/variance pattern using actual tables and columns
- The artifact defines matched, unmatched, partial-match, timing-difference, and duplicate-match treatment where applicable
- Matching logic references a queryable tolerance/policy artifact when tolerances apply, rather than relying only on hard-coded instruction text
- Profiling or test queries calculate match rates, unmatched counts/amounts, and duplicate/many-to-many risks by close period and scope

### Practitioner guidance

- Domain owners approve the economic meaning of a match, tolerance policy, timing window, sign convention, FX treatment, and exception treatment.
- Where intercompany applies, both counterparties align on authoritative matching logic and escalation.
- A table or snippet can document a rule; it cannot prove the rule is suitable for the business purpose.

### Genie Code action script

```text
Assess and build explicit matching and variance logic.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>
- Reconciliation scope: <scope type and selected value>
- Close period: <period identifier>
- Reconciliation type: <for example bank-to-book, intercompany, subledger-to-GL>

STEP 1 — DISCOVER:
1. Identify participating source/target datasets and existing join snippets, SQL examples,
   tolerance tables, and matching documentation.
2. Identify scope fields, period fields, candidate business keys, amount/currency fields, status fields,
   and counterparty fields where relevant.

STEP 2 — CHECK:
3. Does an accessible artifact explicitly define participating datasets, scope filter, period rule,
   join keys, match definition, unmatched treatment, and tolerance reference where applicable?
4. Does an executable SQL example apply those rules with actual tables and columns?
5. Profile selected period for null join keys, duplicate keys, one-to-many/many-to-many matches,
   unmatched items, and amount variance.
6. For intercompany, verify both reporting and counterparty scope are explicit and close period is applied consistently.

STEP 3 — BUILD:
7. Draft a reusable matching SQL snippet, scoped to selected period and reconciliation scope.
8. Draft a variance/unmatched SQL query that records a clear match status and reason.
9. Draft profiling SQL for match rate, duplicate-match risk, and unmatched variance.
10. Draft generic effective-dated tolerance-reference-table fields if policy values are embedded in instructions.

Output an authoritative logic inventory and flags: MISSING_MATCH_RULE, NO_PERIOD_SCOPE,
UNDECLARED_CARDINALITY, MISSING_TOLERANCE_REFERENCE, DUPLICATE_MATCH_RISK, or UNMATCHED_POPULATION.
```

---

## Principle 6: Precompute the Break Summary

**Category:** Reconciliation model

**Statement:** *Precompute a period-specific break summary so preparers begin with an authoritative investigation queue, not ad hoc reconstruction from raw data.*

The break summary is the operational center of the close workflow. It makes the current exception population visible and supports common questions without repeatedly rebuilding reconciliation from raw sources. For each organization-defined reconciliation key and close period, it should expose variance, break state, diagnostic/classification information where available, aging/carry-forward status, and a route to supporting detail.

Define matching and variance logic first. For a two-sided reconciliation—including intercompany—Principle 5 is a prerequisite to finalizing the break-summary definition.

### Pass criteria

- A table or view exists that materializes or reliably exposes a break summary by declared reconciliation scope/key and close period
- The summary contains current-period variance/break state and a declared drill-down identifier or route to supporting detail
- The summary distinguishes current-period exceptions from carry-forward/aged items and exposes originating period, age, or equivalent history where applicable
- The summary includes or can be joined to a comparable prior-period measure when prior-period comparison is in scope
- The summary carries or links to data-status and as-of/snapshot/run evidence required by Principle 2
- Agent instructions designate the summary as the default source for open-break questions, and benchmark cases test that convention

### Practitioner guidance

- Decide whether and how the close process records owner, lifecycle status, evidence reference, resolution/action reference, reviewer, and approval details.
- If workflow evidence is persisted, Genie can report it; the adequacy of investigation, review, approval, and resolution remains human-owned.
- Do not prescribe universal workflow values. Use the organization’s lifecycle and evidence model.

### Genie Code action script

```text
Assess and build the precomputed break summary.

PARAMETERS:
- Catalog: <your_catalog>
- Schema: <your_schema>
- Close period: <period identifier>
- Reconciliation scope field(s): <scope fields>
- Reconciliation type: <type>

PREREQUISITE:
Confirm that matching/variance logic is defined under Principle 5 where this reconciliation compares
multiple populations.

STEP 1 — CHECK:
1. Identify existing break-summary tables/views for scope and reconciliation type.
2. Inspect whether they expose close period, reconciliation scope/key, variance, break state,
   supporting-detail route, current-versus-aged indicator, originating period/age, and prior-period comparison.
3. Inspect whether each summary row can be tied to data status and as-of/snapshot/run evidence of its inputs.
4. Confirm that a selected summary item can be traced to supporting records using declared logic.
5. Identify optional persisted workflow evidence fields if present: owner, lifecycle status, evidence reference,
   reviewer, approver, approval timestamp.

STEP 2 — BUILD:
6. If missing, draft a CREATE VIEW statement using declared matching/variance logic and actual schema names.
7. Include generic fields for scope, close period, reconciliation key, source amount, target amount, variance,
   match/break status, age/origin period, diagnostic dimension where available, and source snapshot/run evidence.
8. Draft an optional companion workflow-evidence specification only if the organization elects to persist workflow information.
9. Draft a concise instruction: "Use the break summary as the default source for open-break questions.
   Drill into supporting detail only to investigate a selected item."

Output a gap assessment: NO_BREAK_SUMMARY, NO_DRILLDOWN_KEY, NO_AGE_HISTORY,
NO_PRIOR_PERIOD_COMPARISON, or NO_SNAPSHOT_LINEAGE.
```

---

## Principle 7: Scope the Genie Space

**Category:** Agent design

**Statement:** *Scope each Genie space to the smallest stable reconciliation context that shares access rules, data model, policy, vocabulary, and investigation workflow.*

A narrowly curated scope reduces ambiguity, table-selection errors, and conflicting instructions. In a tax close, the stable context is often one legal entity. In other domains it may be a bank account, portfolio, business unit, claims cohort, product, or another controlled operational segment.

Group scopes only when they genuinely share access model, data model, relevant policies/tolerances, vocabulary, and investigation flow. If instructions need repeated conditional branches such as “if scope X, then …,” separate spaces or an explicit configuration model are usually safer.

### Pass criteria

- The space description identifies reconciliation scope or an explicitly declared homogeneous scope group, covered reconciliation types, and relevant contextual attributes
- A queryable or documented scope-configuration artifact identifies datasets, policies/reference artifacts, and vocabulary applicable to the space
- Included tables and instructions are limited to declared scope; unrelated scopes are identified and excluded
- Instructions direct Genie to use the break summary for open-break questions and to state uncertainty or ask for clarification when scope is ambiguous
- If multiple scopes share a space, a declared comparison matrix records shared access model, data model, policy/tolerance references, vocabulary, and investigation flow

### Practitioner guidance

- A close/process owner decides whether grouping is operationally appropriate; a comparison matrix can document similarity but cannot prove it.
- Keep instructions lean. Put changing policy values and detailed mappings in governed reference artifacts rather than embedding values in free-text instructions.

### Genie Code action script

```text
Define and assess the Genie space scope.

PARAMETERS:
- Reconciliation scope type: <entity, account, bank account, portfolio, etc.>
- Scope value(s): <one value or a proposed group>
- Covered reconciliation types: <types>
- Catalog.Schema: <catalog.schema>

STEP 1 — CHECK GROUPING:
1. If more than one scope value is proposed, identify whether each shares the same access model,
   relevant data model, policy/tolerance references, vocabulary, and investigation workflow.
2. Identify conditional instructions or scope-specific tables that make the group heterogeneous.
3. Draft a scope-comparison matrix using only declared, queryable/documented attributes; flag attributes
   requiring practitioner judgment.

STEP 2 — DISCOVER AND MAP:
4. List tables/views in stated catalog/schema and assign reconciliation roles.
5. Identify tables relevant to declared scope and flag apparently unrelated scope data.
6. Identify break summaries, policy/tolerance references, readiness artifacts, and matching snippets.

STEP 3 — BUILD:
7. Draft a space description naming reconciliation scope, covered types, and relevant context.
8. Draft lean instructions covering scope boundaries, vocabulary, default break-summary usage,
   provenance expectations, and safe handling of ambiguity.
9. Draft a natural-language investigation flow for the declared scope.

Output the table-role map, scope-comparison matrix where applicable, and proposed instructions.
Flag HETEROGENEOUS_SCOPE_GROUP or OUT_OF_SCOPE_TABLES; do not claim grouping is operationally approved.
```

---

## Principle 8: Security Model: Viewer Run-As

**Category:** Agent design and access

**Statement:** *Enforce reconciliation-scope access in Unity Catalog and run the space under the viewer’s identity; never rely on instructions to enforce segregation.*

Different preparers, reviewers, and approvers may legitimately have different access. Restrictions must be enforced through Unity Catalog object permissions, row filters, column masks, and other applicable platform controls. Agent wording is not a security control.

### Pass criteria

- The Genie space is configured for viewer run-as, where supported and appropriate for intended use
- Reconciliation-relevant tables have inspectable Unity Catalog permissions and, where required, row filters and column masks aligned to the scope model
- A representative-identity access-test matrix exists in a queryable or retained evidence artifact, identifying expected allowed and denied scope access
- Where execution results are persisted, the latest available access-test evidence records identity/role, target object or scope, expected result, actual result, timestamp, and tester/run reference

### Practitioner guidance

- Security and close-control owners approve segregation-of-duties design, representative test identities, privileged-access treatment, and periodic access-review cadence.
- Configuration inspection and recorded tests do not prove every real-world access path is appropriate; investigate failures and exceptions through the organization’s control process.

### Genie Code action script

```text
Assess security configuration and available access-test evidence.

PARAMETERS:
- Genie space: <space name/identifier>
- Catalog.Schema: <catalog.schema>
- Reconciliation scope type: <scope type>

STEP 1 — CHECK CONFIGURATION:
1. Identify space run-as configuration where accessible.
2. List Unity Catalog grants for reconciliation-relevant objects.
3. Identify row filters and column masks applied to objects and map them to scope fields.

STEP 2 — CHECK EVIDENCE:
4. Identify whether a representative-identity access-test matrix or persisted test-result table exists.
5. If accessible, summarize latest results by identity/role, scope, expected access, actual result, and timestamp.
6. Flag missing coverage, stale recorded tests, or recorded denied/allowed mismatches.

STEP 3 — BUILD:
7. Draft a generic access-test matrix specification using fields: test_id, test_identity_or_role,
   target_object_or_scope, expected_result, actual_result, executed_at, evidence_reference, and status.
8. Draft queries to inspect grants and applicable filters/masks.

Output configuration observations and persisted-evidence gaps. Do not alter access grants, filters,
masks, or run-as settings; security changes require authorized human review.
```

---

## Principle 9: Read-Only Investigation Boundary

**Category:** Agent design and access

**Statement:** *Genie investigates and explains reconciliation exceptions; people authorize, record, remediate, and sign off outside the agent.*

Separate investigation from remediation. Genie may quantify an exception, compare periods, surface evidence, propose a hypothesis, and draft a corrective-action specification for a preparer to consider. It must not post journal entries, amend source records, change workflow status, approve a resolution, or perform sign-off.

Root-cause classifications and recommendations are hypotheses unless an approved deterministic business rule supports a conclusion. They should be phrased as evidence-backed possibilities and next investigation steps, not authoritative diagnoses or binding instructions.

### Pass criteria

- Included data sources and supported query patterns are read-only for the assistant’s intended workflow
- Space instructions explicitly prohibit the agent from presenting itself as an automated reconciliation, remediation, approval, or sign-off capability
- Space instructions require recommendations to be framed as hypotheses or options unless a named deterministic rule supports the conclusion
- No accessible action configuration grants the space a write/remediation route for the reconciliation process, where such configurations can be inspected

### Practitioner guidance

- The organization defines who may investigate, propose, approve, post, resolve, and sign off.
- A preparer and reviewer determine whether proposed explanations and actions are correct and sufficiently evidenced.
- If write-capable integrations are introduced, redesign the boundary, permissions, testing, and approvals before enabling them.

### Genie Code action script

```text
Assess the read-only investigation boundary.

STEP 1 — CHECK:
1. List data sources and accessible operations configured for this space, where available.
2. Identify any write-capable action, remediation, workflow-update, posting, or approval integration.
3. Inspect instructions for explicit read-only language and wording that distinguishes investigation from
   remediation and sign-off.
4. Inspect whether recommendation language requires hypotheses/options and human validation unless a
   deterministic rule is named.

STEP 2 — BUILD:
5. Draft instructions stating:
   - "Use this space for read-only investigation and explanation."
   - "Do not post, amend, approve, resolve, or sign off reconciliation items."
   - "Frame root-cause labels and recommended actions as hypotheses or options unless a named
      deterministic rule supports them."
   - "State when preparer or reviewer validation is required."
6. Draft a list of detected write/action integrations for authorized human review.

Output READ_ONLY_CONFIGURED, MISSING_READ_ONLY_INSTRUCTION, or WRITE_ROUTE_DETECTED.
Do not create, modify, or enable integrations.
```

---

## Principle 10: Workflow-Oriented Starter Questions

**Category:** User experience

**Statement:** *Starter questions should give every preparer a safe summary-level entry point and cover the core paths of monthly investigation.*

A new preparer should be able to start from the break summary, then navigate principal investigation paths: quantify, decompose, explain or classify, compare with prior periods, identify aged items, and identify the next accountable action where persisted workflow evidence exists. These are paths, not a mandatory linear sequence.

Use organization-specific terminology, but avoid assuming every close has a formal root-cause taxonomy or identical workflow columns.

### Pass criteria

- At least three starter/common questions are configured or available in a documented space artifact
- At least one question starts at summary level using the break summary for the selected close period
- The collective set covers applicable paths: quantify, decompose, explain/classify, compare, age, and next action/workflow evidence
- Questions include or prompt for close period and reconciliation scope when those are not fixed by space context
- Questions do not imply Genie can approve, remediate, or sign off

### Practitioner guidance

- Test questions with new and experienced preparers. Whether a user understands where to start is a usability finding, not a machine-verifiable fact.
- Adapt language to the organization’s reconciliation lifecycle, taxonomy, and escalation model.

### Genie Code action script

```text
Assess and draft starter questions for the monthly investigation workflow.

PARAMETERS:
- Reconciliation scope type: <scope type>
- Reconciliation type: <type>
- Close period example: <period>

STEP 1 — CHECK:
1. List configured starter/common questions and identify intended source tables/views.
2. Identify whether at least one starts from summary-level open breaks/total variance for a close period.
3. Map the question set to applicable paths: quantify, decompose, explain/classify, compare prior period,
   aged/carry-forward, and next action/workflow evidence.
4. Flag questions requiring fields not present in the break summary or implying approval/remediation authority.

STEP 2 — BUILD:
5. Draft questions using actual available scope and diagnostic fields. Include, where applicable:
   - "What are the open breaks and total variance for <scope> in <period>?"
   - "Which reconciliation segments contribute most to the variance?"
   - "What available diagnostic dimensions explain the largest exceptions?"
   - "How does the current period compare with the prior comparable period?"
   - "Which open exceptions are carried forward or aged?"
   - "What recorded owner, status, evidence, or next action is available for the largest exceptions?"
6. Draft a short onboarding note directing users to begin with the break summary and drill into selected exceptions.

Output a coverage matrix and flags: NO_SUMMARY_ENTRY_POINT, MISSING_INVESTIGATION_PATH,
UNSUPPORTED_DATA_DEPENDENCY, or CONTROL_BOUNDARY_CONFLICT.
```

---

## Principle 11: Traceable Answers and Provenance

**Category:** Controls

**Statement:** *Answers used in close investigation must be traceable to their source data, close period, data status, snapshot context, and generated query or retained interaction record.*

An answer is evidence only when a reviewer can identify what was queried, which period and scope were used, the data’s recorded status and as-of/snapshot context, and the calculation or interaction trail. Native platform monitoring, audit logs, conversation retention, or other observability tools may supply parts of that trail, but the methodology does not depend on a single product feature.

Certification identifies approved sources. It does not replace period readiness or finality; pair certification with Principle 2’s period-specific status and snapshot evidence.

### Pass criteria

- Space instructions require answers presenting official close figures to state source dataset(s), close period, reconciliation scope, recorded data status, and as-of/snapshot/run context where available
- Reconciliation-relevant datasets carry inspectable certification/controlled-source metadata or are represented in an accessible controlled-source registry
- Instructions restrict official close figures to declared controlled/certified sources and require caveats when data is preliminary, stale, incomplete, or outside scope
- A retained, accessible interaction/query/audit mechanism exists that can associate a sampled answer with generated SQL or query information and source objects, subject to platform capabilities and retention settings
- A queryable or sampleable evidence record can show whether defined provenance fields were present in retained answers/interactions

### Practitioner guidance

- The close-control owner decides whether investigation evidence is sufficient for review and sign-off, and which exports or retained records belong in the evidence package.
- Configure retention, privacy, data-access, and audit policies appropriate to the organization and jurisdiction.
- Sampled provenance presence is not proof every answer is accurate or review-ready; use Principles 12 and 13 for quality assurance.

### Genie Code action script

```text
Assess and build traceability and provenance controls.

PARAMETERS:
- Genie space: <space name/identifier>
- Catalog.Schema: <catalog.schema>
- Close period: <period identifier>

STEP 1 — CHECK CONFIGURATION:
1. Inspect instructions for requirements to state source dataset, close period, reconciliation scope,
   data status, as-of/snapshot/run context, caveats, and human-validation boundary.
2. Identify certification tags, controlled-source registry entries, or equivalent metadata for
   reconciliation-relevant datasets.
3. Identify accessible query, conversation, usage, audit, or trace records and fields they retain.

STEP 2 — CHECK PERSISTED EVIDENCE:
4. If retained interactions are accessible, sample relevant records and identify whether source, period,
   scope, data status, snapshot context, and query/SQL reference are available.
5. Flag unavailable, incomplete, or inaccessible provenance fields without claiming sign-off evidence
   is sufficient or insufficient.

STEP 3 — BUILD:
6. Draft concise instructions requiring defined provenance fields for official close figures.
7. Draft controlled-source registry specifications or metadata-tag proposals only for relevant datasets.
8. Draft a generic provenance-sampling report specification using fields: interaction_id, timestamp,
   scope, close_period, source_objects, data_status, snapshot_or_run_id, query_reference,
   and provenance_complete_flag.

Output observations: MISSING_PROVENANCE_INSTRUCTION, UNCONTROLLED_SOURCE, NO_RETAINED_QUERY_TRAIL,
or INCOMPLETE_RETAINED_PROVENANCE.
```

---

## Principle 12: Benchmark and Improve Each Close Cycle

**Category:** Controls

**Statement:** *Operate the agent as a recurring close-cycle improvement loop: benchmark intended behavior, investigate failures, change the underlying artifact, and retest.*

A close cycle is a natural improvement boundary. Maintain benchmarks that reflect user investigation needs, execute them before go-live and after material changes, analyze underlying failures, and improve the data context, metadata, matching logic, summary, instructions, or knowledge artifact rather than merely polishing a response.

Benchmarks should cover:

1. **Calculation correctness** — the result agrees with an independently reproducible trusted calculation for a defined case.
2. **Provenance** — the answer identifies required source, scope, period, status, and snapshot context.
3. **Controlled-source use** — official close figures use declared controlled/certified sources or appropriately flag limitations.
4. **Safe ambiguity handling** — ambiguous, incomplete, preliminary, stale, or out-of-scope requests are clarified, caveated, or declined rather than answered with unsupported certainty.

### Pass criteria

- A benchmark suite exists and maps cases to applicable investigation paths: quantify, decompose, explain/classify, compare, age, and next action/workflow evidence
- Each case identifies one or more acceptance dimensions, expected answer pattern, applicable close period/scope, and trusted expected result or validation method
- The suite collectively covers calculation correctness, provenance, controlled-source use, and safe ambiguity handling
- Where runs are persisted, records identify suite/version, case ID, tested space/version, execution timestamp, result, and evidence or failure reference

### Practitioner guidance

- Define material-change triggers, benchmark cadence, release authority, pass thresholds, and escalation expectations.
- Run the suite before go-live and after material changes; review failures and feedback after each close.
- Track trends only where there is a meaningful baseline and retained evidence. A pass-rate trend does not substitute for professional review of high-impact failures.

### Genie Code action script

```text
Assess and build the recurring benchmark suite.

PARAMETERS:
- Genie space: <space name/identifier>
- Close period example: <period>
- Reconciliation scope example: <scope>

STEP 1 — CHECK:
1. Identify accessible benchmark questions/cases, expected-results artifacts, and persisted benchmark-run evidence.
2. Map each case to the applicable investigation path and acceptance dimensions: calculation correctness,
   provenance, controlled-source use, safe ambiguity handling.
3. Flag missing paths/dimensions, cases without an expected result/validation method, and missing
   run/version evidence where a run log is expected.

STEP 2 — BUILD:
4. Draft benchmark cases using real available tables, columns, scope values, and close periods.
5. For each case, specify: case_id, user question, scope/period context, expected answer pattern,
   trusted result or validation method, acceptance dimensions, and evidence reference.
6. Include at least one ambiguity/incomplete-data/out-of-scope case and one preliminary-or-stale-data case.
7. Draft a generic governed benchmark-run table specification: run_id, suite_version, case_id,
   space_version, executed_at, result, evidence_reference, failure_category, and remediation_reference.

Output a coverage matrix and flags: NO_BENCHMARK_SUITE, MISSING_ACCEPTANCE_DIMENSION,
NO_TRUSTED_VALIDATION_METHOD, or NO_PERSISTED_RUN_EVIDENCE. Do not claim a benchmark ran
unless retained execution evidence is available.
```

---

## Principle 13: Independent Evaluation and Assurance

**Category:** Controls

**Statement:** *Establish an independent assurance layer that evaluates whether outputs are correct, traceable, and safe; start with deterministic checks and sampled human review.*

Monitoring tells the team what the assistant did. Assurance evaluates whether defined outputs met their acceptance criteria. It should compare assistant outputs with trusted references or independently reproducible calculations, retain results, and distinguish deterministic validation from human judgment.

Start with deterministic SQL checks that independently reproduce defined variances from controlled source/target datasets and compare them with the break summary. Then add sampled human review for questions involving terminology, interpretation, scope, or contextual judgment. LLM-as-judge may be added later for triage at higher volume, but it is not a prerequisite for a mature close control.

### Pass criteria

- Deterministic SQL test queries exist that independently calculate defined reconciliation measures from declared controlled sources and compare them to the break summary or trusted reference
- Each deterministic check states close period, scope, source snapshot/run context, expected tolerance/reference, and mismatch treatment
- Where execution results are persisted, deterministic-test records identify test/version, timestamp, result, comparison values, source snapshot/run identifiers, and evidence reference
- A trace/evaluation record design exists that can associate question or benchmark case, deterministic result, and human-review result where artifacts are retained

### Practitioner guidance

- Domain experts determine sampling methods, reviewer qualifications, acceptance thresholds, and response to material failures.
- Human reviewers assess interpretation, ambiguity, and evidence sufficiency; a completed review field does not prove the quality of judgment.
- Add LLM-as-judge only when intended use, limitations, calibration, oversight, and failure handling are defined. It should support triage, not replace deterministic controls or accountable review.

### Genie Code action script

```text
Assess and build the independent evaluation and assurance layer.

PARAMETERS:
- Catalog.Schema: <catalog.schema>
- Reconciliation type: <type>
- Close period: <period>
- Reconciliation scope: <scope>

STEP 1 — DISCOVER:
1. Identify controlled/certified source and target datasets, break summary, trusted reference metrics,
   deterministic test SQL, evaluation traces, and persisted result tables.
2. Identify whether source snapshot/run context can be recorded in test results.

STEP 2 — CHECK:
3. Determine whether deterministic SQL independently calculates defined variance/measure from controlled
   source data and compares it with break summary or trusted reference.
4. Inspect whether each test states scope, period, source snapshot/run context, comparison/tolerance,
   and mismatch treatment.
5. Identify persisted execution evidence and whether it includes test version, timestamp, results,
   comparison values, source context, and evidence reference.
6. Identify the available structure for recording human-review outcomes without claiming reviews occurred.

STEP 3 — BUILD:
7. Draft independent deterministic SQL for selected reconciliation using actual tables and declared
   matching/variance logic.
8. Draft a governed evaluation-result table specification with generic fields: evaluation_id,
   test_or_case_id, version, scope, close_period, snapshot_or_run_id, deterministic_result,
   expected_result, comparison_status, reviewer_id, review_outcome, reviewed_at, and evidence_reference.
9. Draft a human-review sampling-plan template and, only if requested, an optional post-hoc
   LLM-as-judge triage flow.

Output available assurance artifacts and flags: NO_INDEPENDENT_DETERMINISTIC_CHECK,
NO_SNAPSHOT_CONTEXT, NO_PERSISTED_EVALUATION_EVIDENCE, or NO_REVIEW_RECORD_STRUCTURE.
Do not assert human review occurred or controls are effective unless retained evidence supports that statement.
```

---

## Implementation sequence

| Phase | Principles | Dependency rationale |
|---|---|---|
| 1. Data foundation | 1–4 | Establish investigable grain and linkage, initial close baseline, post-baseline change handling, then semantic metadata |
| 2. Reconciliation model | 5–6 | Define matching and variance logic before materializing the break summary |
| 3. Agent design and access | 7–10 | Define stable scope, enforce access, establish read-only boundaries, then create questions tested in final user context |
| 4. Evidence and quality | 11–13 | Configure traceability, define recurring benchmarks, then build deterministic and human assurance |

## Recurring close cadence

| Close timing | Principles to revisit | Focus |
|---|---|---|
| Before investigation begins | 2, 3, 6, 8, 11 | Recorded input readiness/finality; baseline snapshot; change status; refreshed summary; applicable access; provenance/trail availability |
| During close | 3, 9, 10, 11 | Detect post-baseline changes; preserve read-only boundary; support safe investigation; retain traceable/caveated responses |
| Before release or sign-off | 12, 13 | Benchmark/evaluation evidence, deterministic variance checks, and practitioner review of material results |
| After close | 3, 12, 13 | Analyze restatements, failures, feedback, evidence gaps, changes, and follow-up tests |

## Maturity model

| Level | Capability state | Minimum capabilities |
|---|---|---|
| **L1 — Investigable** | The organization can isolate and trace exceptions at an appropriate grain | Principle 1 and documented scope basics from Principle 7 |
| **L2 — Operational** | A ready, period-specific, reproducible exception queue exists; its source context is recorded and post-baseline changes can be detected and disclosed | Principles 2–6 |
| **L3 — Controlled** | The agent operates in a defined scope with enforced access, read-only boundaries, and traceable evidence | Principles 7–11 |
| **L4 — Assured and improving** | Independent deterministic checks, benchmarks, retained evidence, and accountable improvement operate through recurring cycles | Principles 12–13 |

LLM-as-judge is optional at every maturity level. An L4 implementation can rely on deterministic validation and sampled, accountable human review.

## Suggested repository structure

```text
.
├── README.md                         # This methodology
├── notebooks/
│   └── Genie-Reconciliation-Methodology.py
├── sql/                              # Reviewed, approved views and deterministic tests
├── docs/                             # Scope, matching, policy, and evidence artifacts
└── examples/                         # Non-production examples and benchmark cases
```

## Operating boundary

This methodology describes a read-only investigation assistant. It does not authorize automated remediation, workflow updates, journal posting, approval, or close sign-off.

Genie can help the close team investigate exceptions, surface relevant evidence, compare periods, and identify the next question to ask. Accountable preparers, reviewers, approvers, data owners, and control owners retain responsibility for judgment and decisions.

## Contributing

When adapting the framework for a domain, retain the distinction between:

- **Machine-checkable criteria:** accessible artifacts, configuration, metadata, deterministic queries, and persisted evidence.
- **Practitioner guidance:** materiality, approval, adequacy of review, policy interpretation, escalation, and sign-off judgment.

Do not convert a human control obligation into a technical pass criterion merely because a status field or evidence record can be created. A record may show that evidence exists; it does not prove that the control was performed effectively.

## License

Add the repository’s chosen license before publishing or accepting external contributions.
