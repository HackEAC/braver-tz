import plistlib
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from brave_updater.system import (
    compare_versions,
    normalize_macos_app_version,
    read_linux_version,
    read_macos_version,
    read_windows_version,
)


class FakeResult:
    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self.stdout = stdout
        self.stderr = stderr


class SystemTests(unittest.TestCase):
    def test_compare_versions_treats_missing_patch_as_equal_zero(self) -> None:
        self.assertEqual(compare_versions("1.2.3", "v1.2.3.0"), 0)
        self.assertEqual(compare_versions("1.2.2", "1.2.3"), -1)
        self.assertEqual(compare_versions("1.2.4", "1.2.3"), 1)

    def test_read_macos_version_from_plist(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plist_path = Path(temp_dir) / "Info.plist"
            with plist_path.open("wb") as handle:
                plistlib.dump({"CFBundleShortVersionString": "1.2.3"}, handle)

            version = read_macos_version([plist_path])

        self.assertEqual(version, "1.2.3")

    def test_normalize_macos_app_version_prefers_brave_bundle_version(self) -> None:
        self.assertEqual(
            normalize_macos_app_version("143.1.85.118", "185.118"),
            "1.85.118",
        )

    def test_read_linux_version_uses_binary_output(self) -> None:
        def fake_runner(command, capture_output, text, check):
            self.assertEqual(command, ("brave-browser", "--version"))
            return FakeResult(stdout="Brave Browser 1.2.3")

        version = read_linux_version(commands=[("brave-browser", "--version")], runner=fake_runner, which=lambda _: "/usr/bin/brave-browser")

        self.assertEqual(version, "1.2.3")

    def test_read_windows_version_uses_powershell_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / "brave.exe"
            executable.write_text("stub")

            def fake_runner(command, capture_output, text, check):
                self.assertEqual(command[0], "powershell")
                return FakeResult(stdout="1.2.3.4")

            version = read_windows_version([executable], runner=fake_runner)

        self.assertEqual(version, "1.2.3.4")


if __name__ == "__main__":
    unittest.main()
