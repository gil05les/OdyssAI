import { useState, useEffect } from 'react';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { AgentResultCard, FlightCardContent } from '../AgentResultCard';
import { Flight, Destination } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowRight, ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react';
import { searchFlights, extractIataCode, TripRequest } from '@/services/api';

interface FlightAgentProps {
  destination: Destination;
  tripRequest: TripRequest;
  onSelect: (flight: Flight) => void;
  onBack: () => void;
  onSelectionChange?: (flight: Flight | null) => void;
}

export const FlightAgent = ({ destination, tripRequest, onSelect, onBack, onSelectionChange }: FlightAgentProps) => {
  const [isSearching, setIsSearching] = useState(true);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Notify parent when selection changes
  useEffect(() => {
    if (onSelectionChange) {
      const flight = selected ? flights.find(f => f.id === selected) || null : null;
      onSelectionChange(flight);
    }
  }, [selected, flights, onSelectionChange]);

  // Fetch flights from API
  useEffect(() => {
    const fetchFlights = async () => {
      try {
        setIsSearching(true);
        setError(null);

        // Extract IATA codes
        const originIata = extractIataCode(tripRequest.origin);
        const destIata = destination.iataCode || extractIataCode(destination.name);

        // Get dates from trip request
        const dateRange = tripRequest.date_ranges[0];
        if (!dateRange) {
          throw new Error('No date range specified');
        }

        // Format dates as YYYY-MM-DD
        const formatDate = (dateStr: string) => {
          const date = new Date(dateStr);
          return date.toISOString().split('T')[0];
        };

        const departureDate = formatDate(dateRange.from);
        const returnDate = dateRange.to ? formatDate(dateRange.to) : undefined;

        // Use budget upper bound as max price filter
        const maxPrice = tripRequest.budget[1];

        console.log('Flight search params:', {
          origin: originIata,
          destination: destIata,
          departure_date: departureDate,
          return_date: returnDate,
          adults: tripRequest.group_size,
          max_price: maxPrice,
        });

        const results = await searchFlights({
          origin: originIata,
          destination: destIata,
          departure_date: departureDate,
          return_date: returnDate,
          adults: tripRequest.group_size,
          max_price: maxPrice,
        });

        setFlights(results);
        setHasSearched(true);
      } catch (err) {
        console.error('Failed to fetch flights:', err);
        setError(err instanceof Error ? err.message : 'Failed to search flights');
        setHasSearched(true);
      } finally {
        setIsSearching(false);
      }
    };

    fetchFlights();
  }, [destination, tripRequest]);

  const handleContinue = () => {
    const flight = flights.find(f => f.id === selected);
    if (flight) {
      onSelect(flight);
    }
  };

  const handleRetry = () => {
    setError(null);
    setIsSearching(true);
    setHasSearched(false);
    // Trigger re-fetch by updating a dependency
    setFlights([]);
    // The useEffect will handle the retry since flights changed
  };

  if (isSearching) {
    return (
      <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
      <AgentSearchingAnimation
        agentType="flight"
        searchText={`Searching for best flights to ${destination.name}...`}
      />
      </div>
    );
  }

  if (error) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-serif text-fog mb-2">Flight Search Failed</h2>
          <p className="text-fog/70 mb-6">{error}</p>
          <div className="flex justify-center gap-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-fog/80 hover:text-fog"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Destinations
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

  if (hasSearched && flights.length === 0 && !error) {
    return (
      <div className="animate-fade-in max-w-2xl mx-auto">
        <div className="text-center p-8 rounded-2xl glass-sand">
          <AlertCircle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
          <h2 className="text-xl font-serif text-fog mb-2">No Flights Found</h2>
          <p className="text-fog/70 mb-6">
            We couldn't find any flights to {destination.name} within your budget of ${tripRequest.budget[1]}.
            Try adjusting your dates or increasing your budget.
          </p>
          <div className="flex justify-center gap-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="text-fog/80 hover:text-fog"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Choose Different Destination
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
  const departureDateDisplay = dateRange ? formatDisplayDate(dateRange.from) : '';
  const returnDateDisplay = dateRange?.to ? formatDisplayDate(dateRange.to) : null;

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-serif text-fog mb-2">Select Your Flight</h2>
        <p className="text-fog/90">
          I found {flights.length} great option{flights.length !== 1 ? 's' : ''} to {destination.name}
        </p>
        <div className="text-sm text-fog/60 mt-1 space-y-1">
          <p>
            <span className="font-medium">Departure:</span> {departureDateDisplay}
            {returnDateDisplay && (
              <> • <span className="font-medium">Return:</span> {returnDateDisplay}</>
            )}
          </p>
          <p>
            Budget: up to ${tripRequest.budget[1]} • {tripRequest.group_size} traveler{tripRequest.group_size !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div className="grid gap-4 max-w-3xl mx-auto">
        {flights.map((flight, index) => (
          <AgentResultCard
            key={flight.id}
            selected={selected === flight.id}
            onClick={() => setSelected(flight.id)}
            delay={index * 100}
            preferenceScore={flight.preference_score}
            preferenceReasons={flight.preference_match?.reasons}
          >
            <FlightCardContent
              airline={flight.airline}
              airlineLogo={flight.airlineLogo}
              airlineCode={flight.airlineCode || flight.airline}
              departureTime={flight.departureTime}
              arrivalTime={flight.arrivalTime}
              departureAirport={flight.departureAirport}
              arrivalAirport={flight.arrivalAirport}
              duration={flight.duration}
              stops={flight.stops}
              price={flight.price}
              flightClass={flight.class}
              flightNumber={flight.flightNumber}
              returnFlightNumber={flight.returnFlightNumber}
              returnDepartureTime={flight.returnDepartureTime}
              returnArrivalTime={flight.returnArrivalTime}
              returnDepartureAirport={flight.returnDepartureAirport}
              returnArrivalAirport={flight.returnArrivalAirport}
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
          Continue to Hotels <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
};
