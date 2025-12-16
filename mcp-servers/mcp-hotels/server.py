#!/usr/bin/env python3
"""
MCP Hotels Server
Implements the Model Context Protocol (MCP) server for hotel-related tools.
Communicates via JSON-RPC over stdio.
"""
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
import traceback

from amadeus_client import AmadeusClientWrapper
from logger import setup_logger, get_logger
from tools.search_city import search_hotels_in_city
from tools.search_coordinates import search_hotels_by_coordinates
from tools.offer_details import get_hotel_offer_details


# Initialize logger
logger = setup_logger("mcp_hotels_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for hotels tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None
        self.tools = {
            'search_hotels_in_city': {
                'handler': search_hotels_in_city,
                'schema': {
                    'name': 'search_hotels_in_city',
                    'description': 'Find hotels in a specific city with price and guest filters',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'city_code': {
                                'type': 'string',
                                'description': 'IATA city code (e.g., "LIS" for Lisbon)'
                            },
                            'check_in': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Check-in date in YYYY-MM-DD format'
                            },
                            'check_out': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Check-out date in YYYY-MM-DD format'
                            },
                            'guests': {
                                'type': 'integer',
                                'description': 'Number of guests',
                                'default': 1
                            },
                            'max_price_per_night': {
                                'type': 'number',
                                'description': 'Optional maximum price per night filter'
                            }
                        },
                        'required': ['city_code', 'check_in', 'check_out']
                    }
                }
            },
            'search_hotels_by_coordinates': {
                'handler': search_hotels_by_coordinates,
                'schema': {
                    'name': 'search_hotels_by_coordinates',
                    'description': 'Find hotels near a specific location using geographic coordinates',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'latitude': {
                                'type': 'number',
                                'description': 'Latitude coordinate (e.g., 38.7223)'
                            },
                            'longitude': {
                                'type': 'number',
                                'description': 'Longitude coordinate (e.g., -9.1393)'
                            },
                            'radius': {
                                'type': 'number',
                                'description': 'Optional search radius'
                            },
                            'radius_unit': {
                                'type': 'string',
                                'description': 'Unit for radius - "KM" or "MILE"',
                                'default': 'KM'
                            },
                            'check_in': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Optional check-in date in YYYY-MM-DD format'
                            },
                            'check_out': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Optional check-out date in YYYY-MM-DD format'
                            },
                            'guests': {
                                'type': 'integer',
                                'description': 'Number of guests',
                                'default': 1
                            }
                        },
                        'required': ['latitude', 'longitude']
                    }
                }
            },
            'get_hotel_offer_details': {
                'handler': get_hotel_offer_details,
                'schema': {
                    'name': 'get_hotel_offer_details',
                    'description': 'Get detailed information about a specific hotel offer including room details, cancellation policy, and price breakdown',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'offer_id': {
                                'type': 'string',
                                'description': 'Hotel offer ID from search results'
                            }
                        },
                        'required': ['offer_id']
                    }
                }
            }
        }
    
    def _get_client(self) -> AmadeusClientWrapper:
        """Get or create Amadeus client instance."""
        if self.client is None:
            self.client = AmadeusClientWrapper()
        return self.client
    
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
                            'name': 'mcp-hotels',
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
                
                # Add client to arguments
                client = self._get_client()
                
                # Call tool handler
                logger.info(f"Calling tool: {tool_name}")
                logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
                
                try:
                    # Prepare arguments with client
                    tool_args = {**arguments, 'client': client}
                    
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
        logger.info("MCP Hotels Server starting...")
        
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

