import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchPaper, generateQuestions, updateQuestion, publishPaper } from "../api";
import DashboardShell from "../components/DashboardShell";

const POLL_INTERVAL_MS = 3000;

export default function EditPaper() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [drafts, setDrafts] = useState({}); // { [question_id]: { question_text, answer_text } }
  const pollRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchPaper(id);
      setPaper(data);
      return data;
    } catch (e) {
      setError(e.message);
      return null;
    }
  }, [id]);

  useEffect(() => {
    load();
    return () => clearInterval(pollRef.current);
  }, [load]);

  useEffect(() => {
    if (paper?.status === "generating") {
      pollRef.current = setInterval(async () => {
        const updated = await load();
        if (updated && updated.status !== "generating") {
          clearInterval(pollRef.current);
        }
      }, POLL_INTERVAL_MS);
    }
    return () => clearInterval(pollRef.current);
  }, [paper?.status, load]);

  async function handleGenerate() {
    setError("");
    setBusy(true);
    try {
      await generateQuestions(id);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function fieldValue(q, field) {
    return drafts[q.question_id]?.[field] ?? q[field];
  }

  function updateDraft(questionId, field, value) {
    setDrafts((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], [field]: value },
    }));
  }

  async function handleSaveQuestion(q) {
    const payload = {
      question_text: fieldValue(q, "question_text"),
      answer_text: fieldValue(q, "answer_text"),
    };
    try {
      await updateQuestion(id, q.question_id, payload);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handlePublish() {
    setBusy(true);
    try {
      await publishPaper(id);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!paper) {
    return (
      <DashboardShell title="Edit Paper">
        {error ? <p className="error">{error}</p> : <p className="center">Loading...</p>}
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={`Edit Paper: ${paper.paper_name}`}>
      {error && <p className="error">{error}</p>}

      <p>
        Status: <span className={`status-badge status-${paper.status}`}>{paper.status}</span>
      </p>

      {paper.status === "draft" && (
        <button type="button" onClick={handleGenerate} disabled={busy}>
          {busy ? "Starting..." : "Generate Questions"}
        </button>
      )}

      {paper.status === "generating" && (
        <p className="muted">Generating questions from your links... this can take a minute.</p>
      )}

      {paper.status === "failed" && (
        <>
          <p className="error">Generation failed: {paper.error_message}</p>
          <button type="button" onClick={handleGenerate} disabled={busy}>
            Retry
          </button>
        </>
      )}

      {(paper.status === "ready" || paper.status === "published") && (
        <>
          {paper.sections.map((sectionDef) => {
            const letter = sectionDef.section;
            const questions = paper.questions_by_section[letter] || [];
            return (
              <fieldset key={letter} className="section-block">
                <legend>
                  Section {letter} ({sectionDef.num_questions} questions,{" "}
                  {sectionDef.marks_per_question} marks each)
                </legend>
                {questions.length === 0 && <p className="muted">No questions generated.</p>}
                {questions.map((q) => (
                  <div key={q.question_id} className="question-edit-row">
                    <label>
                      Question
                      <textarea
                        rows={2}
                        value={fieldValue(q, "question_text")}
                        onChange={(e) => updateDraft(q.question_id, "question_text", e.target.value)}
                        disabled={paper.status === "published"}
                      />
                    </label>
                    <label>
                      Answer
                      <textarea
                        rows={2}
                        value={fieldValue(q, "answer_text")}
                        onChange={(e) => updateDraft(q.question_id, "answer_text", e.target.value)}
                        disabled={paper.status === "published"}
                      />
                    </label>
                    <span className="muted">Marks: {q.marks}</span>
                    {paper.status === "ready" && (
                      <button type="button" className="link" onClick={() => handleSaveQuestion(q)}>
                        Save
                      </button>
                    )}
                  </div>
                ))}
              </fieldset>
            );
          })}

          {paper.status === "ready" && (
            <button type="button" onClick={handlePublish} disabled={busy}>
              {busy ? "Publishing..." : "Publish Paper"}
            </button>
          )}
        </>
      )}

      <p className="switch">
        <button className="link" onClick={() => navigate("/teacher")}>
          Back to dashboard
        </button>
      </p>
    </DashboardShell>
  );
}