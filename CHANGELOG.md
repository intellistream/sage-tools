# Changelog — isage-tools

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-03-07

### Added

- Initial extraction from `sage.middleware.operators.tools` into standalone package.
- `ArxivPaperSearcher` — HTML-scraper based arXiv search (was `_Searcher_Tool`).
- `ArxivSearcher` — Atom-feed async arXiv search.
- `DuckDuckGoSearcher` — HTML-based DuckDuckGo search (no API key).
- `NatureNewsFetcherTool` — Nature.com news article scraper (was `Nature_News_Fetcher_Tool`).
- `URLTextExtractorTool` — Generic URL to plain-text extractor (was `URL_Text_Extractor_Tool`).
- `ImageCaptioner` — LLM-powered image captioner (optional, requires `isagellm`).
- `TextDetector` — EasyOCR text detector (optional, requires `torch`+`easyocr`; was `text_detector`).
- Backward-compat aliases for all renamed classes.
- Lazy import guard for `torch` in `TextDetector` to avoid import-time crashes.
- `pyproject.toml` with `[vision]`, `[llm]`, and `[mcp]` optional extras.
- **MCP server** (`sage.tools.mcp_server`): exposes all search/extraction tools as
  Model Context Protocol tools so Claude Desktop, VS Code Copilot, Cursor, and
  other MCP clients can call them with zero integration code.
  - Tools: `duckduckgo_search`, `arxiv_search`, `arxiv_paper_search`,
    `url_text_extract`, `nature_news_fetch`
  - Supports `stdio` transport (Claude Desktop / uvx) and `sse` transport (HTTP).
  - `isage-tools-mcp` console_scripts entry-point.
  - Launch: `isage-tools-mcp` or `python -m sage.tools.mcp_server`
