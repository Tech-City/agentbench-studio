"use client";
import { useParams } from "next/navigation";
import { Fragment, useCallback, useEffect, useState } from "react";
import { api, pct, Run, Task } from "@/lib/api";

type Lint = { quality: number; issues: { severity: string; message: string }[] };

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<Task>();
  const [lint, setLint] = useState<Lint>();
  const [runs, setRuns] = useState<Run[]>([]);
  const [models, setModels] = useState("mock:echo, mock:empty");
  const [open, setOpen] = useState<number>();
  const [error, setError] = useState("");

  const loadRuns = useCallback(() => api<Run[]>(`/runs?task_id=${id}`).then(setRuns).catch((e) => setError(e.message)), [id]);
  useEffect(() => {
    api<Task>(`/tasks/${id}`).then(setTask).catch((e) => setError(e.message));
    api<Lint>(`/tasks/${id}/lint`).then(setLint);
    loadRuns();
  }, [id, loadRuns]);
  useEffect(() => {  // poll while anything is in flight
    if (!runs.some((r) => r.status === "queued" || r.status === "running")) return;
    const t = setInterval(loadRuns, 1500);
    return () => clearInterval(t);
  }, [runs, loadRuns]);

  async function start() {
    setError("");
    try {
      await api("/runs", { method: "POST", body: JSON.stringify({ task_id: Number(id), models: models.split(",").map((m) => m.trim()).filter(Boolean) }) });
      loadRuns();
    } catch (e) { setError((e as Error).message); }
  }
  if (!task) return <p className="mute">{error || "Loading task…"}</p>;

  return (
    <>
      <h1>{task.name}</h1>
      <p className="sub">{task.prompt}</p>
      {lint && (
        <div className="panel">
          <b>Task quality: {lint.quality}/100</b>
          {lint.issues.length === 0 ? <p className="ok">No problems found.</p> :
            <ul>{lint.issues.map((i, k) => <li key={k} className={i.severity === "error" ? "bad" : i.severity === "warn" ? "warn" : "mute"}>{i.message}</li>)}</ul>}
        </div>
      )}
      <div className="panel">
        <label htmlFor="models">Models</label>
        <input id="models" value={models} onChange={(e) => setModels(e.target.value)} placeholder="provider:model, comma separated" />
        <p className="mute" style={{ margin: "6px 0" }}>Examples: mock:echo, anthropic:claude-sonnet-5-5, openai:your-model</p>
        <button onClick={start}>Run on models</button>
        {error && <p className="bad" role="alert">{error}</p>}
      </div>
      <h2>Runs</h2>
      {runs.length === 0 ? <p className="mute">No runs yet. Pick models above and run the task.</p> : (
        <table><thead><tr><th>Model</th><th>Status</th><th className="n">Score</th><th className="n">Latency</th><th /></tr></thead><tbody>
          {runs.map((r) => (
            <Fragment key={r.id}>
              <tr>
                <td>{r.model}</td><td>{r.status}</td>
                <td className="n">{r.status === "done" ? pct(r.score) : "–"}</td>
                <td className="n">{r.status === "done" ? `${r.latency_ms} ms` : "–"}</td>
                <td><button className="ghost" onClick={() => setOpen(open === r.id ? undefined : r.id)}>{open === r.id ? "Hide" : "Details"}</button></td>
              </tr>
              {open === r.id && (
                <tr><td colSpan={5}>
                  {r.error && <p className="bad">{r.error}</p>}
                  {r.results.map((c, k) => <div key={k} className={c.passed ? "ok" : "bad"}>{c.passed ? "Pass" : "Fail"}: {c.label} ({c.detail})</div>)}
                  <pre>{r.output || "(empty output)"}</pre>
                </td></tr>
              )}
            </Fragment>
          ))}
        </tbody></table>
      )}
    </>
  );
}
