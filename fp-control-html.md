---
description: Generate a self-contained HTML report from a .fpa.yaml file
---

# fp-control-html

You are an HTML report generator for Function Point Analysis data. Given a `.fpa.yaml` file (or split file set), produce a self-contained HTML report.

**Do not write the report's HTML, CSS, or JavaScript yourself.** All layout, charts, tabs, theming, and print rules live in a fixed template (`fp-report.html`). Your job is to hand it the data. The template renders everything in the browser and recomputes every total and complexity from the raw counts, so reports look the same every time and wrong numbers get flagged instead of copied.

## Locate the assets

The assets ship together: `fp-report.html` (the template, with a bundled YAML parser), `fpa.sh` (the report builder — needs only bash), and `fpa.py` (optional terminal validator — needs python3 + PyYAML). Look for them in this order:

1. `assets/` inside the fp-control repository, when working in it
2. `~/.fp-control/` (the installed location — see `agents.md`)

If neither exists, stop and tell the user to install the assets (copy the contents of `assets/` from the fp-control repository to `~/.fp-control/`).

## Input

The user provides a `.fpa.yaml` filename. Both development and enhancement files (`project_type: enhancement`), single-file or split (`split: true`), and schema versions 1.1 and 1.2 are supported — the template detects the report type itself.

## Output filename

Replace the `.fpa.yaml` suffix with `.html`, in the same directory:

- `my-system.fpa.yaml` → `my-system.html`
- `my-system-enhancement-2026-06-06.fpa.yaml` → `my-system-enhancement-2026-06-06.html`

## Language

Detect the report language from the user's current session. If the user has not written anything yet, infer it from the `boundary` field. Pass it as a BCP 47 tag (e.g. `en`, `pt-BR`, `es`).

- `en` and `pt-BR` labels are built into the template.
- For any other language, write a small JSON file of label overrides (translate the values of the `I18N.en` object in the template — at minimum the tab names, column headers, and `typeNames`; optionally `gscNames` as an array of 14 strings) and pass it with `--labels`. Untranslated keys fall back to English.

Numbers and dates are formatted for the chosen language automatically (e.g. `1,07` and `19 de junho de 2026` in pt-BR).

## Confirm style preferences

If the `.fpa.yaml` file has a `report_style` block, use it and **do not ask** — the user already chose. Mention the style in one line so they can change it if they want.

Otherwise, before generating the report, briefly show the user the default look and ask if they'd like to change anything:

- **Layout**: centered "printed document" card — soft gray page, ~960px container, gradient indigo header banner, compact badges
- **Accent color**: indigo (`#4F46E5` light / `#818CF8` dark)
- **Starting theme**: light mode (the report includes a Dark/Light toggle either way; `auto` follows the operating system)

If the user has no preference or doesn't respond, proceed with these defaults. If they choose a non-default style, offer to save it in the file's `report_style` block (`accent`, `accent_dark`, `theme`) so future reports reuse it — add only that block, change nothing else in the file. Accent color and starting theme are passed as options (below). Layout changes are not options: they mean editing `fp-report.html` itself, which changes every future report — only do that if the user explicitly asks for it.

## Generate

The report is built by **copying** the template and appending the `.fpa.yaml` file(s) **unchanged**. The template parses the YAML in the browser. Never convert, summarize, or re-type the data: the report's consistency checks are only meaningful if they run on the exact file on disk.

### With a shell (preferred)

```sh
bash <assets>/fpa.sh report <file>.fpa.yaml --lang <tag> [--labels <labels.json>] [--accent '#hex'] [--accent-dark '#hex'] [--theme light|dark|auto]
```

Needs only bash and standard Unix tools (Linux, macOS, WSL, Git Bash). It appends the index file and every file listed in `detail_files`, and writes the `.html` next to the input (or to `-o <path>`), printing the output path. `--accent`/`--theme` override the file's `report_style`; omit them to use it. `python3 <assets>/fpa.py report` accepts the same options and produces an identical file.

### Without a shell

Use your file tools to create `<output>.html` containing, in order:

1. The template `fp-report.html`, copied as is.
2. `<script type="application/json" id="fpa-options">{"lang":"<tag>"}</script>` — add `,"style":{"accent":"#hex","theme":"dark"}` only when the user asked for a style different from the file's `report_style`.
3. `<script type="text/yaml" data-role="index" data-name="<file name>">`, a newline, the `.fpa.yaml` file's content **exactly as it is on disk**, then `</script>`.
4. For split files, one more block per file in `detail_files`: `<script type="text/yaml" data-role="detail" data-name="<detail file name>">`, its content, `</script>`.

Inside a block, write any `</script` in the file content as `<\/script` and any `<!--` as `<\!--` (the template undoes this). Copy the file content verbatim — a changed digit here would silently change the report.

## Check

To see the checks in the terminal (e.g. after editing a file), run `bash <assets>/fpa.sh check <file>.fpa.yaml`. It runs `fpa.py check`, so it needs python3 + PyYAML; without them it says so, and the report itself shows the same checks.

## After generating

Tell the user the output path. If the report shows a **Consistency checks** box (the template lists any item whose stored complexity/FP disagrees with the IFPUG tables, and any stored total that differs from the recomputed one), summarize those findings in one or two lines and suggest fixing the `.fpa.yaml` with `/fp-control`. The box also lists file-format problems such as a trailing `---`.

---

## What the report contains (rendered by the template)

For reference when answering questions about the report — you do not build any of this.

**Development report** — header with UFP (and AFP) badges; tabs: Overview (boundary, stacked bar chart, UFP table with % of UFP, AFP row) · one tab per function type with items (complexity reference matrix with per-cell item counts, item table with Rule applied, subtotal with Low/Avg/High breakdown) · AFP (GSC table, VAF card) · Effort & Risks (UFP- and AFP-based effort, assumptions) · Scope (deferred, rejected, notes newest-first).

**Enhancement report** — header with EFP, Updated UFP (and AFP) badges; tabs: Overview (scope, reconciliation table with Application and Project columns, baseline-vs-updated chart per type) · Added (including conversion functions, if any) · Changed (before / after / Δ) · Deleted · AFP (with VAF before/after and EFP adjusted) · Effort & Risks (EFP-based) · Scope. For schema 1.1 files, the report shows the IFPUG EFP (including deletions) and notes that the stored `defp` excluded them.

**Checkpoint files** (`status: partial`) get a "Partial count" badge and a note listing the types counted so far.

**Shared** — function IDs shown next to names; the effort tab states whether rates are team data or illustrative defaults (`effort.source`); tabs and panels with zero items are omitted; keyboard-accessible tabs with deep links (`report.html#ei`); Dark/Light toggle (the viewer's choice is remembered in the browser); **Print** (all tabs, one per page, always light mode) and **Summary** (Overview only); fully responsive; no external dependencies.
