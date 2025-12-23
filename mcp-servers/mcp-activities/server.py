#!/usr/bin/env python3
"""
MCP Activities Server
Implements the Model Context Protocol (MCP) server for activities/business search via Yelp API.
Communicates via JSON-RPC over stdio.
"""
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
import traceback

from yelp_client import YelpClient
from logger import setup_logger, get_logger
from tools.search_activities import search_activities, get_yelp_categories


# Initialize logger
logger = setup_logger("mcp_activities_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for activities tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None
        self.tools = {
            'search_activities': {
                'handler': search_activities,
                'schema': {
                    'name': 'search_activities',
                    'description': 'Search for activities and businesses using Yelp API. Returns restaurants, bars, museums, attractions, and more with Yelp URLs.',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'location': {
                                'type': 'string',
                                'description': 'City or location to search (e.g., "St. Gallen, Switzerland", "Zurich")'
                            },
                            'category': {
                                'type': 'string',
                                'description': 'Category of activities: restaurants, bars, coffee, museums, attractions, parks, tours, nightlife, shopping, fitness, arts',
                                'default': 'restaurants'
                            },
                            'limit': {
                                'type': 'integer',
                                'description': 'Number of results to return (max 50)',
                                'default': 10
                            },
                            'sort_by': {
                                'type': 'string',
                                'description': 'Sort order: best_match, rating, review_count, distance',
                                'default': 'rating'
                            }
                        },
                        'required': ['location']
                    }
                }
            },
            'get_activity_categories': {
                'handler': self._get_categories,
                'schema': {
                    'name': 'get_activity_categories',
                    'description': 'Get available activity categories for Yelp search',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            }
        }
    
    def _get_client(self) -> YelpClient:
        """Get or create Yelp client instance."""
        if self.client is None:
            self.client = YelpClient()
        return self.client
    
    def _get_categories(self) -> Dict[str, str]:
        """Handler for get_activity_categories tool."""
        return get_yelp_categories()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP JSON-RPC request.
        
        Args:
            request: JSON-RPC request object
        
        Returns:
            JSON-RPC response object
        """
        request_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {})
        
        logger.info(f"Received request: {method} (id: {request_id})")
        
        try:
            if method == 'initialize':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'mcp-activities',
                            'version': '1.0.0'
                        }
                    }
                }
            
            elif method == 'tools/list':
                tools_list = [tool_info['schema'] for tool_info in self.tools.values()]
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'tools': tools_list
                    }
                }
            
            elif method == 'tools/call':
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                if tool_name not in self.tools:
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32601,
                            'message': f'Tool not found: {tool_name}'
                        }
                    }
                
                # Get tool handler
                tool_info = self.tools[tool_name]
                handler = tool_info['handler']
                
                # Call tool handler
                logger.info(f"Calling tool: {tool_name}")
                logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
                
                try:
                    # Add client to arguments for search_activities
                    if tool_name == 'search_activities':
                        client = self._get_client()
                        tool_args = {**arguments, 'client': client}
                    else:
                        tool_args = arguments
                    
                    # Call the tool (handle both sync and async)
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(**tool_args)
                    else:
                        result = handler(**tool_args)
                    
                    logger.info(f"Tool {tool_name} completed successfully")
                    
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'result': {
                            'content': [
                                {
                                    'type': 'text',
                                    'text': json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                except Exception as tool_error:
                    error_msg = str(tool_error)
                    logger.error(f"Tool {tool_name} failed: {error_msg}", exc_info=True)
                    return {
                        'jsonrpc': '2.0',
                        'id': request_id,
                        'error': {
                            'code': -32000,
                            'message': f'Tool execution failed: {error_msg}'
                        }
                    }
            
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }
        
        except Exception as error:
            logger.error(f"Error handling request: {str(error)}", exc_info=True)
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(error)}'
                }
            }
    
    async def run(self):
        """Run the MCP server, reading from stdin and writing to stdout."""
        logger.info("MCP Activities Server starting...")
        
        # Read from stdin line by line (JSON-RPC over stdio)
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': 'Parse error'
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response
                print(json.dumps(response), flush=True)
                
            except Exception as error:
                logger.error(f"Error in main loop: {str(error)}", exc_info=True)
                error_response = {
                    'jsonrpc': '2.0',
                    'id': None,
                    'error': {
                        'code': -32603,
                        'message': f'Internal error: {str(error)}'
                    }
                }
                print(json.dumps(error_response), flush=True)


def main():
    """Main entry point."""
    server = MCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as error:
        logger.error(f"Fatal error: {str(error)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

