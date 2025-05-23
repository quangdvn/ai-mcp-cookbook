import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, List, Optional

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionToolParam

# Apply nest_asyncio to allow nested event loops (needed for Jupyter/IPython)
nest_asyncio.apply()

# Load environment variables
load_dotenv("../.env")


class MCPOpenAIClient:
  """Client for interacting with OpenAI models using MCP tools."""

  def __init__(self, model: str = "gpt-4o"):
    """Initialize the OpenAI MCP client.
    Args:
        model: The OpenAI model to use.
    """
    # Initialize session and client objects
    self.mcp_session: Optional[ClientSession] = None
    self.exit_stack = AsyncExitStack()
    self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    self.model = model
    self.stdio: Optional[Any] = None
    self.write: Optional[Any] = None

  async def connect_to_server(self, server_script_path: str = "server.py"):
    """Connect to an MCP server.

    Args:
        server_script_path: Path to the server script.
    """
    # Server configuration
    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
    )

    # Connect to the server
    stdio_transport = await self.exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    self.stdio, self.write = stdio_transport
    self.mcp_session = await self.exit_stack.enter_async_context(
        ClientSession(self.stdio, self.write)
    )

    # Initialize the connection
    await self.mcp_session.initialize()

    # List available tools
    tools_result = await self.mcp_session.list_tools()
    print("\nConnected to server with tools:")
    for tool in tools_result.tools:
      print(f"- {tool.name}: {tool.description}")

  async def get_mcp_tools(self) -> List[ChatCompletionToolParam]:
    """Get available tools from the MCP server in OpenAI format.
    Returns:
        A list of tools in OpenAI format.
    """
    if self.mcp_session is None:
      raise RuntimeError("Session is not initialized")

    tools_result = await self.mcp_session.list_tools()
    return [
        ChatCompletionToolParam(
          type="function",
          function={
              "name": tool.name,
              "description": tool.description or "",
              "parameters": tool.inputSchema,
            }
        )
        for tool in tools_result.tools
    ]

  async def process_query(self, query: str) -> Optional[str]:
    """Process a query using OpenAI and available MCP tools.
    Args:
        query: The user query.
    Returns:
        The response from OpenAI.
    """
    # Get available tools
    mcp_tools = await self.get_mcp_tools()

    # Initial OpenAI API call
    response = await self.openai_client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": query}],
        tools=mcp_tools,  # Load tools from external sources via MCP
        tool_choice="auto",
    )

    # Get assistant's response
    assistant_message = response.choices[0].message

    # Initialize conversation with user query and assistant response
    messages = [
        {"role": "user", "content": query},
        assistant_message,
    ]

    # Handle tool calls if present
    if assistant_message.tool_calls:
      # Process each tool call
      if self.mcp_session is None:
        raise RuntimeError("Session is not initialized")

      for tool_call in assistant_message.tool_calls:
        # Execute tool call
        result = await self.mcp_session.call_tool(
            name=tool_call.function.name,
            arguments=json.loads(tool_call.function.arguments),
        )

        # Add tool response to conversation
        messages.append(
          {
              "role": "tool",
              "tool_call_id": tool_call.id,
              "content": result.content[0].text,  # type: ignore
          }
        )

      # Get final response from OpenAI with tool results
      final_response = await self.openai_client.chat.completions.create(
          model=self.model,
          messages=messages,
          tools=mcp_tools,
          tool_choice="none",  # Don't allow more tool calls
      )
      return final_response.choices[0].message.content

    # No tool calls, just return the direct response
    return assistant_message.content

  async def cleanup(self):
    """Clean up resources."""
    await self.exit_stack.aclose()


async def main():
  """Main entry point for the client."""
  client = MCPOpenAIClient()
  try:
    await client.connect_to_server("server.py")

    # Example: Ask about company vacation policy
    # query = "What is our company's vacation policy?"
    query = "What is the weather in Paris?"
    print(f"\nQuery: {query}")

    response = await client.process_query(query)
    print(f"\nResponse: {response}")
  finally:
    await client.cleanup()


if __name__ == "__main__":
  asyncio.run(main())
