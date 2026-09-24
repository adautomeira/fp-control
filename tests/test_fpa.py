"""Regression tests for assets/fpa.py — run with: python3 -m unittest discover tests"""
import ast
import contextlib
import copy
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "assets"))
import fpa  # noqa: E402

DEV = ROOT / "examples" / "bookshop.fpa.yaml"
ENH = ROOT / "examples" / "bookshop-enhancement-2026-09-20.fpa.yaml"


def check(data=None, text=None):
    """Run `fpa.py check` on a dict or raw YAML text; return (exit code, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "case.fpa.yaml"
        path.write_text(text if text is not None else "---\n" + yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = fpa.main(["check", str(path)])
        return code, out.getvalue()


def load(path):
    return yaml.safe_load(path.read_text())


class TablesTest(unittest.TestCase):
    def test_eiq_uses_eo_matrix(self):
        # FTR 2, DET 5: EO/EQ matrix → Low; the EI matrix would give Avg
        self.assertEqual(fpa.classify("eiq", 2, 5), ("Low", 3))
        self.assertEqual(fpa.classify("ei", 2, 5), ("Avg", 4))
        self.assertEqual(fpa.classify("eiq", 3, 12), ("Avg", 4))

    def test_boundaries(self):
        self.assertEqual(fpa.classify("ilf", 1, 50), ("Low", 7))
        self.assertEqual(fpa.classify("ilf", 2, 51), ("High", 15))
        self.assertEqual(fpa.classify("eif", 6, 19), ("Avg", 7))
        self.assertEqual(fpa.classify("eo", 4, 20), ("High", 7))
        self.assertEqual(fpa.classify("ei", 0, 16), ("Avg", 4))


class ExamplesTest(unittest.TestCase):
    def test_examples_are_clean(self):
        for path in (DEV, ENH):
            code, out = check(text=path.read_text())
            self.assertEqual(code, 0, out)
            self.assertIn("OK", out)


class DevChecksTest(unittest.TestCase):
    def test_wrong_complexity_is_an_error(self):
        d = load(DEV)
        d["eiq"][1].update(complexity="High", fp=6)   # View Order: FTR 2, DET 12 → Avg/4
        d["ufp"] = 66
        code, out = check(d)
        self.assertEqual(code, 1)
        self.assertIn("View Order", out)

    def test_ufp_total_mismatch(self):
        d = load(DEV)
        d["ufp"] = 65
        code, out = check(d)
        self.assertEqual(code, 1)
        self.assertIn("ufp: stored 65, recomputed 64", out)

    def test_duplicate_id_and_name(self):
        d = load(DEV)
        d["ei"][1]["id"] = "ei-01"
        d["ei"][2]["name"] = "Create Book"
        code, out = check(d)
        self.assertIn("duplicate id 'ei-01'", out)
        self.assertIn("duplicate EI name 'Create Book'", out)

    def test_trailing_document_marker_warns(self):
        code, out = check(text=DEV.read_text() + "---\n")
        self.assertEqual(code, 0)
        self.assertIn("ends with '---'", out)

    def test_afp_rounding(self):
        d = load(DEV)
        d["afp"]["afp"] = 65.92
        code, out = check(d)
        self.assertIn("AFP afp: stored 65.92, recomputed 66", out)

    def test_partial_checkpoint_is_not_an_error(self):
        d = load(DEV)
        for t in ("eo", "eiq"):
            del d[t]
        d.update(status="partial", counted_types=["ilf", "eif", "ei"], ufp=44)
        d.pop("afp"); d.pop("effort")
        code, out = check(d)
        self.assertEqual(code, 0, out)
        self.assertIn("partial count", out)


class EnhChecksTest(unittest.TestCase):
    def test_efp_includes_deletions(self):
        d = load(ENH)
        d["efp"] = 23   # ADD + CHG after + CFP, without DEL — the 1.1 mistake
        code, out = check(d)
        self.assertIn("efp: stored 23, recomputed 28", out)

    def test_legacy_defp_is_explained(self):
        d = load(ENH)
        d["fp_control"] = "1.1"
        d.pop("efp")
        d["defp"] = 20
        for k, rate in (("optimistic", 8), ("typical", 14), ("conservative", 20)):
            d["effort"][k]["total_hours"] = 20 * rate
        code, out = check(d)
        self.assertIn("excluded deletions", out)
        self.assertIn("computed from the 1.1 defp", out)
        self.assertNotIn("ERROR  effort", out)

    def test_del_must_exist_in_baseline(self):
        d = load(ENH)
        d["del"]["eif"][0].update(id="eif-09", name="Ghost Feed")
        code, out = check(d)
        self.assertIn("'Ghost Feed' (eif-09) is not in baseline_functions", out)

    def test_add_duplicating_baseline(self):
        d = load(ENH)
        d["add"]["ei"].append({"id": "ei-07", "name": "Place Order", "ftr": 3, "det": 10, "complexity": "High", "fp": 6})
        code, out = check(d)
        self.assertIn("'Place Order' already exists in the baseline", out)

    def test_updated_functions_required_and_summed(self):
        d = load(ENH)
        broken = copy.deepcopy(d)
        broken["updated_functions"]["ilf"].pop()
        self.assertIn("updated_functions (sum)", check(broken)[1])
        d.pop("updated_functions")
        self.assertIn("updated_functions missing", check(d)[1])

    def test_efp_adjusted(self):
        d = load(ENH)
        d["afp"]["efp_adjusted"] = 28
        self.assertIn("afp.efp_adjusted: stored 28, recomputed 29", check(d)[1])


class ReportTest(unittest.TestCase):
    TEMPLATE = (ROOT / "assets" / "fp-report.html").read_text(encoding="utf-8")

    def build_both(self, src, *opts):
        """Build a report with fpa.sh and fpa.py; return both outputs."""
        with tempfile.TemporaryDirectory() as tmp:
            sh_out, py_out = Path(tmp) / "sh.html", Path(tmp) / "py.html"
            subprocess.run(["bash", str(ROOT / "assets" / "fpa.sh"), "report", str(src), "-o", str(sh_out), *opts],
                           check=True, capture_output=True)
            with contextlib.redirect_stdout(io.StringIO()):
                fpa.main(["report", str(src), "-o", str(py_out), *opts])
            return sh_out.read_text(encoding="utf-8"), py_out.read_text(encoding="utf-8")

    @unittest.skipUnless(shutil.which("bash"), "bash not available")
    def test_bash_and_python_reports_are_identical(self):
        for src in (DEV, ENH):
            for opts in ((), ("--lang", "pt-BR", "--theme", "dark", "--accent", "#0f766e")):
                sh, py = self.build_both(src, *opts)
                self.assertEqual(sh, py, f"{src.name} {opts}")

    @unittest.skipUnless(shutil.which("bash"), "bash not available")
    def test_yaml_is_embedded_unchanged_and_escaped(self):
        original = DEV.read_text().replace("Gift cards", "Gift </ScRiPt> <!-- cards")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "hostile.fpa.yaml"
            src.write_text(original)
            sh, _ = self.build_both(src)
        data = sh[len(self.TEMPLATE):]
        self.assertNotRegex(data, r"(?i)</script(?!>\n)")      # only the block terminators remain
        self.assertNotIn("<!--", data)
        block = data.split('data-role="index" data-name="hostile.fpa.yaml">\n', 1)[1].split("</script>\n", 1)[0]
        # undo the escaping exactly as the template does, and get the original file back
        restored = re.sub(r"<\\(/script)", r"<\1", block, flags=re.I).replace("<\\!--", "<!--")
        self.assertEqual(restored, original)

    @unittest.skipUnless(shutil.which("bash"), "bash not available")
    def test_split_detail_files_are_embedded(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = yaml.safe_load(DEV.read_text())
            for t in ("ilf", "ei"):
                Path(tmp, f"shop.fpa.{t}.yaml").write_text(yaml.safe_dump({"fp_control": "1.2", "system": "Bookshop", "type": t, t: index.pop(t)}))
            index.update(split=True, detail_files={"ilf": "shop.fpa.ilf.yaml", "ei": "shop.fpa.ei.yaml"})
            Path(tmp, "shop.fpa.yaml").write_text("---\n" + yaml.safe_dump(index, sort_keys=False))
            sh, py = self.build_both(Path(tmp, "shop.fpa.yaml"))
        self.assertEqual(sh, py)
        self.assertIn('data-role="detail" data-name="shop.fpa.ilf.yaml"', sh)
        self.assertIn('data-role="detail" data-name="shop.fpa.ei.yaml"', sh)

    def test_template_scripts_cannot_end_early(self):
        # the template's own inline scripts must not contain sequences that end a script element
        for body in re.findall(r"<script>(.*?)</script>", self.TEMPLATE, re.S):
            self.assertNotRegex(body, r"(?i)</script|<!--|<script")

    def test_template_bundles_js_yaml(self):
        self.assertIn("js-yaml 4.1.0", self.TEMPLATE)
        self.assertTrue((ROOT / "assets" / "LICENSE-js-yaml").exists())

    def test_ifpug_tables_match_python(self):
        js = self.TEMPLATE
        for name, (row, rows, cols) in {m: (d["row"], d["rows"], d["cols"]) for m, d in fpa.MATRICES.items()}.items():
            m = re.search(name + r":\s*\{ row: '(\w+)', rows: (\[.*?\]\]), cols: (\[.*?\]\]) \}", js)
            self.assertIsNotNone(m, name)
            js_rows = ast.literal_eval(m.group(2).replace("INF", "1e999"))
            js_cols = ast.literal_eval(m.group(3).replace("INF", "1e999"))
            self.assertEqual(m.group(1), row)
            self.assertEqual([hi for _, hi in js_rows], rows, name)
            self.assertEqual([hi for _, hi in js_cols], cols, name)
        for t, (matrix, key, weights) in fpa.TYPE_INFO.items():
            m = re.search(t + r":\s*\{ m: '(\w+)',\s*key: '(\w+)', w: \{ Low: (\d+), Avg: (\d+), High: (\d+) \} \}", js)
            self.assertIsNotNone(m, t)
            self.assertEqual((m.group(1), m.group(2)), (matrix, key), t)
            self.assertEqual([int(x) for x in m.group(3, 4, 5)], [weights["Low"], weights["Avg"], weights["High"]], t)


if __name__ == "__main__":
    unittest.main()
