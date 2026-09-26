import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchDashboard, listPapers } from "../api";
import DashboardShell from "../components/DashboardShell";

export default function TeacherDashboard() {
  const [data, setData] = useState(null);
  const [papers, setPapers] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard().then(setData).catch((e) => setError(e.message));
    listPapers().then(setPapers).catch(() => {});
  }, []);

  return (
    <DashboardShell title="Teacher Dashboard">
      {error && <p className="error">{error}</p>}
      {data && (
        <>
          <h2>{data.message}</h2>
          <button type="button" onClick={() => navigate("/teacher/create-paper")}>
            + Create Paper
          </button>

          <h3 className="section-heading">My Papers</h3>
          {papers.length === 0 && <p className="muted">No papers yet.</p>}
          <ul className="paper-list">
            {papers.map((p) => (
              <li key={p.id} className="paper-list-item">
                <div>
                  <strong>{p.paper_name}</strong>
                  <span className={`status-badge status-${p.status}`}>{p.status}</span>
                </div>
                <button className="link" onClick={() => navigate(`/teacher/edit-paper/${p.id}`)}>
                  Edit
                </button>
              </li>
            ))}
          </ul>

        </>
      )}
    </DashboardShell>
  );
}