import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("spillcheck.py").resolve()


class SpillcheckTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def run_tool(self, program, *options):
        return subprocess.run(
            [
                sys.executable, str(SCRIPT), "-C", str(self.root), *options,
                "--", sys.executable, "-c", program,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_reports_additions_edits_and_deletions(self):
        (self.root / ".gitignore").write_text("debug.log\n", encoding="utf-8")
        (self.root / "edited.txt").write_bytes(b"old")
        (self.root / "removed.txt").touch()

        result = self.run_tool(
            "from pathlib import Path as P; "
            "P('debug.log').touch(); P('edited.txt').write_bytes(b'new'); "
            "P('removed.txt').unlink()"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("+ 'debug.log'", result.stderr)
        self.assertIn("~ 'edited.txt'", result.stderr)
        self.assertIn("- 'removed.txt'", result.stderr)

    def test_allow_matches_paths_not_string_prefixes(self):
        result = self.run_tool(
            "from pathlib import Path as P; "
            "P('dist').mkdir(); P('dist/app.txt').touch(); "
            "P('dist-other.txt').touch(); "
            "P('cache').mkdir(); P('cache/hidden.txt').touch()",
            "--allow", "dist", "--ignore", "cache",
        )

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("+ 'dist/app.txt'\n", result.stderr)
        self.assertIn("+ 'dist-other.txt'  [outside allowlist]", result.stderr)
        self.assertNotIn("hidden.txt", result.stderr)

    def test_allowed_change_passes(self):
        result = self.run_tool(
            "from pathlib import Path; Path('report.txt').touch()",
            "--allow", "report.txt",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preserves_child_failure_and_stdout(self):
        result = self.run_tool(
            "from pathlib import Path; Path('unexpected.txt').touch(); "
            "print('child output'); raise SystemExit(7)",
            "--allow", "dist",
        )

        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(result.stdout, "child output\n")
        self.assertIn("[outside allowlist]", result.stderr)


if __name__ == "__main__":
    unittest.main()
