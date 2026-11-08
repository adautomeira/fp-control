# fp-control — Enhancement Project Mode

Steps E1–E9 for measuring changes to a deployed system. Read this file in full when Mode Detection in `fp-control.md` selects Enhancement Project.

Use this mode when measuring changes to a system that has already been counted and deployed. It follows the IFPUG Enhancement Project counting method: classify every function as Added, Changed, or Deleted; compute the **Enhancement Function Points (EFP)** — the size of the enhancement project — and derive the updated application baseline.

Two numbers come out of this mode, and they answer different questions:

- **EFP** — how big is the *work* of this enhancement? Adds, changes, **and deletions** all count, because removing a function is work too.
- **Updated UFP** — how big is the *application* after the enhancement is deployed? Deletions and the "before" size of changed functions are subtracted.

---

### Step E1 — Load Baseline

Load the baseline function list using the first available source:

1. **Enhancement `.fpa.yaml`** (i.e. `project_type: enhancement`) — read `updated_functions` (the application *after* that enhancement) and use its `updated_ufp` as the new baseline UFP. Do not open any other file.
   - **Legacy files (`fp_control: "1.1"`)** have no `updated_functions`. Derive it: start from `baseline_functions`, remove every `del` entry and every `chg` entry (by type + name), then append every `chg` entry with its `after.fp` and every `add` entry (name + fp). Tell the user you derived it. Also note that the `defp` stored in 1.1 files excluded deletions — it is not comparable with `efp`.
2. **Development `.fpa.yaml`, split format** (i.e. `split: true`) — read `baseline_functions` from the index. Do not load the detail files for baseline loading.
3. **Development `.fpa.yaml`, single-file format** — read the `ilf`, `eif`, `ei`, `eo`, `eiq` lists to build the function list.
4. **No file** — ask the user for the baseline UFP total and proceed without a function list (classification steps will ask the user to enumerate functions manually).

**Function IDs:** match baseline functions by `id`, never by name alone. If the baseline functions have no `id` (files written before schema 1.2), assign them now — `<type>-NN` in list order — tell the user, and use them from here on.

If the source file has an `afp` block, remember its `vaf` — it is the **VAF before** the enhancement, used in Step E6.

Confirm with the user:
- System name
- Baseline UFP (and AFP if present)

Ask the user to briefly describe the scope of the enhancement (what changed and why). This becomes the enhancement boundary description stored in the file and shown in the report.

---

### Step E2 — Classify Data Functions

Present each ILF and EIF from the baseline as a table and ask the user to classify each one:

| ID | Function | Type | Baseline FP | Status |
|----|----------|------|-------------|--------|
| ilf-01 | (name) | ILF | — | Unchanged / Changed / Deleted |

For each **Changed** function, re-count RET and DET at the new size using the same complexity tables as Step 2 of Development Mode. Record both the old FP and the new FP.

For each **Deleted** function, record its baseline FP — deletions count toward EFP.

A function is **Changed** whenever its data (a new, removed or altered DET or RET) or its processing changes — even when its complexity band does not move. It then counts at its full after-size in EFP, and its before-size is subtracted from the Updated UFP. A new field that leaves an ILF at Low is still a CHG (before and after FP are equal); leaving it out understates EFP.

Unchanged functions are neither counted nor subtracted — they affect neither EFP nor the Updated UFP.

**Renames:** a function whose only change is its name is **not** a CHG — it keeps its ID and FP, and only its name changes in `updated_functions`. If the rename comes with a real change (new RET/DET), record it in `chg` under the same ID with the new name and `renamed_from: "<old name>"`.

---

### Step E3 — Classify Transaction Functions

Repeat the classification for EI, EO, and EIQ from the baseline.

For each **Changed** function, re-count FTR and DET at the new size using the same complexity tables as Step 3 of Development Mode (remember: EIQ uses the EO matrix).

When a baseline function is being replaced by a new one (e.g. two catalogs merged into one), classify the old one as **Deleted** and count the replacement under ADD — do not leave the deletion only in an assumption.

