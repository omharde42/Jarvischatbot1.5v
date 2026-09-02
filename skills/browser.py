import webbrowser
import urllib.parse
from typing import Dict, Any

def open_url(url: str) -> Dict[str, Any]:
    try:
        target_url = url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        webbrowser.open(target_url)
        return {
            "success": True,
            "url": target_url,
            "spoken_response": f"Opening {target_url} in browser."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to open web URL."}

def search_web(query: str) -> Dict[str, Any]:
    try:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(search_url)
        return {
            "success": True,
            "query": query,
            "url": search_url,
            "spoken_response": f"Searching the web for {query}."
        }
    except Exception as e:
        return {"success": False, "error": str(e), "spoken_response": "Failed to perform web search."}
