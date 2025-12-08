"""
QA Tool - Web Search Functions
Pure utility functions for web searching and information retrieval.
Can be used standalone or imported by other modules.
"""

from ddgs import DDGS
from typing import Optional, List, Dict
import json


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using DuckDuckGo.
    
    :param query: The search query
    :param max_results: Maximum number of results to return
    :return: List of search result dictionaries with 'title', 'body', and 'href'
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results if results else []
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


def format_search_results(results: List[Dict[str, str]]) -> str:
    """
    Format search results into a readable string.
    
    :param results: List of search result dictionaries
    :return: Formatted string with numbered results
    """
    if not results:
        return "⚠️ No search results found."
    
    formatted = "📊 Search Results:\n\n"
    
    for idx, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        snippet = result.get('body', 'No description')
        url = result.get('href', 'No URL')
        
        formatted += f"[{idx}] {title}\n"
        formatted += f"    {snippet}\n"
        formatted += f"    🔗 {url}\n\n"
    
    return formatted


# For backward compatibility with Open WebUI
class Tools:
    """
    Open WebUI compatible wrapper class.
    Wraps the pure functions for use in Open WebUI.
    """
    
    def __init__(self):
        """Initialize the Tools wrapper"""
        self.max_results = 5
    
    def web_search_qa(
        self, 
        query: str,
        max_results: Optional[int] = 5
    ) -> str:
        """
        Search the web for information (Open WebUI compatible).
        
        :param query: The search query or question from the user
        :param max_results: Maximum number of search results to return
        :return: Formatted search results
        """
        results = web_search(query, max_results)
        return format_search_results(results)
    
    def wikipedia_search(
        self, 
        query: str,
        max_results: Optional[int] = 3
    ) -> str:
        """
        Search Wikipedia for information (Open WebUI compatible).
        
        :param query: The search query
        :param max_results: Maximum number of results
        :return: Wikipedia search results
        """
        wiki_query = f"{query} site:wikipedia.org"
        results = web_search(wiki_query, max_results)
        return format_search_results(results)
    
    def get_current_info(self, query: str) -> str:
        """
        Get current/latest information (Open WebUI compatible).
        
        :param query: The query about current information
        :return: Latest search results
        """
        current_query = f"{query} latest news 2025"
        results = web_search(current_query, max_results=5)
        
        if not results:
            return f"⚠️ No current information found for: {query}"
        
        formatted = "🆕 Latest Information:\n\n"
        for idx, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('body', 'No description')
            url = result.get('href', 'No URL')
            
            formatted += f"[{idx}] {title}\n"
            formatted += f"    {snippet}\n"
            formatted += f"    🔗 {url}\n\n"
        
        formatted += "\n💡 This is the most recent information available."
        return formatted


# Standalone testing
def test_search_functions():
    """Test the pure search functions"""
    
    print("=" * 60)
    print("Testing QA Tool - Pure Functions")
    print("=" * 60)
    
    # Test 1: Basic web search
    print("\n🧪 Test 1: web_search()")
    results = web_search("What is the capital of Taiwan?", max_results=3)
    print(f"Found {len(results)} results")
    formatted = format_search_results(results)
    print(formatted[:200] + "...")
    
    # Test 2: Wikipedia search
    print("\n🧪 Test 2: Wikipedia search")
    wiki_results = web_search("Machine Learning site:wikipedia.org", max_results=2)
    print(f"Found {len(wiki_results)} Wikipedia results")
    
    print("\n" + "=" * 60)
    print("✅ Pure function tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run tests if executed directly
    test_search_functions()
