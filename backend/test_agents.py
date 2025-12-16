"""
Test script for the multi-agent system.

Tests individual agents, the LLM orchestrator, and validation logic.
"""
import os
import sys
import asyncio
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from config import Config
from models import TripRequest, ValidationSeverity
from travel_agents.destination_agent import DestinationAgent
from travel_agents.flight_agent import FlightAgent
from travel_agents.llm_orchestrator import LLMOrchestrator
from travel_agents.agent_registry import AgentRegistry
from travel_agents.base_agent import BaseAgent


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_subheader(text: str):
    """Print a formatted subheader."""
    print(f"\n{Colors.CYAN}--- {text} ---{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")


# =============================================================================
# Test Data
# =============================================================================

VALID_TRIP_REQUEST = TripRequest(
    origin="Zurich",
    destinations=[],
    surprise_me=True,
    date_ranges=[{"from": "2025-06-01", "to": "2025-06-10"}],
    duration=(5, 10),
    traveler_type="couple",
    group_size=2,
    budget=(2000, 5000),
    experiences=["beach", "culture"]
)

INVALID_TRIP_REQUEST = TripRequest(
    origin="",  # Empty origin - ERROR
    destinations=[],
    surprise_me=False,  # No destinations + surprise_me=False - WARNING
    date_ranges=[{"from": "2025-01-01", "to": "2024-12-01"}],  # End before start - ERROR
    duration=(-1, 10),  # Negative duration - ERROR
    traveler_type="solo",
    group_size=5,  # Inconsistent with solo - WARNING
    budget=(-100, 5000),  # Negative budget - ERROR
    experiences=[]
)


# =============================================================================
# Test Functions
# =============================================================================

async def test_configuration():
    """Test 1: Configuration validation."""
    print_header("Test 1: Configuration Validation")
    
    if not Config.validate():
        print_error("Configuration validation failed!")
        print_info("Required environment variables:")
        print("  - AMADEUS_CLIENT_ID")
        print("  - AMADEUS_CLIENT_SECRET")
        print("  - OPENAI_API_KEY (for agents)")
        return False
    
    print_success("Configuration is valid")
    print_info(f"Amadeus API: {Config.get_amadeus_domain()}")
    print_info(f"Model: {Config.DEFAULT_MODEL}")
    return True


