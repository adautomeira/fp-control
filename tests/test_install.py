"""Tests for install.sh — run with: python3 -m unittest discover tests

Each test works in a throwaway HOME and a throwaway git setup: a bare "remote" plus two
clones, so being behind origin/main and the post-merge hook can be exercised offline.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKED = ["fp-control.md", "fp-control-html.md", "install.sh", "assets"]


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "git and bash required")
class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.home), NO_COLOR="1",
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        self.env.pop("FP_CONTROL_HOME", None)
        # a remote containing the current working-tree versions of the installable files
        seed = self.tmp / "seed"
        seed.mkdir()
        for name in TRACKED:
            src = ROOT / name
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, seed / name)
        shutil.rmtree(seed / "assets" / "__pycache__", ignore_errors=True)
        self.git(seed, "init", "-q", "-b", "main")
        self.git(seed, "add", "-A")
        self.git(seed, "commit", "-qm", "seed")
        self.git(self.tmp, "clone", "-q", "--bare", str(seed), "remote.git")
        self.a = self.tmp / "A"
        self.b = self.tmp / "B"
        for clone in (self.a, self.b):
            self.git(self.tmp, "clone", "-q", "remote.git", clone.name)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, check=True, capture_output=True, text=True).stdout

    def run_install(self, clone, *args):
        p = subprocess.run(["bash", str(clone / "install.sh"), *args], env=self.env, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def installed(self, rel):
        return self.home / rel

    def test_fresh_status_reports_missing(self):
        code, out = self.run_install(self.a, "status", "--no-fetch")
        self.assertEqual(code, 1)
        self.assertIn("✔ in sync with origin/main", out)
        self.assertIn("not installed", out)

    def test_install_then_up_to_date(self):
        code, out = self.run_install(self.a, "install", "--no-fetch")
        self.assertEqual(code, 0, out)
        for rel in (".claude/commands/fp-control.md", ".claude/commands/fp-control-html.md",
                    ".fp-control/fp-report.html", ".fp-control/fpa.sh", ".fp-control/INSTALLED"):
            self.assertTrue(self.installed(rel).exists(), rel)
        self.assertTrue(os.access(self.installed(".fp-control/fpa.sh"), os.X_OK))
        self.assertTrue((self.a / ".git" / "hooks" / "post-merge").exists())
        code, out = self.run_install(self.a, "status", "--no-fetch")
        self.assertEqual(code, 0, out)
        self.assertIn("Everything up to date", out)

    def test_behind_remote_and_pull_hook(self):
        self.run_install(self.a, "install", "--no-fetch")
        with open(self.b / "fp-control.md", "a") as f:
            f.write("\n<!-- upstream change -->\n")
        self.git(self.b, "commit", "-qam", "upstream change")
        self.git(self.b, "push", "-q", "origin", "HEAD:main")

        code, out = self.run_install(self.a, "status")          # fetches from the local remote
        self.assertEqual(code, 1)
        self.assertIn("1 commit(s) behind origin/main", out)
        self.assertIn("git pull", out)

        pull = subprocess.run(["git", "pull", "-q", "--no-rebase", "origin", "main"], cwd=self.a,
                              env=self.env, capture_output=True, text=True)
        hook_output = pull.stdout + pull.stderr
        self.assertIn("✔ in sync with origin/main", hook_output)
        self.assertIn("1 installed file(s) need an update", hook_output)

        self.run_install(self.a, "install", "--no-fetch")
        self.assertIn("upstream change", self.installed(".claude/commands/fp-control.md").read_text())

    def test_edited_copy_is_kept_unless_forced(self):
        self.run_install(self.a, "install", "--no-fetch")
        target = self.installed(".claude/commands/fp-control-html.md")
        target.write_text(target.read_text() + "\nmy local note\n")
        code, out = self.run_install(self.a, "status", "--no-fetch")
        self.assertIn("edited since install", out)
        self.run_install(self.a, "install", "--no-fetch")
        self.assertIn("my local note", target.read_text())
        self.run_install(self.a, "install", "--no-fetch", "--force")
        self.assertNotIn("my local note", target.read_text())

    def test_foreign_hook_is_left_alone(self):
        hook = self.a / ".git" / "hooks" / "post-merge"
        hook.write_text("#!/bin/sh\necho mine\n")
        code, out = self.run_install(self.a, "install", "--no-fetch")
        self.assertIn("not ours", out)
        self.assertEqual(hook.read_text(), "#!/bin/sh\necho mine\n")

    def test_no_hook_option(self):
        self.run_install(self.a, "install", "--no-fetch", "--no-hook")
        self.assertFalse((self.a / ".git" / "hooks" / "post-merge").exists())

    def test_platforms_and_dest(self):
        (self.home / ".cursor").mkdir()
        dest = self.tmp / "custom"
        self.run_install(self.a, "install", "--no-fetch", "--platform", "cursor", "--dest", str(dest))
        self.assertTrue(self.installed(".cursor/rules/fp-control.mdc").exists())
        self.assertTrue((dest / "fp-control-html.md").exists())
        self.assertFalse(self.installed(".claude/commands/fp-control.md").exists())
        # later runs reuse the recorded platforms
        code, out = self.run_install(self.a, "status", "--no-fetch")
        self.assertIn("fp-control.mdc", out)
        self.assertNotIn(".claude/commands", out)

    def test_no_platform_found(self):
        shutil.rmtree(self.home / ".claude")
        code, out = self.run_install(self.a, "install", "--no-fetch")
        self.assertEqual(code, 2)
        self.assertIn("no supported agent found", out)

    def test_uninstall_keeps_edited_files(self):
        self.run_install(self.a, "install", "--no-fetch")
        edited = self.installed(".claude/commands/fp-control.md")
        edited.write_text("edited\n")
        code, out = self.run_install(self.a, "uninstall")
        self.assertTrue(edited.exists())
        self.assertFalse(self.installed(".fp-control/fp-report.html").exists())
        self.assertFalse((self.a / ".git" / "hooks" / "post-merge").exists())

    def test_not_a_git_checkout(self):
        plain = self.tmp / "plain"
        shutil.copytree(self.a, plain, ignore=shutil.ignore_patterns(".git"))
        code, out = self.run_install(plain, "install")
        self.assertEqual(code, 0, out)
        self.assertIn("not a git checkout", out)


if __name__ == "__main__":
    unittest.main()
