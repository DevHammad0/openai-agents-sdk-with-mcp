import asyncio
import logging
import os

from agents import Agent, Runner, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams

from llm_setup import model1


# Configure basic logging to see SDK interactions and our own logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# URL of our standalone MCP server (from shared_mcp_server)
MCP_SERVER_URL = "http://localhost:8001/mcp/"


set_tracing_disabled(disabled=True)


async def main():
    logger.info(f"--- Agent Connection Test Start ---")
    logger.info(f"Attempting to connect agent to MCP server at {MCP_SERVER_URL}")

    # 1. Configure parameters for the MCPServerStreamableHttp client
    # These parameters tell the SDK how to reach the MCP server.
    mcp_params = MCPServerStreamableHttpParams(url=MCP_SERVER_URL)
    logger.info(f"MCPServerStreamableHttpParams configured for URL: {mcp_params.get('url')}")

    # 2. Create an instance of the MCPServerStreamableHttp client.
    # This object represents our connection to the specific MCP server.
    # It's an async context manager, so we use `async with` for proper setup and teardown.
    # The `name` parameter is optional but useful for identifying the server in logs or multi-server setups.
    async with MCPServerStreamableHttp(params=mcp_params, name="MySharedMCPServerClient") as mcp_server_client:
        logger.info(f"MCPServerStreamableHttp client '{mcp_server_client.name}' created and entered context.")
        logger.info("The SDK will use this client to interact with the MCP server.")

        # 3. Create an agent and pass the MCP server client to it.
        # When an agent is initialized with mcp_servers, the SDK often attempts
        # to list tools from these servers to make the LLM aware of them.
        # You might see a `list_tools` call logged by your shared_mcp_server.
        try:
            assistant = Agent(
                name="MyMCPConnectedAssistant",
                instructions="You are a helpful assistant designed to test MCP connections. You can also tell Hammad's mood.",
                mcp_servers=[mcp_server_client],
                model=model1,
            )

            logger.info(f"Agent '{assistant.name}' initialized with MCP server: '{mcp_server_client.name}'.")
            logger.info("The SDK may have implicitly called list_tools() on the MCP server.")
            logger.info("Check the logs of your shared_mcp_server for a 'tools/list' request.")

            # 4. Explicitly list tools to confirm connection and tool discovery.
            logger.info(f"Attempting to explicitly list tools from '{mcp_server_client.name}'...")
            tools = await mcp_server_client.list_tools()
            if tools:
                tool_names = [tool.name for tool in tools if tool.name] # Added if tool.name to avoid issues with None
                logger.info(f"Successfully listed tools from MCP server: {tool_names}")
                if "greet_from_shared_server" in tool_names and "mood_from_shared_server" in tool_names:
                    logger.info("Confirmed: 'greet_from_shared_server' and 'mood_from_shared_server' tools are available!")
                else:
                    logger.warning(f"'greet_from_shared_server' or 'mood_from_shared_server' tool NOT found. Check server definition. Found: {tool_names}")
            else:
                logger.warning("No tools found on the MCP server. Ensure the server is running and defines tools.")

            logger.info("\n\nRunning a simple agent interaction...")
            # Example query that might trigger the 'mood_from_shared_server' tool
            result = await Runner.run(assistant, "What is Hammad's mood?")
            logger.info(f"\n\n[AGENT RESPONSE]: {result.final_output}")

        except Exception as e:
            logger.error(f"An error occurred during agent setup or tool listing: {e}", exc_info=True)
            logger.error("Please ensure your Gemini API key is set in .env and the shared MCP server is running.")

    logger.info(f"MCPServerStreamableHttp client '{mcp_server_client.name}' context exited.")
    logger.info(f"--- Agent Connection Test End ---")

if __name__ == "__main__":
    # It's good practice to handle potential asyncio errors or user interrupts
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent script interrupted by user.")
    except Exception as e:
        logger.error(f"An unhandled error occurred in the agent script: {e}", exc_info=True)