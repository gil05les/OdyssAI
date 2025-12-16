import { useState, useEffect, useRef } from 'react';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { AgentResultCard, HotelCardContent } from '../AgentResultCard';
import { Hotel, Destination } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowRight, ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react';
import { searchHotels, extractIataCode, TripRequest } from '@/services/api';

interface HotelAgentProps {
  destination: Destination;
  tripRequest: TripRequest;
  flight?: { arrivalTime?: string; arrivalAirport?: string } | null;
  onSelect: (hotel: Hotel) => void;
  onBack: () => void;
}

export const HotelAgent = ({ destination, tripRequest, flight, onSelect, onBack }: HotelAgentProps) => {
  const [isSearching, setIsSearching] = useState(true);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [retryTrigger, setRetryTrigger] = useState(0);
  const hasRetriedRef = useRef(false);

  // Fetch hotels from API
  useEffect(() => {
    // Reset retry flag when dependencies change
    hasRetriedRef.current = false;

    const fetchHotels = async () => {
      try {
        setIsSearching(true);
        setError(null);

        // Extract city code from destination
        const cityCode = destination.iataCode || extractIataCode(destination.name);
        
        if (!cityCode || cityCode.length !== 3) {
          throw new Error(`Invalid city code: ${cityCode}. Please ensure destination has a valid IATA code.`);
        }

        // Calculate check-in and check-out dates
        // If we have flight info, use arrival date + 1 day as check-in
        // Otherwise use trip request dates
        const dateRange = tripRequest.date_ranges[0];
        if (!dateRange || !dateRange.from) {
          throw new Error('No date range specified in trip request');
        }

        // Format dates as YYYY-MM-DD (handles timezone issues by using local date)
        const formatDate = (date: Date) => {
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
        };

        // Parse the trip start date (YYYY-MM-DD format)
        const tripStartDate = new Date(dateRange.from + 'T12:00:00'); // Use noon to avoid timezone issues
        
        // Check-in: use trip start date (or arrival date + 1 day if flight info available)
        // Since flight.arrivalTime is just "HH:MM" format, we use the trip start date
        // and assume check-in is the same day as trip start (or next day if flight arrives late)
        let checkInDate: Date;
        if (flight?.arrivalTime) {
          // If we have flight info, check-in is typically the day after arrival
          // But since we only have time, we'll use trip start date + 1 day
          checkInDate = new Date(tripStartDate);
          checkInDate.setDate(checkInDate.getDate() + 1);
        } else {
          // Use trip start date directly
          checkInDate = new Date(tripStartDate);
        }

        // Check-out: calculate based on trip duration
        const duration = tripRequest.duration[1] || 3; // Use max duration or default to 3 nights
        const checkOutDate = new Date(checkInDate);
        checkOutDate.setDate(checkOutDate.getDate() + duration);
        
        const checkIn = formatDate(checkInDate);
        const checkOut = formatDate(checkOutDate);

        // Use budget upper bound as max price per night filter
        const maxPricePerNight = tripRequest.budget[1] ? Math.floor(tripRequest.budget[1] / duration) : undefined;

        // Validate dates
        if (!checkIn || !checkOut) {
          throw new Error('Failed to calculate check-in or check-out dates');
        }
        
        // Validate check-out is after check-in
        const checkInDateObj = new Date(checkIn);
        const checkOutDateObj = new Date(checkOut);
        if (checkOutDateObj <= checkInDateObj) {
          throw new Error(`Invalid date range: check-out (${checkOut}) must be after check-in (${checkIn})`);
        }

        console.log('Hotel search params:', {
          city_code: cityCode,
          check_in: checkIn,
          check_out: checkOut,
          guests: tripRequest.group_size,
          max_price_per_night: maxPricePerNight,
        });

        const results = await searchHotels({
          city_code: cityCode,
          check_in: checkIn,
          check_out: checkOut,
          guests: tripRequest.group_size,
          max_price_per_night: maxPricePerNight,
        });

        setHotels(results);
        setHasSearched(true);
        hasRetriedRef.current = false; // Reset on success
      } catch (err) {
        console.error('Failed to fetch hotels:', err);
        
        // Automatically retry once if this is the first attempt
        if (!hasRetriedRef.current) {
          console.log('Retrying hotel search automatically...');
          hasRetriedRef.current = true;
          // Wait a bit before retrying to handle transient errors
          setTimeout(() => {
            fetchHotels();
          }, 500);
          return;
        }
        
        // Only show error after retry attempt
        setError(err instanceof Error ? err.message : 'Failed to search hotels');
        setHasSearched(true);
      } finally {
        setIsSearching(false);
      }
    };

    fetchHotels();
  }, [destination, tripRequest, flight, retryTrigger]);

  const handleContinue = () => {
    const hotel = hotels.find(h => h.id === selected);
    if (hotel) {
      onSelect(hotel);
    }
  };

  const handleRetry = () => {
    setError(null);
    setIsSearching(true);
    setHasSearched(false);
    hasRetriedRef.current = false; // Reset retry flag so it can retry again if needed
    // Trigger re-fetch by updating retryTrigger
    setRetryTrigger(prev => prev + 1);
  };

  if (isSearching) {
    return (
      <AgentSearchingAnimation
        agentType="hotel"
        searchText={`Finding luxury stays in ${destination.name}...`}
      />
    );
  }

  // Only show error if we've actually attempted a search
  if (error && hasSearched) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-serif text-fog mb-2">Hotel Search Failed</h2>
          <p className="text-fog/70 mb-6">{error}</p>
          <div className="flex justify-center gap-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-fog/80 hover:text-fog"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Flights
            </Button>
            <Button
              onClick={handleRetry}
              className="bg-gold hover:bg-gold/90 text-midnight"
            >
              <RefreshCw className="w-4 h-4 mr-2" /> Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (hasSearched && hotels.length === 0 && !error) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <AlertCircle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-serif text-fog mb-2">No Hotels Found</h2>
          <p className="text-fog/70 mb-6">
            We couldn't find any hotels in {destination.name} within your budget.
            Try adjusting your dates or increasing your budget.
          </p>
          <div className="flex justify-center gap-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-fog/80 hover:text-fog"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Flights
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Format dates for display
  const formatDisplayDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const dateRange = tripRequest.date_ranges[0];
  const checkInDate = dateRange ? formatDisplayDate(dateRange.from) : '';
  const duration = tripRequest.duration[1] || 3;

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-serif text-fog mb-2">Choose Your Stay</h2>
        <p className="text-fog/90">
          I found {hotels.length} great option{hotels.length !== 1 ? 's' : ''} in {destination.name}
        </p>
        <div className="text-sm text-fog/60 mt-1 space-y-1">
          <p>
            <span className="font-medium">Check-in:</span> {checkInDate} • 
            <span className="font-medium"> Duration:</span> {duration} night{duration !== 1 ? 's' : ''}
          </p>
          <p>
            Budget: up to ${tripRequest.budget[1] ? Math.floor(tripRequest.budget[1] / duration) : 'N/A'} per night • {tripRequest.group_size} guest{tripRequest.group_size !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div className="grid gap-4 max-w-3xl mx-auto">
        {hotels.map((hotel, index) => (
          <AgentResultCard
            key={hotel.id}
            selected={selected === hotel.id}
            onClick={() => setSelected(hotel.id)}
            delay={index * 100}
          >
            <HotelCardContent
              name={hotel.name}
              stars={hotel.stars}
              image={hotel.image}
              pricePerNight={hotel.pricePerNight}
              amenities={hotel.amenities}
              location={hotel.location}
              rating={hotel.rating}
              reviewCount={hotel.reviewCount}
            />
          </AgentResultCard>
        ))}
      </div>

      <div className="flex justify-between mt-8 max-w-3xl mx-auto">
        <Button
          variant="ghost"
          onClick={onBack}
          className="text-fog/80 hover:text-fog"
        >
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>
        <Button
          onClick={handleContinue}
          disabled={!selected}
          className="bg-gold hover:bg-gold/90 text-midnight px-8"
        >
          Continue to Itinerary <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
};
