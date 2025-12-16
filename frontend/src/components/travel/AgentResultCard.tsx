import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentResultCardProps {
  children: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
  delay?: number;
}

export const AgentResultCard = ({ 
  children, 
  selected, 
  onClick, 
  className,
  delay = 0 
}: AgentResultCardProps) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative p-4 rounded-2xl glass-sand cursor-pointer transition-all duration-300",
        "hover:scale-[1.02] hover:shadow-xl hover:shadow-gold/10",
        "animate-slide-up opacity-0",
        selected && "ring-2 ring-gold shadow-lg shadow-gold/20",
        className
      )}
      style={{ 
        animationDelay: `${delay}ms`,
        animationFillMode: 'forwards'
      }}
    >
      {/* Selection indicator */}
      {selected && (
        <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-gold flex items-center justify-center shadow-lg animate-scale-in">
          <Check className="w-4 h-4 text-midnight" />
        </div>
      )}
      
      {children}
    </div>
  );
};

// Specialized card for destinations
interface DestinationCardContentProps {
  name: string;
  country: string;
  description: string;
  matchReason: string;
  image: string;
  tempRange: string;
  iataCode?: string;
  airportName?: string;
}

export const DestinationCardContent = ({ 
  name, 
  country, 
  description, 
  matchReason, 
  image, 
  tempRange,
  iataCode,
  airportName
}: DestinationCardContentProps) => (
  <div className="flex flex-col md:flex-row gap-4">
    <div className="w-full md:w-32 h-32 rounded-xl overflow-hidden flex-shrink-0 ring-1 ring-gold/20">
      <img src={image} alt={name} className="w-full h-full object-cover" />
    </div>
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-xl font-semibold text-fog">{name}</h3>
        <span className="text-sm text-fog/80">{country}</span>
        <span className="ml-auto text-sm text-gold font-medium">{tempRange}</span>
      </div>
      {(iataCode || airportName) && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs text-fog/70">Arrival:</span>
          {airportName && (
            <span className="text-xs text-fog/80 font-medium">{airportName}</span>
          )}
          {iataCode && (
            <span className="text-xs px-2 py-0.5 bg-gold/20 text-gold font-semibold rounded border border-gold/30">
              {iataCode}
            </span>
          )}
        </div>
      )}
      <p className="text-sm text-fog/90 mb-3 leading-relaxed">{description}</p>
      <span className="inline-block px-3 py-1.5 rounded-full bg-teal/20 text-teal-light text-xs font-medium border border-teal/30">
        {matchReason}
      </span>
    </div>
  </div>
);

// Specialized card for flights
interface FlightCardContentProps {
  airline: string;
  airlineLogo: string;
  airlineCode?: string;  // Airline code for logo image (e.g., "LX", "LH")
  departureTime: string;
  arrivalTime: string;
  departureAirport: string;
  arrivalAirport: string;
  duration: string;
  stops: number;
  price: number;
  flightClass: string;
  flightNumber?: string;
  returnFlightNumber?: string;
  returnDepartureTime?: string;
  returnArrivalTime?: string;
  returnDepartureAirport?: string;
  returnArrivalAirport?: string;
}

