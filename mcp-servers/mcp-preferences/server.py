#!/usr/bin/env python3
"""
MCP Preferences Server
Implements the Model Context Protocol (MCP) server for user travel preferences.
Reads from PostgreSQL database to extract and analyze user preferences.
Communicates via JSON-RPC over stdio.
"""
import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional
import traceback

from db_client import PreferencesDBClient
from logger import setup_logger, get_logger
from tools.form_preferences import get_form_preferences
from tools.destination_preferences import get_destination_preferences
from tools.flight_preferences import get_flight_preferences
from tools.hotel_preferences import get_hotel_preferences
from tools.itinerary_preferences import get_itinerary_preferences
from tools.transport_preferences import get_transport_preferences
from tools.full_profile import get_full_preference_profile


# Initialize logger
logger = setup_logger("mcp_preferences_server", level=logging.DEBUG)


class MCPServer:
    """MCP Server implementation for preferences tools."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.client = None
        self.tools = {
            'get_form_preferences': {
                'handler': get_form_preferences,
                'schema': {
                    'name': 'get_form_preferences',
                    'description': 'Extract form preferences from user trip history (traveler type, environments, climate, trip vibe, experiences, budget, etc.)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_destination_preferences': {
                'handler': get_destination_preferences,
                'schema': {
                    'name': 'get_destination_preferences',
                    'description': 'Extract destination preferences from trip history (countries, regions, destination types, surprise_me patterns)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_flight_preferences': {
                'handler': get_flight_preferences,
                'schema': {
                    'name': 'get_flight_preferences',
                    'description': 'Extract flight preferences from trip history (airlines, class, layovers, price sensitivity, departure times)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_hotel_preferences': {
                'handler': get_hotel_preferences,
                'schema': {
                    'name': 'get_hotel_preferences',
                    'description': 'Extract hotel preferences from trip history (star ratings, amenities, price range, location types)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_itinerary_preferences': {
                'handler': get_itinerary_preferences,
                'schema': {
                    'name': 'get_itinerary_preferences',
                    'description': 'Extract itinerary preferences from trip history (activity categories, pace, activity budget)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_transport_preferences': {
                'handler': get_transport_preferences,
                'schema': {
                    'name': 'get_transport_preferences',
                    'description': 'Extract transport preferences from trip history (transport modes, price sensitivity, walk willingness)',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            },
            'get_full_preference_profile': {
                'handler': get_full_preference_profile,
                'schema': {
                    'name': 'get_full_preference_profile',
                    'description': 'Get comprehensive preference profile combining all preference types with natural language summary for LLM consumption',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'user_id': {
                                'type': 'integer',
                                'description': 'The user ID to get preferences for'
                            }
                        },
                        'required': ['user_id']
                    }
                }
            }
        }
    
    def _get_client(self) -> PreferencesDBClient:
        """Get or create database client instance."""
        if self.client is None:
            self.client = PreferencesDBClient()
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
                            'name': 'mcp-preferences',
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
                    # Add client to arguments for all tools
                    client = self._get_client()
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
        logger.info("MCP Preferences Server starting...")
        
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

