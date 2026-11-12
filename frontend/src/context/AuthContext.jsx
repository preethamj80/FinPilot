import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setCsrfToken } from '../api/client';
import { DEMO_MODE } from '../demo/demoMode';

const AuthContext = createContext(null);
const DEMO_PROTECTED_PATHS = new Set([
  '/',
  '/transactions',
  '/budgets',
  '/budget-optimizer',
  '/coach',
  '/simulator',
  '/insights',
  '/settings',
]);

function createDemoUser() {
  return { full_name: 'Alex Morgan', username: 'Demo account', email: 'Not collected', is_demo: true };
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Check existing session on mount
  const checkSession = useCallback(async () => {
    if (DEMO_MODE) {
      const demoUser = DEMO_PROTECTED_PATHS.has(window.location.pathname) ? createDemoUser() : null;
      setUser(demoUser);
      setLoading(false);
      return demoUser;
    }
    try {
      const userData = await api.get('/api/auth/me');
      setUser(userData);
      // Fetch CSRF token for this active session
      try {
        const csrfData = await api.get('/api/auth/csrf-token');
        if (csrfData && csrfData.csrf_token) {
          setCsrfToken(csrfData.csrf_token);
        }
      } catch {
        // CSRF fetch fallback
      }
    } catch {
      setUser(null);
      setCsrfToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (DEMO_MODE) {
      checkSession();
      return undefined;
    }
    checkSession();

    const handleUnauthorized = () => {
      setUser(null);
      setCsrfToken(null);
    };

    window.addEventListener('finpilot:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('finpilot:unauthorized', handleUnauthorized);
  }, [checkSession]);

  const login = async (email, password) => {
    if (DEMO_MODE) {
      return enterDemo();
    }
    setAuthError(null);
    try {
      const data = await api.post('/api/auth/login', { email, password });
      setUser(data.user);
      if (data.csrf_token) {
        setCsrfToken(data.csrf_token);
      }
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Login failed');
      throw err;
    }
  };

  const register = async (fullName, email, password, confirmPassword) => {
    if (DEMO_MODE) {
      throw new Error('Real account registration is disabled in Demo Mode.');
    }
    setAuthError(null);
    try {
      const data = await api.post('/api/auth/register', {
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword,
      });
      setUser(data.user);
      if (data.csrf_token) {
        setCsrfToken(data.csrf_token);
      }
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Registration failed');
      throw err;
    }
  };

  const logout = async () => {
    try {
      if (!DEMO_MODE) await api.post('/api/auth/logout');
    } catch {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setCsrfToken(null);
    }
  };

  const enterDemo = () => {
    const demoUser = createDemoUser();
    setUser(demoUser);
    setAuthError(null);
    return demoUser;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        authError,
        isAuthenticated: !!user,
        login,
        register,
        enterDemo,
        logout,
        checkSession,
        demoMode: DEMO_MODE,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
