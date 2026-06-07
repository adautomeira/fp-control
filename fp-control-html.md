---
description: Generate a self-contained HTML report from a .fpa.yaml file
---

# fp-control-html

You are an HTML report generator for Function Point Analysis data. Given a `.fpa.yaml` file (or split file set), produce a self-contained HTML report.

## Input

The user provides a `.fpa.yaml` filename. Read the file and detect the report type:

- If `project_type: enhancement` — generate an **Enhancement Report** (see below)
- Otherwise — generate a **Development Report** (see below)

If the file has `split: true`, load each detail file listed in `detail_files` on demand — one per function-type tab. Do not load all detail files upfront; load only what is needed for each section.

For enhancement files with `split: true`, load `detail_files.add` and `detail_files.chg` on demand for the Added and Changed tabs respectively.

## Output filename

Derive the output filename by replacing the `.fpa.yaml` suffix with `.html`:

- `my-system.fpa.yaml` → `my-system.html`
- `my-system-enhancement-2026-06-06.fpa.yaml` → `my-system-enhancement-2026-06-06.html`

The file must have no external dependencies (all CSS and JS inlined) and work in both interactive and print modes.

## Language

Detect the language to use for all report labels, headings, and static text from the user's current session. If the user has not written anything yet, infer from the `boundary` field in the `.fpa.yaml` file. Generate the entire HTML output — tab names, column headers, badge labels, button text — in that language.

---

## Development Report

### Structure

1. **Header** — system name, date, UFP badge. If AFP was calculated (`afp` key present), show a second AFP badge alongside it (e.g. "UFP 142 · AFP 156"). Fixed button group (top-right) with three buttons: **Dark/Light toggle** (switches theme; starts as "🌙 Dark"), **Print** (full print), **Summary** (simplified print — overview tab only)
2. **CSS-only tab navigation** using the radio-button pattern — no JavaScript. Tabs: Overview · ILF · EIF · EI · EO · EIQ · AFP (only if `afp` key present) · Effort & Risks · Scope (only if any of `deferred`, `rejected`, or `notes` is present and non-empty). Each function-type tab label shows its FP subtotal as a small chip (e.g. "ILF · 91"). The Scope tab chip shows the total item count across all three fields (e.g. "Scope · 9").
3. **Overview tab** — system boundary paragraph + inline SVG stacked bar chart + UFP summary table (type, items, FP total, grand total row). If AFP was calculated, append a one-row AFP summary below the UFP table: ID · VAF · AFP.
4. **One tab per function type** (ILF, EIF, EI, EO, EIQ), each containing:
   - A **complexity reference card** showing the IFPUG matrix for that type (RET/DET for data functions; FTR/DET for transaction functions) with the weight for each complexity level
   - A **full item table** with columns:
     - Data functions (ILF / EIF): Name · RET · DET · Rule applied · Complexity · FP
     - Transaction functions (EI / EO / EIQ): Name · FTR · DET · Rule applied · Complexity · FP
   - The **Rule applied** column shows the exact matrix cell used, e.g. `RET 2–5, DET 1–19 → Low` or `FTR 2, DET 5–15 → Avg`
   - Subtotal row at the bottom
5. **AFP tab** (only render if `afp` key present) — two sections:
   - **GSC scoring table**: columns # · General System Characteristic · Score · Bar (a small inline visual bar, e.g. filled squares, proportional to the 0–5 score)
   - **VAF calculation card**: shows UFP, ID, VAF formula (`0.65 + ID × 0.01 = VAF`), and AFP result prominently
