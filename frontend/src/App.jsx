import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { RequireAuth } from "./components/ProtectedRoute";
import Login from "./pages/Login";
import ChangePassword from "./pages/ChangePassword";
import Dashboard from "./pages/Dashboard";
import PaperForm from "./pages/PaperForm";
import EditPaper from "./pages/EditPaper";
import PaperSearch from "./pages/Seacrh"

function RoleRedirect() {
  const { profile, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!profile) return <Navigate to="/login" replace />;
  return <Navigate to={"/dashboard"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><RoleRedirect /></RequireAuth>} />
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                  <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/search-paper"
            element={
              <RequireAuth>
                <PaperSearch />
              </RequireAuth>
            }
          />
          <Route
            path="/create-paper"
            element={
              <RequireAuth>
                <PaperForm />
              </RequireAuth>
            }
          />
          <Route
            path="/edit-paper/:id"
            element={
              <RequireAuth>
                <EditPaper />
              </RequireAuth>
            }
          />
          <Route
            path="/change-password"
            element={
              <RequireAuth>
                <ChangePassword />
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}