import time

from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for current information about a topic."""
    for attempt in range(3):
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))

            if not results:
                return f"No results found for: {query}"

            return "\n---\n".join(
                f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}"
                for r in results
            )

        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return f"Search unavailable: {str(e)}"

    return f"Search failed after retries: {query}"
