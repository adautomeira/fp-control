# Changelog

Schema versions of the `.fpa.yaml` format (the `fp_control` key). Both skills read every version listed here; `/fp-control` always saves with the current one.

## 1.2 — 2026-09-23

### Counting fixes
- **EIQ complexity uses the EO/EQ matrix** (FTR 0–1 / 2–3 / 4+, DET 1–5 / 6–19 / 20+). 1.1 used the EI matrix, which rates some inquiries one level too high (e.g. FTR 3, DET 12 was High/6 instead of Avg/4). Re-check EIQs in 1.1 files with `fpa.py check`.
- **Enhancement size follows IFPUG**: `efp = ADD + CHG_after + CFP + DEL`. 1.1 stored `defp = ADD + CHG_after`, which left out deletions. `defp` is replaced by `efp`; effort is based on `efp`.
- **Rounding**: VAF has 2 decimals; AFP and `efp_adjusted` are whole numbers (half up).

### New fields
- `id` on every function (`ilf-01`, `ei-07`, `cfp-ei-01`) — stable, never renumbered or reused; enhancements match baseline functions by `id`. Renames keep the id (`renamed_from` on a CHG when the rename comes with a real change).
- Enhancement files: `updated_functions` (the application *after* the enhancement — what the next enhancement loads), `cfp` (one-time conversion functions: counted in EFP, not in the application), `baseline_vaf`, `afp.efp_adjusted`.
- `status: partial` and `counted_types` for mid-session checkpoints (1.1 used an assumption string).
- `effort.source` — `team`, `default`, or a short citation. The 8/14/20 hours-per-FP defaults are illustrative, not a published benchmark.
- `report_style` (`accent`, `accent_dark`, `theme`) — saved report preferences, reused by `/fp-control-html`.

### Removed
- `function_counts` in split index files — it repeated totals already derivable from `baseline_functions`. Readers still accept it in 1.1 files.

### Format
- Files start with `---` and no longer end with `---` (the trailing marker made `yaml.safe_load` reject the file).
- Empty lists are written as `[]` or omitted, never as a bare key.

### Migrating a 1.1 file
Load it with `/fp-control` and save it again. The skill assigns IDs in list order, recomputes `efp` including deletions, derives `updated_functions` from `baseline_functions − del − chg(before) + chg(after) + add`, and drops `function_counts`. Run `python3 assets/fpa.py check <file>` afterwards.

## 1.1 — 2026-06-06

First versioned schema: development and enhancement files, split format for more than 50 functions, AFP block, effort, `assumptions`, `deferred`, `rejected`, `notes`.
