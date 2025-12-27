import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';
import { WorkflowProgress, WorkflowStep } from './WorkflowProgress';
import { DestinationAgent } from './agents/DestinationAgent';
import { FlightAgent } from './agents/FlightAgent';
import { HotelAgent } from './agents/HotelAgent';
import { ItineraryAgent } from './agents/ItineraryAgent';
import { TransportAgent } from './agents/TransportAgent';
import { CheckoutAgent } from './agents/CheckoutAgent';
import { BookingConfirmation } from './agents/BookingConfirmation';
import { Destination, Flight, Hotel, Activity, TransportOption } from '@/data/mockAgentData';
import { Button } from '@/components/ui/button';
import { Check, Plane, Building2, Calendar, Car, RotateCcw, CreditCard, Save } from 'lucide-react';
import { planTrip, TripRequest } from '@/services/api';

export interface WorkflowState {
  destination: Destination | null;
  flight: Flight | null;
  hotel: Hotel | null;
  activities: Activity[];
  transport: Record<string, TransportOption | null>;
}

interface TripPlanningWorkflowProps {
  tripRequest: TripRequest;
  onReset: () => void;
  // Props for resuming a saved trip
  initialState?: WorkflowState;
  initialStep?: WorkflowStep;
  tripId?: number;
  availableDestinations?: Destination[];
  // Original trip status for determining save behavior
  originalTripStatus?: 'planned' | 'in_progress';
}

