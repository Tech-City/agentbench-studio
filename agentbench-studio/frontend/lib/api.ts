export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export type Check = { type: string; value?: string; weight?: number };
export type Task = { id: number; name: string; prompt: string; checks: Check[] };
export type Result = { label: string; passed: boolean; detail: string };
export type Run = { id: number; task_id: number; model: string; status: string; output: string; error: string; latency_ms: number; score: number; results: Result[] };
export const CHECK_TYPES = ["contains", "not_contains", "regex", "json_valid", "json_schema", "max_words", "llm_judge"];

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(API + path, { ...init, headers: { "Content-Type": "application/json" }, cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.status === 204 ? (undefined as T) : r.json();
}
export const pct = (n: number) => `${Math.round(n * 100)}%`;
