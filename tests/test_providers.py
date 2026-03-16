import unittest
from unittest import mock

from brave_updater.models import ReleaseAsset, SystemInfo
from brave_updater.providers import (
    OfficialReleaseProvider,
    extract_chromium_version,
    parse_checksum_text,
    parse_sha256_digest,
    pick_asset,
    release_from_payload,
    resolve_expected_hash,
    resolve_provider,
)


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

    def test_resolve_provider_uses_official_provider_and_logs(self) -> None:
        logger = mock.Mock()
        provider = resolve_provider("official", logger)

        self.assertIsInstance(provider, OfficialReleaseProvider)
        logger.assert_called_once()

    def test_resolve_provider_rejects_unknown_source(self) -> None:
        with self.assertRaises(ValueError):
            resolve_provider("mirror", lambda _: None)

    def test_release_from_payload_validates_assets(self) -> None:
        with self.assertRaises(ValueError):
            release_from_payload({"tag_name": "v1.2.3", "assets": [{"name": "foo"}]}, source="github")

    def test_resolve_expected_hash_prefers_digest_and_falls_back_to_checksum_sidecar(self) -> None:
        asset = ReleaseAsset("Brave-Browser.dmg", "https://github.com/file.dmg", digest="sha256:" + "a" * 64)
        release = release_from_payload(
            {
                "tag_name": "v1.2.3",
                "name": "Release",
                "body": "",
                "assets": [
                    {"name": "Brave-Browser.dmg", "browser_download_url": "https://github.com/file.dmg", "digest": "sha256:" + "a" * 64},
                    {"name": "Brave-Browser.dmg.sha256", "browser_download_url": "https://github.com/file.dmg.sha256"},
                ],
            },
            source="github",
        )
        self.assertEqual(resolve_expected_hash(asset, release, lambda _: None), "a" * 64)

        asset = ReleaseAsset("Brave-Browser.dmg", "https://github.com/file.dmg")
        with mock.patch(
            "brave_updater.providers.http_get_text",
            return_value="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb  Brave-Browser.dmg",
        ):
            checksum = resolve_expected_hash(asset, release, lambda _: None)
        self.assertEqual(checksum, "b" * 64)

    def test_extract_chromium_version_returns_none_when_missing(self) -> None:
        self.assertIsNone(extract_chromium_version("No chromium metadata here"))

    def test_resolve_expected_hash_returns_none_without_digest_or_checksum_asset(self) -> None:
        asset = ReleaseAsset("Brave-Browser.dmg", "https://github.com/file.dmg")
        release = release_from_payload(
            {
                "tag_name": "v1.2.3",
                "name": "Release",
                "body": "",
                "assets": [
                    {"name": "Brave-Browser.dmg", "browser_download_url": "https://github.com/file.dmg"},
                ],
            },
            source="github",
        )
        self.assertIsNone(resolve_expected_hash(asset, release, lambda _: None))


if __name__ == "__main__":
    unittest.main()
