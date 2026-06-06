# fp-control — Agent Instructions

This repository contains the `fp-control` skill: a structured Function Point Analysis (IFPUG) facilitator for estimating the functional size of software systems.

## How to use

The skill definition lives in `fp-control.md`. To start a Function Point Analysis session, read that file and follow the steps inside.

**Claude Code** — use the `/fp-control` slash command. It becomes available automatically after the skill self-installs to `~/.claude/commands/` on first use.

**Other agents** — read `fp-control.md` directly. The file is self-contained and includes all counting rules, complexity tables, and output instructions.

## What the skill does

Walks the user through the full IFPUG counting process:

1. Define the system boundary
2. Identify and weight data functions (ILF, EIF)
3. Identify and weight transaction functions (EI, EO, EIQ)
4. Calculate Unadjusted Function Points (UFP)
5. Produce an effort estimate (optional)
6. Save the analysis as a structured `.fpa.md` file
7. Generate a self-contained HTML report
