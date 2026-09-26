import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const COMPANY_NAME = "Paper Maker"; 

export default function DashboardShell({ title, children }) {
  const { profile, logout } = useAuth();
  const currentName = profile?.display_name || profile?.email || "";

  return (
    <div className="page">
      <header className="header">
        <div className="header-left">
          <span className="brand">{COMPANY_NAME}</span>
        </div>
        <div className="header-right">
          <span className="who">{currentName}</span>

          <details className="settings-menu">
            <summary>Settings</summary>
            <div className="settings-dropdown">
              <Link to="/change-password">Change Password</Link>
            </div>
          </details>

          <button className="link logout-btn" onClick={logout}>
            Log Out
          </button>
        </div>
      </header>

      <main className="card wide">
        <h1>{title}</h1>
        {children}
      </main>
    </div>
  );
}