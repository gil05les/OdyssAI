"""
Pydantic models for API request/response types.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class AgentType(str, Enum):
    """Types of available agents."""
    DESTINATION = "destination"
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSPORT = "transport"
    ITINERARY = "itinerary"


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# =============================================================================
# Request Models
# =============================================================================

class TripRequest(BaseModel):
    """Request model for trip planning."""
    origin: str  # Origin city/airport
    destinations: List[str]  # User-specified destinations (or empty for surprise)
    surprise_me: bool
    date_ranges: List[dict]  # [{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}]
    duration: Tuple[int, int]  # min, max days
    traveler_type: str  # solo, couple, family, group
    group_size: int
    budget: Tuple[int, int]  # min, max
    accommodation: Optional[str] = None
    experiences: List[str]
    environments: List[str] = Field(default_factory=list)  # beach, mountains, city, countryside, desert, jungle
    climate: Optional[str] = None  # tropical, mild, cold, any
    trip_vibe: Optional[str] = None  # relaxing, active, balanced, party
    distance_preference: Optional[str] = None  # close, far, offbeat, any
    trip_purpose: Optional[str] = None  # vacation, workation, honeymoon, reunion


# =============================================================================
# Agent-Specific Input/Output Models
# =============================================================================

class DestinationInput(BaseModel):
    """Input schema for destination agent."""
    origin: str
    destinations: List[str] = Field(default_factory=list)
    surprise_me: bool = True
    experiences: List[str] = Field(default_factory=list)
    budget: Tuple[int, int] = (0, 10000)
    duration: Tuple[int, int] = (1, 14)
    traveler_type: str = "solo"
    group_size: int = 1
    date_ranges: List[dict] = Field(default_factory=list)
    accommodation: Optional[str] = None
    environments: List[str] = Field(default_factory=list)  # beach, mountains, city, countryside, desert, jungle
    climate: Optional[str] = None  # tropical, mild, cold, any
    trip_vibe: Optional[str] = None  # relaxing, active, balanced, party
    distance_preference: Optional[str] = None  # close, far, offbeat, any
    trip_purpose: Optional[str] = None  # vacation, workation, honeymoon, reunion


class Destination(BaseModel):
    """Destination model matching frontend interface."""
    id: str
    name: str
    country: str
    description: str
    match_reason: str
    image: str = ""
    temp_range: str  # Temperature range in format "min-max°C" (e.g., "15-25°C")
    iata_code: str  # Airport code for next steps


class DestinationOutput(BaseModel):
    """Output schema for destination agent."""
    destinations: List[Destination]


class FlightInput(BaseModel):
    """Input schema for flight agent."""
    origin: str  # IATA code
    destination: str  # IATA code
    departure_date: str  # YYYY-MM-DD
    return_date: Optional[str] = None  # YYYY-MM-DD
    adults: int = 1
    max_price: Optional[float] = None


class FlightOption(BaseModel):
    """Individual flight option."""
    id: str
    airline: str
    departure_time: str
    arrival_time: str
    departure_airport: str = ""
    arrival_airport: str = ""
    duration: str
    stops: int
    price: float
    currency: str = "CHF"
    flight_number: Optional[str] = None  # Outbound flight number (e.g., "LX123")
    return_flight_number: Optional[str] = None  # Return flight number (e.g., "LX456")
    return_departure_time: Optional[str] = None  # Return departure time
    return_arrival_time: Optional[str] = None  # Return arrival time
    return_departure_airport: Optional[str] = None  # Return departure airport
    return_arrival_airport: Optional[str] = None  # Return arrival airport


class FlightOutput(BaseModel):
    """Output schema for flight agent."""
    flights: List[FlightOption] = Field(default_factory=list)
    search_summary: str = ""


class HotelInput(BaseModel):
    """Input schema for hotel agent."""
    city_code: str  # IATA city code
    check_in: str  # YYYY-MM-DD
    check_out: str  # YYYY-MM-DD
    guests: int = 1
    max_price_per_night: Optional[float] = None


class HotelOption(BaseModel):
    """Individual hotel option."""
    id: str
    name: str
    address: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    price_per_night: float
    total_price: float
    currency: str = "CHF"
    amenities: List[str] = Field(default_factory=list)


class HotelOutput(BaseModel):
    """Output schema for hotel agent."""
    hotels: List[HotelOption] = Field(default_factory=list)
    search_summary: str = ""


class TransportInput(BaseModel):
    """Input schema for transport/car rental agent."""
    pickup_iata: str  # IATA code of pickup airport
    pickup_date: str  # YYYY-MM-DD
    dropoff_date: str  # YYYY-MM-DD
    pickup_time: Optional[str] = None  # HH:MM
    dropoff_time: Optional[str] = None  # HH:MM


class CarRentalOption(BaseModel):
    """Individual car rental option."""
    id: str
    company: str
    vehicle_type: str
    vehicle_name: str
    price_per_day: float
    total_price: float
    currency: str = "CHF"
    features: List[str] = Field(default_factory=list)


class TransportOutput(BaseModel):
    """Output schema for transport agent."""
    car_rentals: List[CarRentalOption] = Field(default_factory=list)
    search_summary: str = ""


class ItineraryInput(BaseModel):
    """Input schema for itinerary agent."""
    destination: str  # City name
    country: str
    num_days: int
    experiences: List[str] = Field(default_factory=list)  # User preferences (culture, food, adventure, etc.)
    budget: Tuple[int, int]
    traveler_type: str
    group_size: int


class ItineraryActivity(BaseModel):
    """Individual activity suggestion."""
    id: str
    name: str
    description: str
    duration: str  # e.g., "2 hours"
    estimated_price: float
    category: str  # Culture, Food, Adventure, etc.
    time_of_day: str  # morning, afternoon, evening
    image: Optional[str] = None  # Image URL from Unsplash


class ItineraryDay(BaseModel):
    """Itinerary for a single day."""
    day: int
    date_label: str  # e.g., "Day 1 - Arrival"
    suggested_activities: List[ItineraryActivity] = Field(default_factory=list)


class ItineraryOutput(BaseModel):
    """Output schema for itinerary agent."""
    days: List[ItineraryDay] = Field(default_factory=list)


# =============================================================================
# Validation Models
# =============================================================================

class ValidationIssue(BaseModel):
    """Individual validation issue."""
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


class ValidationResult(BaseModel):
    """Result of input or output validation."""
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    
    @property
    def errors(self) -> List[str]:
        """Get error messages only."""
        return [issue.message for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[str]:
        """Get warning messages only."""
        return [issue.message for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


# =============================================================================
# Agent Result Models
# =============================================================================

class AgentResult(BaseModel):
    """Result from a single agent execution."""
    agent_type: AgentType
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation: ValidationResult = Field(default_factory=lambda: ValidationResult(is_valid=True))
    retry_count: int = 0


# =============================================================================
# Workflow Response Models
# =============================================================================

class WorkflowResponse(BaseModel):
    """Response from the orchestrator workflow."""
    success: bool
    results: Dict[str, AgentResult] = Field(default_factory=dict)
    input_validation: ValidationResult = Field(default_factory=lambda: ValidationResult(is_valid=True))
    errors: List[str] = Field(default_factory=list)
    
    def get_destinations(self) -> List[Destination]:
        """Extract destinations from results if available."""
        dest_result = self.results.get("destination")
        if dest_result and dest_result.success and dest_result.data:
            destinations_data = dest_result.data.get("destinations", [])
            return [Destination(**d) if isinstance(d, dict) else d for d in destinations_data]
        return []


class TripPlanResponse(BaseModel):
    """Response model for trip planning."""
    destinations: List[Destination]


# =============================================================================
# Chat Models
# =============================================================================

class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    current_form_state: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    form_updates: Dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    updated_fields: List[str] = Field(default_factory=list)  # List of field names that were updated

