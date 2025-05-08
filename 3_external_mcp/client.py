import asyncio

import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # Needed to run interactive python


async def main():
  # Connect to the server using SSE
  async with sse_client("http://localhost:8050/sse") as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as session:
      # Initialize the connection
      await session.initialize()

      # List available tools
      tools_result = await session.list_tools()
      print("Available tools:")
      for tool in tools_result.tools:
        print(f"  - {tool.name}: {tool.description}")

      # Call our calculator tool
      result = await session.call_tool("add", arguments={"a": 2, "b": 3})
      print(f"2 + 3 = {result.content[0].text}")  # type: ignore


if __name__ == "__main__":
  asyncio.run(main())
