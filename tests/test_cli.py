from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import unittest
from unittest import mock

from brave_updater import cli
from brave_updater.models import ReleaseAsset, ReleaseInfo, SystemInfo


class CliTests(unittest.TestCase):
    def test_legacy_print_only_outputs_url(self) -> None:
        release = ReleaseInfo(
            version="v1.2.3",
            name="Release v1.2.3",
            body="Chromium: 120.0.0.1",
            assets=[ReleaseAsset(name="Brave-Browser-universal.dmg", url="https://github.com/example.dmg", digest="sha256:" + "a" * 64)],
        )

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with mock.patch("brave_updater.cli.detect_system", return_value=SystemInfo("macos", "arm64", "unknown")):
                with mock.patch("brave_updater.cli.pick_asset", return_value=(release.assets[0], "macOS: chose universal .dmg")):
                    with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
                        updater = updater_cls.return_value
                        updater.load_release.return_value = release
                        exit_code = cli.main(["--print-only"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue().strip(), "https://github.com/example.dmg")
        self.assertIn("Chosen asset", stderr.getvalue())

    def test_update_subcommand_delegates_to_service(self) -> None:
        with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
            exit_code = cli.main(["update", "--dir", "/tmp", "--yes"])

        self.assertEqual(exit_code, 0)
        updater_cls.return_value.update.assert_called_once()

    def test_download_subcommand_delegates_to_service(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
                exit_code = cli.main(["download", "--dir", "/tmp", "--force"])

        self.assertEqual(exit_code, 0)
        updater_cls.return_value.download_latest.assert_called_once()

    def test_install_subcommand_delegates_to_service(self) -> None:
        with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
            exit_code = cli.main(["install", "/tmp/brave.pkg"])

        self.assertEqual(exit_code, 0)
        updater_cls.return_value.install.assert_called_once()

    def test_check_json_emits_machine_readable_output(self) -> None:
        result = mock.Mock(
            system=SystemInfo("linux", "x64", "debian"),
            installed_version="1.2.2",
            latest_version="1.2.3",
            update_available=True,
            selected_asset=ReleaseAsset(name="brave-browser.deb", url="https://github.com/example.deb"),
            selection_reason="Linux Debian-like: chose first available .deb",
            release_source="github",
            chromium_version="120.0.0.1",
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
                updater_cls.return_value.check.return_value = result
                exit_code = cli.main(["check", "--json"])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn('"latest_version": "1.2.3"', output)
        self.assertIn('"update_available": true', output)

    def test_legacy_install_skips_when_prompt_declined(self) -> None:
        release = ReleaseInfo(
            version="v1.2.3",
            name="Release v1.2.3",
            body="",
            assets=[ReleaseAsset(name="Brave-Browser-universal.dmg", url="https://github.com/example.dmg")],
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            with mock.patch("brave_updater.cli.detect_system", return_value=SystemInfo("macos", "arm64", "unknown")):
                with mock.patch("brave_updater.cli.pick_asset", return_value=(release.assets[0], "reason")):
                    with mock.patch("brave_updater.cli.prompt_yes_no", return_value=False):
                        with mock.patch("brave_updater.cli.BraveUpdater") as updater_cls:
                            updater = updater_cls.return_value
                            updater.load_release.return_value = release
                            exit_code = cli.main(["--install", "--dir", "/tmp"])

        self.assertEqual(exit_code, 0)
        updater.download_latest.assert_called_once()
        updater.install.assert_not_called()


if __name__ == "__main__":
    unittest.main()
