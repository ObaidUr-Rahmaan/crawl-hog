class Crawlhog < Formula
  include Language::Python::Virtualenv

  desc "A robust documentation web scraper"
  homepage "https://github.com/yourusername/crawlhog"
  url "https://github.com/yourusername/crawlhog/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "UPDATE_WITH_ACTUAL_SHA" # You'll need to update this after creating the release
  license "MIT"

  depends_on "python@3.11"

  resource "click" do
    url "https://files.pythonhosted.org/packages/click/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  resource "firecrawl-py" do
    url "https://files.pythonhosted.org/packages/firecrawl-py/firecrawl-py-1.11.0.tar.gz"
    sha256 "UPDATE_WITH_ACTUAL_SHA" # You'll need to update this
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/python-dotenv/python_dotenv-1.0.0.tar.gz"
    sha256 "a8df96034aae6d2d50a4ebe8216326c61c3eb64836776504fcca410e5937a3ba"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "CrawlHog", shell_output("#{bin}/chog --help")
  end
end 