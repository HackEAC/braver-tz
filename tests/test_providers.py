import unittest

from brave_updater.models import ReleaseAsset, SystemInfo
from brave_updater.providers import parse_checksum_text, parse_sha256_digest, pick_asset


class ProviderTests(unittest.TestCase):
    def test_pick_asset_prefers_macos_universal_dmg(self) -> None:
        assets = [
            ReleaseAsset("Brave-Browser-arm64.dmg", "https://github.com/arm64.dmg"),
            ReleaseAsset("Brave-Browser-universal.dmg", "https://github.com/universal.dmg"),
        ]

        asset, reason = pick_asset(assets, SystemInfo("macos", "arm64", "unknown"))

        self.assertEqual(asset.name, "Brave-Browser-universal.dmg")
        self.assertIn("universal", reason)

    def test_pick_asset_prefers_deb_for_debian(self) -> None:
        assets = [
            ReleaseAsset("brave-browser-1.2.3-1.x86_64.rpm", "https://github.com/brave.rpm"),
            ReleaseAsset("brave-browser_1.2.3_amd64.deb", "https://github.com/brave.deb"),
        ]

        asset, reason = pick_asset(assets, SystemInfo("linux", "x64", "debian"))

        self.assertEqual(asset.name, "brave-browser_1.2.3_amd64.deb")
        self.assertIn(".deb", reason)

    def test_parse_sha256_digest(self) -> None:
        digest = parse_sha256_digest("sha256:" + "a" * 64)
        self.assertEqual(digest, "a" * 64)

    def test_parse_checksum_text(self) -> None:
        checksum = parse_checksum_text(
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef  Brave-Browser.dmg",
            "Brave-Browser.dmg",
        )
        self.assertEqual(checksum, "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")


if __name__ == "__main__":
    unittest.main()
