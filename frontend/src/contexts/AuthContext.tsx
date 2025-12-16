import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authService, UserProfile } from '@/services/authService';

interface User {
  id: number;
  email: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user profile
  const loadProfile = async (userId: number) => {
    try {
      const profileData = await authService.getProfile(userId);
      setProfile(profileData);
    } catch (error) {
      // Profile might not exist yet, that's okay
      setProfile(null);
    }
  };

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const storedUserId = localStorage.getItem('user_id');
        if (storedUserId) {
          const userData = await authService.getCurrentUser();
          setUser(userData);
          await loadProfile(userData.id);
        }
      } catch (error) {
        // User not authenticated
        localStorage.removeItem('user_id');
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    const userData = await authService.login(email, password);
    setUser(userData);
    localStorage.setItem('user_id', userData.id.toString());
    await loadProfile(userData.id);
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const userData = await authService.register(email, password, fullName);
    setUser(userData);
    localStorage.setItem('user_id', userData.id.toString());
    await loadProfile(userData.id);
  };

  const logout = () => {
    setUser(null);
    setProfile(null);
    localStorage.removeItem('user_id');
    authService.logout();
  };

  const refreshProfile = async () => {
    if (user) {
      await loadProfile(user.id);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

