import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import { auth } from "../firebase";
import { registerProfile,  fetchMe } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const { setProfile } = useAuth();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "signup") {
        await createUserWithEmailAndPassword(auth, email, password);
        const profile = await registerProfile(role, displayName);
        setProfile(profile);
        navigate("/dashboard");
      } else {
        await signInWithEmailAndPassword(auth, email, password);
        const profile = await fetchMe();
        setProfile(profile);
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h1>{mode === "login" ? "Log In" : "Sign Up"}</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input type="email" value={email} required onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            required
            minLength={6}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {mode === "signup" && (
          <>
            <label>
              Display Name
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
            </label>
            <label>
              I am a...
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>
            </label>
          </>
        )}

        {error && <p className="error">{error}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Please wait..." : mode === "login" ? "Log In" : "Sign Up"}
        </button>
      </form>

      <p className="switch">
        {mode === "login" ? (
          <>
            Need an account?{" "}
            <button className="link" onClick={() => setMode("signup")}>
              Sign up
            </button>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <button className="link" onClick={() => setMode("login")}>
              Log in
            </button>
          </>
        )}
      </p>
    </div>
  );
}
