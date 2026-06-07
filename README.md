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

This repository includes two files that help AI agents understand how to work with the skill without manual setup:

- **`agents.md`** — vendor-agnostic instructions: what the skill does and how to invoke it. Any agent on any platform can read this file.
- **`CLAUDE.md`** — Claude Code's project context file. Claude Code loads it automatically whenever you open this directory, which causes it to also load `agents.md` via the `@agents.md` import. This is why the `/fp-control` command and skill context are available immediately in Claude Code without any extra steps.

Other platforms (Cursor, Windsurf) do not auto-load `CLAUDE.md`, so their users rely on the self-install mechanism described below.

## Self-installing

Both skills install themselves the first time any agent reads `agents.md`. It detects the platform and writes both files to the appropriate global skill locations — no manual setup needed on subsequent use.

| Platform | Installed to |
|----------|-------------|
| Claude Code | `~/.claude/commands/fp-control.md` and `~/.claude/commands/fp-control-html.md` |
| Cursor | `~/.cursor/rules/fp-control.mdc` and `~/.cursor/rules/fp-control-html.mdc` |
| Windsurf | `~/.codeium/windsurf/memories/fp-control.md` and `~/.codeium/windsurf/memories/fp-control-html.md` |
| Any other agent | Platform's global instructions or memories directory |

## Manual installation

If you prefer to install manually — or your platform sandboxes file writes:

| Platform | Commands |
|----------|---------|
| Claude Code | `mkdir -p ~/.claude/commands && cp fp-control.md ~/.claude/commands/fp-control.md && cp fp-control-html.md ~/.claude/commands/fp-control-html.md` |
| Cursor | `mkdir -p ~/.cursor/rules && cp fp-control.md ~/.cursor/rules/fp-control.mdc && cp fp-control-html.md ~/.cursor/rules/fp-control-html.mdc` |
| Windsurf | `mkdir -p ~/.codeium/windsurf/memories && cp fp-control.md ~/.codeium/windsurf/memories/fp-control.md && cp fp-control-html.md ~/.codeium/windsurf/memories/fp-control-html.md` |
| Any other agent | Paste each file's contents as a system prompt or custom skill |

## What the skills cover

**`/fp-control`** — FPA session (Development and Enhancement Project modes):

| Step | Description |
|------|-------------|
| 1 | Define system boundary |
| 2 | Count data functions — ILF and EIF |
| 3 | Count transaction functions — EI, EO, EIQ |
| 4 | Calculate Unadjusted Function Points (UFP) |
| 5 | Rate 14 General System Characteristics and calculate Adjusted Function Points (AFP) (optional) |
| 6 | Estimate effort — UFP and AFP based (optional) |
| 7 | Produce planning summary — including scope tracking: deferred items (future phase), rejected items (explicitly excluded), and dated negotiation notes |
| 8 | Save as `.fpa.yaml` — compact YAML for future sessions, enhancement baseline loading, and HTML generation |

Enhancement Project mode (triggered by referencing an existing `.fpa.yaml`): classify existing functions as ADD / CHG / DEL, compute DEFP and Updated UFP, optionally recalculate AFP, save as a new `.fpa.yaml`.

**`/fp-control-html`** — HTML report generator:

Reads any `.fpa.yaml` (development or enhancement, single-file or split) and produces a self-contained `.html` report with tabbed navigation, SVG charts, dark/light mode, and print support. Includes a **Scope tab** (when present) that surfaces deferred items, rejected scope, and stakeholder notes. The HTML filename matches the YAML filename with `.fpa.yaml` replaced by `.html`.

The entire session is conducted in the language the user writes in. The HTML report is generated in the same language.

## License

MIT — free to use, copy, modify, and distribute. If you fork or derive a project from this work, include a visible reference to the [original repository](https://github.com/adautomeira/fp-control) in your README or documentation.

## Reference

IFPUG Counting Practices Manual (CPM) — [ifpug.org](https://www.ifpug.org)