---

### Step E4 — New Functions (ADD) and Conversion Functions (CFP)

Ask: *"Are there any new data or transaction functions being introduced by this enhancement?"*

Count new ILF, EIF, EI, EO, and EIQ using the same complexity tables as Steps 2 and 3. Give each new function the next free ID of its type (after the highest ID in the baseline, including IDs of functions deleted in this or earlier enhancements — IDs are never reused).

Then ask: *"Does this enhancement need any one-time data conversion or migration functionality (e.g. migrating records from an old structure into a new one)?"*

Conversion functions (CFP) are counted like any other transaction (usually EIs, sometimes an EO for a conversion report). Give them IDs with a `cfp-` prefix (`cfp-ei-01`) — they never enter the application baseline. They are part of the enhancement **project** size (EFP) but are thrown away after deployment, so they are **not** added to the Updated UFP. Skip if none.

---

### Step E5 — Calculate EFP and Updated Baseline

Apply the IFPUG Enhancement Project formulas:

    EFP         = ADD_fp + CHG_after_fp + CFP_fp + DEL_fp
    Updated_UFP = baseline_ufp + ADD_fp + CHG_after_fp − CHG_before_fp − DEL_fp

Present the full reconciliation table:

| Category | Functions | Application (Updated UFP) | Project (EFP) |
|---|---|---|---|
| Baseline UFP | | start | — |
| Added (ADD) | | + | + |
| Changed — after (CHG_after) | | + | + |
| Changed — before (CHG_before) | | − | — |
| Deleted (DEL) | | − | + |
| Conversion (CFP) | | — | + |
| **Total** | | **Updated UFP** | **EFP** |

Explain to the user: EFP measures the size of the enhancement work itself (including deletions and conversion). Updated UFP is the new application baseline after the enhancement is deployed.

**Consistency check:** if the user mentions a function being removed, merged, or replaced anywhere in the session, it must appear in `del`. Before moving on, re-read the assumptions collected so far and confirm no deletion is recorded only as text.

---

### Step E6 — AFP (optional)

Ask: *"Would you like to calculate Adjusted Function Points for this enhancement?"*

If the baseline had AFP, show the previous GSC scores and ask the user to confirm or update any that changed due to the enhancement. If the baseline had no AFP, offer to run the full GSC rating from scratch (same process as Step 5 of Development Mode).

Recalculate:

    ID_after     = sum of updated GSC scores
    VAF_after    = 0.65 + (ID_after × 0.01)
    AFP_after    = Updated_UFP × VAF_after                                  (application, after)
    EFP_adjusted = (ADD_fp + CHG_after_fp + CFP_fp) × VAF_after + DEL_fp × VAF_before   (project)

`VAF_before` is the baseline's VAF. If the baseline had no AFP, use `VAF_after` for the DEL term and add an assumption saying so.

Apply the Step 5 rounding rules (VAF to 2 decimals, AFP and EFP_adjusted to whole numbers).

---

### Step E7 — Effort Estimation (optional)

Ask: *"Would you like an effort estimate for this enhancement?"*

Use **EFP** as the base — not Updated UFP — since effort applies only to the work being done, not the whole application.

As in Step 6, ask for the team's own hours-per-FP data first; otherwise use the illustrative defaults and say they are placeholders. Record the choice in `effort.source`.

| Scenario     | Hours per FP | Total hours   |
|--------------|-------------|---------------|
| Optimistic   | 8           | EFP × 8       |
| Typical      | 14          | EFP × 14      |
| Conservative | 20          | EFP × 20      |

If AFP was calculated in Step E6, show a second effort table using `EFP_adjusted` as the base.

---

### Step E8 — Summary

After the summary, add the **Observations (these do not affect the FP count)** section described in `design-advisor.md` — for an enhancement, the useful signal is usually how widely a small change spreads across CHG functions.

Produce a final planning summary with:

