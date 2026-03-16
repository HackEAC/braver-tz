from pathlib import Path
import unittest
from unittest import mock

from brave_updater.models import ReleaseAsset, ReleaseInfo, SystemInfo
from brave_updater.service import BraveUpdater


class ServiceTests(unittest.TestCase):
    def make_updater(self) -> BraveUpdater:
        with mock.patch("brave_updater.service.resolve_provider", return_value=mock.Mock()):
            return BraveUpdater("github", lambda _: None)

    def make_release(self) -> ReleaseInfo:
        return ReleaseInfo(
            version="v1.2.3",
            name="Release v1.2.3",
            body="Chromium: 120.0.0.1",
            assets=[ReleaseAsset(name="Brave-Browser-universal.dmg", url="https://github.com/example.dmg", digest="sha256:" + "a" * 64)],
            source="github",
        )

    def test_check_reports_up_to_date_when_versions_match(self) -> None:
        updater = self.make_updater()
        system_info = SystemInfo("macos", "arm64", "unknown")
        release = self.make_release()
        asset = release.assets[0]

        with mock.patch.object(updater, "_resolve_target", return_value=(system_info, release, asset, "reason")):
            with mock.patch("brave_updater.service.detect_installed_version", return_value="1.2.3"):
                result = updater.check()

        self.assertFalse(result.update_available)
        self.assertEqual(result.chromium_version, "120.0.0.1")

    def test_download_latest_uses_resolved_hash_and_sanitized_destination(self) -> None:
        updater = self.make_updater()
        release = ReleaseInfo(
            version="v1.2.3",
            name="Release",
            body="",
            assets=[ReleaseAsset(name="../Brave-Browser-universal.dmg", url="https://github.com/example.dmg")],
            source="github",
        )
        system_info = SystemInfo("macos", "arm64", "unknown")
        asset = release.assets[0]

        with mock.patch.object(updater, "_resolve_target", return_value=(system_info, release, asset, "reason")):
            with mock.patch("brave_updater.service.resolve_expected_hash", return_value="b" * 64) as resolve_hash:
                with mock.patch("brave_updater.service.download_file", return_value=Path("/tmp/Brave-Browser-universal.dmg")) as download:
                    result = updater.download_latest(Path("/tmp"))

        resolve_hash.assert_called_once_with(asset, release, updater.log)
        download.assert_called_once()
        self.assertEqual(download.call_args.kwargs["expected_hash"], "b" * 64)
        self.assertEqual(download.call_args.args[1], Path("/tmp/Brave-Browser-universal.dmg"))
        self.assertEqual(result, Path("/tmp/Brave-Browser-universal.dmg"))

    def test_update_noops_when_latest_is_already_installed(self) -> None:
        logs = []
        with mock.patch("brave_updater.service.resolve_provider", return_value=mock.Mock()):
            updater = BraveUpdater("github", logs.append)
        system_info = SystemInfo("macos", "arm64", "unknown")
        release = self.make_release()
        asset = release.assets[0]

        with mock.patch.object(updater, "_resolve_target", return_value=(system_info, release, asset, "reason")):
            with mock.patch("brave_updater.service.detect_installed_version", return_value="1.2.3"):
                with mock.patch("brave_updater.service.download_file") as download:
                    result = updater.update(Path("/tmp"))

        self.assertIsNone(result)
        download.assert_not_called()
        self.assertTrue(any("already up to date" in message for message in logs))

    def test_update_downloads_and_installs_when_confirmed(self) -> None:
        updater = self.make_updater()
        system_info = SystemInfo("macos", "arm64", "unknown")
        release = self.make_release()
        asset = release.assets[0]
        installer = mock.Mock()

        with mock.patch.object(updater, "_resolve_target", return_value=(system_info, release, asset, "reason")):
            with mock.patch("brave_updater.service.detect_installed_version", return_value="1.2.2"):
                with mock.patch("brave_updater.service.resolve_expected_hash", return_value="c" * 64):
                    with mock.patch("brave_updater.service.download_file") as download:
                        with mock.patch("brave_updater.service.get_installer", return_value=installer):
                            result = updater.update(Path("/tmp"), assume_yes=True)

        self.assertEqual(result, Path("/tmp/Brave-Browser-universal.dmg"))
        installer.install.assert_called_once_with(Path("/tmp/Brave-Browser-universal.dmg"))
        self.assertEqual(download.call_args.kwargs["expected_hash"], "c" * 64)

    def test_update_downloads_and_skips_install_when_declined(self) -> None:
        logs = []
        with mock.patch("brave_updater.service.resolve_provider", return_value=mock.Mock()):
            updater = BraveUpdater("github", logs.append)
        system_info = SystemInfo("macos", "arm64", "unknown")
        release = self.make_release()
        asset = release.assets[0]

        with mock.patch.object(updater, "_resolve_target", return_value=(system_info, release, asset, "reason")):
            with mock.patch("brave_updater.service.detect_installed_version", return_value="1.2.2"):
                with mock.patch("brave_updater.service.resolve_expected_hash", return_value=None):
                    with mock.patch("brave_updater.service.download_file") as download:
                        with mock.patch("brave_updater.service.prompt_yes_no", return_value=False):
                            with mock.patch("brave_updater.service.get_installer") as get_installer:
                                result = updater.update(Path("/tmp"))

        self.assertEqual(result, Path("/tmp/Brave-Browser-universal.dmg"))
        download.assert_called_once()
        get_installer.assert_not_called()
        self.assertIn("Install skipped.", logs)

    def test_install_delegates_to_platform_installer(self) -> None:
        updater = self.make_updater()
        installer = mock.Mock()

        with mock.patch("brave_updater.service.detect_system", return_value=SystemInfo("linux", "x64", "debian")):
            with mock.patch("brave_updater.service.get_installer", return_value=installer):
                updater.install(Path("/tmp/brave.deb"))

        installer.install.assert_called_once_with(Path("/tmp/brave.deb"))


if __name__ == "__main__":
    unittest.main()
