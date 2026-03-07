"""
Bocha web search tool — requires BOCHA_API_KEY.

Wraps the Bocha Search API (https://api.bochasearch.com) as a standalone
:class:`BaseTool` so it can be used independently of SAGE streaming pipelines
or exposed as an MCP skill.

Usage::

    from sage.tools import BochaSearcher

    tool = BochaSearcher(api_key="<your-key>")          # or set BOCHA_API_KEY env
    results = tool.call({"query": "SAGE streaming framework", "max_results": 3})
    for r in results:
        print(r["title"], r["url"])

MCP exposure
------------
Registered via the ``sage.mcp.tools`` entry-point so it is automatically
available when running::

    python -m sage.tools.mcp_server
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import requests

from sage.libs.foundation.tools.tool import BaseTool

logger = logging.getLogger(__name__)

_DEFAULT_API_URL = "https://api.bochasearch.com/search"


class BochaSearcher(BaseTool):
    """Bocha web-search tool.

    Calls the Bocha Search API and returns a list of web-page results, each
    represented as a plain dictionary with keys ``title``, ``snippet``,
    ``url``, and ``rank``.

    Args:
        api_key: Bocha API key. Falls back to the ``BOCHA_API_KEY`` environment
            variable when *None*.
        api_url: Override the Bocha endpoint (useful for on-prem deployments).
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = _DEFAULT_API_URL,
        timeout: int = 30,
    ):
        super().__init__(
            tool_name="bocha_search",
            tool_description=(
                "Search the web via the Bocha Search API. "
                "Returns a list of {title, snippet, url, rank} dicts. "
                "Requires a BOCHA_API_KEY."
            ),
            input_types={
                "query": "str - search query",
                "max_results": "int - maximum number of results to return (default 5)",
            },
            output_type="list[dict]",
            demo_commands=[
                "search for large language model benchmarks",
                "find recent papers on retrieval-augmented generation",
            ],
            require_llm_engine=False,
        )

        self._api_key = api_key or os.getenv("BOCHA_API_KEY")
        if not self._api_key:
            raise ValueError(
                "BochaSearcher requires an API key. "
                "Pass api_key= or set the BOCHA_API_KEY environment variable."
            )

        self._api_url = api_url
        self._timeout = timeout
        self._headers = {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # BaseTool interface
    # ------------------------------------------------------------------

    def execute(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute a Bocha web search.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return (capped at 20).

        Returns:
            List of result dicts with keys ``title``, ``snippet``, ``url``,
            ``rank``.  Returns an empty list on error.
        """
        max_results = min(max(1, max_results), 20)
        raw = self._call_api(query, count=max(10, max_results * 2))
        return self._parse_response(raw, max_results=max_results)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_api(self, query: str, count: int = 10) -> dict[str, Any]:
        """Call the Bocha Search API and return the raw JSON response."""
        payload = json.dumps(
            {
                "query": query,
                "summary": True,
                "count": count,
                "page": 1,
            }
        )

        t0 = time.monotonic()
        try:
            resp = requests.post(
                self._api_url,
                headers=self._headers,
                data=payload,
                timeout=self._timeout,
            )
            resp.raise_for_status()
            result: dict[str, Any] = resp.json()
            result["_latency_ms"] = int((time.monotonic() - t0) * 1000)
            return result
        except requests.RequestException as exc:
            logger.error("Bocha API request failed for '%s': %s", query, exc)
            return {"error": str(exc), "_latency_ms": int((time.monotonic() - t0) * 1000)}
        except json.JSONDecodeError as exc:
            logger.error("Bocha API JSON decode failed for '%s': %s", query, exc)
            return {
                "error": "JSON decode error",
                "_latency_ms": int((time.monotonic() - t0) * 1000),
            }

    def _parse_response(self, raw: dict[str, Any], max_results: int) -> list[dict[str, Any]]:
        """Convert raw Bocha API response to a list of result dicts."""
        if "error" in raw:
            logger.warning("Bocha search returned an error: %s", raw["error"])
            return []

        pages: list[dict] = raw.get("data", {}).get("webPages", {}).get("value", [])

        results: list[dict[str, Any]] = []
        for rank, page in enumerate(pages[:max_results], start=1):
            results.append(
                {
                    "title": page.get("name", "").strip(),
                    "snippet": page.get("snippet", "").strip(),
                    "url": page.get("url", "").strip(),
                    "rank": rank,
                }
            )

        return results