async def test_agent_registry():
    """Test 2: Agent Registry."""
    print_header("Test 2: Agent Registry")
    
    try:
        # List available agents
        agents = AgentRegistry.list_agents()
        print_info(f"Registered agents: {agents}")
        
        if len(agents) < 4:
            print_warning(f"Expected 4 agents, found {len(agents)}")
        
        # Check each agent type
        expected_agents = ["destination", "flight", "hotel", "transport"]
        all_found = True
        
        for agent_name in expected_agents:
            if AgentRegistry.has_agent(agent_name):
                print_success(f"Agent '{agent_name}' is registered")
                
                # Verify it's a BaseAgent subclass
                agent_class = AgentRegistry.get(agent_name)
                if agent_class and issubclass(agent_class, BaseAgent):
                    print_success(f"  → Extends BaseAgent correctly")
                else:
                    print_error(f"  → Does not extend BaseAgent")
                    all_found = False
            else:
                print_error(f"Agent '{agent_name}' not found")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print_error(f"Agent registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_input_validation():
    """Test 3: Input Validation."""
    print_header("Test 3: Input Validation (LLM Orchestrator)")
    
    try:
        orchestrator = LLMOrchestrator()
        
        # Test valid request
        print_subheader("Testing valid request")
        valid_result = orchestrator._validate_trip_request(VALID_TRIP_REQUEST)
        
        if valid_result.is_valid:
            print_success("Valid request passed validation")
        else:
            print_error("Valid request failed validation (unexpected)")
            for issue in valid_result.issues:
                print(f"  [{issue.severity.value}] {issue.field}: {issue.message}")
            return False
        
        # Test invalid request
        print_subheader("Testing invalid request")
        invalid_result = orchestrator._validate_trip_request(INVALID_TRIP_REQUEST)
        
        if not invalid_result.is_valid:
            print_success("Invalid request correctly rejected")
        else:
            print_error("Invalid request passed validation (unexpected)")
            return False
        
        # Check that errors and warnings are detected
        errors = [i for i in invalid_result.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in invalid_result.issues if i.severity == ValidationSeverity.WARNING]
        
        print_info(f"Found {len(errors)} errors and {len(warnings)} warnings:")
        for issue in invalid_result.issues:
            if issue.severity == ValidationSeverity.ERROR:
                print(f"  {Colors.RED}[ERROR]{Colors.RESET} {issue.field}: {issue.message}")
            else:
                print(f"  {Colors.YELLOW}[WARNING]{Colors.RESET} {issue.field}: {issue.message}")
        
        if len(errors) >= 3:  # We expect at least: empty origin, invalid dates, negative duration, negative budget
            print_success(f"Detected expected validation errors ({len(errors)})")
        else:
            print_warning(f"Expected more errors, found {len(errors)}")
        
        return True
        
    except Exception as e:
        print_error(f"Input validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_destination_agent():
    """Test 4: Destination Agent."""
    print_header("Test 4: Destination Agent")
    
    try:
        agent = DestinationAgent(model=Config.DEFAULT_MODEL, use_flights_mcp=True)
        
        # Check agent type and schemas
        print_subheader("Checking agent interface")
        print_info(f"Agent type: {agent.agent_type.value}")
        print_info(f"Input schema: {agent.get_input_schema().__name__}")
        print_info(f"Output schema: {agent.get_output_schema().__name__}")
        
        print_subheader("Testing destination discovery")
        query = "I'm looking for beach destinations in Europe for a relaxing vacation."
        print_info(f"Query: {query}")
        
        result = await agent.discover_destinations(query)
        
        if result and len(result) > 50:  # Basic check that we got a response
            print_success("Destination agent returned results")
            print(f"\n{Colors.YELLOW}Sample response (first 200 chars):{Colors.RESET}")
            print(result[:200] + "...")
            await agent.cleanup()
            return True
        else:
            print_error("Destination agent returned empty or too short response")
            await agent.cleanup()
            return False
            
    except Exception as e:
        print_error(f"Destination agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_flight_agent():
    """Test 5: Flight Agent."""
    print_header("Test 5: Flight Agent")
    
    try:
        agent = FlightAgent(model=Config.DEFAULT_MODEL)
        
        # Check agent type and schemas
        print_subheader("Checking agent interface")
        print_info(f"Agent type: {agent.agent_type.value}")
        print_info(f"Input schema: {agent.get_input_schema().__name__}")
        print_info(f"Output schema: {agent.get_output_schema().__name__}")
        
        print_subheader("Testing flight search")
        query = "Find flights from Zurich (ZRH) to Lisbon (LIS) on 2025-05-10 for 1 adult"
        print_info(f"Query: {query}")
        
        result = await agent.handle_flight_query(query)
        
        if result and len(result) > 50:
            print_success("Flight agent returned results")
            print(f"\n{Colors.YELLOW}Sample response (first 200 chars):{Colors.RESET}")
            print(result[:200] + "...")
            await agent.cleanup()
            return True
        else:
            print_error("Flight agent returned empty or too short response")
            await agent.cleanup()
            return False
            
    except Exception as e:
        print_error(f"Flight agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_orchestrator_workflow():
    """Test 6: LLM Orchestrator Workflow."""
    print_header("Test 6: LLM Orchestrator Workflow")
    
    try:
        orchestrator = LLMOrchestrator(model=Config.DEFAULT_MODEL)
        
        print_subheader("Executing workflow with destination agent")
        print_info(f"Request: {VALID_TRIP_REQUEST.origin} -> surprise destinations")
        print_info(f"Budget: ${VALID_TRIP_REQUEST.budget[0]:,} - ${VALID_TRIP_REQUEST.budget[1]:,}")
        print_info(f"Experiences: {', '.join(VALID_TRIP_REQUEST.experiences)}")
        
        response = await orchestrator.execute_workflow(
            request=VALID_TRIP_REQUEST,
            agents_to_invoke=["destination"]
        )
        
        # Check response structure
        print_subheader("Checking response")
        print_info(f"Success: {response.success}")
        print_info(f"Input validation valid: {response.input_validation.is_valid}")
        print_info(f"Errors: {response.errors}")
        print_info(f"Results keys: {list(response.results.keys())}")
        
        if response.success:
            print_success("Workflow completed successfully")
            
            # Check destinations
            destinations = response.get_destinations()
            print_info(f"Found {len(destinations)} destinations:")
            
            for dest in destinations:
                print(f"  - {dest.name}, {dest.country} ({dest.iata_code})")
            
            if len(destinations) >= 3:
                print_success("Got expected number of destinations (3+)")
            else:
                print_warning(f"Expected 3+ destinations, got {len(destinations)}")
            
            await orchestrator.cleanup()
            return True
        else:
            print_error("Workflow failed")
            for error in response.errors:
                print(f"  Error: {error}")
            await orchestrator.cleanup()
            return False
            
    except Exception as e:
        print_error(f"LLM orchestrator workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_backward_compatibility():
    """Test 7: Backward Compatibility."""
    print_header("Test 7: Backward Compatibility (discover_destinations_structured)")
    
    try:
        orchestrator = LLMOrchestrator(model=Config.DEFAULT_MODEL)
        
        print_subheader("Testing backward-compatible method")
        destinations = await orchestrator.discover_destinations_structured(VALID_TRIP_REQUEST)
        
        if destinations and len(destinations) > 0:
            print_success(f"Got {len(destinations)} destinations via backward-compatible method")
            for dest in destinations:
                print(f"  - {dest.name}, {dest.country}")
            await orchestrator.cleanup()
            return True
        else:
            print_error("No destinations returned")
            await orchestrator.cleanup()
            return False
            
    except Exception as e:
        print_error(f"Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_execute_with_validation():
    """Test 8: Agent Execute with Validation."""
    print_header("Test 8: Agent Execute with Validation")
    
    try:
        agent = DestinationAgent(model=Config.DEFAULT_MODEL, use_flights_mcp=True)
        
        print_subheader("Testing execute_with_validation method")
        
        # Prepare input matching the agent's input schema
        agent_input = {
            "origin": "Zurich",
            "destinations": [],
            "surprise_me": True,
            "experiences": ["beach", "adventure"],
            "budget": (1000, 3000),
            "duration": (5, 10),
            "traveler_type": "solo",
            "group_size": 1,
            "date_ranges": [{"from": "2025-07-01", "to": "2025-07-15"}],
            "accommodation": "hotel"
        }
        
        print_info(f"Input: origin={agent_input['origin']}, experiences={agent_input['experiences']}")
        
        result = await agent.execute_with_validation(agent_input, max_retries=1)
        
        print_info(f"Success: {result.success}")
        print_info(f"Agent type: {result.agent_type.value}")
        print_info(f"Validation valid: {result.validation.is_valid}")
        print_info(f"Retry count: {result.retry_count}")
        
        if result.success:
            print_success("Agent execution with validation succeeded")
            
            if result.data and "destinations" in result.data:
                print_info(f"Got {len(result.data['destinations'])} destinations")
            
            await agent.cleanup()
            return True
        else:
            print_error(f"Agent execution failed: {result.error}")
            await agent.cleanup()
            return False
            
    except Exception as e:
        print_error(f"Execute with validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Test Runners
# =============================================================================

async def run_all_tests():
    """Run all tests and report results."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("OdyssAI Agent Testing Suite (v2.0 - LLM Orchestrator)")
    print("=" * 80)
    print(f"{Colors.RESET}")
    
    tests = [
        ("Configuration", test_configuration),
        ("Agent Registry", test_agent_registry),
        ("Input Validation", test_input_validation),
        ("Destination Agent", test_destination_agent),
        ("Flight Agent", test_flight_agent),
        ("LLM Orchestrator Workflow", test_llm_orchestrator_workflow),
        ("Backward Compatibility", test_orchestrator_backward_compatibility),
        ("Agent Execute with Validation", test_agent_execute_with_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1


async def run_quick_test():
    """Run a quick smoke test."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Quick Smoke Test (LLM Orchestrator){Colors.RESET}\n")
    
    if not await test_configuration():
        return 1
    
    print_info("Running quick validation test...")
    orchestrator = LLMOrchestrator(model=Config.DEFAULT_MODEL)
    
    # Test validation only (no API calls)
    validation = orchestrator._validate_trip_request(VALID_TRIP_REQUEST)
    if validation.is_valid:
        print_success("Input validation working")
    else:
        print_error("Input validation failed")
        return 1
    
    print_info("Running quick workflow test...")
    
    try:
        response = await orchestrator.execute_workflow(
            request=VALID_TRIP_REQUEST,
            agents_to_invoke=["destination"]
        )
        
        if response.success:
            print_success("Quick test passed!")
            destinations = response.get_destinations()
            print(f"\nFound {len(destinations)} destinations:")
            for dest in destinations[:3]:  # Show first 3
                print(f"  - {dest.name}, {dest.country}")
            return 0
        else:
            print_error(f"Quick test failed: {response.errors}")
            return 1
    except Exception as e:
        print_error(f"Quick test failed: {e}")
        return 1
    finally:
        await orchestrator.cleanup()


async def run_validation_only():
    """Run validation tests only (no API calls)."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Validation Tests Only{Colors.RESET}\n")
    
    tests = [
        ("Configuration", test_configuration),
        ("Agent Registry", test_agent_registry),
        ("Input Validation", test_input_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Validation tests: {passed}/{total} passed{Colors.RESET}\n")
    return 0 if passed == total else 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the OdyssAI agent system")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke test only"
    )
    parser.add_argument(
        "--validation",
        action="store_true",
        help="Run validation tests only (no API calls)"
    )
    parser.add_argument(
        "--test",
        choices=["config", "registry", "validation", "destination", "flight", "orchestrator", "workflow"],
        help="Run a specific test"
    )
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            exit_code = asyncio.run(run_quick_test())
        elif args.validation:
            exit_code = asyncio.run(run_validation_only())
        elif args.test == "config":
            exit_code = 0 if asyncio.run(test_configuration()) else 1
        elif args.test == "registry":
            exit_code = 0 if asyncio.run(test_agent_registry()) else 1
        elif args.test == "validation":
            exit_code = 0 if asyncio.run(test_input_validation()) else 1
        elif args.test == "destination":
            exit_code = 0 if asyncio.run(test_destination_agent()) else 1
        elif args.test == "flight":
            exit_code = 0 if asyncio.run(test_flight_agent()) else 1
        elif args.test == "orchestrator" or args.test == "workflow":
            exit_code = 0 if asyncio.run(test_llm_orchestrator_workflow()) else 1
        else:
            exit_code = asyncio.run(run_all_tests())
        
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
