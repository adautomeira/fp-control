# fp-control — YAML file formats

The `.fpa.yaml` formats for Step 8 (Save as YAML) of `fp-control.md`. Read this when you are about to save or edit a development count; enhancement files are described in `enhancement-mode.md` (Step E9).

The 50-function threshold uses the total counted in Step 4.

#### Single-file format (≤ 50 functions total)

All detail in one file:

```yaml
---
fp_control: "1.2"
system: "<System Name>"
date: "<YYYY-MM-DD>"
boundary: "<one-sentence boundary description>"
ufp: <total>
ilf:
  - {id: ilf-01, name: "<name>", ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
eif:
  - {id: eif-01, name: "<name>", ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
ei:
  - {id: ei-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
eo:
  - {id: eo-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
eiq:
  - {id: eiq-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
afp:                                    # omit entire key if Step 5 was skipped
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
  id: <sum of scores>
  vaf: <0.65 + id * 0.01>
  afp: <ufp * vaf>
effort:                               # omit if Step 6 was skipped
  source: "<team|default|short citation>"
  optimistic:   {hours_per_fp: 8,  total_hours: <n>}
  typical:      {hours_per_fp: 14, total_hours: <n>}
  conservative: {hours_per_fp: 20, total_hours: <n>}
assumptions:                          # omit if none — one string per item
  - "<assumption or risk>"
deferred:                             # omit if none — features deferred to a future phase
  - "<description>"
rejected:                             # omit if none — features explicitly excluded from scope
  - "<description>"
notes:                                # omit if none — stakeholder / negotiation log
  - {date: "<YYYY-MM-DD>", text: "<note>"}
report_style:                         # omit unless the user chose a report style
  accent: "<#hex>"
  accent_dark: "<#hex>"
  theme: <light|dark|auto>
```

---

#### Split format (> 50 functions total)

Produce one **index file** and up to five **detail files** (one per function type, omit if the type has zero functions).

**Index file** — `<system-name>.fpa.yaml` (always small, always loaded):

```yaml
---
fp_control: "1.2"
system: "<System Name>"
date: "<YYYY-MM-DD>"
boundary: "<one-sentence boundary description>"
ufp: <total>
split: true
status: partial                       # checkpoints only — omit when the count is complete
counted_types: [ilf, ei]              # checkpoints only — types finished so far
detail_files:
  ilf: "<system-name>.fpa.ilf.yaml"    # omit key if type has 0 functions
  eif: "<system-name>.fpa.eif.yaml"
  ei:  "<system-name>.fpa.ei.yaml"
  eo:  "<system-name>.fpa.eo.yaml"
  eiq: "<system-name>.fpa.eiq.yaml"
baseline_functions:                   # id + name + fp only — for enhancement baseline loading and per-type totals
  ilf: [{id: ilf-01, name: "<name>", fp: <n>}]
  eif: [{id: eif-01, name: "<name>", fp: <n>}]
  ei:  [{id: ei-01,  name: "<name>", fp: <n>}]
  eo:  [{id: eo-01,  name: "<name>", fp: <n>}]
  eiq: [{id: eiq-01, name: "<name>", fp: <n>}]
afp:                                  # omit entire key if Step 5 was skipped
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
  id: <sum of scores>
  vaf: <0.65 + id * 0.01>
  afp: <ufp * vaf>
effort:                               # omit if Step 6 was skipped
  source: "<team|default|short citation>"
  optimistic:   {hours_per_fp: 8,  total_hours: <n>}
  typical:      {hours_per_fp: 14, total_hours: <n>}
  conservative: {hours_per_fp: 20, total_hours: <n>}
assumptions:                          # omit if none — one string per item
  - "<assumption or risk>"
deferred:                             # omit if none — features deferred to a future phase
  - "<description>"
rejected:                             # omit if none — features explicitly excluded from scope
  - "<description>"
notes:                                # omit if none — stakeholder / negotiation log
  - {date: "<YYYY-MM-DD>", text: "<note>"}
report_style:                         # omit unless the user chose a report style
  accent: "<#hex>"
  accent_dark: "<#hex>"
  theme: <light|dark|auto>
```

**Detail files** — `<system-name>.fpa.<type>.yaml` (loaded on demand):

```yaml
---
fp_control: "1.2"
system: "<System Name>"
type: <ilf|eif|ei|eo|eiq>
ilf:                                  # key matches type value above
  - {id: ilf-01, name: "<name>", ret: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
```

Transaction function detail files use `ftr` instead of `ret`:

```yaml
---
fp_control: "1.2"
system: "<System Name>"
type: ei
ei:
  - {id: ei-01, name: "<name>", ftr: <n>, det: <n>, complexity: <Low|Avg|High>, fp: <n>}
```