export const TripPlanningWorkflow = ({ 
  tripRequest, 
  onReset,
  initialState,
  initialStep,
  tripId: initialTripId,
  availableDestinations,
  originalTripStatus,
}: TripPlanningWorkflowProps) => {
  // Determine if we're editing an existing trip
  const isEditingExistingTrip = !!initialTripId;
  const { user } = useAuth();
  const [step, setStep] = useState<WorkflowStep>(initialStep || 'destinations');
  const [isLoading, setIsLoading] = useState(!initialStep); // Don't load if resuming
  const [destinations, setDestinations] = useState<Destination[]>(availableDestinations || []);
  const [error, setError] = useState<string | null>(null);
  const [state, setState] = useState<WorkflowState>(initialState || {
    destination: null,
    flight: null,
    hotel: null,
    activities: [],
    transport: {},
  });
  const [tripId, setTripId] = useState<number | undefined>(initialTripId);
  const [isSavingProgress, setIsSavingProgress] = useState(false);
  // Track pending selections (selections made but not yet confirmed with "Continue")
  const [pendingSelections, setPendingSelections] = useState<{
    destination?: Destination;
    flight?: Flight;
    hotel?: Hotel;
    activities?: Activity[];
    transport?: Record<string, TransportOption | null>;
  }>({});
  const [bookingData, setBookingData] = useState<{
    formData: {
      fullName: string;
      email: string;
      phone: string;
      street: string;
      city: string;
      zip: string;
      country: string;
    };
    tripState: WorkflowState;
    bookingReference: string;
  } | null>(null);
  const [isSavingTrip, setIsSavingTrip] = useState(false);

  // Test mode: Jump directly to transport step
  useEffect(() => {
    if (window.location.search.includes('test=transport')) {
      setState({
        destination: {
          id: 'test-1',
          name: 'Santorini',
          country: 'Greece',
          description: 'Test destination for transport testing',
          matchReason: 'Test',
          image: '/placeholder.svg',
          tempRange: '20-25°C',
          iataCode: 'JTR',
          airportName: 'Santorini Airport'
        },
        flight: {
          id: 'test-flight-1',
          airline: 'Test Airline',
          airlineCode: 'TA',
          airlineLogo: '',
          departureTime: '10:00',
          arrivalTime: '14:00',
          departureAirport: 'ZRH',
          arrivalAirport: 'JTR',
          duration: '4h',
          stops: 0,
          price: 500,
          class: 'Economy'
        },
        hotel: {
          id: 'test-hotel-1',
          name: 'Test Hotel',
          stars: 4,
          image: '/placeholder.svg',
          pricePerNight: 100,
          amenities: ['WiFi', 'Pool'],
          location: 'Oia',
          rating: 4.5,
          reviewCount: 150
        },
        activities: [
          {
            id: 'test-act-1',
            name: 'Sunset Wine Tasting',
            description: 'Test activity',
            duration: '3 hours',
            price: 95,
            image: '/placeholder.svg',
            category: 'Experience'
          }
        ],
        transport: {}
      });
      setStep('transport');
      setIsLoading(false);
    }
  }, []);

  // Fetch destinations from API on mount (skip if in test mode or resuming with destinations)
  useEffect(() => {
    if (window.location.search.includes('test=transport')) {
      return; // Skip API call in test mode
    }

    // Skip if we already have destinations (resuming)
    if (availableDestinations && availableDestinations.length > 0) {
      setIsLoading(false);
      return;
    }

    const fetchDestinations = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const results = await planTrip(tripRequest);
        setDestinations(results);
      } catch (err) {
        console.error('Failed to fetch destinations:', err);
        setError(err instanceof Error ? err.message : 'Failed to load destinations');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDestinations();
  }, [tripRequest, availableDestinations]);

  const handleDestinationSelect = (destination: Destination) => {
    setState(prev => ({ ...prev, destination }));
    setPendingSelections(prev => ({ ...prev, destination: undefined })); // Clear pending when confirmed
    setStep('flights');
  };

  const handleFlightSelect = (flight: Flight) => {
    setState(prev => ({ ...prev, flight }));
    setPendingSelections(prev => ({ ...prev, flight: undefined })); // Clear pending when confirmed
    setStep('hotels');
  };

  const handleHotelSelect = (hotel: Hotel) => {
    setState(prev => ({ ...prev, hotel }));
    setPendingSelections(prev => ({ ...prev, hotel: undefined })); // Clear pending when confirmed
    setStep('itineraries');
  };

  const handleActivitiesSelect = (activities: Activity[]) => {
    setState(prev => ({ ...prev, activities }));
    setPendingSelections(prev => ({ ...prev, activities: undefined })); // Clear pending when confirmed
    setStep('transport');
  };

  // Handlers for pending selections (when user selects but hasn't clicked Continue)
  const handlePendingDestinationChange = (destination: Destination | null) => {
    if (destination) {
      setPendingSelections(prev => ({ ...prev, destination }));
    }
  };

  const handlePendingFlightChange = (flight: Flight | null) => {
    if (flight) {
      setPendingSelections(prev => ({ ...prev, flight }));
    }
  };

  const handlePendingHotelChange = (hotel: Hotel | null) => {
    if (hotel) {
      setPendingSelections(prev => ({ ...prev, hotel }));
    }
  };

  const handlePendingActivitiesChange = (activities: Activity[] | null) => {
    if (activities) {
      setPendingSelections(prev => ({ ...prev, activities }));
    }
  };

  const handlePendingTransportChange = (transport: Record<string, TransportOption | null> | null) => {
    if (transport) {
      setPendingSelections(prev => ({ ...prev, transport }));
    }
  };

  const handleTransportComplete = (transport: Record<string, TransportOption | null>) => {
    setState(prev => ({ ...prev, transport }));
    setPendingSelections(prev => ({ ...prev, transport: undefined })); // Clear pending when confirmed
    setStep('complete');
  };

  const handleCheckout = () => {
    setStep('checkout');
  };

  // Handler for clicking on workflow progress steps (when editing existing trip)
  const handleStepClick = (clickedStep: WorkflowStep) => {
    // Navigate to the clicked step while preserving all state
    setStep(clickedStep);
  };

  const handleBookingComplete = (bookingData: {
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
  }) => {
    setBookingData({
      formData: bookingData.formData,
      tripState: bookingData.tripState,
      bookingReference: bookingData.bookingReference,
    });
    setStep('confirmation');
  };

  const calculateTotal = () => {
    let total = 0;
    if (state.flight) total += state.flight.price;
    if (state.hotel) total += state.hotel.pricePerNight * 3; // Assuming 3 nights
    total += state.activities.reduce((sum, a) => sum + a.price, 0);
    Object.values(state.transport).forEach(opt => {
      if (opt) total += opt.price;
    });
    return Math.round(total * 100) / 100; // Round to 2 decimal places
  };

  const handleSaveTrip = async () => {
    if (!user) {
      // Prompt to login
      if (confirm('Please login to save your trip. Would you like to go to the login page?')) {
        window.location.href = '/login';
      }
      return;
    }

    setIsSavingTrip(true);
    try {
      const tripData = {
        tripState: state,
        tripRequest: tripRequest,
      };

      if (tripId) {
        // Update existing trip to 'planned' status
        await authService.updateTrip(user.id, tripId, {
          status: 'planned',
          trip_data: tripData,
        });
      } else {
        await authService.createTrip(user.id, {
          status: 'planned',
          trip_data: tripData,
        });
      }
      alert('Trip saved successfully!');
    } catch (error) {
      console.error('Failed to save trip:', error);
      alert('Failed to save trip. Please try again.');
    } finally {
      setIsSavingTrip(false);
    }
  };

  const handleSaveProgress = async () => {
    if (!user) {
      // Prompt to login
      if (confirm('Please login to save your progress. Would you like to go to the login page?')) {
        window.location.href = '/login';
      }
      return;
    }

    setIsSavingProgress(true);
    try {
      // Merge pending selections with current state to save current selection on the page
      const tripData = {
        tripState: {
          destination: pendingSelections.destination || state.destination,
          flight: pendingSelections.flight || state.flight,
          hotel: pendingSelections.hotel || state.hotel,
          activities: pendingSelections.activities || state.activities,
          transport: pendingSelections.transport || state.transport,
        },
        tripRequest: tripRequest,
        currentStep: step,
        availableDestinations: destinations,
        // Add timestamp for tracking
        savedAt: new Date().toISOString(),
      };

      if (tripId) {
        // Update existing trip - preserve the original status if it was 'planned'
        // (planned trips stay planned, in_progress stays in_progress)
        const statusToSave = originalTripStatus === 'planned' ? 'planned' : 'in_progress';
        await authService.updateTrip(user.id, tripId, {
          status: statusToSave,
          trip_data: tripData,
        });
      } else {
        // Create new trip
        const newTrip = await authService.createTrip(user.id, {
          status: 'in_progress',
          trip_data: tripData,
        });
        setTripId(newTrip.id);
      }
      alert('Progress saved! You can continue planning or come back later.');
    } catch (error) {
      console.error('Failed to save progress:', error);
      alert('Failed to save progress. Please try again.');
    } finally {
      setIsSavingProgress(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden flex flex-col">
      <div className="pt-16 pb-2">
        <WorkflowProgress 
          currentStep={step} 
          onStepClick={isEditingExistingTrip ? handleStepClick : undefined}
          isEditing={isEditingExistingTrip}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {step === 'destinations' && (
          <div className="relative min-h-full">
            <DestinationAgent
              destinations={destinations}
              isLoading={isLoading}
              error={error}
              onSelect={handleDestinationSelect}
              onBack={onReset}
              onSelectionChange={handlePendingDestinationChange}
            />
            {user && destinations.length > 0 && !isLoading && (
              <div className="fixed bottom-4 right-4 z-50">
                <Button
                  onClick={handleSaveProgress}
                  disabled={isSavingProgress}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10 bg-midnight/90 backdrop-blur-sm shadow-lg"
                >
                  <Save className="w-4 h-4 mr-2" /> 
                  {isSavingProgress ? 'Saving...' : 'Save Progress'}
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'flights' && state.destination && (
          <div className="relative min-h-full">
            <FlightAgent
              destination={state.destination}
              tripRequest={tripRequest}
              onSelect={handleFlightSelect}
              onBack={() => setStep('destinations')}
              onSelectionChange={handlePendingFlightChange}
            />
            {user && (
              <div className="fixed bottom-4 right-4 z-50">
                <Button
                  onClick={handleSaveProgress}
                  disabled={isSavingProgress}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10 bg-midnight/90 backdrop-blur-sm shadow-lg"
                >
                  <Save className="w-4 h-4 mr-2" /> 
                  {isSavingProgress ? 'Saving...' : 'Save Progress'}
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'hotels' && state.destination && (
          <div className="relative min-h-full">
            <HotelAgent
              destination={state.destination}
              tripRequest={tripRequest}
              flight={state.flight}
              onSelect={handleHotelSelect}
              onBack={() => setStep('flights')}
              onSelectionChange={handlePendingHotelChange}
            />
            {user && (
              <div className="fixed bottom-4 right-4 z-50">
                <Button
                  onClick={handleSaveProgress}
                  disabled={isSavingProgress}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10 bg-midnight/90 backdrop-blur-sm shadow-lg"
                >
                  <Save className="w-4 h-4 mr-2" /> 
                  {isSavingProgress ? 'Saving...' : 'Save Progress'}
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'itineraries' && state.destination && (
          <div className="relative min-h-full">
            <ItineraryAgent
              destination={state.destination}
              tripRequest={tripRequest}
              onSelect={handleActivitiesSelect}
              onBack={() => setStep('hotels')}
              onSelectionChange={handlePendingActivitiesChange}
            />
            {user && (
              <div className="fixed bottom-4 right-4 z-50">
                <Button
                  onClick={handleSaveProgress}
                  disabled={isSavingProgress}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10 bg-midnight/90 backdrop-blur-sm shadow-lg"
                >
                  <Save className="w-4 h-4 mr-2" /> 
                  {isSavingProgress ? 'Saving...' : 'Save Progress'}
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'transport' && (
          <div className="relative min-h-full">
            <TransportAgent
              onComplete={handleTransportComplete}
              onBack={() => setStep('itineraries')}
              destination={state.destination}
              hotel={state.hotel}
              activities={state.activities}
              tripRequest={tripRequest}
              onSelectionChange={handlePendingTransportChange}
            />
            {user && (
              <div className="fixed bottom-4 right-4 z-50">
                <Button
                  onClick={handleSaveProgress}
                  disabled={isSavingProgress}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10 bg-midnight/90 backdrop-blur-sm shadow-lg"
                >
                  <Save className="w-4 h-4 mr-2" /> 
                  {isSavingProgress ? 'Saving...' : 'Save Progress'}
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'checkout' && (
          <CheckoutAgent
            tripState={state}
            tripRequest={tripRequest}
            onBook={handleBookingComplete}
            onBack={() => setStep('complete')}
          />
        )}

        {step === 'confirmation' && bookingData && (
          <BookingConfirmation
            bookingData={bookingData}
            tripRequest={tripRequest}
            onBack={onReset}
          />
        )}

        {step === 'complete' && (
          <div className="animate-fade-in max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <div className="w-20 h-20 rounded-full bg-gold/20 flex items-center justify-center mx-auto mb-4 animate-scale-in">
                <Check className="w-10 h-10 text-gold" />
              </div>
              <h2 className="text-3xl font-serif text-fog mb-2">Your Trip is Planned!</h2>
              <p className="text-fog/90">Here's a summary of your perfect getaway</p>
            </div>

            {/* Summary Cards */}
            <div className="space-y-4">
              {/* Destination */}
              {state.destination && (
                <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
                  <div className="flex items-center gap-4">
                    <div className="w-24 h-24 rounded-xl overflow-hidden">
                      <img src={state.destination.image} alt={state.destination.name} className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Destination</p>
                      <h3 className="text-xl font-semibold text-fog">{state.destination.name}, {state.destination.country}</h3>
                    </div>
                  </div>
                </div>
              )}

              {/* Flight */}
              {state.flight && (
                <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-gold/20 flex items-center justify-center">
                      <Plane className="w-6 h-6 text-gold" />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Flight</p>
                      <p className="text-fog font-medium">{state.flight.airline} • {state.flight.class}</p>
                      <p className="text-sm text-fog/80">{state.flight.departureTime} → {state.flight.arrivalTime} ({state.flight.duration})</p>
                    </div>
                    <p className="text-lg font-bold text-gold">CHF {state.flight.price}</p>
                  </div>
                </div>
              )}

              {/* Hotel */}
              {state.hotel && (
                <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '300ms', animationFillMode: 'forwards' }}>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-gold/20 flex items-center justify-center">
                      <Building2 className="w-6 h-6 text-gold" />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Hotel</p>
                      <p className="text-fog font-medium">{state.hotel.name}</p>
                      <p className="text-sm text-fog/80">{state.hotel.location} • {state.hotel.stars} stars</p>
                    </div>
                    <p className="text-lg font-bold text-gold">CHF {state.hotel.pricePerNight * 3}</p>
                  </div>
                </div>
              )}

              {/* Activities */}
              <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '400ms', animationFillMode: 'forwards' }}>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gold/20 flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-gold" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Activities</p>
                    <p className="text-fog font-medium">{state.activities.length} experiences selected</p>
                    <p className="text-sm text-fog/80">{state.activities.map(a => a.category).filter((v, i, a) => a.indexOf(v) === i).join(', ')}</p>
                  </div>
                  <p className="text-lg font-bold text-gold">CHF {state.activities.reduce((sum, a) => sum + a.price, 0)}</p>
                </div>
              </div>

              {/* Transport */}
              <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '500ms', animationFillMode: 'forwards' }}>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gold/20 flex items-center justify-center">
                    <Car className="w-6 h-6 text-gold" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Transport</p>
                    <p className="text-fog font-medium">
                      {Object.values(state.transport).filter(Boolean).length} transfers booked
                    </p>
                  </div>
                  <p className="text-lg font-bold text-gold">
                    CHF {Object.values(state.transport).reduce((sum, opt) => sum + (opt?.price || 0), 0)}
                  </p>
                </div>
              </div>

              {/* Total */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-gold/20 to-teal/20 border border-gold/30 animate-slide-up" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }}>
                <div className="flex items-center justify-between">
                  <p className="text-xl font-serif text-fog">Estimated Total</p>
                  <p className="text-3xl font-bold text-gold">CHF {calculateTotal().toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-center gap-4 mt-8">
              <Button
                onClick={onReset}
                variant="outline"
                className="border-gold/30 text-gold hover:bg-gold/10"
              >
                <RotateCcw className="w-4 h-4 mr-2" /> Plan Another Trip
              </Button>
              {user && (
                <Button
                  onClick={handleSaveTrip}
                  disabled={isSavingTrip}
                  variant="outline"
                  className="border-teal/30 text-teal-light hover:bg-teal/10"
                >
                  <Save className="w-4 h-4 mr-2" /> {isSavingTrip ? 'Saving...' : 'Save Trip'}
                </Button>
              )}
              <Button
                onClick={handleCheckout}
                className="bg-gold hover:bg-gold/90 text-midnight px-8"
              >
                <CreditCard className="w-4 h-4 mr-2" /> Book Trip
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
