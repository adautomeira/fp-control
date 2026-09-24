# fp-control

Two vendor-agnostic AI skills for planning software systems using **Function Point Analysis (IFPUG)**: one that runs the full FPA session and saves results to a structured YAML file, and one that reads that file and generates a self-contained HTML report.

## Why Function Points still matter in an AI world

AI can generate code faster than ever, but it cannot tell you **how much** of something you are building. Function Points answer exactly that — they measure the functional size of a system independent of technology, team, or tooling.

This matters more, not less, in an AI-assisted development context:

- **Scope is still the main cost driver.** AI accelerates implementation but does not shrink requirements. A system with 300 FP has the same functional complexity whether it is built by ten developers or one developer with an AI assistant.
- **Estimates need a baseline.** Productivity benchmarks (hours per FP) can now be recalibrated for AI-assisted teams, giving you a defensible, auditable estimate instead of a gut feeling.
- **Contracts and procurement still require sizing.** Fixed-price contracts, government projects, and outsourcing agreements often mandate a functional size metric. FPA is an ISO standard (ISO/IEC 20926) recognized across industries.
- **AI-generated code still needs to be scoped before it is written.** Knowing what you are asking the AI to build — and how much of it — prevents runaway scope and helps you prioritize features objectively.
- **Comparison across projects remains valid.** Because FP counts are technology-agnostic, you can compare velocity, defect density, and cost across projects built with completely different stacks or AI tools.

In short: AI changes how fast you build, not how much you need to build. FPA measures the latter.

## Project files for AI agents

This repository includes two files that help AI agents understand how to work with the skills without manual setup:

- **`agents.md`** — vendor-agnostic instructions: what the skills do, how to invoke them, and how to install them. Any agent on any platform can read this file.
- **`CLAUDE.md`** — Claude Code's project context file. Claude Code loads it automatically whenever you open this directory, which causes it to also load `agents.md` via the `@agents.md` import. That triggers the self-install below, after which `/fp-control` and `/fp-control-html` are available as commands in every Claude Code session.

Other platforms (Cursor, Windsurf) do not auto-load `CLAUDE.md`, so their users rely on the self-install mechanism described below.

## Self-installing