export const FlightCardContent = ({
  airline,
  airlineLogo,
  airlineCode,
  departureTime,
  arrivalTime,
  departureAirport,
  arrivalAirport,
  duration,
  stops,
  price,
  flightClass,
  flightNumber,
  returnFlightNumber,
  returnDepartureTime,
  returnArrivalTime,
  returnDepartureAirport,
  returnArrivalAirport,
}: FlightCardContentProps) => {
  const hasReturnFlight = returnDepartureTime && returnArrivalTime;
  
  // Get airline code for logo (extract from airline name or use provided code)
  const code = airlineCode || airline.substring(0, 2).toUpperCase();
  const logoPath = `/data/airlines_logos/${code}.png`;
  
  return (
    <div className="flex flex-col gap-4">
      {/* Outbound Flight */}
      <div className="flex flex-col md:flex-row items-center gap-4">
        <div className="w-12 h-12 flex items-center justify-center">
          <img 
            src={logoPath} 
            alt={airline}
            className="max-w-full max-h-full object-contain"
            onError={(e) => {
              // Fallback to emoji if image doesn't exist
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              if (target.parentElement) {
                target.parentElement.innerHTML = `<span class="text-3xl">${airlineLogo}</span>`;
              }
            }}
          />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-4 mb-2">
            <div className="text-center">
              <p className="text-xl font-bold text-fog">{departureTime}</p>
              <p className="text-xs text-fog/70">{departureAirport}</p>
            </div>
            <div className="flex-1 flex items-center gap-2">
              <div className="h-px flex-1 bg-fog/30" />
              <div className="text-xs text-fog/70 whitespace-nowrap">
                {duration} • {stops === 0 ? 'Direct' : `${stops} stop`}
              </div>
              <div className="h-px flex-1 bg-fog/30" />
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-fog">{arrivalTime}</p>
              <p className="text-xs text-fog/70">{arrivalAirport}</p>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-fog/80">{airline} • {flightClass}</span>
              {flightNumber && (
                <span className="text-xs px-2 py-0.5 bg-gold/20 text-gold font-semibold rounded border border-gold/30">
                  {flightNumber}
                </span>
              )}
            </div>
            {!hasReturnFlight && (
              <span className="text-lg font-bold text-gold">CHF {price}</span>
            )}
          </div>
        </div>
      </div>
      
      {/* Return Flight */}
      {hasReturnFlight && (
        <>
          <div className="h-px bg-fog/20 my-2" />
          <div className="flex flex-col md:flex-row items-center gap-4">
            <div className="w-12 h-12 flex items-center justify-center opacity-60">
              <img 
                src={logoPath} 
                alt={airline}
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  // Fallback to emoji if image doesn't exist
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  if (target.parentElement) {
                    target.parentElement.innerHTML = `<span class="text-3xl">${airlineLogo}</span>`;
                  }
                }}
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-4 mb-2">
                <div className="text-center">
                  <p className="text-xl font-bold text-fog">{returnDepartureTime}</p>
                  <p className="text-xs text-fog/70">{returnDepartureAirport}</p>
                </div>
                <div className="flex-1 flex items-center gap-2">
                  <div className="h-px flex-1 bg-fog/30" />
                  <div className="text-xs text-fog/70 whitespace-nowrap">
                    Return
                  </div>
                  <div className="h-px flex-1 bg-fog/30" />
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-fog">{returnArrivalTime}</p>
                  <p className="text-xs text-fog/70">{returnArrivalAirport}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-fog/80">{airline} • {flightClass}</span>
                  {returnFlightNumber && (
                    <span className="text-xs px-2 py-0.5 bg-gold/20 text-gold font-semibold rounded border border-gold/30">
                      {returnFlightNumber}
                    </span>
                  )}
                </div>
                <span className="text-lg font-bold text-gold">CHF {price}</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Specialized card for hotels
interface HotelCardContentProps {
  name: string;
  stars: number;
  image: string;
  pricePerNight: number;
  amenities: string[];
  location: string;
  rating: number;
  reviewCount: number;
}

export const HotelCardContent = ({
  name,
  stars,
  image,
  pricePerNight,
  amenities,
  location,
  rating,
  reviewCount,
}: HotelCardContentProps) => (
  <div className="flex flex-col md:flex-row gap-4">
    <div className="w-full md:w-40 h-32 rounded-xl overflow-hidden flex-shrink-0">
      <img src={image} alt={name} className="w-full h-full object-cover" />
    </div>
    <div className="flex-1">
      <div className="flex items-center gap-2 mb-1">
        <h3 className="text-lg font-semibold text-fog">{name}</h3>
        <span className="text-gold">{'★'.repeat(stars)}</span>
      </div>
      <p className="text-sm text-fog/80 mb-2">{location}</p>
      <div className="flex flex-wrap gap-2 mb-2">
        {amenities.slice(0, 3).map((amenity) => (
          <span key={amenity} className="text-xs px-2 py-1 bg-fog/10 rounded-full text-fog/90">
            {amenity}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 bg-teal text-white text-sm font-bold rounded">{rating}</span>
          <span className="text-xs text-fog/80">{reviewCount} reviews</span>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-gold">CHF {pricePerNight}</span>
          <span className="text-xs text-fog/80"> /night</span>
        </div>
      </div>
    </div>
  </div>
);
