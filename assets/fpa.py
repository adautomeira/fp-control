#!/usr/bin/env python3
"""fp-control helper (optional): validate .fpa.yaml files and build HTML reports.

The main tool is fpa.sh, which needs only bash. This script adds terminal validation
(`check`) and needs python3 + PyYAML. `fpa.sh check` calls it when available.

Usage:
    python3 fpa.py check  <file.fpa.yaml> [--strict]
    python3 fpa.py report <file.fpa.yaml> [--lang pt-BR] [--labels labels.json]
                          [--accent '#4F46E5'] [--accent-dark '#818CF8'] [--theme light|dark|auto]
                          [-o <output.html>]

`check` re-applies the IFPUG complexity tables to every item and verifies every stored
total, ID and cross-reference. It exits with status 1 when it finds errors (with --strict,
warnings count as errors too).

`report` produces exactly the same file as `fpa.sh report`: the template followed by the
YAML files, unchanged (tests/test_fpa.py compares the two byte for byte). The template
parses them in the browser and runs the same checks as `check` — keep the IFPUG tables
below in sync with fp-report.html (a test compares them).
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required (pip install pyyaml) — or follow the manual steps in fp-control-html.md")

TEMPLATE = Path(__file__).resolve().with_name("fp-report.html")
CURRENT_SCHEMA = "1.2"

# ── IFPUG tables (mirror of fp-report.html) ──────────────────────────────
INF = float("inf")
GRID = [["Low", "Low", "Avg"], ["Low", "Avg", "High"], ["Avg", "High", "High"]]
MATRICES = {
    "data": {"row": "RET", "rows": [1, 5, INF], "cols": [19, 50, INF]},   # upper bounds
    "ei":   {"row": "FTR", "rows": [1, 2, INF], "cols": [4, 15, INF]},
    "eo":   {"row": "FTR", "rows": [1, 3, INF], "cols": [5, 19, INF]},    # EO and EQ share this matrix
}
TYPES = ["ilf", "eif", "ei", "eo", "eiq"]
TYPE_INFO = {
    "ilf": ("data", "ret", {"Low": 7, "Avg": 10, "High": 15}),
    "eif": ("data", "ret", {"Low": 5, "Avg": 7, "High": 10}),
    "ei":  ("ei", "ftr", {"Low": 3, "Avg": 4, "High": 6}),
    "eo":  ("eo", "ftr", {"Low": 4, "Avg": 5, "High": 7}),
    "eiq": ("eo", "ftr", {"Low": 3, "Avg": 4, "High": 6}),
}
DEFAULT_RATES = {"optimistic": 8, "typical": 14, "conservative": 20}


# ── Loading ──────────────────────────────────────────────────────────────
def load(path, notes=None):
    text = Path(path).read_text(encoding="utf-8")
    docs = list(yaml.safe_load_all(text))
    content = [d for d in docs if d is not None]
    if not content:
        sys.exit(f"{path}: no YAML content")
    if len(docs) > 1 and notes is not None:
        notes.warn(f"{Path(path).name}: file ends with '---' (a second, empty YAML document) — strict parsers reject it; remove the trailing '---'")
    return content[0]


def load_merged(path, notes=None):
    """Load an index file and inline every detail file listed in detail_files."""
    path = Path(path)
    fpa = load(path, notes)
    for key, fname in (fpa.get("detail_files") or {}).items():
        detail_path = path.resolve().parent / fname
        if not detail_path.exists():
            if notes is not None:
                notes.error(f"detail file not found: {fname}")
            continue
        detail = load(detail_path, notes)
        fpa[key] = detail.get(key, detail.get(detail.get("type")))
    return fpa


# ── Checks ───────────────────────────────────────────────────────────────
class Notes:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def lst(v):
    return [x for x in v if x is not None] if isinstance(v, list) else []


def by_type(block):
    block = block or {}
    return {t: lst(block.get(t)) for t in TYPES}


def num(v):
    try:
        return None if v is None or isinstance(v, bool) else float(v)
    except (TypeError, ValueError):
        return None


def fp_of(item):
    return num(item.get("fp")) or 0


def norm_cx(s):
    v = str(s or "").lower()
    if v.startswith(("l", "b")):
        return "Low"
    if v.startswith("alt") or v.startswith("h"):
        return "High"
    if v.startswith(("a", "m")):
        return "Avg"
    return None


def classify(t, rv, det):
    m, _, w = TYPE_INFO[t]
    rows, cols = MATRICES[m]["rows"], MATRICES[m]["cols"]
    ri = next(i for i, hi in enumerate(rows) if rv <= hi)
    ci = next(i for i, hi in enumerate(cols) if det <= hi)
    cx = GRID[ri][ci]
    return cx, w[cx]


def check_item(t, item, notes, label=""):
    _, key, _ = TYPE_INFO[t]
    rv, det = num(item.get(key)), num(item.get("det"))
    name = item.get("name", "?")
    if rv is None or det is None:
        notes.warn(f"{label}{t.upper()} '{name}': missing {key.upper()} or DET — complexity cannot be verified")
        return
    cx, fp = classify(t, rv, det)
    stored_cx, stored_fp = norm_cx(item.get("complexity")), num(item.get("fp"))
    if (stored_cx and stored_cx != cx) or (stored_fp is not None and stored_fp != fp):
        notes.error(f"{label}{t.upper()} '{name}' ({key.upper()} {rv:g}, DET {det:g}): stored {item.get('complexity')}/{item.get('fp')}, IFPUG table gives {cx}/{fp}")


def check_total(label, stored, calc, notes):
    s = num(stored)
    if s is not None and abs(s - calc) > 0.005:
        notes.error(f"{label}: stored {s:g}, recomputed {calc:g}")


def check_ids(lists, notes, where, require):
    """lists: iterable of (type, items). Flags duplicate IDs, duplicate names per type, and missing IDs."""
    seen, missing = {}, 0
    for t, items in lists:
        names = {}
        for it in items:
            iid, name = it.get("id"), it.get("name")
            if iid is None:
                missing += 1
            elif iid in seen:
                notes.error(f"{where}: duplicate id '{iid}' ({seen[iid]} and {name})")
            else:
                seen[iid] = name
            if name in names:
                notes.error(f"{where}: duplicate {t.upper()} name '{name}'")
            names[name] = True
    if missing and require:
        notes.warn(f"{where}: {missing} function(s) without an id — schema 1.2 gives every function a stable id (e.g. ei-07)")


def round_half_up(x):
    return int(x + 0.5 + 1e-9)


def check_afp(afp, base, notes):
    gsc = lst(afp.get("gsc"))
    if len(gsc) != 14:
        notes.warn(f"AFP: {len(gsc)} GSC scores found, 14 expected")
    scores = [num(g.get("score")) or 0 for g in gsc]
    for g, s in zip(gsc, scores):
        if not 0 <= s <= 5:
            notes.error(f"AFP: GSC {g.get('id')} score {s:g} is outside 0–5")
    ident = sum(scores)
    vaf = round(0.65 + ident * 0.01, 2)
    check_total("AFP id (sum of GSC scores)", afp.get("id"), ident, notes)
    check_total("AFP vaf", afp.get("vaf"), vaf, notes)
    check_total("AFP afp", afp.get("afp"), round_half_up(base * vaf), notes)
    return vaf


def check_effort(effort, bases, notes):
    """bases: list of (label, value); the first one is the base for stored total_hours."""
    if not effort:
        return
    if not effort.get("source"):
        notes.warn("effort: no 'source' — record whether the hours-per-FP rates are team data or illustrative defaults")
    label, base = bases[0]
    for k in DEFAULT_RATES:
        row = effort.get(k) or {}
        rate = num(row.get("hours_per_fp"))
        if rate is not None and row.get("total_hours") is not None:
            check_total(f"effort.{k}.total_hours ({label} × {rate:g})", row.get("total_hours"), round_half_up(base * rate), notes)


def check_dev(fpa, notes):
    partial = fpa.get("status") == "partial"
    lists = {t: lst(fpa.get(t)) for t in TYPES}
    for t in TYPES:
        for it in lists[t]:
            check_item(t, it, notes)
        if fpa.get("split") and (fpa.get("detail_files") or {}).get(t) and not lists[t] and not partial:
            notes.error(f"{t.upper()}: detail file listed but no items loaded")
    ufp = sum(fp_of(it) for t in TYPES for it in lists[t])
    check_total("ufp", fpa.get("ufp"), ufp, notes)
    for t, c in (fpa.get("function_counts") or {}).items():
        if t in lists and lists[t]:
            check_total(f"function_counts.{t}.fp", (c or {}).get("fp"), sum(fp_of(i) for i in lists[t]), notes)
            check_total(f"function_counts.{t}.items", (c or {}).get("items"), len(lists[t]), notes)
    if fpa.get("baseline_functions"):
        bf = by_type(fpa["baseline_functions"])
        check_total("baseline_functions (sum)", ufp, sum(fp_of(i) for t in TYPES for i in bf[t]), notes)
    check_ids(lists.items(), notes, "functions", require=str(fpa.get("fp_control")) >= "1.2")
    if partial:
        done = fpa.get("counted_types") or []
        notes.warn(f"partial count (checkpoint): counted {', '.join(done) or 'nothing yet'}; UFP is incomplete")
    afp_val = None
    if fpa.get("afp"):
        vaf = check_afp(fpa["afp"], ufp, notes)
        afp_val = round_half_up(ufp * vaf)
    check_effort(fpa.get("effort"), [("UFP", ufp)] + ([("AFP", afp_val)] if afp_val is not None else []), notes)
    return {"ufp": ufp}


def key_of(t, it):
    return (t, it.get("id")) if it.get("id") else (t, "name:" + str(it.get("name")))


def check_enh(fpa, notes):
    add, chg, dele, cfp = by_type(fpa.get("add")), by_type(fpa.get("chg")), by_type(fpa.get("del")), by_type(fpa.get("cfp"))
    for t in TYPES:
        for it in add[t]:
            check_item(t, it, notes, "add: ")
        for it in cfp[t]:
            check_item(t, it, notes, "cfp: ")
        for it in chg[t]:
            check_item(t, dict(it.get("after") or {}, name=it.get("name")), notes, "chg: ")
    ADD = sum(fp_of(i) for t in TYPES for i in add[t])
    CFP = sum(fp_of(i) for t in TYPES for i in cfp[t])
    CHGA = sum(fp_of(i.get("after") or {}) for t in TYPES for i in chg[t])
    CHGB = sum(fp_of(i.get("before") or {}) for t in TYPES for i in chg[t])
    DEL = sum(fp_of(i) for t in TYPES for i in dele[t])

    base_f = by_type(fpa.get("baseline_functions")) if fpa.get("baseline_functions") else None
    baseline_ufp = num(fpa.get("baseline_ufp"))
    if base_f:
        base_sum = sum(fp_of(i) for t in TYPES for i in base_f[t])
        if baseline_ufp is None:
            baseline_ufp = base_sum
        check_total("baseline_ufp vs baseline_functions", baseline_ufp, base_sum, notes)
        # every CHG/DEL must refer to a baseline function; ADD must not duplicate a surviving one
        base_keys = {key_of(t, i) for t in TYPES for i in base_f[t]}
        base_names = {(t, i.get("name")) for t in TYPES for i in base_f[t]}
        for block, items in (("chg", chg), ("del", dele)):
            for t in TYPES:
                for it in items[t]:
                    if key_of(t, it) not in base_keys and (t, it.get("renamed_from", it.get("name"))) not in base_names:
                        notes.error(f"{block}: {t.upper()} '{it.get('name')}' ({it.get('id', 'no id')}) is not in baseline_functions")
        removed = {(t, i.get("name")) for t in TYPES for i in dele[t]}
        for t in TYPES:
            for it in add[t]:
                if (t, it.get("name")) in base_names and (t, it.get("name")) not in removed:
                    notes.error(f"add: {t.upper()} '{it.get('name')}' already exists in the baseline — should it be a CHG?")
        check_ids([(t, base_f[t]) for t in TYPES], notes, "baseline_functions", require=str(fpa.get("fp_control")) >= "1.2")
    baseline_ufp = baseline_ufp or 0

    EFP = ADD + CHGA + CFP + DEL
    updated = baseline_ufp + ADD + CHGA - CHGB - DEL
    check_total("updated_ufp", fpa.get("updated_ufp"), updated, notes)
    if fpa.get("efp") is not None:
        check_total("efp", fpa.get("efp"), EFP, notes)
    elif fpa.get("defp") is not None:
        notes.warn(f"schema 1.1: stored defp ({num(fpa['defp']):g}) excluded deletions; IFPUG EFP = ADD + CHG after + CFP + DEL = {EFP:g}")
    if fpa.get("updated_functions"):
        upd = by_type(fpa["updated_functions"])
        check_total("updated_functions (sum)", sum(fp_of(i) for t in TYPES for i in upd[t]), updated, notes)
        check_ids([(t, upd[t]) for t in TYPES], notes, "updated_functions", require=True)
    elif str(fpa.get("fp_control")) >= "1.2":
        notes.error("updated_functions missing — the next enhancement needs it to load the application after this one")
    check_ids([(t, add[t] + cfp[t]) for t in TYPES], notes, "add/cfp", require=str(fpa.get("fp_control")) >= "1.2")

    efp_adj = None
    if fpa.get("afp"):
        vaf = check_afp(fpa["afp"], updated, notes)
        vb = num(fpa.get("baseline_vaf"))
        if vb is None:
            vb = vaf
        efp_adj = round_half_up((ADD + CHGA + CFP) * vaf + DEL * vb)
        check_total("afp.efp_adjusted", fpa["afp"].get("efp_adjusted"), efp_adj, notes)
    effort_base = ("EFP", EFP)
    legacy_defp = num(fpa.get("defp")) if fpa.get("efp") is None else None
    if legacy_defp is not None and legacy_defp != EFP:
        # 1.1 files computed effort from DEFP; flag the difference once instead of per row
        notes.warn(f"effort was computed from the 1.1 defp ({legacy_defp:g}); on the IFPUG EFP ({EFP:g}) it is {EFP / legacy_defp:.2f}× higher")
        effort_base = ("defp", legacy_defp)
    check_effort(fpa.get("effort"), [effort_base] + ([("EFP adjusted", efp_adj)] if efp_adj is not None else []), notes)
    return {"efp": EFP, "updated_ufp": updated}


def run_check(path, strict):
    notes = Notes()
    fpa = load_merged(path, notes)
    if str(fpa.get("fp_control")) != CURRENT_SCHEMA:
        notes.warn(f"schema {fpa.get('fp_control')}: current is {CURRENT_SCHEMA} — see CHANGELOG.md; re-save with /fp-control to upgrade")
    totals = check_enh(fpa, notes) if fpa.get("project_type") == "enhancement" else check_dev(fpa, notes)
    summary = ", ".join(f"{k} {v:g}" for k, v in totals.items())
    print(f"{Path(path).name}: {summary}")
    for m in notes.errors:
        print(f"  ERROR  {m}")
    for m in notes.warnings:
        print(f"  warn   {m}")
    failed = bool(notes.errors) or (strict and bool(notes.warnings))
    print(f"  {len(notes.errors)} error(s), {len(notes.warnings)} warning(s)" if notes.errors or notes.warnings else "  OK")
    return 1 if failed else 0


# ── Report (mirror of fpa.sh) ────────────────────────────────────────────
def default_output(src):
    name = src.name
    for suffix in (".fpa.yaml", ".yaml", ".yml"):
        if name.endswith(suffix):
            return src.with_name(name[: -len(suffix)] + ".html")
    return src.with_name(name + ".html")


def escape_block(text):
    """Same escaping as fpa.sh: only "</script" and "<!--" are special inside <script>."""
    return re.sub(r"</(script)", r"<\\/\1", text, flags=re.IGNORECASE).replace("<!--", "<\\!--")


def escape_attr(text):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def options_json(lang, accent, accent_dark, theme):
    style = [f'"{k}":"{v}"' for k, v in (("theme", theme), ("accent", accent), ("accent_dark", accent_dark)) if v]
    return '{"lang":"%s"%s}' % (lang or "en", ',"style":{%s}' % ",".join(style) if style else "")


def build_report(path, lang="en", labels=None, accent=None, accent_dark=None, theme=None):
    path = Path(path)
    read = lambda p: Path(p).read_text(encoding="utf-8")
    parts = [TEMPLATE.read_text(encoding="utf-8"),
             '<script type="application/json" id="fpa-options">%s</script>\n' % options_json(lang, accent, accent_dark, theme)]
    if labels:
        parts.append('<script type="application/json" id="fpa-labels">' + escape_block(read(labels)) + "</script>\n")
    parts.append('<script type="text/yaml" data-role="index" data-name="%s">\n' % escape_attr(path.name)
                 + escape_block(read(path)) + "</script>\n")
    for fname in (load(path).get("detail_files") or {}).values():
        detail = path.parent / fname
        if detail.exists():
            parts.append('<script type="text/yaml" data-role="detail" data-name="%s">\n' % escape_attr(str(fname))
                         + escape_block(read(detail)) + "</script>\n")
        else:
            print(f"fpa.py: warning: detail file not found: {fname}", file=sys.stderr)
    return "".join(parts)


def run_report(args):
    out = args.output or default_output(args.input)
    out.write_text(build_report(args.input, args.lang, args.labels, args.accent, args.accent_dark, args.theme), encoding="utf-8")
    print(out)
    return 0


def lang_tag(v):
    if not re.fullmatch(r"[A-Za-z0-9-]+", v):
        raise argparse.ArgumentTypeError(f"invalid language tag '{v}' (use a tag like en or pt-BR)")
    return v


def hex_color(v):
    if not re.fullmatch(r"#[0-9A-Fa-f]+", v):
        raise argparse.ArgumentTypeError(f"invalid color '{v}' (use #RRGGBB)")
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate a .fpa.yaml file")
    c.add_argument("input", type=Path)
    c.add_argument("--strict", action="store_true", help="treat warnings as errors")
    r = sub.add_parser("report", help="build the HTML report")
    r.add_argument("input", type=Path)
    r.add_argument("-o", "--output", type=Path)
    r.add_argument("--lang", default="en", type=lang_tag, help="BCP 47 tag for labels and number formatting (built in: en, pt-BR)")
    r.add_argument("--labels", type=Path, help="JSON file with label overrides (for languages other than en / pt-BR)")
    r.add_argument("--accent", type=hex_color)
    r.add_argument("--accent-dark", type=hex_color)
    r.add_argument("--theme", choices=["light", "dark", "auto"], help="default: report_style.theme from the file, else light")
    args = ap.parse_args(argv)
    return run_check(args.input, args.strict) if args.cmd == "check" else run_report(args)


if __name__ == "__main__":
    sys.exit(main())
