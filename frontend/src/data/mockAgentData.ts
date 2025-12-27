// Preference match interfaces for different entity types
export interface FlightPreferenceMatch {
  airline_match: boolean;
  direct_match: boolean;
  price_match: boolean;
  time_match: boolean;
  reasons: string[];
}

export interface HotelPreferenceMatch {
  star_rating_match: boolean;
  amenities_match: boolean;
  price_match: boolean;
  reasons: string[];
}

export interface ActivityPreferenceMatch {
  category_match: boolean;
  pace_match: boolean;
  reasons: string[];
}

export interface TransportPreferenceMatch {
  mode_match: boolean;
  price_match: boolean;
  reasons: string[];
}

export interface Destination {
  id: string;
  name: string;
  country: string;
  description: string;
  matchReason: string;
  image: string;
  tempRange: string; // Temperature range in format "min-max°C" (e.g., "15-25°C")
  iataCode?: string; // Airport IATA code for arrival
  airportName?: string; // Airport name for arrival
}

export interface Flight {
  id: string;
  airline: string;
  airlineCode?: string;  // Airline code (e.g., "LX", "LH") for logo lookup
  airlineLogo: string;
  departureTime: string;
  arrivalTime: string;
  departureAirport: string;
  arrivalAirport: string;
  duration: string;
  stops: number;
  price: number;
  class: string;
  flightNumber?: string;  // Outbound flight number (e.g., "LX123")
  returnFlightNumber?: string;  // Return flight number (e.g., "LX456")
  returnDepartureTime?: string;  // Return departure time
  returnArrivalTime?: string;  // Return arrival time
  returnDepartureAirport?: string;  // Return departure airport
  returnArrivalAirport?: string;  // Return arrival airport
  // Preference matching fields
  preference_match?: FlightPreferenceMatch | null;
  preference_score?: number | null;  // 0-100 score
}

export interface Hotel {
  id: string;
  name: string;
  stars: number;
  image: string;
  pricePerNight: number;
  amenities: string[];
  location: string;
  address?: string; // Full address from backend (if available)
  rating: number;
  reviewCount: number;
  // Preference matching fields
  preference_match?: HotelPreferenceMatch | null;
  preference_score?: number | null;  // 0-100 score
}

export interface Activity {
  id: string;
  name: string;
  description: string;
  duration: string;
  price: number;
  image: string;
  category: string;
  url?: string | null;  // Yelp URL for clickable links
  source?: 'yelp' | 'llm';  // Source of the activity
  // Preference matching fields
  preference_match?: ActivityPreferenceMatch | null;
  preference_score?: number | null;  // 0-100 score
}

export interface ItineraryDay {
  day: number;
  date: string;
  activities: Activity[];
}

export interface TransportLeg {
  id: string;
  from: string;
  to: string;
  options: TransportOption[];
}

export interface TransportOption {
  id: string;
  type: 'taxi' | 'uber' | 'public' | 'rental' | 'walk';
  name: string;
  duration: string;
  price: number;
  icon: string;
  image?: string;  // Image URL from Unsplash
  source: 'api' | 'llm';  // Source of the transport option
  // Preference matching fields
  preference_match?: TransportPreferenceMatch | null;
  preference_score?: number | null;  // 0-100 score
}

export const mockDestinations: Destination[] = [
  {
    id: 'dest-1',
    name: 'Santorini',
    country: 'Greece',
    description: 'Iconic white-washed buildings with stunning caldera views and legendary sunsets.',
    matchReason: 'Perfect for romantic getaways & photography lovers',
    image: 'https://images.unsplash.com/photo-1613395877344-13d4a8e0d49e?w=800',
    tempRange: '22-30°C'
  },
  {
    id: 'dest-2',
    name: 'Kyoto',
    country: 'Japan',
    description: 'Ancient temples, traditional gardens, and serene bamboo forests.',
    matchReason: 'Ideal for cultural immersion & mindful travel',
    image: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800',
    tempRange: '18-26°C'
  },
  {
    id: 'dest-3',
    name: 'Amalfi Coast',
    country: 'Italy',
    description: 'Dramatic cliffside villages, azure waters, and exquisite cuisine.',
    matchReason: 'Great for foodies & scenic road trips',
    image: 'https://images.unsplash.com/photo-1534008897995-27a23e859048?w=800',
    tempRange: '20-28°C'
  },
  {
    id: 'dest-4',
    name: 'Bali',
    country: 'Indonesia',
    description: 'Lush rice terraces, spiritual temples, and world-class wellness retreats.',
    matchReason: 'Perfect for adventure & relaxation balance',
    image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800',
    tempRange: '26-32°C'
  }
];

