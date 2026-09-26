import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPaperDraft } from "../api";
import DashboardShell from "../components/DashboardShell";

const SECTION_LETTERS = ["A", "B", "C", "D", "E"];

function makeEmptySection(letter) {
  return { section: letter, num_questions: 1, marks_per_question: 1 };
}

export default function PaperForm() {
  const navigate = useNavigate();

  const [paperName, setPaperName] = useState("");
  const [topics, setTopics] = useState([""]);
  const [externalLinks, setExternalLinks] = useState([""]);
  const [numSections, setNumSections] = useState(1);
  const [sections, setSections] = useState([makeEmptySection("A")]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  function updateListItem(list, setList, index, value) {
    const next = [...list];
    next[index] = value;
    setList(next);
  }

  function addListItem(list, setList) {
    setList([...list, ""]);
  }

  function removeListItem(list, setList, index) {
    setList(list.filter((_, i) => i !== index));
  }

  function handleNumSectionsChange(e) {
    const n = Number(e.target.value);
    setNumSections(n);
    setSections((prev) => {
      const next = [...prev];
      while (next.length < n) {
        next.push(makeEmptySection(SECTION_LETTERS[next.length]));
      }
      return next.slice(0, n);
    });
  }

  function updateSectionField(index, field, value) {
    const next = [...sections];
    next[index] = { ...next[index], [field]: value };
    setSections(next);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    const cleanTopics = topics.map((t) => t.trim()).filter(Boolean);
    const cleanLinks = externalLinks.map((l) => l.trim()).filter(Boolean);

    if (!paperName.trim()) {
      setError("Paper name is required.");
      return;
    }

    const payload = {
      paper_name: paperName.trim(),
      topics: cleanTopics,
      external_links: cleanLinks,
      sections: sections.map((s) => ({
        section: s.section,
        num_questions: Number(s.num_questions),
        marks_per_question: Number(s.marks_per_question),
      })),
    };

    setBusy(true);
    try {
      await createPaperDraft(payload);
      setSuccess("Paper saved as draft.");
      setTimeout(() => navigate("/teacher"), 900);
    } catch (err) {
      setError(err.message || "Could not save paper");
    } finally {
      setBusy(false);
    }
  }

  return (
    <DashboardShell title="Create Paper (Draft)">
      <form className="paper-form" onSubmit={handleSubmit}>
        <label>
          Paper Name
          <input value={paperName} onChange={(e) => setPaperName(e.target.value)} required />
        </label>

        <fieldset>
          <legend>Topics</legend>
          {topics.map((t, i) => (
            <div className="list-row" key={i}>
              <input
                value={t}
                placeholder={`Topic ${i + 1}`}
                onChange={(e) => updateListItem(topics, setTopics, i, e.target.value)}
              />
              {topics.length > 1 && (
                <button type="button" className="link" onClick={() => removeListItem(topics, setTopics, i)}>
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" className="link" onClick={() => addListItem(topics, setTopics)}>
            + Add topic
          </button>
        </fieldset>

        <fieldset>
          <legend>External Links</legend>
          {externalLinks.map((l, i) => (
            <div className="list-row" key={i}>
              <input
                value={l}
                placeholder="https://..."
                type="url"
                onChange={(e) => updateListItem(externalLinks, setExternalLinks, i, e.target.value)}
              />
              {externalLinks.length > 1 && (
                <button
                  type="button"
                  className="link"
                  onClick={() => removeListItem(externalLinks, setExternalLinks, i)}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" className="link" onClick={() => addListItem(externalLinks, setExternalLinks)}>
            + Add link
          </button>
        </fieldset>

        <label>
          Number of Sections
          <select value={numSections} onChange={handleNumSectionsChange}>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <fieldset>
          <legend>Sections</legend>
          {sections.map((s, i) => (
            <div className="section-block" key={s.section}>
              <h3>Section {s.section}</h3>
              <label>
                Number of Questions (1-25)
                <input
                  type="number"
                  min={1}
                  max={25}
                  value={s.num_questions}
                  onChange={(e) => updateSectionField(i, "num_questions", e.target.value)}
                  required
                />
              </label>
              <label>
                Marks per Question
                <input
                  type="number"
                  min={1}
                  value={s.marks_per_question}
                  onChange={(e) => updateSectionField(i, "marks_per_question", e.target.value)}
                  required
                />
              </label>
            </div>
          ))}
        </fieldset>

        {error && <p className="error">{error}</p>}
        {success && <p className="success">{success}</p>}

        <button type="submit" disabled={busy}>
          {busy ? "Saving..." : "Save as Draft"}
        </button>
      </form>
    </DashboardShell>
  );
}