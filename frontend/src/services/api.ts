import { Destination, Flight, Hotel } from '@/data/mockAgentData';

export interface TripRequest {
  origin: string;
  destinations: string[];
  surprise_me: boolean;
  date_ranges: { from: string; to: string }[];
  duration: [number, number];
  traveler_type: string;
  group_size: number;
  budget: [number, number];
  accommodation: string | null;
  experiences: string[];
}

export interface FlightSearchRequest {
  origin: string;           // IATA code (e.g., "ZRH")
  destination: string;      // IATA code (e.g., "LIS")
  departure_date: string;   // YYYY-MM-DD format
  return_date?: string;     // YYYY-MM-DD format (optional)
  adults: number;           // Number of passengers
  max_price?: number;       // Budget filter (optional)
}

export interface HotelSearchRequest {
  city_code: string;        // IATA city code (e.g., "LIS" for Lisbon)
  check_in: string;         // YYYY-MM-DD format
  check_out: string;        // YYYY-MM-DD format
  guests: number;           // Number of guests
  max_price_per_night?: number;  // Optional maximum price per night filter
}

// Backend response format
interface FlightOptionResponse {
  id: string;
  airline: string;
  departure_time: string;
  arrival_time: string;
  departure_airport: string;
  arrival_airport: string;
  duration: string;
  stops: number;
  price: number;
  currency: string;
  flight_number?: string;
  return_flight_number?: string;
  return_departure_time?: string;
  return_arrival_time?: string;
  return_departure_airport?: string;
  return_arrival_airport?: string;
}

interface FlightSearchResponse {
  flights: FlightOptionResponse[];
  search_summary: string;
}

// Backend hotel response format
interface HotelOptionResponse {
  id: string;
  name: string;
  address: string;
  rating: number | null;
  review_count: number | null;
  image_url: string | null;
  price_per_night: number;
  total_price: number;
  currency: string;
  amenities: string[];
}

interface HotelSearchResponse {
  hotels: HotelOptionResponse[];
  search_summary: string;
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Chat message interface
 */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Chat request interface
 */
export interface ChatRequest {
  message: string;
  conversation_history: ChatMessage[];
  current_form_state?: any;
}

/**
 * Chat response interface
 */
export interface ChatResponse {
  response: string;
  form_updates: Record<string, any>;
  needs_clarification: boolean;
  clarification_question?: string;
  updated_fields: string[];
}

/**
 * Get a different stock hotel image for each hotel based on index
 */
function getHotelStockImage(index: number): string {
  const hotelStockImages = [
    'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80',  // Modern luxury hotel
    'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80',  // Elegant hotel lobby
    'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800&q=80',  // Hotel room with view
    'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800&q=80',  // Resort pool area
    'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80',  // Hotel exterior
    'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80',  // Luxury suite
    'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&q=80',  // Modern hotel room
    'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80',  // Hotel balcony view
    'https://images.unsplash.com/photo-1596436889106-be35e843f974?w=800&q=80',  // Boutique hotel
    'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800&q=80',  // Hotel restaurant
  ];
  return hotelStockImages[index % hotelStockImages.length];
}

export async function planTrip(request: TripRequest): Promise<Destination[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const destinations = data.destinations || [];
    // Map snake_case from backend to camelCase for frontend
    return destinations.map((dest: any) => ({
      ...dest,
      iataCode: dest.iata_code || dest.iataCode,
      matchReason: dest.match_reason || dest.matchReason,
      tempRange: dest.temp_range || dest.tempRange || dest.avg_temp || dest.avgTemp || 'N/A', // Support both new and old field names
    }));
  } catch (error) {
    console.error('Error planning trip:', error);
    throw error;
  }
}

/**
 * Extract IATA code from origin string (e.g., "Zurich, Switzerland (ZRH)" -> "ZRH")
 */
export function extractIataCode(origin: string): string {
  // Try to match pattern like "(ZRH)" or "ZRH"
  const match = origin.match(/\(([A-Z]{3})\)/) || origin.match(/\b([A-Z]{3})\b/);
  return match ? match[1] : origin.substring(0, 3).toUpperCase();
}

/**
 * Get airline logo image path based on airline code
 * Uses logos from data/airlines_logos directory
 */
function getAirlineLogo(airline: string): string {
  // Extract airline code (first 2 characters, uppercase)
  const code = airline.substring(0, 2).toUpperCase();
  // Return path to logo image
  return `/data/airlines_logos/${code}.png`;
}

/**
 * Get airline name from code
 */
function getAirlineName(code: string): string {
  const names: Record<string, string> = {
    'LX': 'Swiss',
    'LH': 'Lufthansa',
    'EK': 'Emirates',
    'DL': 'Delta',
    'UA': 'United',
    'AA': 'American Airlines',
    'BA': 'British Airways',
    'AF': 'Air France',
    'KL': 'KLM',
    'TP': 'TAP Portugal',
    'IB': 'Iberia',
    'TK': 'Turkish Airlines',
    'FR': 'Ryanair',
    'U2': 'EasyJet',
    'VY': 'Vueling',
  };
  return names[code] || code;
}

