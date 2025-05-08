import asyncio
from datetime import timedelta

import nest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()  # Needed to run interactive Python


async def main():
  server_params = StdioServerParameters(
      command="python3",  # The command to run MCP server
      args=["server.py"],  	# The arguments to pass to the command
  )
  # Connect to the server
  async with stdio_client(server_params) as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as session:
      # Initialize the connection
      await session.initialize()

      # List available tools
      tools_result = await session.list_tools()
      print("Available tools:")
      for tool in tools_result.tools:
        print(f"- {tool.name}: {tool.description}")

      # Call tools
      first_result = await session.call_tool(
        "MyCalculator",
        arguments={"a": 1, "b": 2},
        read_timeout_seconds=timedelta(seconds=5)
      )
      print(first_result)
      print(first_result.content[0].text)
      second_result = await session.call_tool(
        "MySecondCalculator",
        arguments={"a": 1},
        read_timeout_seconds=timedelta(seconds=5)
      )
      print(second_result)
      print(second_result.content[0].text)

if __name__ == "__main__":
  asyncio.run(main())
