import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Inspection from "./pages/Inspection";
import History from "./pages/History";
import Reports from "./pages/Reports";
import ModelInfo from "./pages/ModelInfo";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

/**
 * Main Layout Shell structure enclosing navbar, sidebar, and page viewports.
 */
const MainLayout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      {/* Top Console Header */}
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar />

        {/* Dynamic Page viewports */}
        <main className="flex-1 overflow-hidden flex flex-col relative bg-background">
          {/* Grid lines background overlay for a military/AI dashboard vibe */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293711_1px,transparent_1px),linear-gradient(to_bottom,#1f293711_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none z-0"></div>
          
          <div className="relative z-10 flex-1 flex flex-col overflow-hidden">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public authentication gate */}
          <Route path="/login" element={<Login />} />

          {/* Secure Diagnostic Console Router */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/inspection" element={<Inspection />} />
              <Route path="/history" element={<History />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/model" element={<ModelInfo />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Route>

          {/* Fallback bounds */}
          <Route path="/404" element={<NotFound />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
