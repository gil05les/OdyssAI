import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { authService, Trip } from '@/services/authService';
import { TripPlanningWorkflow, WorkflowState } from '@/components/travel/TripPlanningWorkflow';
import { WorkflowStep } from '@/components/travel/WorkflowProgress';
import { TripRequest } from '@/services/api';
import { Destination } from '@/data/mockAgentData';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

const ResumePlanning = () => {
  const { tripId } = useParams<{ tripId: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get target step from URL query param (e.g., ?step=hotels)
  const targetStep = searchParams.get('step') as WorkflowStep | null;

  useEffect(() => {
    // Wait for auth to finish loading
    if (authLoading) return;

    // If not logged in, redirect to login
    if (!user) {
      navigate('/login', { replace: true });
      return;
    }

    // Load the trip data
    const loadTrip = async () => {
      if (!tripId) {
        setError('No trip ID provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch all trips and find the one we need
        const trips = await authService.getTrips(user.id);
        const foundTrip = trips.find(t => t.id === parseInt(tripId, 10));
        
        if (!foundTrip) {
          setError('Trip not found');
          setIsLoading(false);
          return;
        }

        // Allow both in_progress and planned trips to be resumed/edited
        if (foundTrip.status !== 'in_progress' && foundTrip.status !== 'planned') {
          setError('This trip cannot be edited. Only in-progress or planned trips can be resumed.');
          setIsLoading(false);
          return;
        }

        setTrip(foundTrip);
      } catch (err) {
        console.error('Failed to load trip:', err);
        setError(err instanceof Error ? err.message : 'Failed to load trip');
      } finally {
        setIsLoading(false);
      }
    };

    loadTrip();
  }, [tripId, user, authLoading, navigate]);

  const handleReset = () => {
    navigate('/');
  };

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-midnight flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-gold animate-spin mx-auto mb-4" />
          <p className="text-fog">Loading your trip...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-midnight flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-serif text-fog mb-2">Unable to Resume Trip</h2>
          <p className="text-fog/80 mb-6">{error}</p>
          <Button 
            onClick={() => navigate('/my-trips')}
            className="bg-gold hover:bg-gold/90 text-midnight"
          >
            Back to My Trips
          </Button>
        </div>
      </div>
    );
  }

  if (!trip || !trip.trip_data) {
    return (
      <div className="min-h-screen bg-midnight flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-serif text-fog mb-2">Trip Data Not Found</h2>
          <p className="text-fog/80 mb-6">The saved trip data could not be loaded.</p>
          <Button 
            onClick={() => navigate('/my-trips')}
            className="bg-gold hover:bg-gold/90 text-midnight"
          >
            Back to My Trips
          </Button>
        </div>
      </div>
    );
  }

  // Extract data from the saved trip
  const tripData = trip.trip_data;
  const tripRequest: TripRequest = tripData.tripRequest;
  const initialState: WorkflowState = tripData.tripState || {
    destination: null,
    flight: null,
    hotel: null,
    activities: [],
    transport: {},
  };
  // Use URL query param step if provided, otherwise use saved currentStep
  const initialStep: WorkflowStep = targetStep || tripData.currentStep || 'destinations';
  const availableDestinations: Destination[] = tripData.availableDestinations || [];

  return (
    <TripPlanningWorkflow
      tripRequest={tripRequest}
      onReset={handleReset}
      initialState={initialState}
      initialStep={initialStep}
      tripId={trip.id}
      availableDestinations={availableDestinations}
      originalTripStatus={trip.status as 'planned' | 'in_progress'}
    />
  );
};

export default ResumePlanning;

