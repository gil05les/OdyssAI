import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import { authService, UserProfile } from '@/services/authService';
import { User, Mail, Phone, MapPin, CreditCard, Save, Loader2 } from 'lucide-react';
import { Header } from '@/components/Header';

export default function Profile() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    street: '',
    city: '',
    zip: '',
    country: '',
  });

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const loadProfile = async () => {
      try {
        const profileData = await authService.getProfile(user.id);
        setProfile(profileData);
        setFormData({
          full_name: profileData.full_name || '',
          phone: profileData.phone || '',
          street: profileData.street || '',
          city: profileData.city || '',
          zip: profileData.zip || '',
          country: profileData.country || '',
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      const updatedProfile = await authService.updateProfile(user.id, formData);
      setProfile(updatedProfile);
      setSuccess('Profile updated successfully!');
      // Refresh profile in AuthContext to update header
      await refreshProfile();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

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
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-serif text-fog mb-2">Profile Settings</h1>
          <p className="text-fog/70">Manage your personal information and preferences</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm">
              {success}
            </div>
          )}

          {/* Personal Information */}
          <div className="p-6 rounded-2xl glass-sand animate-slide-up">
            <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
              <User className="w-5 h-5 text-gold" />
              Personal Information
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => handleChange('full_name', e.target.value)}
                    placeholder="John Doe"
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/20 text-fog/60"
                  />
                </div>
                <p className="text-xs text-fog/60 mt-1">Email cannot be changed</p>
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
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '100ms' }}>
            <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-gold" />
              Address
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
                  className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
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
                    className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
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
                    className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
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
                  className="h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog"
                />
              </div>
            </div>
          </div>

          {/* Payment Methods */}
          <div className="p-6 rounded-2xl glass-sand animate-slide-up" style={{ animationDelay: '200ms' }}>
            <h3 className="text-lg font-serif text-fog mb-6 flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-gold" />
              Payment Methods
            </h3>
            <p className="text-sm text-fog/70">
              Payment methods are stored securely and used during checkout. Add your payment methods when booking a trip.
            </p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              type="submit"
              disabled={isSaving}
              className="bg-gold hover:bg-gold/90 text-midnight px-8 h-12"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" /> Save Changes
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

