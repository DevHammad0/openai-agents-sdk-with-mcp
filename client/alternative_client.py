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

async def test_resource_templates_approach_1(mcp_server_client):
    """Approach 1: Direct server client methods (if available)"""
    logger.info("\n=== Approach 1: Direct Server Client Methods ===")
    
    # Check if the server client itself has resource methods
    direct_methods = [
        'list_resource_templates',
        'list_resources', 
        'get_resource_templates',
        'resources'
    ]
    
    for method_name in direct_methods:
        if hasattr(mcp_server_client, method_name):
            try:
                method = getattr(mcp_server_client, method_name)
                if callable(method):
                    result = await method()
                    logger.info(f"✓ Direct {method_name}() successful")
                    return result
            except Exception as e:
                logger.info(f"✗ Direct {method_name}() failed: {e}")
    
    logger.info("No direct server client resource methods available")
    return None

async def test_resource_templates_approach_2(mcp_server_client):
    """Approach 2: Session-based methods with proper context management"""
    logger.info("\n=== Approach 2: Session-Based Methods ===")
    
    try:
        # Create a new session context
        async with mcp_server_client.session as session:
            logger.info(f"Session established: {type(session)}")
            
            # Try multiple session methods
            session_methods = [
                'list_resource_templates',
                'list_resources',
                'get_resource_templates',
                'resource_templates'
            ]
            
            for method_name in session_methods:
                if hasattr(session, method_name):
                    try:
                        method = getattr(session, method_name)
                        if callable(method):
                            result = await method()
                            logger.info(f"✓ Session {method_name}() successful")
                            return result
                    except Exception as e:
                        logger.info(f"✗ Session {method_name}() failed: {e}")
            
            logger.info("No session resource template methods available")
            return None
            
    except Exception as e:
        logger.error(f"Session context error: {e}")
        return None

async def test_resource_templates_approach_3(mcp_server_client):
    """Approach 3: Initialize session and call MCP protocol methods"""
    logger.info("\n=== Approach 3: MCP Protocol Methods ===")
    
    try:
        async with mcp_server_client.session as session:
            # Try to call initialize if available
            if hasattr(session, 'initialize'):
                try:
                    init_result = await session.initialize()
                    logger.info(f"Session initialized: {init_result}")
                except Exception as e:
                    logger.info(f"Session initialization failed: {e}")
            
            # Try MCP protocol methods
            mcp_methods = [
                'list_resource_templates_mcp',
                'list_resources_mcp',
                'call_mcp',
                'send_request'
            ]
            
            for method_name in mcp_methods:
                if hasattr(session, method_name):
                    try:
                        method = getattr(session, method_name)
                        if callable(method):
                            if 'mcp' in method_name:
                                result = await method()
                            else:
                                # For call_mcp or send_request, we might need parameters
                                continue
                            logger.info(f"✓ MCP {method_name}() successful")
                            return result
                    except Exception as e:
                        logger.info(f"✗ MCP {method_name}() failed: {e}")
            
            logger.info("No MCP protocol methods available")
            return None
            
    except Exception as e:
        logger.error(f"MCP protocol error: {e}")
        return None

async def test_read_resource_robust(mcp_server_client, resource_uri):
    """Robust resource reading with multiple URI formats and error handling"""
    logger.info(f"\n=== Reading Resource: {resource_uri} ===")
    
    # Multiple URI format variations to try
    uri_variations = [
        resource_uri,
        resource_uri.replace("students://", "student://"),
        resource_uri.replace("students://", "resource://students/"),
        resource_uri.replace("students://", "data://students/"),
        resource_uri.replace("students://", ""),  # Just the path
        f"resource://{resource_uri.split('://', 1)[1]}" if "://" in resource_uri else f"resource://{resource_uri}"
    ]
    
    for uri in uri_variations:
        try:
            async with mcp_server_client.session as session:
                if hasattr(session, 'read_resource'):
                    try:
                        content = await session.read_resource(uri)
                        logger.info(f"✓ Successfully read resource with URI: {uri}")
                        
                        # Handle different response formats
                        if hasattr(content, 'contents') and content.contents:
                            return content.contents[0].text
                        elif hasattr(content, 'content'):
                            return content.content
                        elif hasattr(content, 'text'):
                            return content.text
                        else:
                            return str(content)
                            
                    except Exception as e:
                        logger.debug(f"URI {uri} failed: {e}")
                        continue
                else:
                    logger.warning("read_resource method not available on session")
                    break
                    
        except Exception as e:
            logger.debug(f"Session error for URI {uri}: {e}")
            continue
    
    logger.warning(f"All URI variations failed for: {resource_uri}")
    return None

async def run_alternative_client():
    """Run the alternative MCP client with multiple approaches."""
    logger.info(f"Starting alternative MCP client for {SERVER_MCP_ENDPOINT_URL}...")
    
    try:
        mcp_params = MCPServerStreamableHttpParams(url=SERVER_MCP_ENDPOINT_URL)
        
        async with MCPServerStreamableHttp(params=mcp_params, name="AlternativeClient") as mcp_server_client:
            logger.info(f"Connected to MCP server: {mcp_server_client.name}")
            
            # Try different approaches to list resource templates
            resource_templates = None
            
            # Approach 1: Direct server client methods
            result = await test_resource_templates_approach_1(mcp_server_client)
            if result:
                resource_templates = result
            
            # Approach 2: Session-based methods
            if not resource_templates:
                result = await test_resource_templates_approach_2(mcp_server_client)
                if result:
                    resource_templates = result
            
            # Approach 3: MCP protocol methods  
            if not resource_templates:
                result = await test_resource_templates_approach_3(mcp_server_client)
                if result:
                    resource_templates = result
            
            # Process and display results
            if resource_templates:
                logger.info("\n=== Successfully Retrieved Resource Templates ===")
                
                # Handle different result formats
                templates = None
                if hasattr(resource_templates, 'resourceTemplates'):
                    templates = resource_templates.resourceTemplates
                elif hasattr(resource_templates, 'resource_templates'):
                    templates = resource_templates.resource_templates
                elif isinstance(resource_templates, list):
                    templates = resource_templates
                
                if templates:
                    for template in templates:
                        logger.info(f"\nResource Template: {getattr(template, 'name', 'Unknown')}")
                        logger.info(f"URI Template: {getattr(template, 'uriTemplate', 'Unknown')}")
                        logger.info(f"Description: {getattr(template, 'description', 'No description')}")
                        logger.info("-" * 30)
                else:
                    logger.info(f"Resource templates in unknown format: {resource_templates}")
            else:
                logger.warning("Failed to retrieve resource templates using any approach")
            
            # Test resource reading with robust approach
            student_id = "S123"
            resource_uri = f"students://{student_id}/profile"
            content = await test_read_resource_robust(mcp_server_client, resource_uri)
            
            if content:
                logger.info(f"\n=== Student Profile Retrieved ===")
                print(f"Student Profile: {content}")
            else:
                logger.warning("Failed to retrieve student profile")
                
    except ConnectionRefusedError:
        logger.error(f"Error: Connection refused. Ensure the MCP server is running at {SERVER_MCP_ENDPOINT_URL}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

def main():
    """Main entry point for the alternative client."""
    try:
        asyncio.run(run_alternative_client())
        logger.info("Alternative client completed successfully")
    except KeyboardInterrupt:
        logger.info("Alternative client interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main() 