import time
import re

import requests
from langchain_core.tools import tool

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """Fetch DuckDuckGo HTML results and parse them with stdlib."""
    url = "https://html.duckduckgo.com/html/"
    try:
        resp = requests.post(url, data={"q": query}, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e

    html = resp.text
    results = []

    # Each result block: <a class="result__a" href="...">Title</a> ... snippet
    links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)
    raw_snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    snippets = [re.sub(r"<[^>]+>", "", s).strip() for s in raw_snippets]

    for i, (href, title) in enumerate(links[:max_results]):
        snippet = snippets[i] if i < len(snippets) else ""
        results.append({"title": title.strip(), "href": href.strip(), "body": snippet})

    return results


@tool
def web_search(query: str) -> str:
    """Search the web for current information about a topic."""
    for attempt in range(3):
        try:
            results = _ddg_search(query)

            if not results:
                if attempt < 2:
                    time.sleep(1)
                    continue
                return f"No results found for: {query}"

            return "\n---\n".join(
                f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
                for r in results
            )

        except Exception as e:
            if attempt < 2:
                time.sleep(3 ** attempt)
                continue
            return f"Search unavailable: {str(e)}"

    return f"Search failed after retries for: {query}"
