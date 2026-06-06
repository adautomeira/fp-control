# fp-control

A vendor-agnostic AI skill for planning software systems using **Function Point Analysis (IFPUG)**.

The skill guides an AI agent through the full FPA process: defining the system boundary, identifying data and transaction functions, assigning complexity, calculating Unadjusted Function Points, producing an effort estimate, saving the analysis as a structured Markdown file for future sessions, and generating a self-contained HTML report — all in the language the user speaks.

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

The skill installs itself the first time any agent reads `fp-control.md`. It detects the platform and writes the file to the appropriate global skill location — no manual setup needed on subsequent use.

| Platform | Installed to |
|----------|-------------|
| Claude Code | `~/.claude/commands/fp-control.md` |
| Cursor | `~/.cursor/rules/fp-control.mdc` |
| Windsurf | `~/.codeium/windsurf/memories/fp-control.md` |
| Any other agent | Platform's global instructions or memories directory |

## Manual installation

The agent handles this automatically on first read. If you prefer to install it yourself — or your platform sandboxes file writes — copy `fp-control.md` to the appropriate location below:

| Platform | Command |
|----------|---------|
| Claude Code | `mkdir -p ~/.claude/commands && cp fp-control.md ~/.claude/commands/fp-control.md` |
| Cursor | `mkdir -p ~/.cursor/rules && cp fp-control.md ~/.cursor/rules/fp-control.mdc` |
| Windsurf | `mkdir -p ~/.codeium/windsurf/memories && cp fp-control.md ~/.codeium/windsurf/memories/fp-control.md` |
| Any other agent | Paste the contents as a system prompt or load it as a custom skill per your platform's documentation |

## What the skill covers

| Step | Description |
|------|-------------|
| 1 | Define system boundary |
| 2 | Count data functions — ILF and EIF |
| 3 | Count transaction functions — EI, EO, EIQ |
| 4 | Calculate Unadjusted Function Points (UFP) |
| 5 | Estimate effort (optional) |
| 6 | Produce planning summary |
| 7 | Save as `.fpa.md` — YAML frontmatter + human-readable summary for future sessions |
| 8 | Generate a self-contained HTML report (interactive + print-ready) |

The entire session — questions, tables, summary, and HTML output — is conducted in the language the user writes in.

## License

MIT — free to use, copy, modify, and distribute. If you fork or derive a project from this work, include a visible reference to the [original repository](https://github.com/adautomeira/fp-control) in your README or documentation.

## Reference

IFPUG Counting Practices Manual (CPM) — [ifpug.org](https://www.ifpug.org)
