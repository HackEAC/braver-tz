class BraveUpdater < Formula
  include Language::Python::Virtualenv

  desc "Unofficial CLI to download and update Brave Browser from Brave-controlled release sources"
  homepage "https://github.com/HackEAC/braver-tz"
  url "https://github.com/HackEAC/braver-tz/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_SHA256"
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
