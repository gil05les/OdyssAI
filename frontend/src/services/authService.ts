const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface UserProfile {
  id: number;
  user_id: number;
  full_name: string | null;
  phone: string | null;
  street: string | null;
  city: string | null;
  zip: string | null;
  country: string | null;
  visa_status: string | null;
  payment_methods: any[];
  updated_at: string;
}

export interface Trip {
  id: number;
  user_id: number;
  status: 'planned' | 'booked' | 'completed' | 'in_progress';
  booking_reference: string | null;
  trip_data: any;
  created_at: string;
  updated_at: string;
}

class AuthService {
  private getUserId(): number | null {
    const userId = localStorage.getItem('user_id');
    return userId ? parseInt(userId, 10) : null;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    const userId = this.getUserId();
    if (userId) {
      headers['X-User-ID'] = userId.toString();
    }
    
    return headers;
  }

  async register(email: string, password: string, fullName?: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  async login(email: string, password: string): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    return response.json();
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Not authenticated');
    }

    return response.json();
  }

  logout(): void {
    // Clear local storage
    localStorage.removeItem('user_id');
  }

  // Profile methods
  async getProfile(userId: number): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/profile`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch profile');
    }

    return response.json();
  }

  async updateProfile(userId: number, profileData: Partial<UserProfile>): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/profile`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update profile');
    }

    return response.json();
  }

  async getPaymentMethods(userId: number): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/payment-methods`, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch payment methods');
    }

    const data = await response.json();
    return data.payment_methods || [];
  }

  async addPaymentMethod(userId: number, paymentMethod: any): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/payment-methods`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(paymentMethod),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add payment method');
    }

    const data = await response.json();
    return data.payment_methods || [];
  }

  // Trip methods
  async getTrips(userId: number, status?: string): Promise<Trip[]> {
    const url = new URL(`${API_BASE_URL}/api/users/${userId}/trips`);
    if (status) {
      url.searchParams.append('status', status);
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch trips');
    }

    return response.json();
  }

  async createTrip(userId: number, tripData: {
    status: 'planned' | 'booked' | 'completed' | 'in_progress';
    booking_reference?: string;
    trip_data: any;
  }): Promise<Trip> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/trips`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create trip');
    }

    return response.json();
  }

  async updateTrip(userId: number, tripId: number, tripData: Partial<Trip>): Promise<Trip> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/trips/${tripId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update trip');
    }

    return response.json();
  }

  async deleteTrip(userId: number, tripId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}/trips/${tripId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete trip');
    }
  }
}

export const authService = new AuthService();

