"""Offline regression coverage for the disabled legacy translation command."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "translate_sermons.py"

# Install guards before executing the entry point. The source is compiled before
# the audit hook so the command itself has no reason to open any file at all.
GUARDED_RUNNER = r'''
import builtins
import runpy
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    code = compile(source.read(), sys.argv[1], "exec")
original_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name.split(".")[0] in {"anthropic", "openai", "requests"}:
        raise AssertionError("Optional SDK import attempted: " + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded_import

def audit(event, args):
    if (event == "open" or event.startswith("socket.")
            or event.startswith("subprocess.")
            or event in {"os.system", "os.mkdir", "os.remove", "os.rename",
                         "os.rmdir", "os.truncate", "os.symlink", "os.link"}):
        raise AssertionError("Forbidden side effect: " + event)
sys.addaudithook(audit)
sys.argv = sys.argv[1:]
exec(code, {"__name__": "__main__", "__file__": sys.argv[0]})
'''


class LegacyTranslationTests(unittest.TestCase):
    def test_all_invocations_fail_without_dependencies_network_or_writes(self):
        cases = [[], ["--help"], ["--file", "Example"], ["--batch"],
                 ["--file", "Example", "--backend", "claude"],
                 ["--file", "Example", "--backend", "ollama"]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "Example.md"
            sentinel.write_text("original root-level sermon", encoding="utf-8")
            sermon = root / "sermons" / "Example"
            sermon.mkdir(parents=True)
            (sermon / "transcript.md").write_text("complete source", encoding="utf-8")
            (sermon / "translation.md").write_text("original translation", encoding="utf-8")
            before = {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
            for args in cases:
                with self.subTest(args=args):
                    result = subprocess.run(
                        [sys.executable, "-I", "-S", "-B", "-c", GUARDED_RUNNER,
                         str(SCRIPT), *args], cwd=root, capture_output=True,
                        text=True, timeout=10,
                        env={**os.environ, "ANTHROPIC_API_KEY": "test-not-a-real-key"},
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("deprecated and disabled", result.stderr)
                    self.assertIn("3,000", result.stderr)
                    self.assertIn("sermons/<name>/translation.md", result.stderr)
                    self.assertIn("docs/CONTENT_SOP.md", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    after = {str(p.relative_to(root)): p.read_bytes()
                             for p in root.rglob("*") if p.is_file()}
                    self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
