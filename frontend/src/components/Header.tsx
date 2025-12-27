import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { User, LogOut, Plane, Calendar } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export const Header = () => {
  const { user, profile, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getInitials = (name: string | null | undefined, email: string) => {
    if (name) {
      const parts = name.trim().split(' ');
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return name.substring(0, 2).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  };

  const getDisplayName = () => {
    if (profile?.full_name) {
      return profile.full_name;
    }
    return user?.email || '';
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full border-b border-fog/10 bg-midnight-light/95 backdrop-blur-md">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gold/20">
              <Plane className="w-6 h-6 text-gold" />
            </div>
            <span className="text-xl font-serif font-bold text-fog">OdyssAI</span>
          </Link>

          {/* User Menu / Auth Buttons */}
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 hover:bg-gold/10"
                  >
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-gold/20 text-gold">
                        {getInitials(profile?.full_name, user?.email || '')}
                      </AvatarFallback>
                    </Avatar>
                    <span className="hidden sm:inline text-fog">{getDisplayName()}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 glass-sand border-fog/10">
                  {isAuthenticated && (
                    <DropdownMenuItem
                      onClick={() => navigate('/my-trips')}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <Calendar className="w-4 h-4" />
                      My Trips
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={() => navigate('/profile')}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="flex items-center gap-2 cursor-pointer text-red-400"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  onClick={() => navigate('/login')}
                  className="text-fog/80 hover:text-gold"
                >
                  Login
                </Button>
                <Button
                  onClick={() => navigate('/register')}
                  className="bg-gold hover:bg-gold/90 text-midnight"
                >
                  Sign Up
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

