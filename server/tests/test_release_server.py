import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from release_server import ReleaseError, ReleaseStore, parse_version, validate_manifest


def manifest(version="0.1.1", channel="stable", min_bootstrap="0.1.0"):
    return {
        "schema": 1,
        "product": "clawos",
        "board": "esp-mosaico",
        "channel": channel,
        "version": version,
        "release_id": f"clawos:esp-mosaico:{version}",
        "entry": "main.lua",
        "min_bootstrap": min_bootstrap,
        "files": [
            {
                "path": "main.lua",
                "url": f"https://updates.example.com/files/esp-mosaico/{version}/main.lua",
                "size": 10,
            }
        ],
    }


class VersionTests(unittest.TestCase):
    def test_numeric_order(self):
        self.assertLess(parse_version("0.1.9"), parse_version("0.1.10"))

    def test_channel_order(self):
        self.assertLess(parse_version("0.2.0-dev.9"), parse_version("0.2.0-beta.1"))
        self.assertLess(parse_version("0.2.0-beta.9"), parse_version("0.2.0-rc.1"))
        self.assertLess(parse_version("0.2.0-rc.9"), parse_version("0.2.0"))

    def test_reject_bad_version(self):
        for value in ["v0.1.0", "0.01.0", "latest", "0.1.0+build.1"]:
            with self.assertRaises(ReleaseError):
                parse_version(value)


class ManifestTests(unittest.TestCase):
    def test_manifest_ok(self):
        validate_manifest(manifest())

    def test_channel_mismatch(self):
        bad = manifest("0.2.0-beta.1", "stable")
        with self.assertRaises(ReleaseError):
            validate_manifest(bad)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ReleaseStore(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def write_release(self, version, channel="stable", min_bootstrap="0.1.0"):
        m = manifest(version, channel, min_bootstrap)
        root = self.store.release_root("esp-mosaico", version)
        root.mkdir(parents=True, exist_ok=True)
        (root / "main.lua").write_text("return {}\n", encoding="utf-8")
        m["files"][0]["size"] = (root / "main.lua").stat().st_size
        (root / "manifest.json").write_text(json.dumps(m), encoding="utf-8")

    def test_latest(self):
        self.write_release("0.1.1")
        self.write_release("0.1.10")
        latest = self.store.latest("esp-mosaico", "stable", "0.1.0", "0.1.0")
        self.assertEqual(latest["version"], "0.1.10")

    def test_bootstrap_filter(self):
        self.write_release("0.1.1", min_bootstrap="0.2.0")
        self.assertIsNone(self.store.latest("esp-mosaico", "stable", "0.1.0", "0.1.0"))


if __name__ == "__main__":
    unittest.main()
