import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Plane, Building2, Calendar, Car, MapPin, User, Mail, Phone, Download, X, CreditCard, PlayCircle, Clock, Check, Edit2 } from 'lucide-react';
import { Trip } from '@/services/authService';
import { generateBookingPDF } from '@/utils/pdfGenerator';
import { TripBookingFlow } from './TripBookingFlow';
import { cn } from '@/lib/utils';

interface TripDetailsDialogProps {
  trip: Trip | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTripUpdated?: () => void;
}

export const TripDetailsDialog = ({ trip, open, onOpenChange, onTripUpdated }: TripDetailsDialogProps) => {
  const navigate = useNavigate();
  const [showBookingFlow, setShowBookingFlow] = useState(false);

  if (!trip) return null;

  const tripData = trip.trip_data;
  const tripState = tripData?.tripState || tripData;
  const tripRequest = tripData?.tripRequest;
  const formData = tripData?.formData;
  const destination = tripState?.destination;
  const dateRange = tripRequest?.date_ranges?.[0];
  const isPlanned = trip.status === 'planned';
  const isInProgress = trip.status === 'in_progress';
  const currentStep = tripData?.currentStep;

  const getStepLabel = (step: string) => {
    const labels: Record<string, string> = {
      destinations: 'Selecting Destination',
      flights: 'Choosing Flights',
      hotels: 'Picking Hotels',
      itineraries: 'Planning Activities',
      transport: 'Arranging Transport',
      complete: 'Review & Book',
    };
    return labels[step] || step;
  };

  const handleContinuePlanning = () => {
    onOpenChange(false);
    navigate(`/resume-planning/${trip.id}`);
  };

  const handleResumeAtStep = (step: string) => {
    onOpenChange(false);
    navigate(`/resume-planning/${trip.id}?step=${step}`);
  };

  // Define workflow steps for the step selector
  const workflowSteps = [
    { key: 'destinations', label: 'Destination', icon: MapPin, hasData: !!tripState?.destination },
    { key: 'flights', label: 'Flight', icon: Plane, hasData: !!tripState?.flight },
    { key: 'hotels', label: 'Hotel', icon: Building2, hasData: !!tripState?.hotel },
    { key: 'itineraries', label: 'Activities', icon: Calendar, hasData: tripState?.activities?.length > 0 },
    { key: 'transport', label: 'Transport', icon: Car, hasData: Object.values(tripState?.transport || {}).filter(Boolean).length > 0 },
  ];

  const calculateTotal = () => {
    let total = 0;
    if (tripState?.flight) total += tripState.flight.price || 0;
    if (tripState?.hotel) {
      const nights = dateRange ? Math.ceil(
        (new Date(dateRange.to).getTime() - new Date(dateRange.from).getTime()) / (1000 * 60 * 60 * 24)
      ) : 3;
      total += (tripState.hotel.pricePerNight || 0) * nights;
    }
    if (tripState?.activities) {
      total += tripState.activities.reduce((sum: number, a: any) => sum + (a.price || 0), 0);
    }
    if (tripState?.transport) {
      Object.values(tripState.transport).forEach((opt: any) => {
        if (opt && opt.price) total += opt.price;
      });
    }
    return total;
  };

  const handleDownloadPDF = () => {
    if (!tripState || !tripRequest || !formData) return;
    
    const bookingData = {
      formData,
      tripState,
      bookingReference: trip.booking_reference || 'N/A',
    };
    generateBookingPDF(bookingData, tripRequest);
  };

  const transportOptions = tripState?.transport 
    ? Object.values(tripState.transport).filter(Boolean) 
    : [];

  const nights = dateRange 
    ? Math.ceil((new Date(dateRange.to).getTime() - new Date(dateRange.from).getTime()) / (1000 * 60 * 60 * 24))
    : 3;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto glass-sand border-fog/20 bg-midnight/95 [&>button]:text-fog [&>button]:hover:text-gold [&>button]:hover:bg-gold/10">
        <DialogHeader className="border-b border-fog/10 pb-4 mb-6">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl font-serif text-fog">
              Trip Details
            </DialogTitle>
            {trip.booking_reference && (
              <div className="px-4 py-2 rounded-xl bg-gold/10 border-2 border-gold/30">
                <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Booking Reference</p>
                <p className="text-lg font-bold text-gold font-mono">{trip.booking_reference}</p>
              </div>
            )}
          </div>
        </DialogHeader>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content - Left Column (2/3 on desktop) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Information */}
            {formData && (
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                  <User className="w-5 h-5 text-gold" />
                  Customer Information
                </h3>
                <div className="space-y-3">
                  {formData.fullName && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Full Name</p>
                      <p className="text-fog font-medium">{formData.fullName}</p>
                    </div>
                  )}
                  {formData.email && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Email</p>
                      <p className="text-fog font-medium flex items-center gap-2">
                        <Mail className="w-4 h-4 text-gold" />
                        {formData.email}
                      </p>
                    </div>
                  )}
                  {formData.phone && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Phone</p>
                      <p className="text-fog font-medium flex items-center gap-2">
                        <Phone className="w-4 h-4 text-gold" />
                        {formData.phone}
                      </p>
                    </div>
                  )}
                  {(formData.street || formData.city) && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Billing Address</p>
                      <p className="text-fog font-medium flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gold" />
                        {[
                          formData.street,
                          formData.city,
                          formData.zip,
                          formData.country
                        ].filter(Boolean).join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Trip Summary */}
            <div className="p-6 rounded-2xl glass-sand">
              <h3 className="text-lg font-serif text-fog mb-6">Trip Summary</h3>
              <div className="space-y-4">
                {destination && (
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Destination</p>
                    <p className="text-fog font-medium">{destination.name}{destination.country ? `, ${destination.country}` : ''}</p>
                  </div>
                )}
                {dateRange && (
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Travel Dates</p>
                    <p className="text-fog font-medium flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gold" />
                      {formatDate(dateRange.from)} - {formatDate(dateRange.to)}
                    </p>
                  </div>
                )}
                {tripRequest && (
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Travelers</p>
                    <p className="text-fog font-medium">{tripRequest.group_size} {tripRequest.traveler_type}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Flight Details */}
            {tripState?.flight && (
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                  <Plane className="w-5 h-5 text-gold" />
                  Flight Details
                </h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Airline</p>
                    <p className="text-fog font-medium">{tripState.flight.airline}{tripState.flight.class ? ` • ${tripState.flight.class}` : ''}</p>
                  </div>
                  {tripState.flight.flightNumber && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Flight Number</p>
                      <p className="text-fog font-medium">{tripState.flight.flightNumber}</p>
                    </div>
                  )}
                  {tripState.flight.departureTime && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Departure</p>
                      <p className="text-fog font-medium">
                        {tripState.flight.departureTime}{tripState.flight.departureAirport ? ` from ${tripState.flight.departureAirport}` : ''}
                      </p>
                    </div>
                  )}
                  {tripState.flight.arrivalTime && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Arrival</p>
                      <p className="text-fog font-medium">
                        {tripState.flight.arrivalTime}{tripState.flight.arrivalAirport ? ` at ${tripState.flight.arrivalAirport}` : ''}
                      </p>
                    </div>
                  )}
                  {tripState.flight.duration && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Duration</p>
                      <p className="text-fog font-medium">{tripState.flight.duration}</p>
                    </div>
                  )}
                  {tripState.flight.returnFlightNumber && (
                    <div className="pt-2 border-t border-fog/10">
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Return Flight</p>
                      <p className="text-fog font-medium">{tripState.flight.returnFlightNumber}</p>
                      {tripState.flight.returnDepartureTime && tripState.flight.returnArrivalTime && (
                        <p className="text-sm text-fog/80 mt-1">
                          {tripState.flight.returnDepartureTime} → {tripState.flight.returnArrivalTime}
                        </p>
                      )}
                    </div>
                  )}
                  {tripState.flight.price && (
                    <div className="pt-2 border-t border-fog/10">
                      <p className="text-sm text-gold font-semibold">CHF {tripState.flight.price.toFixed(2)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Hotel Details */}
            {tripState?.hotel && (
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-gold" />
                  Accommodation
                </h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Hotel</p>
                    <p className="text-fog font-medium">{tripState.hotel.name}</p>
                  </div>
                  {tripState.hotel.location && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Location</p>
                      <p className="text-fog font-medium">{tripState.hotel.location}</p>
                    </div>
                  )}
                  {tripState.hotel.stars && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Rating</p>
                      <p className="text-fog font-medium">{tripState.hotel.stars} stars</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Nights</p>
                    <p className="text-fog font-medium">{nights} nights</p>
                  </div>
                  {tripState.hotel.amenities && tripState.hotel.amenities.length > 0 && (
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Amenities</p>
                      <p className="text-fog font-medium text-sm">{tripState.hotel.amenities.slice(0, 5).join(', ')}</p>
                    </div>
                  )}
                  {tripState.hotel.pricePerNight && (
                    <div className="pt-2 border-t border-fog/10">
                      <p className="text-sm text-gold font-semibold">
                        CHF {(tripState.hotel.pricePerNight * nights).toFixed(2)} ({nights} nights)
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Activities */}
            {tripState?.activities && tripState.activities.length > 0 && (
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-gold" />
                  Activities & Experiences
                </h3>
                <div className="space-y-3">
                  {tripState.activities.map((activity: any, index: number) => (
                    <div key={activity.id || index} className="pb-3 border-b border-fog/10 last:border-0">
                      <p className="text-fog font-medium">{index + 1}. {activity.name}</p>
                      {(activity.category || activity.duration) && (
                        <p className="text-sm text-fog/70 mt-1">
                          {[activity.category, activity.duration].filter(Boolean).join(' • ')}
                        </p>
                      )}
                      {activity.price && (
                        <p className="text-sm text-gold font-semibold mt-1">CHF {activity.price.toFixed(2)}</p>
                      )}
                    </div>
                  ))}
                  <div className="pt-2 border-t border-fog/10">
                    <p className="text-sm text-gold font-semibold">
                      Total: CHF {tripState.activities.reduce((sum: number, a: any) => sum + (a.price || 0), 0).toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Transport */}
            {transportOptions.length > 0 && (
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                  <Car className="w-5 h-5 text-gold" />
                  Transport
                </h3>
                <div className="space-y-3">
                  {transportOptions.map((transport: any, index: number) => (
                    <div key={transport.id || index} className="pb-3 border-b border-fog/10 last:border-0">
                      <p className="text-fog font-medium">{index + 1}. {transport.name}</p>
                      {(transport.type || transport.duration) && (
                        <p className="text-sm text-fog/70 mt-1">
                          {[transport.type, transport.duration].filter(Boolean).join(' • ')}
                        </p>
                      )}
                      {transport.price && (
                        <p className="text-sm text-gold font-semibold mt-1">CHF {transport.price.toFixed(2)}</p>
                      )}
                    </div>
                  ))}
                  <div className="pt-2 border-t border-fog/10">
                    <p className="text-sm text-gold font-semibold">
                      Total: CHF {transportOptions.reduce((sum: number, opt: any) => sum + (opt.price || 0), 0).toFixed(2)}
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
              <div className="p-6 rounded-2xl glass-sand">
                <h3 className="text-lg font-serif text-fog mb-6">Pricing Summary</h3>
                <div className="space-y-3">
                  {tripState?.flight && (
                    <div className="flex justify-between text-sm">
                      <span className="text-fog/80">Flight</span>
                      <span className="text-fog font-medium">CHF {(tripState.flight.price || 0).toFixed(2)}</span>
                    </div>
                  )}
                  {tripState?.hotel && tripState.hotel.pricePerNight && (
                    <div className="flex justify-between text-sm">
                      <span className="text-fog/80">Accommodation</span>
                      <span className="text-fog font-medium">CHF {(tripState.hotel.pricePerNight * nights).toFixed(2)}</span>
                    </div>
                  )}
                  {tripState?.activities && tripState.activities.length > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-fog/80">Activities</span>
                      <span className="text-fog font-medium">
                        CHF {tripState.activities.reduce((sum: number, a: any) => sum + (a.price || 0), 0).toFixed(2)}
                      </span>
                    </div>
                  )}
                  {transportOptions.length > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-fog/80">Transport</span>
                      <span className="text-fog font-medium">
                        CHF {transportOptions.reduce((sum: number, opt: any) => sum + (opt.price || 0), 0).toFixed(2)}
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

              {/* In Progress Status */}
              {isInProgress && currentStep && (
                <div className="p-6 rounded-2xl glass-sand border border-teal/30 mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Clock className="w-5 h-5 text-teal-light" />
                    <h3 className="text-lg font-serif text-fog">Trip In Progress</h3>
                  </div>
                  <p className="text-sm text-fog/80 mb-3">
                    You stopped at: <span className="text-teal-light font-medium">{getStepLabel(currentStep)}</span>
                  </p>
                  
                  {/* Progress Summary */}
                  {(() => {
                    const hasDestination = !!tripState?.destination;
                    const hasFlight = !!tripState?.flight;
                    const hasHotel = !!tripState?.hotel;
                    const activitiesCount = tripState?.activities?.length || 0;
                    const transportCount = Object.values(tripState?.transport || {}).filter(Boolean).length;
                    const totalSteps = 5;
                    const completedSteps = [
                      hasDestination,
                      hasFlight,
                      hasHotel,
                      activitiesCount > 0,
                      transportCount > 0
                    ].filter(Boolean).length;
                    const progressPercentage = Math.round((completedSteps / totalSteps) * 100);
                    
                    return (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-fog/60">Progress</span>
                          <span className="text-teal-light font-medium">{progressPercentage}%</span>
                        </div>
                        <div className="w-full bg-fog/10 rounded-full h-2">
                          <div 
                            className="bg-teal-light h-2 rounded-full transition-all"
                            style={{ width: `${progressPercentage}%` }}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs text-fog/70 mt-2">
                          {hasDestination && (
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3 h-3 text-gold" />
                              <span>Destination selected</span>
                            </div>
                          )}
                          {hasFlight && (
                            <div className="flex items-center gap-1">
                              <Plane className="w-3 h-3 text-gold" />
                              <span>Flight selected</span>
                            </div>
                          )}
                          {hasHotel && (
                            <div className="flex items-center gap-1">
                              <Building2 className="w-3 h-3 text-gold" />
                              <span>Hotel selected</span>
                            </div>
                          )}
                          {activitiesCount > 0 && (
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-gold" />
                              <span>{activitiesCount} activities</span>
                            </div>
                          )}
                          {transportCount > 0 && (
                            <div className="flex items-center gap-1">
                              <Car className="w-3 h-3 text-gold" />
                              <span>{transportCount} transport</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Resume/Edit at Step - for both planned and in_progress trips */}
              {(isPlanned || isInProgress) && (
                <div className="p-6 rounded-2xl glass-sand">
                  <h3 className="text-lg font-serif text-fog mb-4 flex items-center gap-2">
                    <Edit2 className="w-5 h-5 text-gold" />
                    Edit Trip
                  </h3>
                  <p className="text-sm text-fog/70 mb-4">
                    Click any step to resume or edit your trip from that point
                  </p>
                  <div className="space-y-2">
                    {workflowSteps.map((step) => {
                      const Icon = step.icon;
                      return (
                        <button
                          key={step.key}
                          onClick={() => handleResumeAtStep(step.key)}
                          className={cn(
                            "w-full flex items-center gap-3 p-3 rounded-xl transition-all",
                            "hover:bg-gold/10 hover:border-gold/30 border border-transparent",
                            "group cursor-pointer text-left"
                          )}
                        >
                          <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center transition-colors",
                            step.hasData 
                              ? "bg-gold/20 text-gold" 
                              : "bg-fog/10 text-fog/40"
                          )}>
                            {step.hasData ? (
                              <Check className="w-4 h-4" />
                            ) : (
                              <Icon className="w-4 h-4" />
                            )}
                          </div>
                          <div className="flex-1">
                            <p className={cn(
                              "text-sm font-medium",
                              step.hasData ? "text-fog" : "text-fog/60"
                            )}>
                              {step.label}
                            </p>
                            <p className="text-xs text-fog/50">
                              {step.hasData ? 'Click to edit' : 'Click to add'}
                            </p>
                          </div>
                          <Edit2 className="w-4 h-4 text-fog/30 group-hover:text-gold transition-colors" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="p-6 rounded-2xl glass-sand">
                <div className="space-y-3">
                  {isInProgress && (
                    <Button
                      onClick={handleContinuePlanning}
                      className="w-full bg-teal hover:bg-teal/90 text-midnight"
                    >
                      <PlayCircle className="w-4 h-4 mr-2" /> Continue Planning
                    </Button>
                  )}
                  {isPlanned && (
                    <Button
                      onClick={() => setShowBookingFlow(true)}
                      className="w-full bg-gold hover:bg-gold/90 text-midnight"
                    >
                      <CreditCard className="w-4 h-4 mr-2" /> Book Trip
                    </Button>
                  )}
                  {formData && tripRequest && (
                    <Button
                      onClick={handleDownloadPDF}
                      className="w-full bg-gold hover:bg-gold/90 text-midnight"
                    >
                      <Download className="w-4 h-4 mr-2" /> Download PDF
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>

      {/* Booking Flow Dialog */}
      {showBookingFlow && trip && (
        <TripBookingFlow
          trip={trip}
          open={showBookingFlow}
          onOpenChange={(open) => {
            setShowBookingFlow(open);
            if (!open && onTripUpdated) {
              onTripUpdated();
            }
          }}
        />
      )}
    </Dialog>
  );
};
