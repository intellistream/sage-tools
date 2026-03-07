"""Smoke tests for sage.tools — verify imports and instantiation without network."""

import pytest


def test_import_package():
    """Package imports cleanly."""
    import sage.tools as tools

    assert tools.__version__ == "0.1.0"


def test_arxiv_paper_searcher_init():
    from sage.tools import ArxivPaperSearcher

    tool = ArxivPaperSearcher()
    assert tool.tool_name == "arxiv_paper_searcher"
    meta = tool.get_metadata()
    assert meta["name"] == "arxiv_paper_searcher"


def test_arxiv_searcher_init():
    from sage.tools import ArxivSearcher

    tool = ArxivSearcher()
    assert tool.tool_name == "arxiv_searcher"


def test_duckduckgo_searcher_init():
    from sage.tools import DuckDuckGoSearcher

    tool = DuckDuckGoSearcher()
    assert tool.tool_name == "duckduckgo_search"


def test_nature_news_fetcher_init():
    from sage.tools import NatureNewsFetcherTool

    tool = NatureNewsFetcherTool()
    assert tool.tool_name == "nature_news_fetcher"


def test_url_text_extractor_init():
    from sage.tools import URLTextExtractorTool

    tool = URLTextExtractorTool()
    assert tool.tool_name == "url_text_extractor"


def test_backward_compat_aliases():
    """Old middleware-style class names are still importable."""
    from sage.tools.arxiv_paper_searcher import _Searcher_Tool
    from sage.tools.nature_news_fetcher import Nature_News_Fetcher_Tool
    from sage.tools.text_detector import text_detector
    from sage.tools.url_text_extractor import URL_Text_Extractor_Tool

    assert _Searcher_Tool is not None
    assert Nature_News_Fetcher_Tool is not None
    assert text_detector is not None
    assert URL_Text_Extractor_Tool is not None


@pytest.mark.network
def test_url_extractor_basic(monkeypatch):
    """URL extractor returns expected structure (mocked HTTP)."""
    from unittest.mock import MagicMock, patch

    mock_response = MagicMock()
    mock_response.content = b"<html><body><p>Hello world</p></body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("requests.get", return_value=mock_response):
        from sage.tools import URLTextExtractorTool

        tool = URLTextExtractorTool()
        result = tool.execute("https://example.com")

    assert "url" in result
    assert "extracted_text" in result
    assert "Hello world" in result["extracted_text"]


@pytest.mark.asyncio
@pytest.mark.network
async def test_duckduckgo_no_network(monkeypatch):
    """DuckDuckGo searcher returns empty list on connection failure."""
    from unittest.mock import AsyncMock, MagicMock, patch

    import aiohttp

    with patch(
        "aiohttp.ClientSession.post",
        side_effect=aiohttp.ClientConnectionError("no network"),
    ):
        from sage.tools import DuckDuckGoSearcher

        tool = DuckDuckGoSearcher()
        results = await tool.execute("test query", max_results=3)

    assert results == []
