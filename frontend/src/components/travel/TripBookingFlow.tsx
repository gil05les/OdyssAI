import { useState } from 'react';
import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog';
import { CheckoutAgent } from './agents/CheckoutAgent';
import { BookingConfirmation } from './agents/BookingConfirmation';
import { Trip } from '@/services/authService';
import { TripRequest } from '@/services/api';
import { Destination, Flight, Hotel, Activity, TransportOption } from '@/data/mockAgentData';
import { authService } from '@/services/authService';
import { useAuth } from '@/contexts/AuthContext';

interface TripBookingFlowProps {
  trip: Trip;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const TripBookingFlow = ({ trip, open, onOpenChange }: TripBookingFlowProps) => {
  const { user } = useAuth();
  const [step, setStep] = useState<'checkout' | 'confirmation'>('checkout');
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
    tripState: {
      destination: Destination | null;
      flight: Flight | null;
      hotel: Hotel | null;
      activities: Activity[];
      transport: Record<string, TransportOption | null>;
    };
    bookingReference: string;
  } | null>(null);

  const tripData = trip.trip_data;
  const tripState = tripData?.tripState || tripData;
  const tripRequest = tripData?.tripRequest as TripRequest;

  // Ensure tripState has the correct structure
  const normalizedTripState = {
    destination: tripState?.destination || null,
    flight: tripState?.flight || null,
    hotel: tripState?.hotel || null,
    activities: Array.isArray(tripState?.activities) ? tripState.activities : [],
    transport: tripState?.transport && typeof tripState.transport === 'object' 
      ? tripState.transport 
      : {},
  };

  const handleBook = async (data: {
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
    if (!user) return;

    try {
      // Update the existing trip to booked status
      await authService.updateTrip(user.id, trip.id, {
        status: 'booked',
        booking_reference: data.bookingReference,
        trip_data: {
          ...tripData,
          tripState: data.tripState,
          tripRequest: tripRequest,
          formData: data.formData,
        },
      });

      setBookingData(data);
      setStep('confirmation');
    } catch (error) {
      console.error('Failed to update trip:', error);
      alert('Failed to complete booking. Please try again.');
    }
  };

  const handleBack = () => {
    if (step === 'confirmation') {
      setStep('checkout');
    } else {
      onOpenChange(false);
    }
  };

  const handleConfirmationClose = () => {
    onOpenChange(false);
    setStep('checkout');
    setBookingData(null);
  };

  if (!normalizedTripState || !tripRequest) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl max-h-[95vh] overflow-y-auto glass-sand border-fog/20 bg-midnight/95 [&>button]:text-fog [&>button]:hover:text-gold [&>button]:hover:bg-gold/10 p-0">
        {step === 'checkout' && (
          <div className="p-6">
            <CheckoutAgent
              tripState={normalizedTripState}
              tripRequest={tripRequest}
              onBook={handleBook}
              onBack={handleBack}
            />
          </div>
        )}

        {step === 'confirmation' && bookingData && (
          <div className="p-6">
            <BookingConfirmation
              bookingData={bookingData}
              tripRequest={tripRequest}
              onBack={handleConfirmationClose}
              skipAutoSave={true}
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

