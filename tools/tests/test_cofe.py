import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
COFE = ROOT / "cofe"


class CofeTests(unittest.TestCase):
    def run_cofe(self, *args, uname="Darwin", caffeinate_exit=None):
        with tempfile.TemporaryDirectory() as directory:
            stub_dir = pathlib.Path(directory)
            uname_stub = stub_dir / "uname"
            uname_stub.write_text("#!/bin/sh\nprintf '%s\\n' '" + uname + "'\n")
            uname_stub.chmod(0o755)
            caffeinate_stub = stub_dir / "caffeinate"
            if caffeinate_exit is None:
                caffeinate_stub.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$COFE_ARGV_FILE\"\nexit 0\n")
            else:
                caffeinate_stub.write_text("#!/bin/sh\nexit " + str(caffeinate_exit) + "\n")
            caffeinate_stub.chmod(0o755)
            test_script = stub_dir / "cofe"
            script_text = COFE.read_text()
            script_text = script_text.replace("/usr/bin/uname", "uname")
            script_text = script_text.replace("/usr/bin/caffeinate", str(caffeinate_stub))
            test_script.write_text(script_text)
            test_script.chmod(0o755)
            argv_file = stub_dir / "argv"
            env = os.environ.copy()
            env["PATH"] = str(stub_dir) + os.pathsep + env.get("PATH", "")
            env["COFE_ARGV_FILE"] = str(argv_file)
            result = subprocess.run([str(test_script), *args], text=True, capture_output=True, env=env)
            recorded = argv_file.read_text().strip() if argv_file.exists() else None
            return result, recorded

    def test_help(self):
        result, recorded = self.run_cofe("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("does not keep the display awake", result.stdout)
        self.assertIsNone(recorded)

    def test_extra_arguments_rejected(self):
        for args in (("3600",), ("--help", "extra"), ("-i",)):
            with self.subTest(args=args):
                result, recorded = self.run_cofe(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Usage:", result.stderr)
                self.assertIsNone(recorded)

    def test_non_macos_rejected_before_caffeinate(self):
        result, recorded = self.run_cofe(uname="Linux")
        self.assertEqual(result.returncode, 1)
        self.assertIn("only on macOS", result.stderr)
        self.assertIsNone(recorded)

    def test_execs_absolute_caffeinate_with_only_idle_assertion(self):
        result, recorded = self.run_cofe()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(recorded, "-i")

    def test_propagates_caffeinate_failure(self):
        result, _recorded = self.run_cofe(caffeinate_exit=7)
        self.assertEqual(result.returncode, 7)


if __name__ == "__main__":
    unittest.main()
