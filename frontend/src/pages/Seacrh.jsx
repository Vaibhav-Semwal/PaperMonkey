import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { searchOtherPapers } from "../api";
import DashboardShell from "../components/DashboardShell";

export default function PaperSearch() {
  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const runSearch = useCallback((q) => {
    setLoading(true);
    setError("");
    searchOtherPapers(q).then(setPapers).catch(() => setError("Failed to load papers.")).finally(() => setLoading(false));
  }, []);

  useEffect(() => runSearch(""), [runSearch]);

  return (
    <DashboardShell title="Teacher Dashboard">
        <div className="search-box">
            <button onClick={() => navigate("/dashboard")}>← Back</button>
            <input type="text" value={query} placeholder="Search papers..." className="search-bar"
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runSearch(query)}
            />
            <button onClick={() => runSearch(query)} disabled={loading}>
                {loading ? "Searching..." : "Search"}
            </button>
        </div>

        {error && <p className="error">{error}</p>}
        {!loading && !error && papers.length === 0 && <p>No results found.</p>}

        {papers.map((p) => (
            <li key={p.id} className="paper-list-item">
                <div>
                    <strong>{p.paper_name}</strong>
                    <span className={`status-badge status-${p.status}`}>{p.status}</span>
                    <div>Created: {new Date(p.created_at).toLocaleString()}</div>
                </div>
                <strong>{p.teacher_display_name}</strong>
                <button onClick={() => navigate(`/edit-paper/${p.id}`)}>
                    Edit
                </button>
            </li>
        ))}

    </DashboardShell>
  );
}