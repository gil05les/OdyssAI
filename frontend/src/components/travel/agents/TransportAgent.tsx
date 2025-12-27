import { useState, useEffect } from 'react';
import { AgentSearchingAnimation } from '../AgentSearchingAnimation';
import { TransportLeg, TransportOption } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Check, MapPin, X, UserRound } from 'lucide-react';
import { cn } from '@/lib/utils';
import { API_BASE_URL, searchTransport, TransportSearchRequest } from '@/services/api';
import { Destination, Hotel, Activity } from '@/data/mockAgentData';
import { TripRequest } from '@/services/api';
import { PreferenceBadge } from '@/components/ui/PreferenceBadge';

interface TransportAgentProps {
  onComplete: (choices: Record<string, TransportOption | null>) => void;
  onBack: () => void;
  destination?: Destination | null;
  hotel?: Hotel | null;
  activities?: Activity[];
  tripRequest?: TripRequest;
  onSelectionChange?: (transport: Record<string, TransportOption | null> | null) => void;
}

export const TransportAgent = ({ 
  onComplete, 
  onBack, 
  destination, 
  hotel, 
  activities = [],
  tripRequest,
  onSelectionChange
}: TransportAgentProps) => {
  const [isSearching, setIsSearching] = useState(true);
  const [choices, setChoices] = useState<Record<string, TransportOption | null>>({});
  const [declined, setDeclined] = useState<Set<string>>(new Set());
  const [transportLegs, setTransportLegs] = useState<TransportLeg[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Notify parent when selection changes
  useEffect(() => {
    if (onSelectionChange) {
      const hasAnySelection = Object.values(choices).some(choice => choice !== null);
      onSelectionChange(hasAnySelection ? choices : null);
    }
  }, [choices, onSelectionChange]);

  // Fetch transport options from API
  useEffect(() => {
    const fetchTransportOptions = async () => {
      if (!destination || !hotel || !tripRequest) {
        console.warn('Missing trip context for transport search');
        setIsSearching(false);
        return;
      }

      try {
        setIsSearching(true);
        setError(null);

        // Extract itinerary locations from activities
        // The backend will add city/country context when geocoding for better accuracy
        const itineraryLocations = activities
          .map(activity => activity.name)
          .filter((name, index, self) => self.indexOf(name) === index); // Unique names

        // Get date range from trip request
        const dateRange = tripRequest.date_ranges?.[0];
        const arrivalDate = dateRange?.from || '';
        const departureDate = dateRange?.to || '';

        // Build transport search request
        // Clean and validate hotel address - prefer address, but if it looks like room type/description,
        // use hotel name with city/country for better geocoding
        let hotelAddress = hotel.address || hotel.location || hotel.name;
        
        // Clean up address: remove newlines and extra whitespace
        hotelAddress = hotelAddress.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
        
        // Check if address looks like a real address (contains street indicators or is very short)
        // If it looks like a room type/description (contains keywords like "NON-REFUNDABLE", "ROOM ONLY", etc.)
        // or is just the hotel name, use hotel name + city for better geocoding
        const roomTypeKeywords = ['NON-REFUNDABLE', 'ROOM ONLY', 'SUPERIOR', 'DOUBLE', 'SINGLE', 'SUITE', 'DELUXE'];
        const looksLikeRoomType = roomTypeKeywords.some(keyword => 
          hotelAddress.toUpperCase().includes(keyword)
        );
        
        // If address is just the hotel name or looks like room description, use name + city
        if (looksLikeRoomType || hotelAddress === hotel.name || hotelAddress.length < 10) {
          hotelAddress = `${hotel.name}, ${destination.name}, ${destination.country}`;
        } else if (!hotelAddress.includes(',') && !hotelAddress.match(/\d/)) {
          // If no commas (street address format) and no numbers, likely not a real address
          hotelAddress = `${hotel.name}, ${destination.name}, ${destination.country}`;
        }
        
        const transportRequest: TransportSearchRequest = {
          destination_city: destination.name,
          destination_country: destination.country,
          hotel_address: hotelAddress,
          airport_code: destination.iataCode || '',
          itinerary_locations: itineraryLocations,
          arrival_datetime: arrivalDate,
          departure_datetime: departureDate,
          group_size: tripRequest.group_size || 1,
        };

        // Call API
        const legs = await searchTransport(transportRequest);
        setTransportLegs(legs);

        // Fetch images for transport options
        const updatedLegs = await Promise.all(
          legs.map(async (leg) => {
            const updatedOptions = await Promise.all(
              leg.options.map(async (option) => {
                if (option.image) {
                  return option; // Already has image
                }
                try {
                  // Fetch image from backend API
                  const response = await fetch(
                    `${API_BASE_URL}/images/transport?name=${encodeURIComponent(option.name)}&type=${encodeURIComponent(option.type)}`
                  );
                  if (response.ok) {
                    const data = await response.json();
                    return { ...option, image: data.image_url };
                  }
                } catch (error) {
                  console.warn(`Failed to fetch image for ${option.name}:`, error);
                }
                return option;
              })
            );
            return { ...leg, options: updatedOptions };
          })
        );
        setTransportLegs(updatedLegs);
      } catch (err) {
        console.error('Failed to fetch transport options:', err);
        setError(err instanceof Error ? err.message : 'Failed to load transport options');
      } finally {
        setIsSearching(false);
      }
    };

    fetchTransportOptions();
  }, [destination, hotel, activities, tripRequest]);

  const selectOption = (legId: string, option: TransportOption) => {
    setChoices(prev => ({ ...prev, [legId]: option }));
    setDeclined(prev => {
      const next = new Set(prev);
      next.delete(legId);
      return next;
    });
  };

  const declineLeg = (legId: string) => {
    setChoices(prev => ({ ...prev, [legId]: null }));
    setDeclined(prev => new Set(prev).add(legId));
  };

  // Decline all legs that don't have a selection yet
  const declineAllRemaining = () => {
    const newChoices = { ...choices };
    const newDeclined = new Set(declined);
    
    transportLegs.forEach(leg => {
      // Only decline legs that don't already have a selection
      if (choices[leg.id] === undefined) {
        newChoices[leg.id] = null;
        newDeclined.add(leg.id);
      }
    });
    
    setChoices(newChoices);
    setDeclined(newDeclined);
  };

  const handleComplete = () => {
    onComplete(choices);
  };

  // Count legs that still need a decision
  const undecidedLegsCount = transportLegs.filter(
    leg => choices[leg.id] === undefined && !declined.has(leg.id)
  ).length;

  const allLegsDecided = transportLegs.every(
    leg => choices[leg.id] !== undefined || declined.has(leg.id)
  );

  if (isSearching) {
    return (
      <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
      <AgentSearchingAnimation
        agentType="transport"
        searchText="Finding transport options for your journey..."
      />
      </div>
    );
  }

  if (error) {
    return (
      <div className="animate-fade-in">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-serif text-fog mb-2">Transport Options</h2>
          <p className="text-red-400">{error}</p>
        </div>
        <div className="flex justify-center mt-8">
          <Button
            variant="ghost"
            onClick={onBack}
            className="text-fog/80 hover:text-fog"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-serif text-fog mb-2">Transport Options</h2>
        <p className="text-fog/90">Choose or decline transport for each leg of your journey</p>
        
        {/* Button to arrange all remaining transport myself */}
        {undecidedLegsCount > 0 && (
          <div className="mt-6 flex justify-center">
            <Button
              variant="outline"
              onClick={declineAllRemaining}
              className="border-teal/50 text-teal hover:text-teal hover:bg-teal/10 hover:border-teal px-6 py-2"
            >
              <UserRound className="w-4 h-4 mr-2" />
              Arrange all remaining transport myself
              {undecidedLegsCount > 1 && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-teal/20 text-teal">
                  {undecidedLegsCount} legs
                </span>
              )}
            </Button>
          </div>
        )}
      </div>

      <div className="max-w-3xl mx-auto space-y-6">
        {transportLegs.map((leg, legIndex) => {
          const isDeclined = declined.has(leg.id);
          const selectedOption = choices[leg.id];

          return (
            <div
              key={leg.id}
              className="animate-slide-up p-6 rounded-2xl glass-sand"
              style={{ animationDelay: `${legIndex * 100}ms`, animationFillMode: 'forwards' }}
            >
              {/* Route header */}
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-teal/20 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-teal" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-sm text-fog">
                    <span className="font-medium">{leg.from}</span>
                    <span className="text-fog/60">→</span>
                    <span className="font-medium">{leg.to}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => declineLeg(leg.id)}
                  className={cn(
                    "text-xs",
                    isDeclined ? "text-red-500" : "text-fog/60 hover:text-red-500"
                  )}
                >
                  {isDeclined ? (
                    <>
                      <X className="w-3 h-3 mr-1" /> Declined
                    </>
                  ) : (
                    "I'll arrange myself"
                  )}
                </Button>
              </div>

              {/* Transport options */}
              <div className={cn(
                "grid grid-cols-1 sm:grid-cols-3 gap-3 transition-opacity",
                isDeclined && "opacity-30 pointer-events-none"
              )}>
                {leg.options.map(option => {
                  const isSelected = selectedOption?.id === option.id;
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectOption(leg.id, option)}
                      className={cn(
                        "p-4 rounded-xl border-2 transition-all duration-300 text-left",
                        "hover:scale-[1.02] hover:shadow-md overflow-hidden",
                        isSelected
                          ? "border-gold bg-gold/10 shadow-md"
                          : "border-fog/20 bg-white/50 hover:border-gold/50"
                      )}
                    >
                      {/* Image background or Icon */}
                      <div 
                        className="relative w-full h-24 mb-2 rounded-lg overflow-hidden"
                        style={{
                          backgroundImage: option.image ? `url(${option.image})` : 'none',
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          backgroundColor: option.image ? 'transparent' : 'rgba(255, 255, 255, 0.05)'
                        }}
                      >
                        {/* Dark overlay for better text readability */}
                        {option.image && (
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
                        )}
                        {/* Icon fallback if no image */}
                        {!option.image && (
                          <div className="w-full h-full flex items-center justify-center">
                            <span className="text-4xl">{option.icon}</span>
                          </div>
                        )}
                        {isSelected && (
                          <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-gold flex items-center justify-center z-10 shadow-lg">
                            <Check className="w-3 h-3 text-midnight" />
                          </div>
                        )}
                        {/* AI Estimate badge */}
                        {option.source === 'llm' && (
                          <span className="absolute top-2 left-2 px-2 py-0.5 text-xs rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 z-10 backdrop-blur-sm">
                            AI Estimate
                          </span>
                        )}
                        {/* Preference badge */}
                        {option.preference_score && option.preference_score >= 50 && !option.source?.includes('llm') && (
                          <div className="absolute bottom-2 left-2 z-10">
                            <PreferenceBadge 
                              score={option.preference_score} 
                              reasons={option.preference_match?.reasons}
                              className="backdrop-blur-sm"
                            />
                          </div>
                        )}
                      </div>
                      <p className={cn(
                        "font-medium text-sm",
                        option.image ? "text-white drop-shadow-lg" : "text-fog"
                      )}>{option.name}</p>
                      <div className={cn(
                        "flex items-center justify-between mt-2 text-xs",
                        option.image ? "text-white/90 drop-shadow" : "text-fog/80"
                      )}>
                        <span>{option.duration}</span>
                        <span className="font-semibold text-gold drop-shadow">
                          {option.price === 0 ? 'Free' : `CHF ${option.price}`}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
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
          onClick={handleComplete}
          disabled={!allLegsDecided}
          className="bg-gold hover:bg-gold/90 text-midnight px-8"
        >
          Complete Trip Planning
        </Button>
      </div>
    </div>
  );
};
