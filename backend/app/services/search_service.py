import os
from typing import List, Dict
from tavily import TavilyClient

def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Executes a web search and returns a list of source dicts:
    [{ 'title': ..., 'url': ..., 'content': ... }]
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not configured in .env")

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=max_results, search_depth="basic")

    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", "Untitled Source"),
            "url": item.get("url", ""),
            "content": item.get("content", "")
        })
    return results