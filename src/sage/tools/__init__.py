"""
sage.tools — Agent-callable data-gathering tools (L3)

Provides lightweight, composable search / extraction tools that can be called
from SAGE agentic pipelines.  Each tool extends ``BaseTool`` exported by
``sage.libs.foundation.tools``.

Available tools
---------------
- ``ArxivPaperSearcher``    — HTML-based arXiv full-text scraper
- ``ArxivSearcher``         — Atom-feed arXiv search (async)
- ``BochaSearcher``         — Bocha API web search (requires BOCHA_API_KEY)
- ``DuckDuckGoSearcher``    — HTML-based DuckDuckGo search (no API key)
- ``NatureNewsFetcherTool`` — Nature.com news article scraper
- ``URLTextExtractorTool``  — Generic URL → plain-text extractor
- ``ImageCaptioner``        — LLM-powered image captioner (requires isagellm)
- ``TextDetector``          — EasyOCR text detector (requires torch + easyocr)

MCP Server
----------
All tools above are also exposed as an MCP server so any MCP-compatible
AI client (Claude Desktop, VS Code Copilot, Cursor …) can call them directly::

    # stdio (Claude Desktop / uvx)
    python -m sage.tools.mcp_server

    # HTTP/SSE (VS Code, remote)
    python -m sage.tools.mcp_server --transport sse --port 8765

    # after: pip install 'isage-tools[mcp]'
    isage-tools-mcp

Usage::

    from sage.tools import ArxivSearcher, DuckDuckGoSearcher
    searcher = DuckDuckGoSearcher()
    results = searcher.call({"query": "SAGE streaming framework"})
"""

from sage.tools._version import __version__
from sage.tools.arxiv_paper_searcher import ArxivPaperSearcher
from sage.tools.arxiv_searcher import ArxivSearcher
from sage.tools.bocha_searcher import BochaSearcher
from sage.tools.duckduckgo_searcher import DuckDuckGoSearcher
from sage.tools.nature_news_fetcher import NatureNewsFetcherTool
from sage.tools.url_text_extractor import URLTextExtractorTool

# Optional heavy tools — avoid import-time crashes when deps are missing
try:
    from sage.tools.image_captioner import ImageCaptioner

    _HAS_IMAGE_CAPTIONER = True
except ImportError:
    _HAS_IMAGE_CAPTIONER = False
    ImageCaptioner = None  # type: ignore[assignment,misc]

try:
    from sage.tools.text_detector import TextDetector

    _HAS_TEXT_DETECTOR = True
except ImportError:
    _HAS_TEXT_DETECTOR = False
    TextDetector = None  # type: ignore[assignment,misc]

__all__ = [
    "__version__",
    # Always available
    "ArxivPaperSearcher",
    "ArxivSearcher",
    "BochaSearcher",
    "DuckDuckGoSearcher",
    "NatureNewsFetcherTool",
    "URLTextExtractorTool",
    # Optional (vision extras)
    "ImageCaptioner",
    "TextDetector",
]
