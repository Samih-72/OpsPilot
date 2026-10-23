import os
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_core.tools import tool

load_dotenv()
@tool
def web_search(query:str) -> str:
    """Search the web for information relevant to a business question."""
    api_key=os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web research is unavailable because TAVILY_API_KEY is not configured."
    try:
        client = TavilyClient(api_key=api_key)
        response=client.search(
            query=query,
            max_results=5
        )
        results=response.get("results",[])
        if not results:
            return "No relevant web search results were found"
        formatted_results=[]
        for result in results:
            title=result.get("title","Untitled")
            url = result.get("url", "")
            content = result.get("content", "")
            formatted_results.append(
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Summary: {content}\n"
            )
        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"web search failed:{type(e).__name__}:{e}"
