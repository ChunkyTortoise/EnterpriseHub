from fastmcp import FastMCP
import httpx
import os

# Create an MCP server
mcp = FastMCP("Perplexity")

@mcp.tool()
async def search_perplexity(query: str) -> str:
    """
    Search the web using Perplexity AI.
    Use this for current events, news, facts, and general web search.
    
    Args:
        query: The search query to send to Perplexity.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return "Error: PERPLEXITY_API_KEY environment variable is not set."

    url = "https://api.perplexity.ai/chat/completions"
    
    # Use sonar-pro for best reasoning/search capabilities
    # or sonar-reasoning-pro if available
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful search assistant. Provide precise, up-to-date information with citations where possible."
            },
            {"role": "user", "content": query}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            citations = result.get("citations", [])
            
            if citations:
                formatted_citations = "\n\nCitations:\n" + "\n".join([f"- {c}" for c in citations])
                return content + formatted_citations
            return content
            
    except Exception as e:
        return f"Error searching Perplexity: {str(e)}"

if __name__ == "__main__":
    mcp.run()
