"""
FastMCP Server: Context Compressor for Gemini
Reduces input token count for large documents/code.
"""

from fastmcp import FastMCP
import re

# Initialize FastMCP server
mcp = FastMCP("Gemini Context Compressor")

@mcp.tool()
async def compress_markdown(content: str, max_tokens: int = 5000) -> str:
    """
    Summarize Markdown document: keep headings + bullets, truncate long paragraphs.
    Returns compressed content with token estimate.
    """
    lines = content.split("\n")
    compressed = []
    
    for line in lines:
        if line.startswith("#"):  # Keep headings
            compressed.append(line)
        elif line.strip().startswith(("-", "*", "•")):  # Keep bullets
            compressed.append(line)
        elif len(line.strip()) > 150:  # Truncate long paragraphs
            truncated = line[:150] + "..."
            compressed.append(truncated)
        elif len(line.strip()) > 0:  # Keep short paragraphs
            compressed.append(line)
    
    result = "\n".join(compressed)
    estimated_tokens = len(result) // 4
    
    return f"""
[COMPRESSED]
Original: {len(content)} chars (~{len(content) // 4} tokens)
Compressed: {len(result)} chars (~{estimated_tokens} tokens)
Reduction: {100 * (1 - len(result) / len(content)):.1f}%

---
{result}"""

@mcp.tool()
async def compress_code(code: str, keep_functions: list[str]) -> str:
    """
    Extract only specified functions/classes from code.
    Reduces context for targeted analysis.
    """
    # Simple regex-based extraction
    lines = code.split("\n")
    extracted = []
    in_function = False
    indent_level = 0
    
    for line in lines:
        # Check if line defines a function or class we want
        found = False
        for func in keep_functions:
            if re.match(rf"^\s*(def|class)\s+{re.escape(func)}\b", line):
                in_function = True
                indent_level = len(line) - len(line.lstrip())
                found = True
                break
        
        if in_function:
            extracted.append(line)
            # Check if we've exited the function (new def/class at same or lower indent)
            if not found and line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                if re.match(r"^\s*(def|class)\s+", line):
                    in_function = False
                    # Remove the last line if it belongs to another function
                    extracted.pop()
    
    result = "\n".join(extracted)
    return f"""
[EXTRACTED FUNCTIONS]
Functions: {', '.join(keep_functions)}
Token estimate: {len(result) // 4}

---
{result}"""

@mcp.tool()
async def estimate_tokens(content: str) -> dict:
    """
    Rough token estimation for content.
    Uses ~4 characters per token heuristic.
    """
    estimated_tokens = len(content) // 4
    
    return {
        "content_chars": len(content),
        "estimated_tokens": estimated_tokens,
        "estimated_cost_flash_usd": (estimated_tokens * 0.0000375) / 1_000_000,
        "estimated_cost_pro_usd": (estimated_tokens * 0.0015) / 1_000_000,
    }

if __name__ == "__main__":
    mcp.run()