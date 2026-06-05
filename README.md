# fp-control

A vendor-agnostic AI skill for planning software systems using **Function Point Analysis (IFPUG)**.

The skill guides an AI agent through the full FPA process: defining the system boundary, identifying data and transaction functions, assigning complexity, calculating Unadjusted Function Points, producing an effort estimate, and generating a self-contained HTML report — all in the language the user speaks.

## Why Function Points still matter in an AI world

AI can generate code faster than ever, but it cannot tell you **how much** of something you are building. Function Points answer exactly that — they measure the functional size of a system independent of technology, team, or tooling.

This matters more, not less, in an AI-assisted development context:

- **Scope is still the main cost driver.** AI accelerates implementation but does not shrink requirements. A system with 300 FP has the same functional complexity whether it is built by ten developers or one developer with an AI assistant.
- **Estimates need a baseline.** Productivity benchmarks (hours per FP) can now be recalibrated for AI-assisted teams, giving you a defensible, auditable estimate instead of a gut feeling.
- **Contracts and procurement still require sizing.** Fixed-price contracts, government projects, and outsourcing agreements often mandate a functional size metric. FPA is an ISO standard (ISO/IEC 20926) recognized across industries.
- **AI-generated code still needs to be scoped before it is written.** Knowing what you are asking the AI to build — and how much of it — prevents runaway scope and helps you prioritize features objectively.
- **Comparison across projects remains valid.** Because FP counts are technology-agnostic, you can compare velocity, defect density, and cost across projects built with completely different stacks or AI tools.

In short: AI changes how fast you build, not how much you need to build. FPA measures the latter.

## Self-installing

The skill installs itself the first time any agent reads `fp-control.md`. It detects the platform and writes the file to the appropriate global skill location — no manual setup needed on subsequent use.

| Platform | Installed to |
|----------|-------------|
| Claude Code | `~/.claude/commands/fp-control.md` |
| Cursor | `~/.cursor/rules/fp-control.mdc` |
| Windsurf | `~/.codeium/windsurf/memories/fp-control.md` |
| Any other agent | Platform's global instructions or memories directory |

## Manual installation

### Claude Code

```bash
mkdir -p ~/.claude/commands
cp fp-control.md ~/.claude/commands/fp-control.md
```

Invoke inside a session:

```
/fp-control
```

### Any other LLM / agent platform

Paste the contents of `fp-control.md` as a system prompt, or load it as a custom skill/tool per your platform's documentation. No external dependencies required.

## What the skill covers

| Step | Description |
|------|-------------|
| 1 | Define system boundary |
| 2 | Count data functions — ILF and EIF |
| 3 | Count transaction functions — EI, EO, EIQ |
| 4 | Calculate Unadjusted Function Points (UFP) |
| 5 | Estimate effort (optional) |
| 6 | Produce planning summary |
| 7 | Generate a self-contained HTML report (interactive + print-ready) |

The entire session — questions, tables, summary, and HTML output — is conducted in the language the user writes in.

## Reference

IFPUG Counting Practices Manual (CPM) — [ifpug.org](https://www.ifpug.org)
