"use client";
import { useEffect, useState } from "react";
import { api, pct } from "@/lib/api";

type Bench = {
  models: { model: string; runs: number; errors: number; mean_score: number; pass_rate: number; p50_latency_ms: number }[];
  tasks: { task_id: number; name: string; scores: Record<string, number> }[];
};

export default function Benchmarks() {
  const [b, setB] = useState<Bench>();
  const [error, setError] = useState("");
  useEffect(() => { api<Bench>("/benchmarks").then(setB).catch((e) => setError(e.message)); }, []);
  if (!b) return <p className="mute">{error || "Loading benchmarks…"}</p>;
  if (b.models.length === 0) return <><h1>Benchmarks</h1><p className="mute">No finished runs yet. Run a task on two or more models to compare them.</p></>;

  return (
    <>
      <h1>Benchmarks</h1>
      <p className="sub">Models ranked by mean score across every finished run. Pass rate counts runs where every check passed.</p>
      <table><thead><tr><th>Model</th><th>Mean score</th><th className="n">Pass rate</th><th className="n">Median latency</th><th className="n">Runs</th><th className="n">Errors</th></tr></thead><tbody>
        {b.models.map((m) => (
          <tr key={m.model}>
            <td>{m.model}</td>
            <td><div className="bar" role="img" aria-label={pct(m.mean_score)}><i style={{ width: pct(m.mean_score) }} /></div>{pct(m.mean_score)}</td>
            <td className="n">{pct(m.pass_rate)}</td><td className="n">{m.p50_latency_ms} ms</td><td className="n">{m.runs}</td><td className="n">{m.errors}</td>
          </tr>
        ))}
      </tbody></table>
      <h2>Score by task</h2>
      <table><thead><tr><th>Task</th>{b.models.map((m) => <th key={m.model} className="n">{m.model}</th>)}</tr></thead><tbody>
        {b.tasks.map((t) => (
          <tr key={t.task_id}><td>{t.name}</td>{b.models.map((m) => <td key={m.model} className="n">{t.scores[m.model] === undefined ? "–" : pct(t.scores[m.model])}</td>)}</tr>
        ))}
      </tbody></table>
    </>
  );
}