export const mockFlights: Flight[] = [
  {
    id: 'flight-1',
    airline: 'Emirates',
    airlineLogo: '✈️',
    departureTime: '09:45',
    arrivalTime: '18:30',
    departureAirport: 'JFK',
    arrivalAirport: 'ATH',
    duration: '10h 45m',
    stops: 0,
    price: 1250,
    class: 'Business'
  },
  {
    id: 'flight-2',
    airline: 'Lufthansa',
    airlineLogo: '🛫',
    departureTime: '14:20',
    arrivalTime: '08:15+1',
    departureAirport: 'JFK',
    arrivalAirport: 'ATH',
    duration: '11h 55m',
    stops: 1,
    price: 890,
    class: 'Economy Plus'
  },
  {
    id: 'flight-3',
    airline: 'Delta',
    airlineLogo: '🔷',
    departureTime: '22:00',
    arrivalTime: '14:30+1',
    departureAirport: 'JFK',
    arrivalAirport: 'ATH',
    duration: '9h 30m',
    stops: 0,
    price: 1580,
    class: 'First Class'
  },
  {
    id: 'flight-4',
    airline: 'Turkish Airlines',
    airlineLogo: '🌙',
    departureTime: '11:30',
    arrivalTime: '06:45+1',
    departureAirport: 'JFK',
    arrivalAirport: 'ATH',
    duration: '13h 15m',
    stops: 1,
    price: 720,
    class: 'Economy'
  }
];

export const mockHotels: Hotel[] = [
  {
    id: 'hotel-1',
    name: 'Canaves Oia Epitome',
    stars: 5,
    image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800',
    pricePerNight: 650,
    amenities: ['Infinity Pool', 'Spa', 'Fine Dining', 'Butler Service'],
    location: 'Oia, Caldera View',
    rating: 9.6,
    reviewCount: 342
  },
  {
    id: 'hotel-2',
    name: 'Mystique Resort',
    stars: 5,
    image: 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800',
    pricePerNight: 480,
    amenities: ['Private Terrace', 'Pool', 'Wellness Center', 'Concierge'],
    location: 'Oia, Cliffside',
    rating: 9.4,
    reviewCount: 567
  },
  {
    id: 'hotel-3',
    name: 'Santo Maris Oia',
    stars: 5,
    image: 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800',
    pricePerNight: 380,
    amenities: ['Beach Access', 'Restaurant', 'Bar', 'Gym'],
    location: 'Oia, Beachfront',
    rating: 9.2,
    reviewCount: 891
  },
  {
    id: 'hotel-4',
    name: 'Athina Luxury Suites',
    stars: 4,
    image: 'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800',
    pricePerNight: 220,
    amenities: ['Hot Tub', 'Breakfast', 'Airport Transfer'],
    location: 'Fira, Town Center',
    rating: 8.9,
    reviewCount: 1243
  }
];

