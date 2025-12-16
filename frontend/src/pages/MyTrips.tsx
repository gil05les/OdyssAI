import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import { authService, Trip } from '@/services/authService';
import { Plane, Building2, Calendar, Car, MapPin, Loader2, Trash2 } from 'lucide-react';
import { Header } from '@/components/Header';
import { cn } from '@/lib/utils';
import { TripDetailsDialog } from '@/components/travel/TripDetailsDialog';

export default function MyTrips() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'booked' | 'planned' | 'completed'>('booked');
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

    const handleCardClick = (e: React.MouseEvent) => {
      // Don't open dialog if clicking on delete button
      if ((e.target as HTMLElement).closest('button')) {
        return;
      }
      setSelectedTrip(trip);
      setIsDialogOpen(true);
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
          <span className="text-xl font-bold text-gold">CHF {total.toFixed(2)}</span>
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
        <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
          <Loader2 className="w-8 h-8 text-gold animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-midnight">
      <Header />
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-fog mb-2">My Trips</h1>
          <p className="text-fog/70">Manage and view all your travel plans</p>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-3 glass-sand mb-8">
            <TabsTrigger value="booked" className="data-[state=active]:bg-gold data-[state=active]:text-midnight">
              Booked
            </TabsTrigger>
            <TabsTrigger value="planned" className="data-[state=active]:bg-gold data-[state=active]:text-midnight">
              Planned
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