Both skills install themselves when an agent reads `agents.md` inside this repository. It detects the platform and writes the two skill files to the appropriate global skill locations, plus the report assets to `~/.fp-control/`. The installed files are copies — see [Updating](#updating) to refresh them after pulling changes.

| Platform | Installed to |
|----------|-------------|
| Claude Code | `~/.claude/commands/fp-control.md` and `~/.claude/commands/fp-control-html.md` |
| Cursor | `~/.cursor/rules/fp-control.mdc` and `~/.cursor/rules/fp-control-html.mdc` |
| Windsurf | `~/.codeium/windsurf/memories/fp-control.md` and `~/.codeium/windsurf/memories/fp-control-html.md` |
| Any other agent | Platform's global instructions or memories directory |
| All platforms (report assets) | `~/.fp-control/` — every file in `assets/` |

## Manual installation

If you prefer to install manually — or your platform sandboxes file writes:

| Platform | Commands |
|----------|---------|
| Claude Code | `mkdir -p ~/.claude/commands && cp fp-control.md ~/.claude/commands/fp-control.md && cp fp-control-html.md ~/.claude/commands/fp-control-html.md` |
| Cursor | `mkdir -p ~/.cursor/rules && cp fp-control.md ~/.cursor/rules/fp-control.mdc && cp fp-control-html.md ~/.cursor/rules/fp-control-html.mdc` |
| Windsurf | `mkdir -p ~/.codeium/windsurf/memories && cp fp-control.md ~/.codeium/windsurf/memories/fp-control.md && cp fp-control-html.md ~/.codeium/windsurf/memories/fp-control-html.md` |
| Any other agent | Paste each file's contents as a system prompt or custom skill |
| Report assets (all platforms) | `mkdir -p ~/.fp-control && cp assets/* ~/.fp-control/` |

## Updating

Installed skills and assets are copies, so they do not change when you `git pull`. Refresh them by opening the repository with your agent again (the self-install overwrites files that differ) or by rerunning the manual installation commands above. After updating, check the schema changes in [`CHANGELOG.md`](CHANGELOG.md): saved `.fpa.yaml` files from older versions still load, and re-saving them with `/fp-control` upgrades them.

## What the skills cover

**`/fp-control`** — FPA session (Development and Enhancement Project modes):

| Step | Description |
|------|-------------|
| 1 | Define system boundary |
| 2 | Count data functions — ILF and EIF |
| 3 | Count transaction functions — EI, EO, EIQ |
| 4 | Calculate Unadjusted Function Points (UFP) — every function gets a stable ID (`ilf-01`, `ei-07`); large sessions can save a partial checkpoint (`status: partial`) and resume later |
| 5 | Rate 14 General System Characteristics and calculate Adjusted Function Points (AFP) (optional) |
| 6 | Estimate effort — UFP and AFP based (optional). Asks for the team's own hours-per-FP data first; the built-in 8/14/20 rates are illustrative defaults, not a benchmark, and the file records which was used |
| 7 | Produce planning summary — including scope tracking: deferred items (future phase), rejected items (explicitly excluded), and dated negotiation notes |
| 8 | Save as `.fpa.yaml` (schema 1.2) — compact YAML for future sessions, enhancement baseline loading, and HTML generation; files over 50 functions are split into an index plus one file per type. The file is then validated with `fpa.sh check` when Python is available (see [Tools](#tools)) |

Enhancement Project mode (reference an existing `.fpa.yaml` and say you want to measure changes to the deployed system; referencing a file alone opens it for review or editing): baseline functions are matched by ID and classified as ADD / CHG / DEL, plus one-time conversion functions (CFP). The skill computes EFP (IFPUG enhancement size: ADD + CHG after + CFP + DEL) and Updated UFP, optionally recalculates AFP and EFP adjusted, and saves a new `.fpa.yaml` that includes `updated_functions`, the application after the enhancement, which the next enhancement loads.

**`/fp-control-html`** — HTML report generator:

Reads any `.fpa.yaml` (development or enhancement, single-file or split) and produces a self-contained `.html` report. The agent does not write the HTML or convert any data: it copies a fixed template (`assets/fp-report.html`) and appends the `.fpa.yaml` file(s) unchanged — `assets/fpa.sh` does this with nothing but bash. The template parses the YAML in the browser, renders the report, and recomputes every total and complexity from the raw counts — any stored value that disagrees with the IFPUG tables is listed in a **Consistency checks** box. The report has tabbed navigation, SVG charts, dark/light mode, and print support. Includes a **Scope tab** (when present) that surfaces deferred items, rejected scope, and stakeholder notes. The HTML filename matches the YAML filename with `.fpa.yaml` replaced by `.html`.

- **Style**: the skill asks once about accent color and starting theme; a choice saved in the file's `report_style` block is reused without asking.
- **Languages**: labels for English and Brazilian Portuguese (`en`, `pt-BR`) are built in; for other languages the agent passes a small JSON file of translated labels. Numbers and dates follow the chosen language.
- **No shell?** Agents without a shell (e.g. on Windows without WSL or Git Bash) build the same report with their file tools: copy the template and append the YAML verbatim, as described in `fp-control-html.md`.

The entire session is conducted in the language the user writes in. The HTML report is generated in the same language.

## Tools

`assets/fpa.sh` is the main tool and needs only bash and standard Unix tools (Linux, macOS, WSL, Git Bash):

```sh
bash assets/fpa.sh report examples/bookshop.fpa.yaml               # → examples/bookshop.html
bash assets/fpa.sh report my-system.fpa.yaml --lang pt-BR --theme dark
bash assets/fpa.sh check  my-system.fpa.yaml                       # optional, see below
```

The report is the validator: it re-applies the IFPUG complexity tables to every item and checks stored totals (UFP, EFP, Updated UFP, AFP), duplicate IDs and names, enhancement cross-references (every CHG/DEL must exist in the baseline), and file format, listing any problem in a **Consistency checks** box.

**Optional: terminal validation.** `fpa.sh check` runs `assets/fpa.py check`, which needs **python3 + PyYAML** (`pip install pyyaml`). It prints the same checks plus effort totals and exits with status 1 on errors (`--strict`: warnings too) — useful for CI, pre-commit hooks, and for agents checking a file right after saving it. Nothing in the skills requires Python; without it, `fpa.sh check` says so and exits with status 2.

`fpa.py report` produces a file identical to `fpa.sh report`. The IFPUG tables live in both `fpa.py` and `fp-report.html`; the test suite fails if they differ. The template bundles [js-yaml](https://github.com/nodeca/js-yaml) 4.1.0 (MIT, see `assets/LICENSE-js-yaml`).

## Repository layout

| Path | Contents |
|------|----------|
| `fp-control.md`, `fp-control-html.md` | The two skills |
| `assets/` | Report template, `fpa.sh` (builder), `fpa.py` (optional validator) — installed to `~/.fp-control/` |
| `examples/` | A small development count and an enhancement of it (schema 1.2) — valid inputs for trying the report |
| `tests/` | Regression tests (python3 + PyYAML): `python3 -m unittest discover tests` |
| `CHANGELOG.md` | Schema versions and migration notes |

## License

MIT — free to use, copy, modify, and distribute. If you fork or derive a project from this work, include a visible reference to the [original repository](https://github.com/adautomeira/fp-control) in your README or documentation.

## Reference

IFPUG Counting Practices Manual (CPM) — [ifpug.org](https://www.ifpug.org)
