
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv("../.env")

# Creater an MCP server
mcp = FastMCP(
    name="Calculator",
    host="0.0.0.0",  # Only used for SSE transport (Localhost)
    port=8050  # Only used for SSE transport (Any port)
)


@mcp.tool(name="MyCalculator", description="A calculator tool")
def add(a: int, b: int) -> int:
  return a + b


@mcp.tool(name="MySecondCalculator", description="A calculator tool")
def add_three(a: int) -> int:
  return a + 3


# Run the server
if __name__ == "__main__":
  transport = "sse"  # Should be read from .env
  if transport == "sse":
    print("Using SSE transport")
    mcp.run(transport="sse")
  elif transport == "stdio":
    print("Using stdio transport")
    mcp.run(transport="stdio")
  else:
    raise ValueError(f"Invalid transport: {transport}")
