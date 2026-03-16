from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from brave_updater.installers import (
    LinuxInstaller,
    MacOSInstaller,
    WindowsInstaller,
    _replace_macos_app_bundle,
    get_installer,
)
from brave_updater.models import SystemInfo


class InstallerTests(unittest.TestCase):
    def test_get_installer_returns_platform_specific_adapter(self) -> None:
        self.assertIsInstance(get_installer(SystemInfo("macos", "arm64", "unknown"), lambda _: None), MacOSInstaller)
        self.assertIsInstance(get_installer(SystemInfo("windows", "x64", "unknown"), lambda _: None), WindowsInstaller)
        self.assertIsInstance(get_installer(SystemInfo("linux", "x64", "debian"), lambda _: None), LinuxInstaller)

    def test_get_installer_rejects_unknown_platform(self) -> None:
        with self.assertRaises(RuntimeError):
            get_installer(SystemInfo("plan9", "x64", "unknown"), lambda _: None)

    def test_macos_pkg_install_runs_installer(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "Brave.pkg"
            pkg.write_text("stub")
            logger = mock.Mock()
            installer = MacOSInstaller(logger)

            with mock.patch("subprocess.check_call") as check_call:
                installer.install(pkg)

        check_call.assert_called_once_with(
            ["sudo", "installer", "-pkg", str(pkg), "-target", "/"],
            timeout=600,
        )
        logger.assert_any_call("Install finished.")

    def test_macos_dmg_install_stages_and_moves_app(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dmg = Path(temp_dir) / "Brave.dmg"
            dmg.write_text("stub")
            logger = mock.Mock()
            installer = MacOSInstaller(logger)
            mountpoint = Path("/Volumes/BraveTmpMount")
            app_path = mountpoint / "Brave Browser.app"
            target = Path("/Applications/Brave Browser.app")
            temp_target = Path("/Applications/Brave Browser.app.new")

            def fake_exists(path_obj):
                path = str(path_obj)
                mapping = {
                    str(dmg): True,
                    str(mountpoint): False,
                    str(app_path): True,
                    str(target): False,
                    str(temp_target): False,
                }
                return mapping.get(path, False)

            with mock.patch("pathlib.Path.exists", fake_exists):
                with mock.patch("pathlib.Path.mkdir") as mkdir:
                    with mock.patch("subprocess.check_call") as check_call:
                        with mock.patch("subprocess.run") as run:
                            installer.install(dmg)

        mkdir.assert_called_once()
        self.assertEqual(
            check_call.call_args_list[0].args[0],
            ["hdiutil", "attach", str(dmg), "-mountpoint", str(mountpoint), "-nobrowse", "-quiet"],
        )
        self.assertEqual(
            check_call.call_args_list[-1].args[0],
            ["sudo", "mv", str(temp_target), str(target)],
        )
        run.assert_called_once_with(
            ["hdiutil", "detach", str(mountpoint), "-quiet"],
            timeout=10,
            capture_output=True,
            check=False,
        )

    def test_macos_replace_restores_backup_if_swap_fails(self) -> None:
        target = Path("/Applications/Brave Browser.app")
        temp_target = Path("/Applications/Brave Browser.app.new")
        backup_target = Path("/Applications/Brave Browser.app.old")
        state = {
            str(target): True,
            str(temp_target): True,
            str(backup_target): False,
        }

        def fake_exists(path_obj):
            return state.get(str(path_obj), False)

        def fake_check_call(command, timeout):
            if command == ["sudo", "mv", str(target), str(backup_target)]:
                state[str(target)] = False
                state[str(backup_target)] = True
                return 0
            if command == ["sudo", "mv", str(temp_target), str(target)]:
                raise subprocess.CalledProcessError(1, command)
            if command == ["sudo", "mv", str(backup_target), str(target)]:
                state[str(target)] = True
                state[str(backup_target)] = False
                return 0
            return 0

        with mock.patch("pathlib.Path.exists", fake_exists):
            with mock.patch("subprocess.check_call", side_effect=fake_check_call) as check_call:
                with self.assertRaises(RuntimeError) as error:
                    _replace_macos_app_bundle(target, temp_target)

        self.assertIn("restored the previous Brave app", str(error.exception))
        self.assertIn(mock.call(["sudo", "mv", str(backup_target), str(target)], timeout=60), check_call.call_args_list)

    def test_macos_replace_raises_clear_error_if_restore_also_fails(self) -> None:
        target = Path("/Applications/Brave Browser.app")
        temp_target = Path("/Applications/Brave Browser.app.new")
        backup_target = Path("/Applications/Brave Browser.app.old")
        state = {
            str(target): True,
            str(temp_target): True,
            str(backup_target): False,
        }

        def fake_exists(path_obj):
            return state.get(str(path_obj), False)

        def fake_check_call(command, timeout):
            if command == ["sudo", "mv", str(target), str(backup_target)]:
                state[str(target)] = False
                state[str(backup_target)] = True
                return 0
            if command in (
                ["sudo", "mv", str(temp_target), str(target)],
                ["sudo", "mv", str(backup_target), str(target)],
            ):
                raise subprocess.CalledProcessError(1, command)
            return 0

        with mock.patch("pathlib.Path.exists", fake_exists):
            with mock.patch("subprocess.check_call", side_effect=fake_check_call):
                with self.assertRaises(RuntimeError) as error:
                    _replace_macos_app_bundle(target, temp_target)

        self.assertIn("Backup remains at", str(error.exception))

    def test_windows_install_launches_startfile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exe = Path(temp_dir) / "BraveSetup.exe"
            exe.write_text("stub")
            installer = WindowsInstaller(lambda _: None)

            with mock.patch("os.startfile", create=True) as startfile:
                installer.install(exe)

        startfile.assert_called_once_with(str(exe))

    def test_linux_deb_prefers_apt_get(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "brave.deb"
            pkg.write_text("stub")
            installer = LinuxInstaller(lambda _: None, "debian")

            with mock.patch("shutil.which", side_effect=lambda name: "/usr/bin/apt-get" if name == "apt-get" else None):
                with mock.patch("subprocess.check_call") as check_call:
                    installer.install(pkg)

        check_call.assert_called_once_with(["sudo", "apt-get", "install", "-y", str(pkg)], timeout=600)

    def test_linux_deb_falls_back_to_dpkg(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "brave.deb"
            pkg.write_text("stub")
            installer = LinuxInstaller(lambda _: None, "debian")

            with mock.patch("shutil.which", return_value=None):
                with mock.patch("subprocess.check_call") as check_call:
                    installer.install(pkg)

        check_call.assert_called_once_with(["sudo", "dpkg", "-i", str(pkg)], timeout=600)

    def test_linux_rpm_prefers_dnf_then_yum_then_rpm(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "brave.rpm"
            pkg.write_text("stub")

            installer = LinuxInstaller(lambda _: None, "rhel")
            with mock.patch("shutil.which", side_effect=lambda name: "/usr/bin/dnf" if name == "dnf" else None):
                with mock.patch("subprocess.check_call") as check_call:
                    installer.install(pkg)
            check_call.assert_called_once_with(["sudo", "dnf", "install", "-y", str(pkg)], timeout=600)

            installer = LinuxInstaller(lambda _: None, "rhel")
            with mock.patch("shutil.which", side_effect=lambda name: "/usr/bin/yum" if name == "yum" else None):
                with mock.patch("subprocess.check_call") as check_call:
                    installer.install(pkg)
            check_call.assert_called_once_with(["sudo", "yum", "install", "-y", str(pkg)], timeout=600)

            installer = LinuxInstaller(lambda _: None, "rhel")
            with mock.patch("shutil.which", return_value=None):
                with mock.patch("subprocess.check_call") as check_call:
                    installer.install(pkg)
            check_call.assert_called_once_with(["sudo", "rpm", "-Uvh", str(pkg)], timeout=600)

    def test_linux_installer_rejects_unknown_file_type(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "brave.zip"
            pkg.write_text("stub")
            installer = LinuxInstaller(lambda _: None, "unknown")

            with self.assertRaises(RuntimeError):
                installer.install(pkg)

    def test_linux_installer_rejects_unsupported_distribution_family(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pkg = Path(temp_dir) / "brave.deb"
            pkg.write_text("stub")
            installer = LinuxInstaller(lambda _: None, "arch")

            with mock.patch("subprocess.check_call") as check_call:
                with self.assertRaises(RuntimeError) as error:
                    installer.install(pkg)

        self.assertIn("Unsupported Linux distribution family", str(error.exception))
        check_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
