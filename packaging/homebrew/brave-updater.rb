class BraveUpdater < Formula
  include Language::Python::Virtualenv

  desc "Unofficial CLI to download and update Brave Browser from Brave-controlled release sources"
  homepage "https://github.com/HackEAC/braver-tz"
  version "REPLACE_WITH_VERSION"
  url "https://github.com/HackEAC/braver-tz/releases/download/v#{version}/brave_updater-#{version}.tar.gz"
  sha256 "REPLACE_WITH_SDIST_SHA256"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{bin}/brave-updater --help")
    assert_match "update", output
  end
end
