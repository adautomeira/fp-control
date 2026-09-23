"""Regression tests for assets/fpa.py — run with: python3 -m unittest discover tests"""
import contextlib
import copy
import io
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
    def test_payload_escapes_script_and_keeps_style(self):
        d = load(DEV)
        d["notes"].append({"date": "2026-09-02", "text": "</script><b>x"})
        d["report_style"] = {"accent": "#0f766e", "theme": "dark"}
        payload = fpa.build_payload(d, "pt-BR", theme=None)
        self.assertNotIn("</script>", payload)
        self.assertIn('"accent": "#0f766e"', payload)
        self.assertIn('"theme": "dark"', payload)
        self.assertIn('"theme": "auto"', fpa.build_payload(d, theme="auto"))


if __name__ == "__main__":
    unittest.main()
