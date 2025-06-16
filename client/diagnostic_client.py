import asyncio
import logging
from agents import Agent, ModelSettings, Runner, set_tracing_disabled # type: ignore
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams, MCPServer # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress the specific cleanup error from openai.agents
logging.getLogger("openai.agents").setLevel(logging.CRITICAL)

# Define the MCP server endpoint URL
SERVER_MCP_ENDPOINT_URL = "http://localhost:8000/mcp/" 
    
set_tracing_disabled(True)

async def diagnose_mcp_session():
    """Diagnose the MCP session to understand available methods and capabilities."""
    logger.info(f"Starting MCP diagnostic client for {SERVER_MCP_ENDPOINT_URL}...")
    
    try:
        mcp_params = MCPServerStreamableHttpParams(url=SERVER_MCP_ENDPOINT_URL)
        
        async with MCPServerStreamableHttp(params=mcp_params, name="DiagnosticClient") as mcp_server_client:
            logger.info(f"Connected to MCP server: {mcp_server_client.name}")
            
            # Diagnose the server client object
            logger.info("\n=== MCP Server Client Inspection ===")
            server_methods = [method for method in dir(mcp_server_client) if not method.startswith('_')]
            logger.info("Available server client methods:")
            for method in server_methods:
                if callable(getattr(mcp_server_client, method)):
                    logger.info(f"  - {method}")
            
            # Test session access
            logger.info("\n=== Session Inspection ===")
            try:
                async with mcp_server_client.session as session:
                    logger.info(f"Session type: {type(session)}")
                    logger.info(f"Session: {session}")
                    
                    # List all available methods on the session
                    session_methods = [method for method in dir(session) if not method.startswith('_')]
                    logger.info("\nAll session methods:")
                    for method in sorted(session_methods):
                        if callable(getattr(session, method)):
                            logger.info(f"  - {method}")
                    
                    # Focus on resource-related methods
                    logger.info("\nResource-related methods:")
                    resource_methods = [method for method in session_methods if 'resource' in method.lower()]
                    for method in resource_methods:
                        logger.info(f"  - {method}")
                    
                    # Focus on template-related methods
                    logger.info("\nTemplate-related methods:")
                    template_methods = [method for method in session_methods if 'template' in method.lower()]
                    for method in template_methods:
                        logger.info(f"  - {method}")
                    
                    # Focus on list methods
                    logger.info("\nList methods:")
                    list_methods = [method for method in session_methods if 'list' in method.lower()]
                    for method in list_methods:
                        logger.info(f"  - {method}")
                    
                    # Test basic connectivity
                    logger.info("\n=== Testing Basic Session Methods ===")
                    
                    # Test list_tools if available
                    if hasattr(session, 'list_tools'):
                        try:
                            tools_result = await session.list_tools()
                            logger.info(f"✓ list_tools() successful, type: {type(tools_result)}")
                            if hasattr(tools_result, 'tools'):
                                logger.info(f"  Tools count: {len(tools_result.tools)}")
                            else:
                                logger.info(f"  Direct tools list: {len(tools_result) if hasattr(tools_result, '__len__') else 'Unknown'}")
                        except Exception as e:
                            logger.error(f"✗ list_tools() failed: {e}")
                    
                    # Test resource methods
                    logger.info("\n=== Testing Resource Methods ===")
                    
                    # Test each possible resource method
                    resource_test_methods = [
                        'list_resources',
                        'list_resource_templates', 
                        'list_resource_templates_mcp',
                        'resources',
                        'resource_templates'
                    ]
                    
                    for method_name in resource_test_methods:
                        if hasattr(session, method_name):
                            try:
                                method = getattr(session, method_name)
                                if callable(method):
                                    result = await method()
                                    logger.info(f"✓ {method_name}() successful, type: {type(result)}")
                                    
                                    # Try to inspect the result structure
                                    if hasattr(result, '__dict__'):
                                        logger.info(f"  Result attributes: {list(result.__dict__.keys())}")
                                    elif hasattr(result, '__len__'):
                                        logger.info(f"  Result length: {len(result)}")
                                    
                                    # Try common attribute names
                                    for attr in ['resources', 'resourceTemplates', 'resource_templates', 'templates']:
                                        if hasattr(result, attr):
                                            attr_value = getattr(result, attr)
                                            logger.info(f"  Has {attr}: {type(attr_value)}, length: {len(attr_value) if hasattr(attr_value, '__len__') else 'N/A'}")
                                else:
                                    logger.info(f"  {method_name} is not callable")
                            except Exception as e:
                                logger.error(f"✗ {method_name}() failed: {e}")
                        else:
                            logger.info(f"  {method_name} not available")
                    
                    # Test read_resource if we can find any resource URIs
                    logger.info("\n=== Testing Resource Reading ===")
                    test_uris = [
                        "students://S123/profile",
                        "student://S123/profile", 
                        "resource://students/S123/profile",
                        "data://students/S123/profile"
                    ]
                    
                    for uri in test_uris:
                        if hasattr(session, 'read_resource'):
                            try:
                                result = await session.read_resource(uri)
                                logger.info(f"✓ read_resource('{uri}') successful, type: {type(result)}")
                                if hasattr(result, '__dict__'):
                                    logger.info(f"  Result attributes: {list(result.__dict__.keys())}")
                                break
                            except Exception as e:
                                logger.info(f"✗ read_resource('{uri}') failed: {e}")
                        else:
                            logger.info("  read_resource method not available")
                            break
                    
            except Exception as e:
                logger.error(f"Error accessing session: {e}")
                
    except ConnectionRefusedError:
        logger.error(f"Error: Connection refused. Ensure the MCP server is running at {SERVER_MCP_ENDPOINT_URL}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

def main():
    """Main entry point for the diagnostic tool."""
    try:
        asyncio.run(diagnose_mcp_session())
        logger.info("Diagnostic completed successfully")
    except KeyboardInterrupt:
        logger.info("Diagnostic interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main() 