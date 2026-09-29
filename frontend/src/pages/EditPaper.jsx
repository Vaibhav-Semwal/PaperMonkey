import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchPaper, generateQuestions, updateQuestion, publishPaper } from "../api";
import { jsPDF } from "jspdf";
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

  const dirty = Object.values(paper?.questions_by_section ?? {})
    .flat()
    .filter((query) => Object.entries(drafts[query.question_id] ?? {}).some(([k, v]) => v !== query[k]
  ));

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

  async function handleSaveAll() {
    setError("");
    setBusy(true);
    const results = await Promise.allSettled(
      dirty.map((q) =>
        updateQuestion(id, q.question_id, {
          question_text: fieldValue(q, "question_text"),
          answer_text: fieldValue(q, "answer_text"),
        })
      )
    );
    const failed = results.filter((r) => r.status === "rejected").length;
    if (failed) setError(`${failed} question(s) failed to save. Your edits are kept, so try again.`);
    await load();
    setBusy(false);
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

  function handleExportPDF(isAnswerSheet = false) {
    const doc = new jsPDF();
    let y = 20;
    const write = (text, size = 11, bold = false) => {
      doc.setFont("helvetica", bold ? "bold" : "normal").setFontSize(size);
      doc.splitTextToSize(text, 180).forEach((line) => {
        if (y > 280) { doc.addPage(); y = 20; }
        doc.text(line, 15, y);
        y += size * 0.5;
      });
      y += 3;
    };

    write(paper.paper_name, 16, true);
    paper.sections.forEach(({ section, marks_per_question }) => {
      write(`Section ${section} (${marks_per_question} marks each)`, 13, true);
      (paper.questions_by_section[section] || []).forEach((q, i) => {
        write(`${i + 1}. ${fieldValue(q, "question_text")} [${q.marks} Marks]`); 
        if (isAnswerSheet) { write(`Answer: ${fieldValue(q, "answer_text")}`); }
      });
    });

    if (isAnswerSheet) { doc.save(`${paper.paper_name}_Answers.pdf`); }
    else { doc.save(`${paper.paper_name}.pdf`); }
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
              <fieldset key={letter} className="section-question-block">
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
                  </div>
                ))}
              </fieldset>
            );
          })}

          {paper.status === "ready" && (
            <div style={{display: "flex", justifyContent: "center", gap:"8px"}}>
              <button onClick={handleSaveAll} disabled={busy || !dirty.length}>
                {dirty.length ? `Save All Changes (${dirty.length})` : "All changes saved"}
              </button>
              <button onClick={handlePublish} disabled={busy || dirty.length > 0}>
                Publish Paper
              </button>
              <button onClick={() => handleExportPDF(false)} disabled={busy}>
                Export
              </button>
              <button onClick={() => handleExportPDF(true)} disabled={busy}>
                Export with Answers
              </button>
            </div>
          )}
        </>
      )}

      <p className="switch">
        <button className="link" onClick={() => navigate("/dashboard")}>
          Back to dashboard
        </button>
      </p>
    </DashboardShell>
  );
}