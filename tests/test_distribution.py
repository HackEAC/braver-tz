from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from brave_updater.distribution import (
    release_asset_url,
    render_homebrew_formula,
    render_scoop_manifest,
    sha256_for_file,
    source_distribution_name,
    windows_distribution_name,
    write_distribution_files,
)


class DistributionTests(unittest.TestCase):
    def test_release_asset_url_uses_tagged_release_assets(self) -> None:
        url = release_asset_url("HackEAC/braver-tz", "1.1.0", "artifact.zip")
        self.assertEqual(url, "https://github.com/HackEAC/braver-tz/releases/download/v1.1.0/artifact.zip")

    def test_render_homebrew_formula_uses_release_sdist(self) -> None:
        formula = render_homebrew_formula("1.1.0", "HackEAC/braver-tz", "a" * 64)

        self.assertIn('version "1.1.0"', formula)
        self.assertIn(source_distribution_name("1.1.0"), formula)
        self.assertIn("releases/download/v1.1.0", formula)
        self.assertIn('"{}"'.format("a" * 64), formula)

    def test_render_scoop_manifest_uses_windows_zip(self) -> None:
        manifest = render_scoop_manifest("1.1.0", "HackEAC/braver-tz", "b" * 64)

        self.assertIn('"version": "1.1.0"', manifest)
        self.assertIn(windows_distribution_name(), manifest)
        self.assertIn('"hash": "{}"'.format("b" * 64), manifest)
        self.assertIn('"bin": "brave-updater.exe"', manifest)

    def test_write_distribution_files_writes_expected_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "release-manifests"
            written = write_distribution_files(
                output_dir=output_dir,
                version="1.1.0",
                repository="HackEAC/braver-tz",
                source_sha256="c" * 64,
                windows_sha256="d" * 64,
            )

            self.assertTrue(written["homebrew"].exists())
            self.assertTrue(written["scoop"].exists())
            self.assertIn("BraveUpdater < Formula", written["homebrew"].read_text())
            self.assertIn('"version": "1.1.0"', written["scoop"].read_text())

    def test_sha256_for_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "payload.txt"
            path.write_text("brave-updater")

            self.assertEqual(
                sha256_for_file(path),
                "2032a3e6e499399ad94754846dd1e72979bba185ac8318e2729fd3e3c7f2f10c",
            )


if __name__ == "__main__":
    unittest.main()
