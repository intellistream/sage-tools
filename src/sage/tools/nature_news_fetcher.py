"""
Nature.com news article scraper.
"""

import logging
import os
import random
import time

import requests
from bs4 import BeautifulSoup, Tag

from sage.libs.foundation.tools import BaseTool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class NatureNewsFetcherTool(BaseTool):
    """Fetch the latest news articles from Nature.com."""

    def __init__(self):
        super().__init__(
            tool_name="nature_news_fetcher",
            tool_description="A tool that fetches the latest news articles from Nature.",
            input_types={
                "num_articles": "int - The number of articles to fetch (default: 100).",
                "max_pages": "int - The maximum number of pages to fetch (default: 5).",
            },
            output_type="list - A list of dictionaries containing information about the latest Nature news articles.",
            demo_commands=[
                {
                    "command": "execution = tool.execute()",
                    "description": "Fetch the latest 100 news articles from Nature.",
                },
                {
                    "command": "execution = tool.execute(num_articles=50, max_pages=3)",
                    "description": "Fetch the latest 50 news articles from Nature, searching up to 3 pages.",
                },
            ],
        )
        self.tool_version = "1.0.0"
        self.base_url = "https://www.nature.com/nature/articles"
        # 控制每次抓取后的等待时间，可在测试中覆盖
        self.sleep_time = 1

    def fetch_page(self, page_number):
        """Fetch a single page of news articles from Nature's website."""
        params = {
            "searchType": "journalSearch",
            "sort": "PubDate",
            "type": "news",
            "page": str(page_number),
        }
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        headers = {"User-Agent": random.choice(user_agents)}
        response = requests.get(self.base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.text

    def parse_articles(self, html_content):
        """Parse HTML content and extract article information."""
        soup = BeautifulSoup(html_content, "html.parser")
        articles_section = soup.find("section", id="new-article-list")
        if not isinstance(articles_section, Tag):
            return []

        articles = []
        for article in articles_section.find_all("article", class_="c-card"):  # type: ignore
            if not isinstance(article, Tag):
                continue

            title_elem = article.find("h3", class_="c-card__title")  # type: ignore
            title = title_elem.text.strip() if isinstance(title_elem, Tag) else "No title found"
            url_elem = title_elem.find("a") if isinstance(title_elem, Tag) else None  # type: ignore
            url = (
                "https://www.nature.com" + str(url_elem["href"])
                if isinstance(url_elem, Tag) and url_elem.has_attr("href")
                else "No URL found"
            )

            description_elem = article.find("div", {"data-test": "article-description"})  # type: ignore
            description = (
                description_elem.text.strip()
                if isinstance(description_elem, Tag)
                else "No description available"
            )

            authors_elem = article.find("ul", {"data-test": "author-list"})  # type: ignore
            authors = (
                [
                    author.text.strip()
                    for author in authors_elem.find_all("li")
                    if isinstance(author, Tag)
                ]
                if isinstance(authors_elem, Tag)
                else ["No authors found"]
            )

            date_elem = article.find("time")  # type: ignore
            date = (
                date_elem["datetime"]
                if isinstance(date_elem, Tag) and date_elem.has_attr("datetime")
                else "No date found"
            )

            image_elem = article.find("img")  # type: ignore
            image_url = (
                image_elem["src"]
                if isinstance(image_elem, Tag) and image_elem.has_attr("src")
                else "No image found"
            )

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "authors": authors,
                    "date": date,
                    "image_url": image_url,
                }
            )

        return articles

    def execute(self, num_articles=100, max_pages=5):
        """Fetch the latest news articles from Nature's website."""
        all_articles = []
        page_number = 1

        try:
            while len(all_articles) < num_articles and page_number <= max_pages:
                html_content = self.fetch_page(page_number)
                page_articles = self.parse_articles(html_content)

                if not page_articles:
                    logger.info(f"No articles found on page {page_number}. Stopping fetch.")
                    break

                all_articles.extend(page_articles)
                page_number += 1
                if len(all_articles) < num_articles and page_number <= max_pages:
                    time.sleep(self.sleep_time)

            return all_articles[:num_articles]
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error occurred: {e}")
            return [{"error": f"Network error: {str(e)}"}]
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return [{"error": f"Unexpected error: {str(e)}"}]

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata


# Backward-compat alias
Nature_News_Fetcher_Tool = NatureNewsFetcherTool


if __name__ == "__main__":
    import json

    tool = NatureNewsFetcherTool()
    metadata = tool.get_metadata()
    print(metadata)

    try:
        execution = tool.execute(num_articles=5, max_pages=1)
        print(json.dumps(execution, indent=4))
    except Exception as e:
        print(f"Execution failed: {e}")

    print("Done!")
