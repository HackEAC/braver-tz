from pathlib import Path
import unittest

from brave_updater import __version__
from brave_updater.network import USER_AGENT


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_pyproject_uses_dynamic_version_from_package(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text()

        self.assertIn('dynamic = ["version"]', pyproject)
        self.assertIn('version = {attr = "brave_updater.__version__"}', pyproject)

    def test_setup_py_defers_metadata_to_pyproject(self) -> None:
        setup_py = (ROOT / "setup.py").read_text()

        self.assertIn("setup()", setup_py)
        self.assertNotIn("version=", setup_py)

    def test_network_user_agent_tracks_package_version(self) -> None:
        self.assertEqual(USER_AGENT, "brave-updater/{}".format(__version__))


if __name__ == "__main__":
    unittest.main()
