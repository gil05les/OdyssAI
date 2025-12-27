import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import { authService, Trip } from '@/services/authService';
import { Plane, Building2, Calendar, Car, MapPin, Loader2, Trash2, PlayCircle, Clock, Edit2 } from 'lucide-react';
import { Header } from '@/components/Header';
import { cn } from '@/lib/utils';
import { TripDetailsDialog } from '@/components/travel/TripDetailsDialog';

export default function MyTrips() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'booked' | 'planned' | 'in_progress' | 'completed'>('booked');
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const loadTrips = async () => {
    if (!user) return;
    try {
      const allTrips = await authService.getTrips(user.id);
      setTrips(allTrips);
    } catch (err) {
      console.error('Failed to load trips:', err);
    }
  };

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const fetchTrips = async () => {
      setIsLoading(true);
      await loadTrips();
      setIsLoading(false);
    };

    fetchTrips();
  }, [user, navigate]);

  const handleDeleteTrip = async (tripId: number) => {
    if (!user) return;
    if (!confirm('Are you sure you want to delete this trip?')) return;

    try {
      await authService.deleteTrip(user.id, tripId);
      setTrips(trips.filter(t => t.id !== tripId));
    } catch (err) {
      console.error('Failed to delete trip:', err);
    }
  };

  const getFilteredTrips = (status: string) => {
    return trips.filter(trip => trip.status === status);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateTotal = (tripData: any) => {
    let total = 0;
    if (tripData.flight) total += tripData.flight.price || 0;
    if (tripData.hotel) {
      const nights = 3; // Could be calculated from dates
      total += (tripData.hotel.pricePerNight || 0) * nights;
    }
    if (tripData.activities) {
      total += tripData.activities.reduce((sum: number, a: any) => sum + (a.price || 0), 0);
    }
    if (tripData.transport) {
      Object.values(tripData.transport).forEach((opt: any) => {
        if (opt && opt.price) total += opt.price;
      });
    }
    return total;
  };

  const TripCard = ({ trip }: { trip: Trip }) => {
    const tripData = trip.trip_data;
    const destination = tripData?.destination || tripData?.tripState?.destination;
    const destinationName = destination?.name || 'Unknown Destination';
    const destinationCountry = destination?.country || '';
    const dateRange = tripData?.tripRequest?.date_ranges?.[0];
    const total = calculateTotal(tripData?.tripState || tripData);
    const isPlanned = trip.status === 'planned';

    const handleCardClick = (e: React.MouseEvent) => {
      // Don't open dialog if clicking on buttons
      if ((e.target as HTMLElement).closest('button')) {
        return;
      }
      setSelectedTrip(trip);
      setIsDialogOpen(true);
    };

    const handleEditTrip = (e: React.MouseEvent) => {
      e.stopPropagation();
      navigate(`/resume-planning/${trip.id}`);
    };

    return (
      <div 
        className="p-6 rounded-2xl glass-sand animate-slide-up hover:scale-[1.02] hover:border-gold/30 border border-transparent transition-all cursor-pointer"
        onClick={handleCardClick}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-gold" />
              <h3 className="text-xl font-semibold text-fog">{destinationName}</h3>
              {destinationCountry && (
                <span className="text-sm text-fog/60">{destinationCountry}</span>
              )}
            </div>
            {dateRange && (
              <p className="text-sm text-fog/70 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {formatDate(dateRange.from)} - {formatDate(dateRange.to)}
              </p>
            )}
            {trip.booking_reference && (
              <p className="text-xs text-teal-light mt-2">
                Booking: {trip.booking_reference}
              </p>
            )}
          </div>
          <div className="flex items-center gap-1">
            {isPlanned && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleEditTrip}
                className="text-teal-light hover:text-teal hover:bg-teal/10"
                title="Edit Trip"
              >
                <Edit2 className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteTrip(trip.id);
              }}
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          {tripData?.tripState?.flight && (
            <div className="flex items-center gap-2 text-sm text-fog/80">
              <Plane className="w-4 h-4 text-gold" />
              <span>{tripData.tripState.flight.airline}</span>
            </div>
          )}
          {tripData?.tripState?.hotel && (
            <div className="flex items-center gap-2 text-sm text-fog/80">
              <Building2 className="w-4 h-4 text-gold" />
              <span>{tripData.tripState.hotel.name}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-fog/10">
          <span className="text-xs text-fog/60">Total</span>
          <div className="flex items-center gap-3">
            {isPlanned && (
              <Button
                onClick={handleEditTrip}
                variant="outline"
                size="sm"
                className="border-teal/30 text-teal-light hover:bg-teal/10"
              >
                <Edit2 className="w-3 h-3 mr-1" /> Edit
              </Button>
            )}
            <span className="text-xl font-bold text-gold">CHF {total.toFixed(2)}</span>
          </div>
        </div>
      </div>
    );
  };

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

  const InProgressTripCard = ({ trip, onDelete }: { trip: Trip; onDelete: (id: number) => void }) => {
    const tripData = trip.trip_data;
    const tripState = tripData?.tripState || {};
    const destination = tripState?.destination;
    const destinationName = destination?.name || 'Trip in Progress';
    const destinationCountry = destination?.country || '';
    const currentStep = tripData?.currentStep || 'destinations';
    const dateRange = tripData?.tripRequest?.date_ranges?.[0];
    
    // Calculate progress details
    const hasDestination = !!tripState?.destination;
    const hasFlight = !!tripState?.flight;
    const hasHotel = !!tripState?.hotel;
    const activitiesCount = tripState?.activities?.length || 0;
    const transportCount = Object.values(tripState?.transport || {}).filter(Boolean).length;
    
    // Calculate progress percentage
    const totalSteps = 5; // destination, flight, hotel, activities, transport
    const completedSteps = [
      hasDestination,
      hasFlight,
      hasHotel,
      activitiesCount > 0,
      transportCount > 0
    ].filter(Boolean).length;
    const progressPercentage = Math.round((completedSteps / totalSteps) * 100);

    const handleContinue = () => {
      navigate(`/resume-planning/${trip.id}`);
    };

    const handleCardClick = (e: React.MouseEvent) => {
      // Don't open dialog if clicking on buttons
      if ((e.target as HTMLElement).closest('button')) {
        return;
      }
      setSelectedTrip(trip);
      setIsDialogOpen(true);
    };

    return (
      <div 
        className="p-6 rounded-2xl glass-sand animate-slide-up border border-teal/30 hover:scale-[1.02] hover:border-gold/30 transition-all cursor-pointer"
        onClick={handleCardClick}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-teal-light" />
              <h3 className="text-xl font-semibold text-fog">{destinationName}</h3>
              {destinationCountry && (
                <span className="text-sm text-fog/60">{destinationCountry}</span>
              )}
            </div>
            {dateRange && (
              <p className="text-sm text-fog/70 flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4" />
                {formatDate(dateRange.from)} - {formatDate(dateRange.to)}
              </p>
            )}
            <p className="text-sm text-teal-light mb-3 flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full bg-teal/20 text-xs">
                {getStepLabel(currentStep)}
              </span>
            </p>
            
            {/* Progress Summary */}
            <div className="space-y-2 mb-3">
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
            </div>

            {/* Selected Items Summary */}
            <div className="grid grid-cols-2 gap-2 text-xs text-fog/70">
              {hasDestination && (
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-gold" />
                  <span>Destination</span>
                </div>
              )}
              {hasFlight && (
                <div className="flex items-center gap-1">
                  <Plane className="w-3 h-3 text-gold" />
                  <span>{tripState.flight.airline || 'Flight'}</span>
                </div>
              )}
              {hasHotel && (
                <div className="flex items-center gap-1">
                  <Building2 className="w-3 h-3 text-gold" />
                  <span>{tripState.hotel.name || 'Hotel'}</span>
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
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(trip.id);
            }}
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-fog/10">
          <span className="text-xs text-fog/60">
            Last updated: {formatDate(trip.updated_at)}
          </span>
          <Button 
            onClick={(e) => {
              e.stopPropagation();
              handleContinue();
            }}
            className="bg-teal hover:bg-teal/90 text-midnight"
          >
            <PlayCircle className="w-4 h-4 mr-2" /> Continue Planning
          </Button>
        </div>
      </div>
    );
  };

  const EmptyState = ({ message }: { message: string }) => (
    <div className="text-center py-12">
      <div className="w-16 h-16 rounded-full bg-gold/20 flex items-center justify-center mx-auto mb-4">
        <Calendar className="w-8 h-8 text-gold" />
      </div>
      <p className="text-fog/70">{message}</p>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-midnight">
        <Header />
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)] pt-16">
          <Loader2 className="w-8 h-8 text-gold animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-midnight">
      <Header />
      <div className="container mx-auto px-4 py-12 max-w-6xl pt-20">
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-fog mb-2">My Trips</h1>
          <p className="text-fog/70">Manage and view all your travel plans</p>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
          <TabsList className="grid w-full max-w-xl grid-cols-4 glass-sand mb-8">
            <TabsTrigger value="booked" className="data-[state=active]:bg-gold data-[state=active]:text-midnight">
              Booked
            </TabsTrigger>
            <TabsTrigger value="planned" className="data-[state=active]:bg-gold data-[state=active]:text-midnight">
              Planned
            </TabsTrigger>
            <TabsTrigger value="in_progress" className="data-[state=active]:bg-gold data-[state=active]:text-midnight flex items-center gap-1">
              <Clock className="w-3 h-3" /> In Progress
            </TabsTrigger>
            <TabsTrigger value="completed" className="data-[state=active]:bg-gold data-[state=active]:text-midnight">
              Past
            </TabsTrigger>
          </TabsList>

          <TabsContent value="booked" className="space-y-4">
            {getFilteredTrips('booked').length > 0 ? (
              getFilteredTrips('booked').map(trip => (
                <TripCard key={trip.id} trip={trip} />
              ))
            ) : (
              <EmptyState message="No booked trips yet. Complete a booking to see it here." />
            )}
          </TabsContent>

          <TabsContent value="planned" className="space-y-4">
            {getFilteredTrips('planned').length > 0 ? (
              getFilteredTrips('planned').map(trip => (
                <TripCard key={trip.id} trip={trip} />
              ))
            ) : (
              <EmptyState message="No planned trips yet. Save a trip plan to see it here." />
            )}
          </TabsContent>

          <TabsContent value="in_progress" className="space-y-4">
            {getFilteredTrips('in_progress').length > 0 ? (
              getFilteredTrips('in_progress').map(trip => (
                <InProgressTripCard key={trip.id} trip={trip} onDelete={handleDeleteTrip} />
              ))
            ) : (
              <EmptyState message="No trips in progress. Save your progress while planning to see it here." />
            )}
          </TabsContent>

          <TabsContent value="completed" className="space-y-4">
            {getFilteredTrips('completed').length > 0 ? (
              getFilteredTrips('completed').map(trip => (
                <TripCard key={trip.id} trip={trip} />
              ))
            ) : (
              <EmptyState message="No past trips yet. Completed trips will appear here." />
            )}
          </TabsContent>
        </Tabs>
      </div>

      <TripDetailsDialog
        trip={selectedTrip}
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onTripUpdated={async () => {
          await loadTrips();
          // Switch to booked tab if a trip was just booked
          if (selectedTrip?.status === 'planned') {
            setActiveTab('booked');
          }
        }}
      />
    </div>
  );
}