1. **System name and enhancement scope** — one paragraph
2. **Reconciliation table** — from Step E5 (EFP and Updated UFP)
3. **AFP_after, VAF, and EFP_adjusted** — from Step E6, if completed
4. **Effort range** — from Step E7, if requested
5. **Key assumptions and risks** — items the user should revisit
6. **Deferred items** — changes agreed to handle in a later enhancement
7. **Rejected items** — changes explicitly excluded, with the rationale noted in the string
8. **Notes** — dated entries capturing stakeholder decisions, open questions, or negotiation outcomes

Collect assumptions, deferred, rejected, and notes explicitly before saving, following the same rules as Step 7 of Development Mode. All four fields are optional — omit any that are empty.

---

### Step E9 — Save as YAML (optional)

Ask: *"Would you like to save this enhancement analysis as a YAML file?"*

If yes, use the default filename `<system-name-in-kebab-case>-enhancement-<YYYY-MM-DD>.fpa.yaml`.

Produce a YAML-only `.fpa.yaml` file — no Markdown body. To generate a visual HTML report from the saved file, use `/fp-control-html`.

The enhancement file carries two compact snapshots (id + name + fp only):

- `baseline_functions` — the application **before** this enhancement (used for the reconciliation and the report's baseline-vs-updated chart)
- `updated_functions` — the application **after** this enhancement: baseline minus `del`, with `chg` entries at their `after.fp`, plus `add`. Conversion functions are **not** included. This is what the next enhancement loads (Step E1), so it never has to open any prior file in the chain.

Check before saving: the sum of `updated_functions` must equal `updated_ufp`, and every `chg`/`del` ID must exist in `baseline_functions`. Then validate with `fpa.py check` as described in Step 8.

If the total number of add + chg + cfp functions exceeds 50, apply a split format: produce an index file plus separate detail files. The `del` block always stays in the index (name + fp only, always small), and so do both snapshots. In the index, replace the full `add`, `chg`, and `cfp` blocks with a `split: true` flag and pointers:

```yaml
# enhancement index (split mode) — replaces add/chg/cfp blocks with pointers:
split: true
detail_files:
  add: "<system-name>-enhancement-<YYYY-MM-DD>.fpa.add.yaml"
  chg: "<system-name>-enhancement-<YYYY-MM-DD>.fpa.chg.yaml"
  cfp: "<system-name>-enhancement-<YYYY-MM-DD>.fpa.cfp.yaml"   # omit if no conversion functions
```

Each detail file starts with `fp_control`, `system`, and `type: <add|chg|cfp>`, followed by one block with the same key and structure as in the single-file schema below.

For the non-split (≤ 50 add+chg+cfp functions) case, the full schema is:

```yaml
---
fp_control: "1.2"
project_type: enhancement
baseline_file: "<baseline-filename>.fpa.yaml"   # omit if unknown
system: "<System Name>"
date: "<YYYY-MM-DD>"
boundary: "<one-sentence description of what this enhancement changed and why>"
baseline_ufp: <n>
baseline_afp: <n>                              # omit if baseline had no AFP
baseline_vaf: <n.nn>                           # omit if baseline had no AFP
baseline_functions:                            # application BEFORE — id + name + fp only
  ilf: [{id: ilf-NN, name: "<name>", fp: <n>}]
  eif: [{id: eif-NN, name: "<name>", fp: <n>}]
  ei:  [{id: ei-NN, name: "<name>", fp: <n>}]
  eo:  [{id: eo-NN, name: "<name>", fp: <n>}]
  eiq: [{id: eiq-NN, name: "<name>", fp: <n>}]
add:                                           # omit a type key (or use []) when it has no items
  ilf: [{id: ilf-NN, name: "<name>", ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
  eif: [{id: eif-NN, name: "<name>", ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
  ei:  [{id: ei-NN, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
  eo:  [{id: eo-NN, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
  eiq: [{id: eiq-NN, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
chg:                                           # same id as in baseline_functions; add renamed_from: "<old>" if the name changed
  ilf: [{id: ilf-NN, name: "<name>", before: {fp: <n>}, after: {ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}}]
  eif: [{id: eif-NN, name: "<name>", before: {fp: <n>}, after: {ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}}]
  ei:  [{id: ei-NN, name: "<name>", before: {fp: <n>}, after: {ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}}]
  eo:  [{id: eo-NN, name: "<name>", before: {fp: <n>}, after: {ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}}]
  eiq: [{id: eiq-NN, name: "<name>", before: {fp: <n>}, after: {ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}}]
del:
  ilf: [{id: ilf-NN, name: "<name>", fp: <n>}]
  eif: [{id: eif-NN, name: "<name>", fp: <n>}]
  ei:  [{id: ei-NN, name: "<name>", fp: <n>}]
  eo:  [{id: eo-NN, name: "<name>", fp: <n>}]
  eiq: [{id: eiq-NN, name: "<name>", fp: <n>}]
cfp:                                           # omit if no conversion functions
  ei:  [{id: cfp-ei-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
  eo:  [{id: cfp-eo-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}]
updated_functions:                             # application AFTER — id + name + fp only; no cfp
  ilf: [{id: ilf-NN, name: "<name>", fp: <n>}]
  eif: [{id: eif-NN, name: "<name>", fp: <n>}]
  ei:  [{id: ei-NN, name: "<name>", fp: <n>}]
  eo:  [{id: eo-NN, name: "<name>", fp: <n>}]
  eiq: [{id: eiq-NN, name: "<name>", fp: <n>}]
efp: <add_fp + chg_after_fp + cfp_fp + del_fp>
updated_ufp: <baseline_ufp + add_fp + chg_after_fp - chg_before_fp - del_fp>
afp:                                           # omit if Step E6 was skipped
  gsc:
    - {id: 1,  name: "Data Communications",          score: <n>}
    - {id: 2,  name: "Distributed Data Processing",  score: <n>}
    - {id: 3,  name: "Performance",                  score: <n>}
    - {id: 4,  name: "Heavily Used Configuration",   score: <n>}
    - {id: 5,  name: "Transaction Rate",             score: <n>}
    - {id: 6,  name: "Online Data Entry",            score: <n>}
    - {id: 7,  name: "End-User Efficiency",          score: <n>}
    - {id: 8,  name: "Online Update",                score: <n>}
    - {id: 9,  name: "Complex Processing",           score: <n>}
    - {id: 10, name: "Reusability",                  score: <n>}
    - {id: 11, name: "Installation Ease",            score: <n>}
    - {id: 12, name: "Operational Ease",             score: <n>}
    - {id: 13, name: "Multiple Sites",               score: <n>}
    - {id: 14, name: "Facilitate Change",            score: <n>}
  id: <sum>
  vaf: <0.65 + id * 0.01>                      # VAF_after, 2 decimals
  afp: <round(updated_ufp * vaf)>              # application AFP after the enhancement
  efp_adjusted: <round((add + chg_after + cfp) * vaf + del * baseline_vaf)>
effort:                               # omit if Step E7 was skipped
  source: "<team|default|short citation>"
  optimistic:   {hours_per_fp: 8,  total_hours: <efp * 8>}
  typical:      {hours_per_fp: 14, total_hours: <efp * 14>}
  conservative: {hours_per_fp: 20, total_hours: <efp * 20>}
assumptions:                          # omit if none — one string per item
  - "<assumption or risk>"
deferred:                             # omit if none — changes deferred to a later enhancement
  - "<description>"
rejected:                             # omit if none — changes explicitly excluded from scope
  - "<description>"
notes:                                # omit if none — stakeholder / negotiation log
  - {date: "<YYYY-MM-DD>", text: "<note>"}
report_style:                         # omit unless the user chose a report style
  accent: "<#hex>"
  accent_dark: "<#hex>"
  theme: <light|dark|auto>
```
