#!/usr/bin/env python3
"""
MCP Cars Server
Implements the Model Context Protocol (MCP) server for car rental-related tools.
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
from tools.search_airport import search_cars_at_airport
from tools.offer_details import get_car_offer_details


# Initialize logger
logger = setup_logger("mcp_cars_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for car rental tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None
        self.tools = {
            'search_cars_at_airport': {
                'handler': search_cars_at_airport,
                'schema': {
                    'name': 'search_cars_at_airport',
                    'description': 'Find rental cars available at a specific airport',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'pickup_iata': {
                                'type': 'string',
                                'description': 'IATA code of the pickup airport (e.g., "LIS")'
                            },
                            'pickup_date': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Pickup date in YYYY-MM-DD format'
                            },
                            'dropoff_date': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Dropoff date in YYYY-MM-DD format'
                            },
                            'pickup_time': {
                                'type': 'string',
                                'description': 'Optional pickup time in HH:MM format (default: "10:00")'
                            },
                            'dropoff_time': {
                                'type': 'string',
                                'description': 'Optional dropoff time in HH:MM format (default: "10:00")'
                            }
                        },
                        'required': ['pickup_iata', 'pickup_date', 'dropoff_date']
                    }
                }
            },
            'get_car_offer_details': {
                'handler': get_car_offer_details,
                'schema': {
                    'name': 'get_car_offer_details',
                    'description': 'Get detailed information about a specific car rental offer including insurance, cancellation policy, and vehicle specifications',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'offer_id': {
                                'type': 'string',
                                'description': 'Car rental offer ID from search results'
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
                            'name': 'mcp-cars',
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
        logger.info("MCP Cars Server starting...")
        
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

