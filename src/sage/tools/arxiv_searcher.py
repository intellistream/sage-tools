"""
Arxiv 论文搜索工具 — Atom-feed based asynchronous search.
"""

import asyncio
import logging
import urllib.parse
from typing import Any

import aiohttp
import feedparser

from sage.libs.foundation.tools.tool import BaseTool

logger = logging.getLogger(__name__)


class ArxivSearcher(BaseTool):
    """arXiv academic paper search tool (Atom API, async)."""

    def __init__(self):
        super().__init__(
            tool_name="arxiv_searcher",
            tool_description="Search Arxiv for academic papers. Returns title, authors, summary, and link.",
            input_types=["str"],
            output_type="list",
            demo_commands=["search for transformer papers", "find papers about LLM agents"],
            require_llm_engine=False,
        )
        self.base_url = "http://export.arxiv.org/api/query"

    async def execute(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute Arxiv search."""
        logger.info(f"Searching Arxiv for: {query}")

        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Arxiv API failed with status {response.status}")
                        return []

                    content = await response.text()

            feed = feedparser.parse(content)

            results = []
            for entry in feed.entries:
                paper = {
                    "title": entry.title.replace("\n", " ").strip(),
                    "authors": [author.name for author in entry.authors],
                    "summary": entry.summary.replace("\n", " ").strip(),
                    "published": entry.published,
                    "link": entry.link,
                    "pdf_link": next(
                        (link.href for link in entry.links if link.title == "pdf"), None
                    ),
                }
                results.append(paper)

            logger.info(f"Found {len(results)} papers")
            return results

        except Exception as e:
            logger.error(f"Arxiv search failed: {e}")
            return []

    def call(self, arguments: dict) -> Any:
        """Sync wrapper for MCP / AgentRuntime."""
        query = arguments.get("query")
        if not query:
            return []

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return asyncio.run(self.execute(query))
        except RuntimeError:
            return asyncio.run(self.execute(query))

        return asyncio.run(self.execute(query))
