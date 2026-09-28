import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function RequireAuth({ children }) {
  const { firebaseUser, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!firebaseUser) return <Navigate to="/login" replace />;
  return children;
}
