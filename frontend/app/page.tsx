"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Check, CHECK_TYPES, Task } from "@/lib/api";

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [checks, setChecks] = useState<Check[]>([]);
  const [error, setError] = useState("");
  const load = () => api<Task[]>("/tasks").then(setTasks).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const patch = (i: number, p: Partial<Check>) => setChecks(checks.map((c, j) => (j === i ? { ...c, ...p } : c)));
  async function save() {
    setError("");
    try {
      await api("/tasks", { method: "POST", body: JSON.stringify({ name, prompt, checks }) });
      setName(""); setPrompt(""); setChecks([]); load();
    } catch (e) { setError((e as Error).message); }
  }

  return (
    <>
      <h1>Tasks</h1>
      <p className="sub">A task is a prompt plus checks that decide whether an answer is good. Run it on any model, then compare.</p>
      <div className="panel">
        <label htmlFor="name">Task name</label><input id="name" value={name} onChange={(e) => setName(e.target.value)} />
        <label htmlFor="prompt">Prompt</label><textarea id="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
        <label>Checks</label>
        {checks.map((c, i) => (
          <div className="row" key={i}>
            <select aria-label="Check type" value={c.type} onChange={(e) => patch(i, { type: e.target.value })}>
              {CHECK_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
            <input aria-label="Check value" value={c.value ?? ""} placeholder="value, pattern, schema or rubric" onChange={(e) => patch(i, { value: e.target.value })} />
            <button className="ghost" aria-label="Remove check" onClick={() => setChecks(checks.filter((_, j) => j !== i))}>Remove</button>
          </div>
        ))}
        <div className="row"><button className="ghost" onClick={() => setChecks([...checks, { type: "contains", value: "" }])}>Add check</button>
          <button onClick={save} disabled={!name || !prompt}>Save task</button></div>
        {error && <p className="bad" role="alert">{error}</p>}
      </div>
      {tasks.length === 0 ? <p className="mute">No tasks yet. Write a prompt above and add at least one check.</p> : (
        <table><thead><tr><th>Name</th><th className="n">Checks</th></tr></thead><tbody>
          {tasks.map((t) => <tr key={t.id}><td><Link href={`/tasks/${t.id}`}>{t.name}</Link></td><td className="n">{t.checks.length}</td></tr>)}
        </tbody></table>
      )}
    </>
  );
}
