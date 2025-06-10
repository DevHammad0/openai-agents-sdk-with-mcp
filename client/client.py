# client/http_client.py
import asyncio
import logging
from agents import Agent, ModelSettings, Runner, set_tracing_disabled
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams, MCPServer
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dataclasses import dataclass

from llm_setup import model1, model_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the MCP server endpoint URL
SERVER_MCP_ENDPOINT_URL = "http://localhost:8000/mcp/"

    
    
set_tracing_disabled(True)


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        mcp_servers=[mcp_server],
        model=model1,
        # model_settings=model_settings,
    )

    # Use the tools to get information
    # message = "What is the current schedule for AI-101 section A?"
    
    # message = "Give me the student's basic profile information of S123"
    
    message = "give me current topic covered in AI-101"
    print(f"Running: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)




async def run_http_client():
    logger.info(f"Starting MCP HTTP client to connect to {SERVER_MCP_ENDPOINT_URL}...")
    try:
        mcp_params = MCPServerStreamableHttpParams(url=SERVER_MCP_ENDPOINT_URL)
        
        async with MCPServerStreamableHttp(params=mcp_params, name="Streamable HTTP Python Server") as server:
            logger.info(f"Connected to MCP server: {server.name}")
            await run(server)


                # # List Resources
                # logger.info("Listing resources...")
                # resources = await session.list_resource_templates()
                
                # logger.info("\nAvailable Resource Templates:")
                # logger.info("=" * 50)
                # for template in resources.resourceTemplates:
                #     logger.info(f"\nResource: {template.name}")
                #     logger.info(f"URI Template: {template.uriTemplate}")
                #     logger.info(f"Description: {template.description}")
                #     logger.info("-" * 30)
                    
                # # listing Tools
                # logger.info("\n=== Listing Tools ===")
                # tools = await session.list_tools()
                
                # logger.info("\nAvailable Tools:")
                # logger.info("=" * 50)
                # for tool in tools.tools:
                #     logger.info(f"\nTool: {tool.name}")
                #     logger.info(f"Description: {tool.description}")
                #     logger.info("-" * 30)
                
                # Read Resource
                # student_id = "S123"
                # logger.info("\n=== Getting Student Profile ===")
                # content = await session.read_resource(f"students://{student_id}/profile")
                # print(f"Student Profile: {content.contents[0].text}\n")

                
            # assistant = Agent(
            #     name="EducationalAssistant",
            #     instructions="""You are an educational assistant with access to the following capabilities:
            #     - Get class schedules for specific courses and sections
            #     - Find the next scheduled class time for any course and section
            #     - Check the current topic being covered in any course
            #     - View the list of topics a student has covered so far
                
            #     You can help students and faculty with course scheduling, progress tracking, and curriculum information.
            #     When asked about course information, make sure to specify both the course code (AI-101, AI-201, AI-202, or AI-301) 
            #     and section (A, B, or C) where required.
                
            #     For student-specific queries, you'll need their student ID.""",
            #     mcp_servers=[mcp_server_client],
            #     model=model1,
            # )
            
            # result = await Runner.run(assistant, "What is the current schedule for AI-101 section A?")
            # logger.info(f"[AGENT RESPONSE]: {result.final_output}")
                

    except ConnectionRefusedError:
        logger.error(f"Error: Connection refused. Ensure the MCP server is running at {SERVER_MCP_ENDPOINT_URL}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        raise

def main():
    try:
        asyncio.run(run_http_client())
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()