/**
 * Search for flights using the backend API
 */
export async function searchFlights(request: FlightSearchRequest): Promise<Flight[]> {
  try {
    console.log('Searching flights with request:', request);
    
    const response = await fetch(`${API_BASE_URL}/api/flights`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: FlightSearchResponse = await response.json();
    const flights = data.flights || [];
    
    console.log(`Found ${flights.length} flights`);
    
    // Map backend response to frontend Flight interface
    return flights.map((flight: FlightOptionResponse, index: number) => {
      // Backend returns airline as code (e.g., "LX"), we need both name and code
      const airlineCode = flight.airline.toUpperCase();
      return {
        id: flight.id || `flight-${index + 1}`,
        airline: getAirlineName(airlineCode),
        airlineCode: airlineCode,  // Preserve the code for logo lookup
        airlineLogo: getAirlineLogo(airlineCode),
        departureTime: flight.departure_time,
        arrivalTime: flight.arrival_time,
        departureAirport: flight.departure_airport || request.origin,
        arrivalAirport: flight.arrival_airport || request.destination,
        duration: flight.duration,
        stops: flight.stops,
        price: flight.price,
        class: 'Economy', // Default class - not returned by API
        flightNumber: flight.flight_number,
        returnFlightNumber: flight.return_flight_number,
        returnDepartureTime: flight.return_departure_time,
        returnArrivalTime: flight.return_arrival_time,
        returnDepartureAirport: flight.return_departure_airport,
        returnArrivalAirport: flight.return_arrival_airport,
      };
    });
  } catch (error) {
    console.error('Error searching flights:', error);
    throw error;
  }
}

/**
 * Search for hotels using the backend API
 */
export async function searchHotels(request: HotelSearchRequest): Promise<Hotel[]> {
  try {
    console.log('Searching hotels with request:', request);
    
    const response = await fetch(`${API_BASE_URL}/api/hotels`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: HotelSearchResponse = await response.json();
    const hotels = data.hotels || [];
    
    console.log(`Found ${hotels.length} hotels`);
    
    // Map backend response to frontend Hotel interface
    return hotels.map((hotel: HotelOptionResponse, index: number) => ({
      id: hotel.id || `hotel-${index + 1}`,
      name: hotel.name,
      stars: hotel.rating ? Math.round(hotel.rating) : 4, // Convert rating to stars, default to 4
      image: hotel.image_url || getHotelStockImage(index), // Use provided image or different stock image for each hotel
      pricePerNight: hotel.price_per_night,
      amenities: hotel.amenities && hotel.amenities.length > 0 
        ? hotel.amenities 
        : ['WiFi', 'Air Conditioning', 'Room Service'], // Default amenities
      location: hotel.address || request.city_code, // Use address or fallback to city code
      rating: hotel.rating || 0, // Use rating if available, else 0
      reviewCount: hotel.review_count || 0, // Use review count if available, else 0
    }));
  } catch (error) {
    console.error('Error searching hotels:', error);
    throw error;
  }
}

/**
 * Itinerary generation request interface
 */
export interface ItineraryRequest {
  destination: string;
  country: string;
  num_days: number;
  experiences: string[];
  budget: [number, number];
  traveler_type: string;
  group_size: number;
}

/**
 * Activity suggestion from backend
 */
export interface ItineraryActivityResponse {
  id: string;
  name: string;
  description: string;
  duration: string;
  estimated_price: number;
  category: string;
  time_of_day: string;
  image?: string;  // Image URL from Unsplash
}

/**
 * Day itinerary from backend
 */
export interface ItineraryDayResponse {
  day: number;
  date_label: string;
  suggested_activities: ItineraryActivityResponse[];
}

/**
 * Itinerary response from backend
 */
interface ItineraryResponse {
  days: ItineraryDayResponse[];
}

/**
 * Generate itinerary suggestions for a destination
 */
export async function generateItinerary(request: ItineraryRequest): Promise<ItineraryDayResponse[]> {
  try {
    console.log('Generating itinerary with request:', request);
    
    const response = await fetch(`${API_BASE_URL}/api/itinerary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: ItineraryResponse = await response.json();
    const days = data.days || [];
    
    console.log(`Generated itinerary with ${days.length} days`);
    
    return days;
  } catch (error) {
    console.error('Error generating itinerary:', error);
    throw error;
  }
}

/**
 * Chat with the travel assistant
 */
export async function chatWithAssistant(
  message: string,
  conversationHistory: ChatMessage[],
  currentFormState?: any
): Promise<ChatResponse> {
  try {
    const request: ChatRequest = {
      message,
      conversation_history: conversationHistory,
      current_form_state: currentFormState,
    };

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error chatting with assistant:', error);
    throw error;
  }
}

