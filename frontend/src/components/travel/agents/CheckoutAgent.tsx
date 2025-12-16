import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { ArrowLeft, CreditCard, User, Mail, Phone, MapPin, Loader2, Save } from 'lucide-react';
import { Destination, Flight, Hotel, Activity, TransportOption } from '@/data/mockAgentData';
import { TripRequest } from '@/services/api';
import { cn } from '@/lib/utils';
import { generateBookingReference } from '@/utils/pdfGenerator';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

interface CheckoutAgentProps {
  tripState: {
    destination: Destination | null;
    flight: Flight | null;
    hotel: Hotel | null;
    activities: Activity[];
    transport: Record<string, TransportOption | null>;
  };
  tripRequest: TripRequest;
  onBook: (bookingData: {
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
  }) => void;
  onBack: () => void;
}

export const CheckoutAgent = ({ tripState, tripRequest, onBook, onBack }: CheckoutAgentProps) => {
  const { user, profile } = useAuth();
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    street: '',
    city: '',
    zip: '',
    country: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isBooking, setIsBooking] = useState(false);
  const [useSavedInfo, setUseSavedInfo] = useState(false);
  const [saveToProfile, setSaveToProfile] = useState(true);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [savedPaymentMethods, setSavedPaymentMethods] = useState<any[]>([]);

  // Load profile data and payment methods on mount
  useEffect(() => {
    const loadProfileData = async () => {
      if (user && profile) {
        setIsLoadingProfile(true);
        try {
          // Load payment methods
          const paymentMethods = await authService.getPaymentMethods(user.id);
          setSavedPaymentMethods(paymentMethods);
        } catch (error) {
          console.error('Failed to load payment methods:', error);
        } finally {
          setIsLoadingProfile(false);
        }
      }
    };

    loadProfileData();
  }, [user, profile]);

  // Populate form when "use saved info" is toggled
  useEffect(() => {
    if (useSavedInfo && profile && user) {
      setFormData({
        fullName: profile.full_name || '',
        email: user.email || '',
        phone: profile.phone || '',
        street: profile.street || '',
        city: profile.city || '',
        zip: profile.zip || '',
        country: profile.country || '',
      });
    }
  }, [useSavedInfo, profile, user]);

  const calculateTotal = () => {
    let total = 0;
    if (tripState.flight) total += tripState.flight.price;
    if (tripState.hotel) total += tripState.hotel.pricePerNight * 3; // Assuming 3 nights
    total += tripState.activities.reduce((sum, a) => sum + a.price, 0);
    Object.values(tripState.transport).forEach(opt => {
      if (opt) total += opt.price;
    });
    return total;
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsBooking(true);
    
    try {
      // Save to profile if user is logged in and option is enabled
      if (saveToProfile && user) {
        try {
          await authService.updateProfile(user.id, {
            full_name: formData.fullName,
            phone: formData.phone,
            street: formData.street,
            city: formData.city,
            zip: formData.zip,
            country: formData.country,
          });
        } catch (error) {
          console.error('Failed to save to profile:', error);
          // Continue with booking even if profile save fails
        }
      }

      // Simulate booking process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate booking reference and pass booking data to confirmation
      const bookingReference = generateBookingReference();
      onBook({
        formData,
        tripState,
        bookingReference,
      });
    } finally {
      setIsBooking(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };


  return (
    <div className="animate-fade-in max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-serif text-fog mb-2">Complete Your Booking</h2>
        <p className="text-fog/90">Enter your details to finalize your trip</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Booking Form - Left Column (2/3 on desktop) */}
        <div className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Profile Options - Only show if user is logged in */}
            {user && profile && (
              <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '50ms', animationFillMode: 'forwards' }}>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 p-4 rounded-xl border border-gold/20 bg-gold/5">
                    <Checkbox
                      id="useSavedInfo"
                      checked={useSavedInfo}
                      onCheckedChange={(checked) => setUseSavedInfo(checked === true)}
                      className="border-gold/50 data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                    />
                    <label
                      htmlFor="useSavedInfo"
                      className="flex-1 text-sm text-fog cursor-pointer"
                    >
                      <span className="font-medium text-fog">Use saved information from profile</span>
                      <span className="block text-xs text-fog/60 mt-1">
                        Automatically fill in your personal information and billing address
                      </span>
                    </label>
                  </div>
                  
                  <div className="flex items-center space-x-3 p-4 rounded-xl border border-fog/10 bg-midnight-light/20">
                    <Checkbox
                      id="saveToProfile"
                      checked={saveToProfile}
                      onCheckedChange={(checked) => setSaveToProfile(checked === true)}
                      className="border-gold/50 data-[state=checked]:bg-gold data-[state=checked]:border-gold"
                    />
                    <label
                      htmlFor="saveToProfile"
                      className="flex-1 text-sm text-fog cursor-pointer"
                    >
                      <span className="font-medium text-fog">Save information to profile</span>
                      <span className="block text-xs text-fog/60 mt-1">
                        Save this information for future bookings
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Personal Information */}
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '100ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <User className="w-5 h-5 text-gold" />
                Personal Information
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                    Full Name *
                  </label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                    <Input
                      type="text"
                      value={formData.fullName}
                      onChange={(e) => handleChange('fullName', e.target.value)}
                      placeholder="John Doe"
                      className={cn(
                        "pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground",
                        errors.fullName && "border-red-500/50"
                      )}
                      required
                    />
                  </div>
                  {errors.fullName && (
                    <p className="text-xs text-red-400 mt-1">{errors.fullName}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                    Email Address *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      placeholder="john.doe@example.com"
                      className={cn(
                        "pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground",
                        errors.email && "border-red-500/50"
                      )}
                      required
                    />
                  </div>
                  {errors.email && (
                    <p className="text-xs text-red-400 mt-1">{errors.email}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                    <Input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleChange('phone', e.target.value)}
                      placeholder="+1 (555) 123-4567"
                      className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Information */}
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '200ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-gold" />
                Payment Information
              </h3>
              
              {savedPaymentMethods.length > 0 ? (
                <div className="space-y-3">
                  {savedPaymentMethods.map((method, index) => (
                    <div
                      key={index}
                      className="p-4 rounded-xl border-2 border-gold/30 bg-gold/5 hover:bg-gold/10 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-lg bg-gold/20 flex items-center justify-center">
                          <CreditCard className="w-6 h-6 text-gold" />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-fog/60 uppercase tracking-wider mb-1">Saved Payment Method</p>
                          <p className="text-fog font-medium">
                            {method.card_type || 'Card'} ending in •••• {method.last_four || '1234'}
                          </p>
                          <p className="text-xs text-fog/60 mt-1">
                            Expires {method.expiry_month || 'MM'}/{method.expiry_year || 'YY'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl border-2 border-gold/30 bg-gold/5">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-gold/20 flex items-center justify-center">
                      <CreditCard className="w-6 h-6 text-gold" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-fog/60 uppercase tracking-wider mb-1">Payment Method</p>
                      <p className="text-fog font-medium">Card ending in •••• 1234</p>
                      <p className="text-xs text-fog/60 mt-1">Payment processing is stubbed for demo purposes</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Billing Address */}
            <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '300ms', animationFillMode: 'forwards' }}>
              <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-gold" />
                Billing Address (Optional)
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                    Street Address
                  </label>
                  <Input
                    type="text"
                    value={formData.street}
                    onChange={(e) => handleChange('street', e.target.value)}
                    placeholder="123 Main Street"
                    className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                      City
                    </label>
                    <Input
                      type="text"
                      value={formData.city}
                      onChange={(e) => handleChange('city', e.target.value)}
                      placeholder="New York"
                      className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                      ZIP Code
                    </label>
                    <Input
                      type="text"
                      value={formData.zip}
                      onChange={(e) => handleChange('zip', e.target.value)}
                      placeholder="10001"
                      className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                    Country
                  </label>
                  <Input
                    type="text"
                    value={formData.country}
                    onChange={(e) => handleChange('country', e.target.value)}
                    placeholder="United States"
                    className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                  />
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-between items-center pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={onBack}
                className="text-fog/80 hover:text-fog"
              >
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
              <div className="flex items-center gap-4">
                {saveToProfile && user && (
                  <div className="flex items-center gap-2 text-xs text-fog/60">
                    <Save className="w-4 h-4 text-gold" />
                    <span>Will save to profile</span>
                  </div>
                )}
                <Button
                  type="submit"
                  disabled={isBooking}
                  className="bg-gold hover:bg-gold/90 text-midnight px-8"
                >
                  {isBooking ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-4 h-4 mr-2" /> Book Trip
                    </>
                  )}
                </Button>
              </div>
            </div>
          </form>
        </div>

        {/* Trip Summary - Right Column (1/3 on desktop) */}
        <div className="lg:col-span-1">
          <div className="p-6 rounded-2xl glass-sand sticky top-8 animate-slide-up" style={{ animationDelay: '400ms', animationFillMode: 'forwards' }}>
            <h3 className="text-lg font-serif text-fog mb-6">Trip Summary</h3>
            
            <div className="space-y-4">
              {/* Destination */}
              {tripState.destination && (
                <div className="pb-4 border-b border-fog/10">
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Destination</p>
                  <p className="text-sm text-fog font-medium">{tripState.destination.name}</p>
                </div>
              )}

              {/* Flight */}
              {tripState.flight && (
                <div className="pb-4 border-b border-fog/10">
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Flight</p>
                  <p className="text-sm text-fog font-medium">{tripState.flight.airline}</p>
                  <p className="text-xs text-fog/60 mt-1">{tripState.flight.departureTime} → {tripState.flight.arrivalTime}</p>
                  <p className="text-sm text-gold font-semibold mt-2">CHF {tripState.flight.price}</p>
                </div>
              )}

              {/* Hotel */}
              {tripState.hotel && (
                <div className="pb-4 border-b border-fog/10">
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Hotel</p>
                  <p className="text-sm text-fog font-medium">{tripState.hotel.name}</p>
                  <p className="text-xs text-fog/60 mt-1">{tripState.hotel.stars} stars • 3 nights</p>
                  <p className="text-sm text-gold font-semibold mt-2">CHF {tripState.hotel.pricePerNight * 3}</p>
                </div>
              )}

              {/* Activities */}
              {tripState.activities.length > 0 && (
                <div className="pb-4 border-b border-fog/10">
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Activities</p>
                  <p className="text-sm text-fog font-medium">{tripState.activities.length} experiences</p>
                  <p className="text-sm text-gold font-semibold mt-2">
                    CHF {tripState.activities.reduce((sum, a) => sum + a.price, 0)}
                  </p>
                </div>
              )}

              {/* Transport */}
              {Object.values(tripState.transport).filter(Boolean).length > 0 && (
                <div className="pb-4 border-b border-fog/10">
                  <p className="text-xs text-teal-light uppercase tracking-wider mb-1">Transport</p>
                  <p className="text-sm text-fog font-medium">
                    {Object.values(tripState.transport).filter(Boolean).length} transfers
                  </p>
                  <p className="text-sm text-gold font-semibold mt-2">
                    CHF {Object.values(tripState.transport).reduce((sum, opt) => sum + (opt?.price || 0), 0)}
                  </p>
                </div>
              )}

              {/* Total */}
              <div className="pt-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-base font-serif text-fog">Total</p>
                  <p className="text-2xl font-bold text-gold">CHF {calculateTotal()}</p>
                </div>
                <p className="text-xs text-fog/60">All prices in CHF</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

