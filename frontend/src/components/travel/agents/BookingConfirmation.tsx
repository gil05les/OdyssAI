import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Download, CheckCircle2, Plane, Building2, Calendar, Car, User, Mail, Phone, MapPin, RotateCcw, FileText } from 'lucide-react';
import { Destination, Flight, Hotel, Activity, TransportOption } from '@/data/mockAgentData';
import { TripRequest } from '@/services/api';
import { generateBookingPDF, generateBookingReference } from '@/utils/pdfGenerator';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

interface BookingConfirmationProps {
  bookingData: {
    formData: {
      fullName: string;
      email: string;
      phone: string;
      street: string;
      city: string;
      zip: string;
      country: string;
    };
    tripState: {
      destination: Destination | null;
      flight: Flight | null;
      hotel: Hotel | null;
      activities: Activity[];
      transport: Record<string, TransportOption | null>;
    };
    bookingReference: string;
  };
  tripRequest: TripRequest;
  onBack: () => void;
  skipAutoSave?: boolean; // If true, skip auto-saving the trip (useful when trip is already saved/updated externally)
}

export const BookingConfirmation = ({ bookingData, tripRequest, onBack, skipAutoSave = false }: BookingConfirmationProps) => {
  const { user } = useAuth();
  const [tripSaved, setTripSaved] = useState(false);

  useEffect(() => {
    // Save trip to database if user is logged in and auto-save is not skipped
    const saveTrip = async () => {
      if (skipAutoSave) {
        setTripSaved(true);
        return;
      }

      if (user && !tripSaved) {
        try {
          await authService.createTrip(user.id, {
            status: 'booked',
            booking_reference: bookingData.bookingReference,
            trip_data: {
              tripState: bookingData.tripState,
              tripRequest: tripRequest,
              formData: bookingData.formData,
            },
          });
          setTripSaved(true);
        } catch (error) {
          console.error('Failed to save trip:', error);
        }
      }
    };

    saveTrip();
  }, [user, bookingData, tripRequest, tripSaved, skipAutoSave]);

  const calculateTotal = () => {
    let total = 0;
    if (bookingData.tripState.flight) total += bookingData.tripState.flight.price;
    if (bookingData.tripState.hotel) {
      const nights = 3; // Could be calculated from tripRequest.date_ranges
      total += bookingData.tripState.hotel.pricePerNight * nights;
    }
    total += bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0);
    Object.values(bookingData.tripState.transport).forEach(opt => {
      if (opt) total += opt.price;
    });
    return total;
  };

  const handleDownloadPDF = () => {
    generateBookingPDF(bookingData, tripRequest);
  };

  const transportOptions = Object.values(bookingData.tripState.transport).filter(Boolean) as TransportOption[];

  return (
    <div className="animate-fade-in max-w-6xl mx-auto">
      {/* Success Header */}
      <div className="text-center mb-8">
        <div className="w-24 h-24 rounded-full bg-gold/20 flex items-center justify-center mx-auto mb-6 animate-scale-in">
          <CheckCircle2 className="w-12 h-12 text-gold" />
        </div>
        <h2 className="text-3xl font-serif text-fog mb-2">Booking Confirmed!</h2>
        <p className="text-fog/90 mb-4">Your trip has been successfully booked</p>
        <div className="inline-block px-6 py-3 rounded-xl bg-gold/10 border-2 border-gold/30">
          <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Booking Reference</p>
          <p className="text-xl font-bold text-gold font-mono">{bookingData.bookingReference}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Content - Left Column (2/3 on desktop) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer Information */}
          <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
            <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
              <User className="w-5 h-5 text-gold" />
              Customer Information
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Full Name</p>
                <p className="text-fog font-medium">{bookingData.formData.fullName}</p>
              </div>
              <div>
                <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Email</p>
                <p className="text-fog font-medium flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gold" />
                  {bookingData.formData.email}
                </p>
              </div>
              {bookingData.formData.phone && (
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Phone</p>
                  <p className="text-fog font-medium flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gold" />
                    {bookingData.formData.phone}
                  </p>
                </div>
              )}
              {(bookingData.formData.street || bookingData.formData.city) && (
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Billing Address</p>
                  <p className="text-fog font-medium flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gold" />
                    {[
                      bookingData.formData.street,
                      bookingData.formData.city,
                      bookingData.formData.zip,
                      bookingData.formData.country
                    ].filter(Boolean).join(', ')}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Trip Summary */}
          <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}>
            <h3 className="text-lg font-serif text-fog mb-6">Trip Summary</h3>
            <div className="space-y-4">
              {bookingData.tripState.destination && (
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Destination</p>
                  <p className="text-fog font-medium">{bookingData.tripState.destination.name}, {bookingData.tripState.destination.country}</p>
                </div>
              )}
              {tripRequest.date_ranges && tripRequest.date_ranges.length > 0 && (
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Travel Dates</p>
                  <p className="text-fog font-medium">{tripRequest.date_ranges[0].from} to {tripRequest.date_ranges[0].to}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Travelers</p>
                <p className="text-fog font-medium">{tripRequest.group_size} {tripRequest.traveler_type}</p>
              </div>
            </div>
          </div>

          {/* Flight Details */}
          {bookingData.tripState.flight && (
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '300ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <Plane className="w-5 h-5 text-gold" />
                Flight Details
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Airline</p>
                  <p className="text-fog font-medium">{bookingData.tripState.flight.airline} • {bookingData.tripState.flight.class}</p>
                </div>
                {bookingData.tripState.flight.flightNumber && (
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Flight Number</p>
                    <p className="text-fog font-medium">{bookingData.tripState.flight.flightNumber}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Departure</p>
                  <p className="text-fog font-medium">{bookingData.tripState.flight.departureTime} from {bookingData.tripState.flight.departureAirport}</p>
                </div>
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Arrival</p>
                  <p className="text-fog font-medium">{bookingData.tripState.flight.arrivalTime} at {bookingData.tripState.flight.arrivalAirport}</p>
                </div>
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Duration</p>
                  <p className="text-fog font-medium">{bookingData.tripState.flight.duration}</p>
                </div>
                {bookingData.tripState.flight.returnFlightNumber && (
                  <>
                    <div className="pt-2 border-t border-fog/10">
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Return Flight</p>
                      <p className="text-fog font-medium">{bookingData.tripState.flight.returnFlightNumber}</p>
                      <p className="text-sm text-fog/80 mt-1">
                        {bookingData.tripState.flight.returnDepartureTime} → {bookingData.tripState.flight.returnArrivalTime}
                      </p>
                    </div>
                  </>
                )}
                <div className="pt-2 border-t border-fog/10">
                  <p className="text-sm text-gold font-semibold">CHF {bookingData.tripState.flight.price.toFixed(2)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Hotel Details */}
          {bookingData.tripState.hotel && (
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '400ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-gold" />
                Accommodation
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Hotel</p>
                  <p className="text-fog font-medium">{bookingData.tripState.hotel.name}</p>
                </div>
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Location</p>
                  <p className="text-fog font-medium">{bookingData.tripState.hotel.location}</p>
                </div>
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Rating</p>
                  <p className="text-fog font-medium">{bookingData.tripState.hotel.stars} stars</p>
                </div>
                <div>
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Nights</p>
                  <p className="text-fog font-medium">3 nights</p>
                </div>
                {bookingData.tripState.hotel.amenities && bookingData.tripState.hotel.amenities.length > 0 && (
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Amenities</p>
                    <p className="text-fog font-medium text-sm">{bookingData.tripState.hotel.amenities.slice(0, 5).join(', ')}</p>
                  </div>
                )}
                <div className="pt-2 border-t border-fog/10">
                  <p className="text-sm text-gold font-semibold">CHF {(bookingData.tripState.hotel.pricePerNight * 3).toFixed(2)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Activities */}
          {bookingData.tripState.activities.length > 0 && (
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '500ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-gold" />
                Activities & Experiences
              </h3>
              <div className="space-y-3">
                {bookingData.tripState.activities.map((activity, index) => (
                  <div key={activity.id} className="pb-3 border-b border-fog/10 last:border-0">
                    <p className="text-fog font-medium">{index + 1}. {activity.name}</p>
                    <p className="text-sm text-fog/70 mt-1">{activity.category} • {activity.duration}</p>
                    <p className="text-sm text-gold font-semibold mt-1">CHF {activity.price.toFixed(2)}</p>
                  </div>
                ))}
                <div className="pt-2 border-t border-fog/10">
                  <p className="text-sm text-gold font-semibold">
                    Total: CHF {bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Transport */}
          {transportOptions.length > 0 && (
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <Car className="w-5 h-5 text-gold" />
                Transport
              </h3>
              <div className="space-y-3">
                {transportOptions.map((transport, index) => (
                  <div key={transport.id} className="pb-3 border-b border-fog/10 last:border-0">
                    <p className="text-fog font-medium">{index + 1}. {transport.name}</p>
                    <p className="text-sm text-fog/70 mt-1">{transport.type} • {transport.duration}</p>
                    <p className="text-sm text-gold font-semibold mt-1">CHF {transport.price.toFixed(2)}</p>
                  </div>
                ))}
                <div className="pt-2 border-t border-fog/10">
                  <p className="text-sm text-gold font-semibold">
                    Total: CHF {transportOptions.reduce((sum, opt) => sum + opt.price, 0).toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Right Column (1/3 on desktop) */}
        <div className="lg:col-span-1">
          <div className="sticky top-8 space-y-6">
            {/* Pricing Summary */}
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '700ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6">Pricing Summary</h3>
              <div className="space-y-3">
                {bookingData.tripState.flight && (
                  <div className="flex justify-between text-sm">
                    <span className="text-fog/80">Flight</span>
                    <span className="text-fog font-medium">CHF {bookingData.tripState.flight.price.toFixed(2)}</span>
                  </div>
                )}
                {bookingData.tripState.hotel && (
                  <div className="flex justify-between text-sm">
                    <span className="text-fog/80">Accommodation</span>
                    <span className="text-fog font-medium">CHF {(bookingData.tripState.hotel.pricePerNight * 3).toFixed(2)}</span>
                  </div>
                )}
                {bookingData.tripState.activities.length > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-fog/80">Activities</span>
                    <span className="text-fog font-medium">
                      CHF {bookingData.tripState.activities.reduce((sum, a) => sum + a.price, 0).toFixed(2)}
                    </span>
                  </div>
                )}
                {transportOptions.length > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-fog/80">Transport</span>
                    <span className="text-fog font-medium">
                      CHF {transportOptions.reduce((sum, opt) => sum + opt.price, 0).toFixed(2)}
                    </span>
                  </div>
                )}
                <div className="pt-3 border-t border-fog/10">
                  <div className="flex justify-between items-center">
                    <span className="text-base font-serif text-fog">Total</span>
                    <span className="text-2xl font-bold text-gold">CHF {calculateTotal().toFixed(2)}</span>
                  </div>
                  <p className="text-xs text-fog/60 mt-1">All prices in CHF</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '800ms', animationFillMode: 'forwards' }}>
              <div className="space-y-3">
                <Button
                  onClick={handleDownloadPDF}
                  className="w-full bg-gold hover:bg-gold/90 text-midnight"
                >
                  <Download className="w-4 h-4 mr-2" /> Download PDF
                </Button>
                <Button
                  onClick={onBack}
                  variant="outline"
                  className="w-full border-gold/30 text-gold hover:bg-gold/10"
                >
                  <RotateCcw className="w-4 h-4 mr-2" /> Plan Another Trip
                </Button>
              </div>
              <div className="mt-6 pt-6 border-t border-fog/10">
                <p className="text-xs text-fog/60 text-center">
                  A confirmation email has been sent to <span className="text-fog font-medium">{bookingData.formData.email}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