6. **Effort & Risks tab** — effort estimate table (optimistic / typical / conservative); if AFP was calculated, show a second effort block using AFP as the base alongside the UFP block. If the `assumptions` key is present in the YAML and non-empty, render the list below the effort table. Omit the section entirely if the key is absent.
7. **Scope tab** (only render if at least one of `deferred`, `rejected`, or `notes` is present and non-empty) — three optional sections, each omitted when the corresponding key is absent:
   - **Deferred** — labeled section with a bullet list of `deferred` items. Use a distinct visual treatment (e.g. amber/yellow accent or clock icon) to convey "pending future scope."
   - **Rejected** — labeled section with a bullet list of `rejected` items. Use a muted or strikethrough-adjacent treatment (e.g. red/gray accent or × icon) to convey "out of scope."
   - **Notes** — labeled section rendered as a two-column table (Date · Note), sorted newest-first. Each entry is `{date, text}`; if an entry is a plain string (no `date` key), render it without a date. Use a neutral accent (e.g. indigo or blue).

---

## Enhancement Report

### Structure

**Header** — system name, date, DEFP badge ("DEFP 38"), Updated UFP badge ("Updated UFP 180"). AFP badge if `afp` key present.

**Tabs**: Overview · Added · Changed · Deleted · AFP (only if `afp` key present) · Effort & Risks · Scope (only if any of `deferred`, `rejected`, or `notes` is present and non-empty; same structure and rules as the Development Report Scope tab)

**Overview tab**
- Enhancement scope paragraph (from `boundary`)
- Reconciliation table: Baseline UFP · DEL (−) · CHG_before (−) · CHG_after (+) · ADD (+) · Updated UFP · DEFP
- Inline SVG grouped bar chart: baseline vs. updated UFP per function type (ILF, EIF, EI, EO, EIQ)

**Added tab** — new functions from the `add` block, grouped by type (ILF, EIF, EI, EO, EIQ), each with its full detail table (same columns as the Development report function-type tabs)

**Changed tab** — functions from the `chg` block, grouped by type; each row shows Name · Before FP · After (new metrics + complexity + FP) · Delta FP

**Deleted tab** — functions from the `del` block, grouped by type; columns: Name · Baseline FP

**AFP tab** (only if `afp` key present) — same structure as the Development Report AFP tab, using the updated GSC scores and Updated UFP as the base

**Effort & Risks tab** — effort table using DEFP as the base. If the `assumptions` key is present in the YAML and non-empty, render the list below the effort table. Omit the section entirely if the key is absent.

**Scope tab** — same structure and rendering rules as the Development Report Scope tab.

---

## Shared rules

### Interactivity

- CSS-only tabs using hidden radio inputs (`position:absolute; opacity:0; pointer-events:none`) and the `~` sibling combinator — radio inputs must be the first children of the tabs container, followed by the tab bar and panels
- **Dark/Light toggle**: JavaScript `toggleTheme()` adds/removes a `dark` class on `<body>` and updates the button label accordingly
- **Print button** triggers `window.print()` directly
- **Summary print button** triggers `printSimple()`: adds class `print-simple` to `<body>`, calls `window.print()`, then removes the class via the `afterprint` event

### Print (`@media print`)

- Hide the button group and tab bar
- Force all panels visible (`display: block !important`) — except when `body.print-simple` is set, which shows only the Overview panel
- Each panel starts on a new page (`page-break-before: always` on `.panel + .panel`)
- Remove shadows and border-radius
- Ensure tables paginate cleanly (`break-inside: avoid` on rows)
- SVG chart must render correctly on paper — use dark fills or patterns instead of color-only encoding
- **Always print in light mode**: reset all CSS custom properties to light values inside `@media print { :root, body.dark { ... } }` — dark mode must never appear in print output

### Style

- Implement theming with CSS custom properties (`:root` for light defaults, `body.dark` overrides for dark mode)
- Light mode: white background, dark text, indigo accent (#4F46E5)
- Dark mode: near-black background (#0f0f1a), light text, lighter indigo (#818CF8) for accents; badge colors inverted for legibility
- Tab bar scrollable horizontally on small screens (`overflow-x: auto; scrollbar-width: none`)
- Fully responsive layout
- Self-contained — no `<link>` to external stylesheets, no `<script src="">` to CDNs
