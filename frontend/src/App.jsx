import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { RequireAuth, RequireRole } from "./components/ProtectedRoute";
import Login from "./pages/Login";
import ChangePassword from "./pages/ChangePassword";
import TeacherDashboard from "./pages/TeacherDashboard";
import StudentDashboard from "./pages/StudentDashboard";
import PaperForm from "./pages/PaperForm";
import EditPaper from "./pages/EditPaper";

function RoleRedirect() {
  const { profile, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!profile) return <Navigate to="/login" replace />;
  return <Navigate to={profile.role === "teacher" ? "/teacher" : "/student"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><RoleRedirect /></RequireAuth>} />
          <Route
            path="/teacher"
            element={
              <RequireAuth>
                <RequireRole role="teacher">
                  <TeacherDashboard />
                </RequireRole>
              </RequireAuth>
            }
          />
          <Route
            path="/teacher/create-paper"
            element={
              <RequireAuth>
                <RequireRole role="teacher">
                  <PaperForm />
                </RequireRole>
              </RequireAuth>
            }
          />
          <Route
            path="/teacher/edit-paper/:id"
            element={
              <RequireAuth>
                <RequireRole role="teacher">
                  <EditPaper />
                </RequireRole>
              </RequireAuth>
            }
          />
          <Route
            path="/student"
            element={
              <RequireAuth>
                <RequireRole role="student">
                  <StudentDashboard />
                </RequireRole>
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