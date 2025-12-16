#!/usr/bin/env python3
"""
MCP Flights Server
Implements the Model Context Protocol (MCP) server for flight-related tools.
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
from tools.autocomplete import autocomplete_airport_or_city
from tools.search import search_flights
from tools.pricing import price_flight_offer
from tools.booking import book_flight
from tools.routes import get_airline_routes


# Initialize logger
logger = setup_logger("mcp_flights_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for flights tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None
        self.tools = {
            'autocomplete_airport_or_city': {
                'handler': autocomplete_airport_or_city,
                'schema': {
                    'name': 'autocomplete_airport_or_city',
                    'description': 'Convert city or airport name to IATA codes',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'City or airport name (e.g., "Zurich", "New York")'
                            },
                            'country_code': {
                                'type': 'string',
                                'description': 'Optional country code (e.g., "CH", "US")'
                            }
                        },
                        'required': ['query']
                    }
                }
            },
            'search_flights': {
                'handler': search_flights,
                'schema': {
                    'name': 'search_flights',
                    'description': 'Search for available flights between origin and destination',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'origin': {
                                'type': 'string',
                                'description': 'Origin airport code (e.g., "ZRH")'
                            },
                            'destination': {
                                'type': 'string',
                                'description': 'Destination airport code (e.g., "LIS")'
                            },
                            'departure_date': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Departure date in YYYY-MM-DD format'
                            },
                            'return_date': {
                                'type': 'string',
                                'format': 'date',
                                'description': 'Optional return date in YYYY-MM-DD format'
                            },
                            'adults': {
                                'type': 'integer',
                                'description': 'Number of adult passengers',
                                'default': 1
                            },
                            'max_price': {
                                'type': 'number',
                                'description': 'Optional maximum price filter'
                            }
                        },
                        'required': ['origin', 'destination', 'departure_date']
                    }
                }
            },
            'price_flight_offer': {
                'handler': price_flight_offer,
                'schema': {
                    'name': 'price_flight_offer',
                    'description': 'Get final pricing for a flight offer before booking',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'offer_id': {
                                'type': 'string',
                                'description': 'Offer identifier'
                            },
                            'offer_data': {
                                'type': 'object',
                                'description': 'Full offer object from search_flights (required)'
                            }
                        },
                        'required': ['offer_id', 'offer_data']
                    }
                }
            },
            'book_flight': {
                'handler': book_flight,
                'schema': {
                    'name': 'book_flight',
                    'description': 'Create a flight booking (PNR)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'priced_offer_id': {
                                'type': 'string',
                                'description': 'Priced offer identifier'
                            },
                            'priced_offer_data': {
                                'type': 'object',
                                'description': 'Full priced offer object from price_flight_offer'
                            },
                            'passengers': {
                                'type': 'array',
                                'description': 'List of passenger information',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'firstName': {'type': 'string'},
                                        'lastName': {'type': 'string'},
                                        'dateOfBirth': {'type': 'string'},
                                        'gender': {'type': 'string'},
                                        'contact': {'type': 'object'}
                                    }
                                }
                            },
                            'contact_email': {
                                'type': 'string',
                                'description': 'Contact email address'
                            }
                        },
                        'required': ['priced_offer_id', 'priced_offer_data', 'passengers', 'contact_email']
                    }
                }
            },
            'get_airline_routes': {
                'handler': get_airline_routes,
                'schema': {
                    'name': 'get_airline_routes',
                    'description': 'Get destinations served by an airline from a specific origin',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'airline_code': {
                                'type': 'string',
                                'description': 'IATA airline code (e.g., "LX" for Swiss)'
                            },
                            'origin': {
                                'type': 'string',
                                'description': 'Optional origin airport code (e.g., "ZRH")'
                            }
                        },
                        'required': ['airline_code']
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
                            'name': 'mcp-flights',
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
                logger.info("=" * 80)
                logger.info(f"=== MCP TOOL CALL: {tool_name} ===")
                logger.info("=" * 80)
                logger.info(f"Tool Name: {tool_name}")
                logger.info(f"Request ID: {request_id}")
                logger.info(f"Full Tool Input: {json.dumps(arguments, indent=2, default=str)}")
                logger.info("=" * 80)
                
                try:
                    # Prepare arguments with client
                    tool_args = {**arguments, 'client': client}
                    
                    # Call the tool (handle both sync and async)
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(**tool_args)
                    else:
                        result = handler(**tool_args)
                    
                    # Log full tool output
                    logger.info("=" * 80)
                    logger.info(f"=== MCP TOOL OUTPUT: {tool_name} ===")
                    logger.info("=" * 80)
                    logger.info(f"Tool Name: {tool_name}")
                    logger.info(f"Request ID: {request_id}")
                    logger.info(f"Status: SUCCESS")
                    logger.info(f"Full Tool Output: {json.dumps(result, indent=2, default=str)}")
                    logger.info("=" * 80)
                    
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
        logger.info("MCP Flights Server starting...")
        
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

