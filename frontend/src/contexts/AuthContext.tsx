import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import type { User, TokenResponse } from "../types";

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

axios.defaults.baseURL = API_BASE_URL;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem("railvision_token"));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Sync token with axios headers and state on boot
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      setUser({ username: "admin" }); // Single demo user configuration
    } else {
      delete axios.defaults.headers.common["Authorization"];
      setUser(null);
    }
    setLoading(false);
  }, [token]);

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post<TokenResponse>("/login", {
        username,
        password,
      });
      
      const { access_token } = response.data;
      localStorage.setItem("railvision_token", access_token);
      setToken(access_token);
    } catch (error) {
      localStorage.removeItem("railvision_token");
      setToken(null);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("railvision_token");
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common["Authorization"];
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
