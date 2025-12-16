import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';
import { Mail, Lock, User, Loader2, Plane } from 'lucide-react';
import { Header } from '@/components/Header';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, fullName || undefined);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-midnight">
      <Header />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full bg-gold/20 flex items-center justify-center mx-auto mb-4">
              <Plane className="w-8 h-8 text-gold" />
            </div>
            <h1 className="text-3xl font-serif text-fog mb-2">Create Account</h1>
            <p className="text-fog/70">Join OdyssAI to start planning your perfect trip</p>
          </div>

          <div className="p-8 rounded-2xl glass-sand animate-fade-in">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Full Name (Optional)
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Doe"
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-fog/70 tracking-widest uppercase mb-2">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gold" />
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    className="pl-12 h-14 border-fog/10 bg-midnight-light/30 focus:border-gold/30 text-fog placeholder:text-muted-foreground"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gold hover:bg-gold/90 text-midnight h-14"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-fog/70">
                Already have an account?{' '}
                <Link to="/login" className="text-gold hover:text-gold-light font-medium">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


