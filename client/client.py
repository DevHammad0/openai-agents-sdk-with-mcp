import asyncio
import logging
from agents import Agent, ModelSettings, Runner, set_tracing_disabled # type: ignore
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams, MCPServer # type: ignore

from llm_setup import model1, model_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress the specific cleanup error from openai.agents
logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

# Define the MCP server endpoint URL
SERVER_MCP_ENDPOINT_URL = "http://localhost:8000/mcp/" 
    
set_tracing_disabled(True)


async def run_agent_with_mcp(mcp_server_client: MCPServer):
    """Run the agent with the given MCP server client."""
    try:    
        agent = Agent(
            name="MyMCPConnectedAssistant",
            instructions="You are a helpful assistant designed to test MCP connections.",
            mcp_servers=[mcp_server_client],
            model=model1,
            # model_settings=model_settings,
        )
        
        logger.info(f"Agent '{agent.name}' initialized with MCP server: '{mcp_server_client.name}'.")

        # message = "What is the current schedule for AI-101 section A?"
        
        # message = "Give me the student's basic profile information of S123"
    
        message = "give me current topic covered in AI-101"
        print(f"Running: {message}")
        result = await Runner.run(starting_agent=agent, input=message)
        print(result.final_output)
        
    except Exception as e:
        logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
        raise


async def list_tools(mcp_server_client: MCPServer):
    """List available tools from the MCP server."""
    try:
        logger.info("\n=== Listing Tools ===")
        tools = await mcp_server_client.list_tools()
        
        logger.info("\nAvailable Tools:")
        logger.info("=" * 50)
        for tool in tools:
            logger.info(f"\nTool: {tool.name}")
            logger.info(f"Description: {tool.description}")
            logger.info("-" * 30)
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")


async def list_and_read_resources(mcp_server_client: MCPServer):
    """List resource templates and read a specific resource."""
    try:
        async with mcp_server_client.session as session:
            # List resource templates
            logger.info("\n=== Listing Resource Templates ===")
            resources = await session.list_resource_templates()
            
            logger.info("\nAvailable Resource Templates:")
            logger.info("=" * 50)
            for template in resources.resourceTemplates:
                logger.info(f"\nResource: {template.name}")
                logger.info(f"URI Template: {template.uriTemplate}")
                logger.info(f"Description: {template.description}")
                logger.info("-" * 30)
            
            # Read a specific resource
            student_id = "S123"
            logger.info(f"\n=== Getting Student Profile for {student_id} ===")
            content = await session.read_resource(f"students://{student_id}/profile")
            print(f"Student Profile: {content.contents[0].text}\n")
            
    except Exception as e:
        logger.error(f"Error with resource operations: {str(e)}", exc_info=True)
        raise


async def run_http_client():
    """Run the HTTP client to connect to the MCP server."""
    logger.info(f"Starting MCP HTTP client to connect to {SERVER_MCP_ENDPOINT_URL}...")
    
    try:
        mcp_params = MCPServerStreamableHttpParams(url=SERVER_MCP_ENDPOINT_URL)
        
        async with MCPServerStreamableHttp(params=mcp_params, name="EduClient") as mcp_server_client:
            logger.info(f"Connected to MCP server: {mcp_server_client.name}")
            
            # Uncomment to run agent
            await run_agent_with_mcp(mcp_server_client)
            
            # Uncomment to list tools
            # await list_tools(mcp_server_client)
            
            # List resources and read student profile
            # await list_and_read_resources(mcp_server_client)

    except ConnectionRefusedError:
        logger.error(f"Error: Connection refused. Ensure the MCP server is running at {SERVER_MCP_ENDPOINT_URL}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        raise


def main():
    """Main entry point for the application."""
    try:
        asyncio.run(run_http_client())
        logger.info("Client completed successfully")
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()