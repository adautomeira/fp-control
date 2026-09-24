# fp-control — Agent Instructions

## Installation — always visible to the user

The two skills work best installed as global commands, with the report assets in `~/.fp-control/`. Installing writes files outside this repository, so it is **never silent**: always tell the user what the status is and what you are about to do.

When you read this file inside this repository:

1. **Check the status (read-only).** Run `bash install.sh status`. It compares the installed copies with this checkout and this checkout with `origin/main` (it runs `git fetch`; add `--no-fetch` if the network is unavailable). Tell the user the result in one or two lines — lead with the sync state, e.g. *"fp-control: ✔ in sync with origin/main (2b7b307); installed copies up to date"* or *"fp-control is 2 commits behind origin/main — run `git pull`"*.
2. **Everything up to date** (exit status 0): nothing else to do.
3. **Something is missing or outdated** (exit status 1): say which files, and ask the user whether to install or update — unless they already asked you to. If the checkout is behind `origin/main`, suggest `git pull` first so the newest version is installed.
4. **Install on the user's go-ahead:** `bash install.sh install`. By default it installs for every agent platform found on the machine and repeats the platforms of the previous install; limit it with `--platform claude|cursor|windsurf` or add `--dest <dir>` for another agent. It keeps installed files the user edited (unless `--force`), records what it installed in `~/.fp-control/INSTALLED`, and adds a git `post-merge` hook that prints the status after every `git pull` (`--no-hook` to skip). Report its summary to the user and remind them to restart open agent sessions.

**If you cannot run shell commands or write outside the workspace**, say so plainly and give the user the command to run themselves (in Claude Code: `! bash install.sh install`), or the manual copy steps below. Do not claim the skills are installed when they are not.

Manual installation (what `install.sh` does):

| Platform | Skill locations |
|----------|-----------------------|
| Claude Code | `~/.claude/commands/fp-control.md` and `~/.claude/commands/fp-control-html.md` |
| Cursor | `~/.cursor/rules/fp-control.mdc` and `~/.cursor/rules/fp-control-html.mdc` |
| Windsurf | `~/.codeium/windsurf/memories/fp-control.md` and `~/.codeium/windsurf/memories/fp-control-html.md` |
| Any other agent | Both files in the platform's global instructions or memories directory |
| All platforms (report assets) | `~/.fp-control/` — every file in `assets/` (`fp-report.html`, `fpa.sh`, `fpa.py`, `LICENSE-js-yaml`) |

Other commands: `bash install.sh uninstall` removes what was installed (keeping edited files unless `--force`), and `bash install.sh --help` lists every option.

## How to use

This repository provides two skills:

- **`fp-control`** — runs an FPA session (counting, AFP, enhancement mode) and saves results to a `.fpa.yaml` file
- **`fp-control-html`** — reads a `.fpa.yaml` file and generates a self-contained HTML report

**Claude Code** — use `/fp-control` and `/fp-control-html` as slash commands once installed (see above).

**Other agents** — read `fp-control.md` or `fp-control-html.md` directly. Both files are self-contained.

## What the skills do

**`fp-control`** supports two counting modes:

*Development Project* — counting a new system from scratch:
1. Define the system boundary
2. Identify and weight data functions (ILF, EIF)
3. Identify and weight transaction functions (EI, EO, EIQ)
4. Calculate Unadjusted Function Points (UFP)
5. Rate the 14 General System Characteristics and calculate Adjusted Function Points (AFP) (optional)
6. Produce an effort estimate (optional)
7. Produce a planning summary — including scope tracking: deferred items, rejected items, and dated negotiation notes
8. Save the analysis as a `.fpa.yaml` file

*Enhancement Project* — measuring changes to a deployed system:
1. Load a baseline `.fpa.yaml` (or a known baseline UFP)
2. Classify existing functions as Unchanged / Changed / Deleted
3. Count new functions (ADD) and one-time conversion functions (CFP)
4. Calculate EFP (size of the enhancement: ADD + CHG after + CFP + DEL) and Updated UFP (new application baseline)
5. Recalculate AFP on the updated baseline (optional)
6. Produce an effort estimate based on EFP (optional)
7. Save as a new `.fpa.yaml` with `project_type: enhancement`

**`fp-control-html`** — reads any `.fpa.yaml` (development or enhancement, single-file or split) and generates a self-contained HTML report from a fixed template (`assets/fp-report.html`) — with tabs, charts, dark/light mode, print support, and a **Scope tab** (when present) surfacing deferred items, rejected scope, and stakeholder notes.
