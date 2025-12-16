"""
Main application for the travel agent backend.
Uses orchestrator to coordinate multiple specialized agents.
"""
import os
import sys
import asyncio
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass

from config import Config
from travel_agents.orchestrator import Orchestrator


async def main():
    """Main function to run the travel agent orchestrator."""
    
    # Validate configuration
    if not Config.validate():
        print("Error: Configuration validation failed. Please set required environment variables.")
        return
    
    # Determine Amadeus API domain based on hostname
    amadeus_domain = Config.get_amadeus_domain()
    
    print("Starting Travel Agent Orchestrator...")
    print(f"Amadeus API: {amadeus_domain}")
    print(f"Model: {Config.DEFAULT_MODEL}")
    print()
    
    # Create orchestrator
    orchestrator = Orchestrator(model=Config.DEFAULT_MODEL)
    
    try:
        print("Orchestrator initialized. Testing with sample queries...")
        print()
        
        # Test query 1: Destination discovery
        test_query_1 = """
        I'm looking for beach destinations in Europe for a relaxing vacation.
        Suggest some options and find flights from Zurich.
        """
        
        print("=" * 80)
        print("Test Query 1: Destination Discovery")
        print("=" * 80)
        print(f"Query: {test_query_1.strip()}")
        print()
        
        result_1 = await orchestrator.orchestrate(test_query_1)
        
        print("=" * 80)
        print("Orchestrator Response:")
        print("=" * 80)
        print(result_1)
        print()
        
        # Test query 2: Direct flight search
        test_query_2 = """
        Find flights from Zurich (ZRH) to Lisbon (LIS) on 2025-05-10 for 1 adult.
        Show me the available options with prices.
        """
        
        print("=" * 80)
        print("Test Query 2: Direct Flight Search")
        print("=" * 80)
        print(f"Query: {test_query_2.strip()}")
        print()
        
        result_2 = await orchestrator.orchestrate(test_query_2)
        
        print("=" * 80)
        print("Orchestrator Response:")
        print("=" * 80)
        print(result_2)
        print("=" * 80)
        
    finally:
        # Clean up resources
        await orchestrator.cleanup()
        print("\nOrchestrator cleaned up.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

