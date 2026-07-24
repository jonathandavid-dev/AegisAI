import React, { createContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';
import { Account, LoginRequest } from '../types/auth';

interface AuthContextType {
  user: Account | null;
  loading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (username: string, email: string, password: string, full_name?: string, role?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Account | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const token = localStorage.getItem('aegis_token');
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const response = await api.get<Account>('/auth/me');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('aegis_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', credentials);
      localStorage.setItem('aegis_token', response.data.access_token);
      await refreshUser();
    } catch (error) {
      setLoading(false);
      throw error;
    }
  };

  const register = async (username: string, email: string, password: string, full_name?: string, role?: string) => {
    setLoading(true);
    try {
      await api.post('/auth/register', { 
        username, 
        email, 
        password,
        full_name,
        role: role || "VIEWER"
      });
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.warn("Logout endpoint call failed", err);
    } finally {
      localStorage.removeItem('aegis_token');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};
