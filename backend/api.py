"""
FastAPI server for travel planning API.

Uses the LLM Orchestrator to coordinate specialized agents with
input/output validation.
"""
import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from sqlalchemy.orm import Session
import bcrypt

# Import and setup comprehensive logging
from utils.logging_config import setup_logging, get_api_logger, log_api_request, log_api_response
setup_logging(level=logging.DEBUG, enable_file_logging=True, enable_console_logging=True)
logger = get_api_logger()

# Add paths for imports
backend_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(backend_dir, '..', 'python-mcp-sandbox-openai-sdk-main', 'src'))
sys.path.insert(0, backend_dir)

from models import (
    TripRequest,
    TripPlanResponse,
    Destination,
    WorkflowResponse,
    ValidationResult,
    FlightInput,
    FlightOutput,
    FlightOption,
    HotelInput,
    HotelOutput,
    HotelOption,
    ItineraryInput,
    ItineraryOutput,
    ItineraryDay,
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from travel_agents.llm_orchestrator import LLMOrchestrator
from travel_agents.flight_agent import FlightAgent
from travel_agents.hotel_agent import HotelAgent
from travel_agents.itinerary_agent import ItineraryAgent
from config import Config
from services.image_service import fetch_destination_image, fetch_activity_image, fetch_transport_image
from services.temperature_service import fetch_temperature_range
from services.chat_service import ChatService
from database.connection import get_db, init_db
from database.models import User, UserProfile, Trip
from database.schemas import (
    UserRegister, UserLogin, UserResponse,
    UserProfileUpdate, UserProfileResponse, PaymentMethodAdd,
    TripCreate, TripUpdate, TripResponse
)

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
except ImportError:
    pass

app = FastAPI(
    title="OdyssAI Travel Planning API",
    version="2.0.0",
    description="Travel planning API with LLM-powered orchestration and validation"
)

# Configure CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    
    # Log request
    headers_dict = dict(request.headers)
    log_api_request(
        logger,
        method=request.method,
        path=str(request.url.path),
        headers=headers_dict,
        body=None  # Don't log body in middleware to avoid reading stream
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    log_api_response(
        logger,
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        response_data=None,  # Don't log full response in middleware
        duration=duration
    )
    
    return response

# Global agent instances
_orchestrator: Optional[LLMOrchestrator] = None
_flight_agent: Optional[FlightAgent] = None
_hotel_agent: Optional[HotelAgent] = None
_itinerary_agent: Optional[ItineraryAgent] = None


async def get_orchestrator() -> LLMOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LLMOrchestrator(model=Config.DEFAULT_MODEL)
    return _orchestrator


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup (non-blocking)."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def init_db_sync():
        """Synchronous database initialization."""
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            logger.error("Please ensure PostgreSQL is running and accessible")
            # Don't raise - allow server to start but endpoints will fail gracefully
    
    # Run database initialization in background to avoid blocking the event loop
    # This allows the server to start immediately while DB initializes
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    # Fire and forget - don't await, let it run in background
    loop.run_in_executor(executor, init_db_sync)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global _orchestrator, _flight_agent, _hotel_agent, _itinerary_agent
    if _orchestrator:
        await _orchestrator.cleanup()
        _orchestrator = None
    if _flight_agent:
        await _flight_agent.cleanup()
        _flight_agent = None
    if _hotel_agent:
        await _hotel_agent.cleanup()
        _hotel_agent = None
    if _itinerary_agent:
        await _itinerary_agent.cleanup()
        _itinerary_agent = None


# Helper function to get current user from header (mock auth)
async def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[int]:
    """Get current user ID from header (mock authentication)."""
    if x_user_id:
        try:
            return int(x_user_id)
        except ValueError:
            return None
    return None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "OdyssAI Travel Planning API",
        "version": "2.0.0",
        "orchestrator": "LLMOrchestrator"
    }


@app.get("/api/images/{city}")
async def get_city_image(city: str):
    """
    Fetch an image for a specific city from Unsplash.
    
    Args:
        city: Name of the city (e.g., "Zurich", "Paris")
    
    Returns:
        Dictionary with city name and image URL
    """
    try:
        image_url = fetch_destination_image(city)
        return {
            "city": city,
            "image_url": image_url
        }
    except Exception as e:
        logger.error(f"Error fetching image for {city}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching image for {city}: {str(e)}"
        )


@app.get("/api/images/transport")
async def get_transport_image(name: str, type: str = ""):
    """
    Fetch an image for a transport option from Unsplash.
    
    Args:
        name: Name of the transport (e.g., "Private Taxi", "Airport Bus")
        type: Optional transport type (taxi, uber, public, rental, walk)
    
    Returns:
        Dictionary with transport name and image URL
    """
    try:
        image_url = fetch_transport_image(name, type)
        return {
            "name": name,
            "type": type,
            "image_url": image_url
        }
    except Exception as e:
        logger.error(f"Error fetching transport image for {name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching transport image for {name}: {str(e)}"
        )


@app.post("/api/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripRequest):
    """
    Plan a trip based on user preferences.
    
    Invokes the LLM orchestrator to coordinate destination discovery
    with input/output validation.
    
    Returns:
        TripPlanResponse with discovered destinations
    """
    logger.info(f"Received plan request: {request}")
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        if not Config.validate():
            logger.error("Configuration validation failed!")
            raise HTTPException(
                status_code=500,
                detail="Server configuration is invalid. Please check environment variables."
            )
        
        logger.info("Getting LLM orchestrator...")
        orchestrator = await get_orchestrator()
        
        # Invoke destination agent through orchestrator
        logger.info("Invoking destination discovery via LLM orchestrator...")
        destinations = await orchestrator.discover_destinations_structured(request)
        
        # Fetch images and temperatures for each destination (separate from agents)
        logger.info(f"Fetching images and temperatures for {len(destinations)} destinations...")
        for destination in destinations:
            if destination.name:
                # Fetch image
                destination.image = fetch_destination_image(destination.name)
                
                # Fetch temperature if not already set or if it's a placeholder
                if not destination.temp_range or destination.temp_range == "N/A":
                    temp_range = fetch_temperature_range(destination.name, destination.country)
                    if temp_range:
                        destination.temp_range = temp_range
                        logger.info(f"Updated temperature for {destination.name}: {temp_range}")
        
        logger.info(f"Found {len(destinations)} destinations")
        return TripPlanResponse(destinations=destinations)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error planning trip: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error planning trip: {str(e)}"
        )


@app.post("/api/workflow", response_model=WorkflowResponse)
async def execute_workflow(
    request: TripRequest,
    agents: Optional[List[str]] = None
):
    """
    Execute a full workflow with validation information.
    
    This endpoint provides detailed information about the orchestration
    process, including input validation results and per-agent results.
    
    Args:
        request: TripRequest with user preferences
        agents: Optional list of agents to invoke (default: ["destination"])
    
    Returns:
        WorkflowResponse with full details including validation
    """
    logger.info(f"Received workflow request: {request}")
    logger.info(f"Agents to invoke: {agents or ['destination']}")
    
    try:
        # Validate configuration
        if not Config.validate():
            logger.error("Configuration validation failed!")
            raise HTTPException(
                status_code=500,
                detail="Server configuration is invalid. Please check environment variables."
            )
        
        orchestrator = await get_orchestrator()
        
        # Execute the full workflow
        response = await orchestrator.execute_workflow(
            request=request,
            agents_to_invoke=agents or ["destination"]
        )
        
        # Fetch images and temperatures for destinations if present
        destinations = response.get_destinations()
        if destinations:
            logger.info(f"Fetching images and temperatures for {len(destinations)} destinations...")
            for destination in destinations:
                if destination.name:
                    # Fetch image
                    destination.image = fetch_destination_image(destination.name)
                    
                    # Fetch temperature if not already set or if it's a placeholder
                    if not destination.temp_range or destination.temp_range == "N/A":
                        temp_range = fetch_temperature_range(destination.name, destination.country)
                        if temp_range:
                            destination.temp_range = temp_range
                            logger.info(f"Updated temperature for {destination.name}: {temp_range}")
            
            # Update the destinations in the response
            if "destination" in response.results and response.results["destination"].data:
                response.results["destination"].data["destinations"] = [
                    d.model_dump() for d in destinations
                ]
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error executing workflow: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error executing workflow: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Chat endpoint for conversational travel planning.
    
    Parses user messages to extract travel preferences and update form fields.
    Can ask clarifying questions when information is ambiguous.
    
    Args:
        request: ChatRequest with message, conversation history, and current form state
        
    Returns:
        ChatResponse with AI response, form updates, and clarification info
    """
    logger.info(f"Received chat request: message='{request.message[:50]}...'")
    
    try:
        # Initialize chat service
        chat_service = ChatService()
        
        # Convert ChatMessage objects to dicts for the service
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]
        
        # Process the message
        result = await chat_service.process_message(
            message=request.message,
            conversation_history=history,
            current_form_state=request.current_form_state
        )
        
        logger.info(f"Chat response generated. Updated fields: {result.get('updated_fields', [])}")
        
        return ChatResponse(**result)
    
    except Exception as e:
        import traceback
        logger.error(f"Error in chat endpoint: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@app.get("/api/agents")
async def list_agents():
    """
    List all available agents in the registry.
    
    Returns:
        Dictionary with list of available agent names
    """
    from travel_agents.agent_registry import AgentRegistry
    
    return {
        "agents": AgentRegistry.list_agents(),
        "description": "Available agents for workflow execution"
    }


async def get_flight_agent() -> FlightAgent:
    """Get or create flight agent instance."""
    global _flight_agent
    if _flight_agent is None:
        _flight_agent = FlightAgent(model=Config.DEFAULT_MODEL)
    return _flight_agent


async def get_hotel_agent() -> HotelAgent:
    """Get or create hotel agent instance."""
    global _hotel_agent
    if _hotel_agent is None:
        _hotel_agent = HotelAgent(model=Config.DEFAULT_MODEL)
    return _hotel_agent


async def get_itinerary_agent() -> ItineraryAgent:
    """Get or create itinerary agent instance."""
    global _itinerary_agent
    if _itinerary_agent is None:
        _itinerary_agent = ItineraryAgent(model=Config.DEFAULT_MODEL)
    return _itinerary_agent


@app.post("/api/flights", response_model=FlightOutput)
async def search_flights(request: FlightInput):
    """
    Search for flights between origin and destination.
    
    Args:
        request: FlightInput with search parameters:
            - origin: IATA code (e.g., "ZRH")
            - destination: IATA code (e.g., "LIS")
            - departure_date: YYYY-MM-DD format
            - return_date: Optional YYYY-MM-DD format
            - adults: Number of passengers (default: 1)
            - max_price: Optional budget filter
    
    Returns:
        FlightOutput with list of flight options
    """
    import time
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("🛫 API: /api/flights - Flight Search Request")
    logger.info("=" * 70)
    logger.info(f"  Route:      {request.origin} → {request.destination}")
    logger.info(f"  Departure:  {request.departure_date}")
    logger.info(f"  Return:     {request.return_date or 'One-way'}")
    logger.info(f"  Passengers: {request.adults}")
    logger.info(f"  Max Price:  ${request.max_price}" if request.max_price else "  Max Price:  No limit")
    logger.info("-" * 70)
    
    try:
        # Validate configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed!")
            raise HTTPException(
                status_code=500,
                detail="Server configuration is invalid. Please check environment variables."
            )
        
        # Get flight agent
        logger.info("📡 Getting Flight Agent...")
        flight_agent = await get_flight_agent()
        
        # Execute flight search
        logger.info("🔍 Executing flight search...")
        result = await flight_agent.execute(request.model_dump())
        
        elapsed = time.time() - start_time
        
        if not result.success:
            logger.error(f"❌ Flight search failed after {elapsed:.2f}s: {result.error}")
            raise HTTPException(
                status_code=500,
                detail=f"Flight search failed: {result.error}"
            )
        
        # Extract flights from result
        flights_data = result.data.get("flights", []) if result.data else []
        search_summary = result.data.get("search_summary", "") if result.data else ""
        
        logger.info("-" * 70)
        logger.info(f"✅ Flight search completed in {elapsed:.2f}s")
        logger.info(f"   Found {len(flights_data)} flights")
        
        # Log price range
        if flights_data:
            prices = [f.get('price', 0) for f in flights_data if isinstance(f, dict)]
            if prices:
                logger.info(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        
        logger.info("=" * 70)
        
        return FlightOutput(
            flights=[FlightOption(**f) if isinstance(f, dict) else f for f in flights_data],
            search_summary=search_summary
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        elapsed = time.time() - start_time
        logger.error(f"❌ Error searching flights after {elapsed:.2f}s: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error searching flights: {str(e)}"
        )


@app.post("/api/hotels", response_model=HotelOutput)
async def search_hotels(request: HotelInput):
    """
    Search for hotels in a specific city.
    
    Args:
        request: HotelInput with search parameters:
            - city_code: IATA city code (e.g., "LIS" for Lisbon)
            - check_in: Check-in date in YYYY-MM-DD format
            - check_out: Check-out date in YYYY-MM-DD format
            - guests: Number of guests (default: 1)
            - max_price_per_night: Optional maximum price per night filter
    
    Returns:
        HotelOutput with list of hotel options
    """
    import time
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("🏨 API: /api/hotels - Hotel Search Request")
    logger.info("=" * 70)
    logger.info(f"  City:        {request.city_code}")
    logger.info(f"  Check-in:    {request.check_in}")
    logger.info(f"  Check-out:   {request.check_out}")
    logger.info(f"  Guests:      {request.guests}")
    logger.info(f"  Max Price:   ${request.max_price_per_night}/night" if request.max_price_per_night else "  Max Price:   No limit")
    logger.info("-" * 70)
    
    try:
        # Validate configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed!")
            raise HTTPException(
                status_code=500,
                detail="Server configuration is invalid. Please check environment variables."
            )
        
        # Get hotel agent
        logger.info("📡 Getting Hotel Agent...")
        hotel_agent = await get_hotel_agent()
        
        # Execute hotel search
        logger.info("🔍 Executing hotel search...")
        result = await hotel_agent.execute(request.model_dump())
        
        elapsed = time.time() - start_time
        
        if not result.success:
            logger.error(f"❌ Hotel search failed after {elapsed:.2f}s: {result.error}")
            raise HTTPException(
                status_code=500,
                detail=f"Hotel search failed: {result.error}"
            )
        
        # Extract hotels from result
        hotels_data = result.data.get("hotels", []) if result.data else []
        search_summary = result.data.get("search_summary", "") if result.data else ""
        
        logger.info("-" * 70)
        logger.info(f"✅ Hotel search completed in {elapsed:.2f}s")
        logger.info(f"   Found {len(hotels_data)} hotels")
        
        # Log price range
        if hotels_data:
            prices = [h.get('price_per_night', 0) for h in hotels_data if isinstance(h, dict)]
            if prices:
                logger.info(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f} per night")
        
        logger.info("=" * 70)
        
        return HotelOutput(
            hotels=[HotelOption(**h) if isinstance(h, dict) else h for h in hotels_data],
            search_summary=search_summary
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        elapsed = time.time() - start_time
        logger.error(f"❌ Error searching hotels after {elapsed:.2f}s: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error searching hotels: {str(e)}"
        )


@app.post("/api/itinerary", response_model=ItineraryOutput)
async def generate_itinerary(request: ItineraryInput):
    """
    Generate a day-by-day itinerary with activity suggestions.
    
    Args:
        request: ItineraryInput with:
            - destination: City name
            - country: Country name
            - num_days: Number of days for the trip
            - experiences: List of preferred experience types
            - budget: Budget range (min, max)
            - traveler_type: Type of traveler (solo, couple, family, etc.)
            - group_size: Number of travelers
    
    Returns:
        ItineraryOutput with day-by-day activity suggestions
    """
    import time
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("📅 API: /api/itinerary - Itinerary Generation Request")
    logger.info("=" * 70)
    logger.info(f"  Destination:  {request.destination}, {request.country}")
    logger.info(f"  Duration:     {request.num_days} days")
    logger.info(f"  Experiences:  {', '.join(request.experiences) if request.experiences else 'None specified'}")
    logger.info(f"  Budget:       ${request.budget[0]:,} - ${request.budget[1]:,}")
    logger.info(f"  Traveler:     {request.traveler_type} ({request.group_size} people)")
    logger.info("-" * 70)
    
    try:
        # Validate configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed!")
            raise HTTPException(
                status_code=500,
                detail="Server configuration is invalid. Please check environment variables."
            )
        
        # Get itinerary agent
        logger.info("📡 Getting Itinerary Agent...")
        itinerary_agent = await get_itinerary_agent()
        
        # Execute itinerary generation
        logger.info("🔍 Generating itinerary...")
        result = await itinerary_agent.execute(request.model_dump())
        
        elapsed = time.time() - start_time
        
        if not result.success:
            logger.error(f"❌ Itinerary generation failed after {elapsed:.2f}s: {result.error}")
            raise HTTPException(
                status_code=500,
                detail=f"Itinerary generation failed: {result.error}"
            )
        
        # Extract days from result
        days_data = result.data.get("days", []) if result.data else []
        
        # Fetch images for all activities
        total_activities = sum(len(day.get("suggested_activities", [])) for day in days_data)
        if total_activities > 0:
            logger.info(f"Fetching images for {total_activities} activities...")
            for day in days_data:
                activities = day.get("suggested_activities", [])
                for activity in activities:
                    if not activity.get("image"):
                        activity_name = activity.get("name", "")
                        activity_desc = activity.get("description", "")
                        activity["image"] = fetch_activity_image(activity_name, activity_desc)
        
        logger.info("-" * 70)
        logger.info(f"✅ Itinerary generation completed in {elapsed:.2f}s")
        logger.info(f"   Generated {len(days_data)} days")
        
        # Log activity count
        if total_activities > 0:
            logger.info(f"   Total activities: {total_activities}")
            # Debug: Log URL and source for each activity
            for day in days_data:
                for activity in day.get("suggested_activities", []):
                    logger.debug(f"   Activity: {activity.get('name')[:30]}, url={activity.get('url')}, source={activity.get('source')}")
        
        logger.info("=" * 70)
        
        return ItineraryOutput(
            days=[ItineraryDay(**d) if isinstance(d, dict) else d for d in days_data]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        elapsed = time.time() - start_time
        logger.error(f"❌ Error generating itinerary after {elapsed:.2f}s: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating itinerary: {str(e)}"
        )


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password (mock - using bcrypt for demo)
        password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        new_user = User(
            email=user_data.email,
            password_hash=password_hash
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create profile if full_name provided
        if user_data.full_name:
            profile = UserProfile(
                user_id=new_user.id,
                full_name=user_data.full_name
            )
            db.add(profile)
            db.commit()
        
        logger.info(f"User registered: {new_user.email}")
        return UserResponse.model_validate(new_user)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error registering user: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        # Check if it's a database connection error
        if "could not connect" in str(e).lower() or "connection refused" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Database connection failed. Please ensure PostgreSQL is running."
            )
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")


@app.post("/api/auth/login", response_model=UserResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user (mock authentication)."""
    try:
        # Find user
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password (mock - using bcrypt)
        if not bcrypt.checkpw(credentials.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"User logged in: {user.email}")
        return UserResponse.model_validate(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error logging in: {str(e)}")


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse.model_validate(user)


# ============================================================================
# User Profile Endpoints
# ============================================================================

@app.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile."""
    # Check authorization (user can only access their own profile)
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        # Create empty profile if it doesn't exist
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return UserProfileResponse.model_validate(profile)


@app.put("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Profile updated for user {user_id}")
    return UserProfileResponse.model_validate(profile)


@app.post("/api/users/{user_id}/payment-methods")
async def add_payment_method(
    user_id: int,
    payment_method: PaymentMethodAdd,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add payment method to user profile."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    
    # Add payment method
    payment_methods = profile.payment_methods or []
    payment_methods.append(payment_method.model_dump())
    profile.payment_methods = payment_methods
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Payment method added for user {user_id}")
    return {"message": "Payment method added", "payment_methods": profile.payment_methods}


@app.get("/api/users/{user_id}/payment-methods")
async def get_payment_methods(
    user_id: int,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user payment methods."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return {"payment_methods": []}
    
    return {"payment_methods": profile.payment_methods or []}


# ============================================================================
# Trip Management Endpoints
# ============================================================================

@app.get("/api/users/{user_id}/trips", response_model=List[TripResponse])
async def get_user_trips(
    user_id: int,
    status: Optional[str] = None,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user trips with optional status filter."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Trip).filter(Trip.user_id == user_id)
    if status:
        query = query.filter(Trip.status == status)
    
    trips = query.order_by(Trip.created_at.desc()).all()
    return [TripResponse.model_validate(trip) for trip in trips]


@app.post("/api/users/{user_id}/trips", response_model=TripResponse)
async def create_trip(
    user_id: int,
    trip_data: TripCreate,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trip."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_trip = Trip(
        user_id=user_id,
        status=trip_data.status,
        booking_reference=trip_data.booking_reference,
        trip_data=trip_data.trip_data
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    
    logger.info(f"Trip created for user {user_id}: {new_trip.id}")
    return TripResponse.model_validate(new_trip)


@app.put("/api/users/{user_id}/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    user_id: int,
    trip_id: int,
    trip_data: TripUpdate,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a trip."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Update fields
    update_data = trip_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trip, key, value)
    
    db.commit()
    db.refresh(trip)
    
    logger.info(f"Trip updated: {trip_id}")
    return TripResponse.model_validate(trip)


@app.delete("/api/users/{user_id}/trips/{trip_id}")
async def delete_trip(
    user_id: int,
    trip_id: int,
    current_user_id: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trip."""
    # Check authorization
    if not current_user_id or current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    db.delete(trip)
    db.commit()
    
    logger.info(f"Trip deleted: {trip_id}")
    return {"message": "Trip deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
