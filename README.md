# isage-tools

**SAGE agent-callable data-gathering tools** (L3)

`isage-tools` provides lightweight, composable tool implementations that SAGE
agentic pipelines can call to fetch information from the web, academic databases,
and local images.  Each tool extends `BaseTool` from `isage-libs` (L2).

> **MCP support:** All tools are also served as a [Model Context Protocol](https://modelcontextprotocol.io) server so any MCP-compatible AI client (Claude Desktop, VS Code Copilot, Cursor …) can call them directly — no integration code needed.

## Layer

| | |
|---|---|
| Package | `isage-tools` |
| Import path | `sage.tools` |
| Layer | **L3** |
| Depends on | `isage-libs` (L2) — `BaseTool` interface |

## Available tools

| Class | MCP tool name | Description | Key deps |
|---|---|---|---|
| `ArxivPaperSearcher` | `arxiv_paper_search` | HTML-based arXiv full-text scraper | `requests`, `beautifulsoup4` |
| `ArxivSearcher` | `arxiv_search` | Atom-feed arXiv academic search (async) | `aiohttp`, `feedparser` |
| `DuckDuckGoSearcher` | `duckduckgo_search` | Web search via DuckDuckGo (no API key) | `aiohttp`, `beautifulsoup4` |
| `NatureNewsFetcherTool` | `nature_news_fetch` | Nature.com news article scraper | `requests`, `beautifulsoup4` |
| `URLTextExtractorTool` | `url_text_extract` | Generic URL → plain text extractor | `requests`, `beautifulsoup4` |
| `ImageCaptioner` | — | LLM-powered image captioner *(optional)* | `isagellm` |
| `TextDetector` | — | EasyOCR text detection *(optional)* | `torch`, `easyocr` |

## Installation

```bash
# Base (search + scraping tools)
pip install isage-tools

# With MCP server support
pip install 'isage-tools[mcp]'

# With vision tools (torch + easyocr)
pip install 'isage-tools[vision]'

# Development
pip install -e '.[dev]'
```

## MCP Server

`isage-tools` ships a built-in MCP server so you can use all tools from any
MCP-compatible AI client without writing any integration code.

### Quick launch

```bash
# Requires: pip install 'isage-tools[mcp]'

# stdio (for Claude Desktop, uvx)
isage-tools-mcp
# or:
python -m sage.tools.mcp_server

# SSE / HTTP (for VS Code Copilot, remote use)
isage-tools-mcp --transport sse --port 8765
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "sage-tools": {
      "command": "python",
      "args": ["-m", "sage.tools.mcp_server"]
    }
  }
}
```

Or with `uvx` (no pre-install needed):

```json
{
  "mcpServers": {
    "sage-tools": {
      "command": "uvx",
      "args": ["isage-tools"]
    }
  }
}
```

### VS Code (GitHub Copilot / Continue.dev)

Add to `.vscode/mcp.json` or `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "sage-tools": {
        "type": "sse",
        "url": "http://localhost:8765/sse"
      }
    }
  }
}
```

Then start the server:
```bash
isage-tools-mcp --transport sse --port 8765
```

### Available MCP tools

| Tool | Description |
|---|---|
| `duckduckgo_search` | Web search, no API key, returns title/link/snippet |
| `arxiv_search` | Academic paper search via Atom API |
| `arxiv_paper_search` | arXiv HTML scraper (title + abstract + link) |
| `url_text_extract` | Extract plain text from any URL (up to 10 000 chars) |
| `nature_news_fetch` | Latest articles from Nature.com |

## SAGE Pipeline usage

```python
from sage.tools import ArxivSearcher, DuckDuckGoSearcher, URLTextExtractorTool

# Search arXiv (async)
import asyncio
searcher = ArxivSearcher()
papers = asyncio.run(searcher.execute("SAGE streaming framework", max_results=5))

# DuckDuckGo search (sync wrapper)
duckduckgo = DuckDuckGoSearcher()
results = duckduckgo.call({"query": "SAGE streaming framework", "max_results": 3})

# Extract text from a URL
extractor = URLTextExtractorTool()
text = extractor.execute("https://intellistream.github.io/SAGE-Pub/")
```

## Development setup

```bash
git clone https://github.com/intellistream/sage-tools
cd sage-tools
./quickstart.sh --dev --yes
pytest -v
```

## Backward compatibility

All public classes have backward-compat aliases matching the original names in
`sage.middleware.operators.tools`:

```python
# Old (deprecated — still works via sage-middleware re-export)
from sage.middleware.operators.tools import ArxivSearcher

# New (preferred)
from sage.tools import ArxivSearcher
```

## Note on BochaSearchTool

`BochaSearchTool` (and `EnhancedBochaSearchTool`) are **not** part of
`isage-tools` because they depend on `sage.middleware.operators.context` types
(`ModelContext`, `SearchSession`, etc.).  They remain in
`sage.middleware.operators.tools.searcher_tool`.

---

Part of the [SAGE ecosystem](https://github.com/intellistream/SAGE).
