# Simple web search module for SkillSling AI
# Uses free Tavily API

def web_search(query, max_results=3):
    """
    Simple web search function using Tavily
    Returns list of search results
    """
    try:
        from tavily import TavilyClient
        
        # You can get free API key from https://app.tavily.com/
        # For now, we'll use a simple fallback
        
        client = TavilyClient(api_key="")
        results = client.search(query=query, max_results=max_results)
        
        return results.get("results", [])
    except Exception as e:
        print(f"Search error: {e}")
        return []

# For testing without API key
def web_search_fallback(query):
    """Fallback when no API key"""
    return []
