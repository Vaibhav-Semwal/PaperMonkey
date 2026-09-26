import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function RequireAuth({ children }) {
  const { firebaseUser, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!firebaseUser) return <Navigate to="/login" replace />;
  return children;
}

export function RequireRole({ role, children }) {
  const { profile, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!profile) return <Navigate to="/login" replace />;
  if (profile.role !== role) {
    return <Navigate to={profile.role === "teacher" ? "/teacher" : "/student"} replace />;
  }
  return children;
}
