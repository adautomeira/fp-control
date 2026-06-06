# fp-control — Agent Instructions

This repository contains the `fp-control` skill: a structured Function Point Analysis (IFPUG) facilitator for estimating the functional size of software systems.

## How to use

The skill definition lives in `fp-control.md`. To start a Function Point Analysis session, read that file and follow the steps inside.

**Claude Code** — use the `/fp-control` slash command. It becomes available automatically after the skill self-installs to `~/.claude/commands/` on first use.

**Other agents** — read `fp-control.md` directly. The file is self-contained and includes all counting rules, complexity tables, and output instructions.

## What the skill does

The skill supports two counting modes:

**Development Project** — counting a new system from scratch:
1. Define the system boundary
2. Identify and weight data functions (ILF, EIF)
3. Identify and weight transaction functions (EI, EO, EIQ)
4. Calculate Unadjusted Function Points (UFP)
5. Rate the 14 General System Characteristics and calculate Adjusted Function Points (AFP) (optional)
6. Produce an effort estimate (optional)
7. Save the analysis as a structured `.fpa.yaml` file
8. Generate a self-contained HTML report

**Enhancement Project** — measuring changes to a deployed system:
1. Load a baseline `.fpa.yaml` (or a known baseline UFP)
2. Classify existing functions as Unchanged / Changed / Deleted
3. Count new functions (ADD)
4. Calculate DEFP (size of the enhancement) and Updated UFP (new application baseline)
5. Recalculate AFP on the updated baseline (optional)
6. Produce an effort estimate based on DEFP (optional)
7. Save as a new `.fpa.yaml` with `project_type: enhancement`
8. Generate a self-contained HTML report with before/after comparison
