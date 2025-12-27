#!/usr/bin/env python3
"""
MCP Transport Server
Implements the Model Context Protocol (MCP) server for transport-related tools.
Communicates via JSON-RPC over stdio.
"""
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
import traceback

from google_maps_client import GoogleMapsClient
from uber_client import UberClient
from logger import setup_logger, get_logger
from tools.geocoding import geocode_location
from tools.directions import (
    get_directions_driving,
    get_directions_transit,
    get_directions_walking
)
from tools.uber_estimate import get_uber_estimate


# Initialize logger
logger = setup_logger("mcp_transport_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for transport tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.google_client = GoogleMapsClient()
        self.uber_client = UberClient()
        self.tools = {
            'geocode_location': {
                'handler': geocode_location,
                'schema': {
                    'name': 'geocode_location',
                    'description': 'Convert an address or place name to coordinates (latitude, longitude)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'address': {
                                'type': 'string',
                                'description': 'Address or place name to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA" or "Eiffel Tower")'
                            }
                        },
                        'required': ['address']
                    }
                }
            },
            'get_uber_estimate': {
                'handler': get_uber_estimate,
                'schema': {
                    'name': 'get_uber_estimate',
                    'description': 'Get Uber ride price and time estimates between two locations',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'origin_latitude': {
                                'type': 'number',
                                'description': 'Starting latitude coordinate'
                            },
                            'origin_longitude': {
                                'type': 'number',
                                'description': 'Starting longitude coordinate'
                            },
                            'destination_latitude': {
                                'type': 'number',
                                'description': 'Destination latitude coordinate'
                            },
                            'destination_longitude': {
                                'type': 'number',
                                'description': 'Destination longitude coordinate'
                            }
                        },
                        'required': ['origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude']
                    }
                }
            },
            'get_directions_driving': {
                'handler': get_directions_driving,
                'schema': {
                    'name': 'get_directions_driving',
                    'description': 'Get driving directions between two locations with duration and distance',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'origin': {
                                'type': 'string',
                                'description': 'Origin address or coordinates (e.g., "New York, NY" or "40.7128,-74.0060")'
                            },
                            'destination': {
                                'type': 'string',
                                'description': 'Destination address or coordinates (e.g., "Los Angeles, CA" or "34.0522,-118.2437")'
                            }
                        },
                        'required': ['origin', 'destination']
                    }
                }
            },
            'get_directions_transit': {
                'handler': get_directions_transit,
                'schema': {
                    'name': 'get_directions_transit',
                    'description': 'Get public transit directions between two locations with route steps, duration, and distance',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'origin': {
                                'type': 'string',
                                'description': 'Origin address or coordinates'
                            },
                            'destination': {
                                'type': 'string',
                                'description': 'Destination address or coordinates'
                            },
                            'departure_time': {
                                'type': 'string',
                                'description': 'Optional departure time as Unix timestamp (for transit scheduling)'
                            }
                        },
                        'required': ['origin', 'destination']
                    }
                }
            },
            'get_directions_walking': {
                'handler': get_directions_walking,
                'schema': {
                    'name': 'get_directions_walking',
                    'description': 'Get walking directions between two locations with duration and distance',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'origin': {
                                'type': 'string',
                                'description': 'Origin address or coordinates'
                            },
                            'destination': {
                                'type': 'string',
                                'description': 'Destination address or coordinates'
                            }
                        },
                        'required': ['origin', 'destination']
                    }
                }
            }
        }
    
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
                            'name': 'mcp-transport',
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
                    # Add appropriate client to arguments based on tool
                    # (done after logging to avoid serialization issues)
                    if tool_name == 'get_uber_estimate':
                        tool_args = {**arguments, 'client': self.uber_client}
                    elif tool_name in ['geocode_location', 'get_directions_driving', 'get_directions_transit', 'get_directions_walking']:
                        tool_args = {**arguments, 'client': self.google_client}
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
        logger.info("MCP Transport Server starting...")
        
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

