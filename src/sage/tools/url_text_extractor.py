"""
URL Text Extractor — generic URL to plain-text extraction tool.
"""

import os

import requests
from bs4 import BeautifulSoup

from sage.libs.foundation.tools.tool import BaseTool


class URLTextExtractorTool(BaseTool):
    """Extract all visible text from a given URL."""

    def __init__(self):
        super().__init__(
            tool_name="url_text_extractor",
            tool_description="A tool that extracts all text from a given URL.",
            input_types={
                "url": "str - The URL from which to extract text.",
            },
            output_type="dict - A dictionary containing the extracted text and any error messages.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(url="https://example.com")',
                    "description": "Extract all text from the example.com website.",
                },
                {
                    "command": 'execution = tool.execute(url="https://en.wikipedia.org/wiki/Python_(programming_language)")',
                    "description": "Extract all text from the Wikipedia page about Python programming language.",
                },
            ],
        )
        self.tool_version = "1.0.0"

    def extract_text_from_url(self, url):
        """Extract all text from the given URL."""
        url = url.replace("arxiv.org/pdf", "arxiv.org/abs")

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            text = text[:10000]  # limit to 10 000 characters
            return text
        except requests.RequestException as e:
            return f"Error fetching URL: {str(e)}"
        except Exception as e:
            return f"Error extracting text: {str(e)}"

    def execute(self, url):
        extracted_text = self.extract_text_from_url(url)
        return {"url": url, "extracted_text": extracted_text}

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata


# Backward-compat alias
URL_Text_Extractor_Tool = URLTextExtractorTool


if __name__ == "__main__":
    import json

    tool = URLTextExtractorTool()
    url = "https://intellistream.github.io/SAGE-Pub/get_start/install/"
    try:
        execution = tool.execute(url=url)
        print(json.dumps(execution, indent=4))
    except ValueError as e:
        print(f"Execution failed: {e}")

    print("Done!")
