"""
arXiv Full-Text Searcher — HTML scraper for arXiv search results.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from sage.libs.foundation.tools import BaseTool


class ArxivPaperSearcher(BaseTool):
    """Search arXiv using its HTML search endpoint (no API key required)."""

    def __init__(self):
        super().__init__(
            tool_name="arxiv_paper_searcher",
            tool_description="A tool that searches arXiv for papers based on a given query.",
            input_types={
                "query": "str - The search query for arXiv papers.",
                "size": "int - The number of results per page (25, 50, 100, or 200). If None, use 25.",
                "max_results": "int - The maximum number of papers to return (default: 25). Should be less than or equal to 100.",
            },
            output_type="list - A list of dictionaries containing paper information.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(query="tool agents with large language models")',
                    "description": "Search for papers about tool agents with large language models.",
                },
                {
                    "command": 'execution = tool.execute(query="quantum computing", size=100, max_results=50)',
                    "description": "Search for quantum computing papers, with 100 results per page, returning a maximum of 50 papers.",
                },
                {
                    "command": 'execution = tool.execute(query="machine learning", max_results=75)',
                    "description": "Search for machine learning papers, returning a maximum of 75 papers.",
                },
            ],
        )
        self.tool_version = "1.0.0"
        self.valid_sizes = [25, 50, 100, 200]
        self.base_url = "https://arxiv.org/search/"

    def build_tool(self):
        """No specific build required for this tool."""
        pass

    def execute(self, query, size=None, max_results=25):
        """
        Execute the arXiv search.

        Parameters:
            query (str): The search query for arXiv papers.
            size (int): The number of results per page.
            max_results (int): The maximum number of papers to return.

        Returns:
            list: A list of dictionaries containing paper information.
        """
        valid_sizes = self.valid_sizes
        base_url = self.base_url

        if size is None:
            size = 25
        elif size not in valid_sizes:
            size = min(valid_sizes, key=lambda x: abs(x - size))

        results = []
        start = 0

        max_results = min(max_results, 100)  # limit to 100 for traffic reasons

        while len(results) < max_results:
            params = {
                "searchtype": "all",
                "query": query,
                "abstracts": "show",
                "order": "",
                "size": str(size),
                "start": str(start),
            }

            try:
                response = requests.get(base_url, params=params)
                soup = BeautifulSoup(response.content, "html.parser")

                papers = soup.find_all("li", class_="arxiv-result")  # type: ignore
                if not papers:
                    break

                for paper in papers:
                    if len(results) >= max_results:
                        break

                    title_elem = paper.find("p", class_="title")  # type: ignore
                    title = title_elem.text.strip() if title_elem else "No title found"

                    authors_elem = paper.find("p", class_="authors")  # type: ignore
                    authors = authors_elem.text.strip() if authors_elem else "No authors found"
                    authors = re.sub(r"^Authors:\s*", "", authors)
                    authors = re.sub(r"\s+", " ", authors).strip()

                    abstract_elem = paper.find("span", class_="abstract-full")  # type: ignore
                    abstract = (
                        abstract_elem.text.strip() if abstract_elem else "No abstract available"
                    )
                    abstract = abstract.replace("△ Less", "").strip()

                    link_elem = paper.find("p", class_="list-title")  # type: ignore
                    link_tag = link_elem.find("a") if isinstance(link_elem, Tag) else None  # type: ignore
                    link = (
                        link_tag["href"]
                        if isinstance(link_tag, Tag) and link_tag.has_attr("href")
                        else "No link found"
                    )

                    results.append(
                        {
                            "title": title,
                            "authors": authors,
                            "abstract": abstract,
                            "link": link,
                        }
                    )

                start += size

            except Exception as e:
                logging.error(f"Error searching arXiv: {e}")
                break

        return results[:max_results]

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata


# Backward-compat alias (original name was a private-looking `_Searcher_Tool`)
_Searcher_Tool = ArxivPaperSearcher


if __name__ == "__main__":
    import json

    tool = ArxivPaperSearcher()
    metadata = tool.get_metadata()
    print("Tool Metadata:", metadata)

    query = "tool agents large language models"
    try:
        execution = tool.execute(query=query, size=50, max_results=5)
        print(json.dumps(execution, indent=4))
    except Exception as e:
        print(f"Execution failed: {e}")
