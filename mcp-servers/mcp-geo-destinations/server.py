#!/usr/bin/env python3
"""
MCP Geo Destinations Server
Implements the Model Context Protocol (MCP) server for geographical destination tools.
Communicates via JSON-RPC over stdio.
"""
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
import traceback

from logger import setup_logger, get_logger
from tools.country_info import get_country_info
from tools.travel_season import get_best_travel_season
from tools.points_of_interest import get_points_of_interest
from tools.weather_forecast import get_weather_forecast


# Initialize logger
logger = setup_logger("mcp_geo_destinations_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for geo destination tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.tools = {
            'get_country_info': {
                'handler': get_country_info,
                'schema': {
                    'name': 'get_country_info',
                    'description': 'Get comprehensive information about a country including currency, languages, timezone, and basic visa notes from RestCountries API',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'country_code': {
                                'type': 'string',
                                'description': 'ISO 3166-1 alpha-2 or alpha-3 country code (e.g., "CH", "CHE", "US", "USA")'
                            },
                            'country_name': {
                                'type': 'string',
                                'description': 'Country name (e.g., "Switzerland", "United States")'
                            }
                        }
                    }
                }
            },
            'get_best_travel_season': {
                'handler': get_best_travel_season,
                'schema': {
                    'name': 'get_best_travel_season',
                    'description': 'Determine the best travel season for a destination based on historical weather data from OpenWeatherMap API',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'latitude': {
                                'type': 'number',
                                'description': 'Latitude coordinate of the destination'
                            },
                            'longitude': {
                                'type': 'number',
                                'description': 'Longitude coordinate of the destination'
                            },
                            'city_name': {
                                'type': 'string',
                                'description': 'Optional city name for display purposes'
                            },
                            'country_code': {
                                'type': 'string',
                                'description': 'Optional country code for context'
                            },
                            'months_to_analyze': {
                                'type': 'integer',
                                'description': 'Number of months to analyze (default: 12)',
                                'default': 12
                            }
                        },
                        'required': ['latitude', 'longitude']
                    }
                }
            },
            'get_points_of_interest': {
                'handler': get_points_of_interest,
                'schema': {
                    'name': 'get_points_of_interest',
                    'description': 'Get points of interest near a specific location using Amadeus POIs API',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'latitude': {
                                'type': 'number',
                                'description': 'Latitude coordinate'
                            },
                            'longitude': {
                                'type': 'number',
                                'description': 'Longitude coordinate'
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
                            'categories': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': 'Optional list of POI categories to filter'
                            }
                        },
                        'required': ['latitude', 'longitude']
                    }
                }
            },
            'get_weather_forecast': {
                'handler': get_weather_forecast,
                'schema': {
                    'name': 'get_weather_forecast',
                    'description': 'Get temperature range for a specific date range using OpenWeatherMap API',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'latitude': {
                                'type': 'number',
                                'description': 'Latitude coordinate of the destination'
                            },
                            'longitude': {
                                'type': 'number',
                                'description': 'Longitude coordinate of the destination'
                            },
                            'from_date': {
                                'type': 'string',
                                'description': 'Start date in YYYY-MM-DD format'
                            },
                            'to_date': {
                                'type': 'string',
                                'description': 'End date in YYYY-MM-DD format (inclusive)'
                            },
                            'city_name': {
                                'type': 'string',
                                'description': 'Optional city name for display purposes'
                            }
                        },
                        'required': ['latitude', 'longitude', 'from_date', 'to_date']
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
                            'name': 'mcp-geo-destinations',
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
                    # Call the tool (handle both sync and async)
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(**arguments)
                    else:
                        result = handler(**arguments)
                    
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
        logger.info("MCP Geo Destinations Server starting...")
        
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






