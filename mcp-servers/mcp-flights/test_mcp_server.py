#!/usr/bin/env python3
"""
Test script for MCP Server via JSON-RPC.
Tests the MCP protocol implementation directly.
"""
import json
import os
import subprocess
import sys
import time


def send_request(process, request):
    """Send a JSON-RPC request to the MCP server."""
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json.encode())
    process.stdin.flush()
    
    # Read response
    response_line = process.stdout.readline()
    if response_line:
        return json.loads(response_line.decode())
    return None


def test_mcp_server():
    """Test the MCP server via stdio."""
    print("Testing MCP Server via JSON-RPC")
    print("="*80)
    
    # Start the server process
    server_path = "server.py"
    print(f"Starting server: {server_path}")
    
    try:
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Wait a bit for server to start
        time.sleep(1)
        
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        response = send_request(process, init_request)
        if response and 'result' in response:
            print("✅ Initialize successful")
            print(f"   Server: {response['result'].get('serverInfo', {}).get('name')}")
        else:
            print(f"❌ Initialize failed: {response}")
            return False
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        response = send_request(process, list_request)
        if response and 'result' in response:
            tools = response['result'].get('tools', [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.get('name')}")
        else:
            print(f"❌ List tools failed: {response}")
            return False
        
        # Test 3: Call autocomplete tool
        print("\n3. Testing tools/call (autocomplete_airport_or_city)...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "autocomplete_airport_or_city",
                "arguments": {
                    "query": "Zurich",
                    "country_code": "CH"
                }
            }
        }
        response = send_request(process, call_request)
        if response and 'result' in response:
            print("✅ Tool call successful")
            content = response['result'].get('content', [])
            if content:
                result_data = json.loads(content[0].get('text', '{}'))
                locations = result_data.get('locations', [])
                print(f"   Found {len(locations)} locations")
                if locations:
                    print(f"   First: {locations[0]}")
        else:
            error = response.get('error', {}) if response else {}
            print(f"❌ Tool call failed: {error.get('message', 'Unknown error')}")
            if 'error' in response:
                print(f"   Error details: {response['error']}")
        
        # Cleanup
        process.terminate()
        process.wait(timeout=5)
        
        print("\n" + "="*80)
        print("MCP Server Test Complete")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'process' in locals():
            process.terminate()
        return False


if __name__ == "__main__":
    import os
    test_mcp_server()