export const mockItinerary: ItineraryDay[] = [
  {
    day: 1,
    date: 'Day 1 - Arrival & Sunset',
    activities: [
      {
        id: 'act-1a',
        name: 'Airport Transfer & Hotel Check-in',
        description: 'Private luxury transfer to your hotel with welcome drinks.',
        duration: '2 hours',
        price: 0,
        image: 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=400',
        category: 'Transfer'
      },
      {
        id: 'act-1b',
        name: 'Sunset Wine Tasting',
        description: 'Sample local Assyrtiko wines while watching the famous Santorini sunset.',
        duration: '3 hours',
        price: 95,
        image: 'https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?w=400',
        category: 'Experience'
      },
      {
        id: 'act-1c',
        name: 'Traditional Greek Dinner',
        description: 'Farm-to-table dining experience at a cliffside restaurant.',
        duration: '2 hours',
        price: 120,
        image: 'https://images.unsplash.com/photo-1544124499-58912cbddaad?w=400',
        category: 'Dining'
      }
    ]
  },
  {
    day: 2,
    date: 'Day 2 - Exploration',
    activities: [
      {
        id: 'act-2a',
        name: 'Caldera Sailing Cruise',
        description: 'Full-day catamaran cruise with swimming, snorkeling, and BBQ lunch.',
        duration: '6 hours',
        price: 180,
        image: 'https://images.unsplash.com/photo-1500514966906-fe245eea9344?w=400',
        category: 'Adventure'
      },
      {
        id: 'act-2b',
        name: 'Hot Springs Visit',
        description: 'Swim in the volcanic hot springs near Nea Kameni.',
        duration: '1 hour',
        price: 0,
        image: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400',
        category: 'Experience'
      },
      {
        id: 'act-2c',
        name: 'Ammoudi Bay Dinner',
        description: 'Fresh seafood dinner at the iconic bay with sunset views.',
        duration: '2.5 hours',
        price: 85,
        image: 'https://images.unsplash.com/photo-1559339352-11d035aa65de?w=400',
        category: 'Dining'
      }
    ]
  },
  {
    day: 3,
    date: 'Day 3 - Culture & Departure',
    activities: [
      {
        id: 'act-3a',
        name: 'Ancient Akrotiri Tour',
        description: 'Guided tour of the preserved Minoan Bronze Age settlement.',
        duration: '2 hours',
        price: 45,
        image: 'https://images.unsplash.com/photo-1603565816030-6b389eeb23cb?w=400',
        category: 'Culture'
      },
      {
        id: 'act-3b',
        name: 'Red Beach & Black Beach',
        description: 'Visit Santorini\'s famous volcanic beaches.',
        duration: '3 hours',
        price: 25,
        image: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400',
        category: 'Nature'
      },
      {
        id: 'act-3c',
        name: 'Farewell Spa Treatment',
        description: 'Relaxing massage before your departure.',
        duration: '1.5 hours',
        price: 150,
        image: 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?w=400',
        category: 'Wellness'
      }
    ]
  }
];

export const mockTransportLegs: TransportLeg[] = [
  {
    id: 'leg-1',
    from: 'Santorini Airport (JTR)',
    to: 'Canaves Oia Epitome',
    options: [
      { id: 'opt-1a', type: 'taxi', name: 'Private Taxi', duration: '25 min', price: 45, icon: '🚕', source: 'api' },
      { id: 'opt-1b', type: 'uber', name: 'Premium Uber', duration: '25 min', price: 38, icon: '🚗', source: 'api' },
      { id: 'opt-1c', type: 'public', name: 'Airport Bus', duration: '45 min', price: 8, icon: '🚌', source: 'api' }
    ]
  },
  {
    id: 'leg-2',
    from: 'Hotel',
    to: 'Sunset Wine Tasting',
    options: [
      { id: 'opt-2a', type: 'taxi', name: 'Hotel Taxi', duration: '15 min', price: 20, icon: '🚕', source: 'api' },
      { id: 'opt-2b', type: 'rental', name: 'ATV Rental', duration: '15 min', price: 35, icon: '🛵', source: 'api' },
      { id: 'opt-2c', type: 'walk', name: 'Scenic Walk', duration: '35 min', price: 0, icon: '🚶', source: 'api' }
    ]
  },
  {
    id: 'leg-3',
    from: 'Hotel',
    to: 'Caldera Sailing Cruise',
    options: [
      { id: 'opt-3a', type: 'taxi', name: 'Included Transfer', duration: '20 min', price: 0, icon: '🚐', source: 'api' },
      { id: 'opt-3b', type: 'rental', name: 'Car Rental', duration: '20 min', price: 55, icon: '🚗', source: 'api' }
    ]
  },
  {
    id: 'leg-4',
    from: 'Hotel',
    to: 'Santorini Airport (JTR)',
    options: [
      { id: 'opt-4a', type: 'taxi', name: 'Private Taxi', duration: '25 min', price: 45, icon: '🚕', source: 'api' },
      { id: 'opt-4b', type: 'uber', name: 'Uber', duration: '25 min', price: 35, icon: '🚗', source: 'api' },
      { id: 'opt-4c', type: 'public', name: 'Local Bus', duration: '50 min', price: 5, icon: '🚌', source: 'api' }
    ]
  }
];
