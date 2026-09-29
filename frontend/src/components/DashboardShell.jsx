import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const COMPANY_NAME = "Paper Maker"; 

export default function DashboardShell({ title, children }) {
  const { profile, logout } = useAuth();
  const currentName = profile?.display_name || profile?.email || "";
  const [dark, setDark] = useState(() =>
    (localStorage.theme ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark"
  );

  useEffect(() => {
    const t = dark ? "dark" : "light";
    document.documentElement.dataset.theme = t;
    localStorage.theme = t;
  }, [dark]);


  return (
    <div className="page">
      <header className="header">
        <div className="header-left">
          <span className="brand">{COMPANY_NAME}</span>
        </div>
        <div className="header-right">
          <span className="who">{currentName}</span>

          <details className="settings-menu">
            <summary>Menu</summary>
            <div className="settings-dropdown">
              <div className="theme-toggle">
                Dark Mode
                <button className="theme-switch" role="switch" aria-checked={dark} aria-label="Toggle dark mode"
                  onClick={() => setDark(d => !d)} />
              </div>
              <Link to="/change-password">Change Password</Link>
              <button onClick={logout}>
                Log Out
              </button>
            </div>
          </details>
        </div>
      </header>

      <main className="card wide">
        <h1>{title}</h1>
        {children}
      </main>
    </div>
  );
}