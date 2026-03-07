"""
sage.tools MCP Server
=====================

Exposes SAGE data-gathering tools as a Model Context Protocol (MCP) server.
AI assistants (Claude Desktop, VS Code Copilot, Cursor, etc.) can call these
tools directly without any additional integration code.

Available tools exposed over MCP
----------------------------------
- ``duckduckgo_search``      — web search (no API key)
- ``arxiv_search``           — academic paper search (Atom API)
- ``arxiv_paper_search``     — arXiv HTML full-text scraper
- ``bocha_search``           — Bocha API web search (requires BOCHA_API_KEY)
- ``url_text_extract``       — extract plain text from any URL
- ``nature_news_fetch``      — fetch latest Nature.com news articles

Usage
-----
stdio (default, works with Claude Desktop / uvx)::

    python -m sage.tools.mcp_server
    # or via uvx after publishing to PyPI:
    uvx isage-tools

SSE / HTTP (for VS Code MCP extension, remote access)::

    python -m sage.tools.mcp_server --transport sse --port 8765

Claude Desktop config (``claude_desktop_config.json``)::

    {
      "mcpServers": {
        "sage-tools": {
          "command": "python",
          "args": ["-m", "sage.tools.mcp_server"]
        }
      }
    }

VS Code settings (``settings.json``)::

    "mcp": {
      "servers": {
        "sage-tools": {
          "type": "sse",
          "url": "http://localhost:8765/sse"
        }
      }
    }
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_mcp():
    """Lazy import FastMCP — only needed when running the server."""
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]
    except ImportError as e:
        raise ImportError(
            "mcp package is required to run the SAGE Tools MCP server.\n"
            "Install with: pip install 'isage-tools[mcp]'  or  pip install mcp"
        ) from e
    return FastMCP


# ---------------------------------------------------------------------------
# Plugin registration — called by sage-mcp aggregator via entry_points
# ---------------------------------------------------------------------------

def register_tools(mcp: Any) -> None:
    """Register all sage.tools MCP tools onto the given FastMCP instance.

    This function is the entry-point for the ``sage.mcp.tools`` plugin group.
    The ``sage-mcp`` aggregator discovers and calls it automatically when
    ``isage-tools`` is installed.

    Example (manual use)::

        from mcp.server.fastmcp import FastMCP
        from sage.tools.mcp_server import register_tools

        mcp = FastMCP("my-server")
        register_tools(mcp)
        mcp.run()
    """
    # ── DuckDuckGo search ──────────────────────────────────────────────────
    @mcp.tool()
    async def duckduckgo_search(
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the web via DuckDuckGo (no API key required).

        Args:
            query:       Search query text.
            max_results: Number of results to return (1–20, default 5).

        Returns:
            List of dicts with keys: title, link, content, source.
        """
        from sage.tools.duckduckgo_searcher import DuckDuckGoSearcher

        tool = DuckDuckGoSearcher()
        return await tool.execute(query, max_results=max_results)

    # ── Arxiv atom-feed search ─────────────────────────────────────────────
    @mcp.tool()
    async def arxiv_search(
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search arXiv for academic papers using the Atom API.

        Args:
            query:       Search query (e.g. "streaming vector database").
            max_results: Number of papers to return (default 5).

        Returns:
            List of dicts with keys: title, authors, summary, published,
            link, pdf_link.
        """
        from sage.tools.arxiv_searcher import ArxivSearcher

        tool = ArxivSearcher()
        return await tool.execute(query, max_results=max_results)

    # ── Arxiv HTML full-text scraper ──────────────────────────────────────
    @mcp.tool()
    def arxiv_paper_search(
        query: str,
        max_results: int = 10,
        size: int = 25,
    ) -> list[dict[str, Any]]:
        """Search arXiv papers using the HTML search page (richer metadata).

        Returns title, authors, abstract, and link for each paper.

        Args:
            query:       Search query.
            max_results: Maximum papers to return (capped at 100, default 10).
            size:        Results per page: 25, 50, 100, or 200 (default 25).

        Returns:
            List of dicts with keys: title, authors, abstract, link.
        """
        from sage.tools.arxiv_paper_searcher import ArxivPaperSearcher

        tool = ArxivPaperSearcher()
        return tool.execute(query, size=size, max_results=max_results)

    # ── URL text extractor ─────────────────────────────────────────────────
    @mcp.tool()
    def url_text_extract(url: str) -> dict[str, str]:
        """Extract all readable text from a URL (up to 10 000 characters).

        Handles arXiv PDF links by redirecting to the abstract page.

        Args:
            url: Any HTTP/HTTPS URL.

        Returns:
            Dict with keys: url (str), extracted_text (str).
        """
        from sage.tools.url_text_extractor import URLTextExtractorTool

        tool = URLTextExtractorTool()
        return tool.execute(url)

    # ── Nature news fetcher ────────────────────────────────────────────────
    @mcp.tool()
    def nature_news_fetch(
        num_articles: int = 10,
        max_pages: int = 2,
    ) -> list[dict[str, Any]]:
        """Fetch the latest news articles from Nature.com.

        Args:
            num_articles: Number of articles to return (default 10).
            max_pages:    Maximum pages to scrape (default 2).

        Returns:
            List of dicts with keys: title, url, description, authors,
            date, image_url.
        """
        from sage.tools.nature_news_fetcher import NatureNewsFetcherTool

        tool = NatureNewsFetcherTool()
        tool.sleep_time = 0  # no sleep inside MCP server — caller controls rate
        return tool.execute(num_articles=num_articles, max_pages=max_pages)

    # ── Bocha search ───────────────────────────────────────────────────────
    @mcp.tool()
    def bocha_search(
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Search the web via the Bocha Search API (requires BOCHA_API_KEY).

        Args:
            query:       Search query text.
            max_results: Number of results to return (1–20, default 5).

        Returns:
            List of dicts with keys: title, snippet, url, rank.
            Returns an empty list when BOCHA_API_KEY is not set.
        """
        import os

        if not os.getenv("BOCHA_API_KEY"):
            logger.warning(
                "bocha_search: BOCHA_API_KEY is not set — returning empty results."
            )
            return []

        from sage.tools.bocha_searcher import BochaSearcher

        tool = BochaSearcher()
        return tool.execute(query, max_results=max_results)


# ---------------------------------------------------------------------------
# Build the standalone server (wraps register_tools)
# ---------------------------------------------------------------------------

def _build_server():
    FastMCP = _get_mcp()
    mcp = FastMCP(
        "sage-tools",
        description=(
            "SAGE data-gathering tools: web search (DuckDuckGo + Bocha), "
            "academic paper search, URL text extraction, and news fetching."
        ),
    )
    register_tools(mcp)
    return mcp


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    """CLI entry-point for the SAGE Tools MCP server."""
    parser = argparse.ArgumentParser(
        prog="isage-tools-mcp",
        description="SAGE Tools MCP Server — exposes SAGE data-gathering tools over MCP.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode: 'stdio' (Claude Desktop / uvx) or 'sse' (HTTP).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port number for SSE transport (default: 8765).",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE transport (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    server = _build_server()

    if args.transport == "stdio":
        logger.info("Starting SAGE Tools MCP server (stdio transport)...")
        server.run(transport="stdio")
    else:
        logger.info(
            "Starting SAGE Tools MCP server (SSE transport) on %s:%s ...",
            args.host,
            args.port,
        )
        server.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
