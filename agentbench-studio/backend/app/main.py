import os
import statistics
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .checks import lint_task
from .db import Base, engine, get_db
from .models import Run, Task
from .runner import execute_run
from .schemas import RunRequest, TaskIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    for attempt in range(30):  # wait for Postgres
        try:
            Base.metadata.create_all(engine)
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(1)
    yield


app = FastAPI(title="AgentBench Studio", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def task_out(t: Task) -> dict:
    return {"id": t.id, "name": t.name, "prompt": t.prompt, "checks": t.checks, "created_at": t.created_at}


def run_out(r: Run) -> dict:
    return {"id": r.id, "task_id": r.task_id, "model": r.model, "status": r.status, "output": r.output,
            "error": r.error, "latency_ms": r.latency_ms, "score": r.score, "results": r.results,
            "created_at": r.created_at}


@app.get("/health")
def health():
    return {"ok": True}


# ---- Authoring ----
@app.post("/tasks", status_code=201)
def create_task(body: TaskIn, db: Session = Depends(get_db)):
    t = Task(name=body.name, prompt=body.prompt, checks=[c.model_dump() for c in body.checks])
    db.add(t); db.commit()
    return task_out(t)


@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return [task_out(t) for t in db.scalars(select(Task).order_by(Task.id.desc()))]


def get_task(db: Session, task_id: int) -> Task:
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    return t


@app.get("/tasks/{task_id}")
def read_task(task_id: int, db: Session = Depends(get_db)):
    return task_out(get_task(db, task_id))


@app.put("/tasks/{task_id}")
def update_task(task_id: int, body: TaskIn, db: Session = Depends(get_db)):
    t = get_task(db, task_id)
    t.name, t.prompt, t.checks = body.name, body.prompt, [c.model_dump() for c in body.checks]
    db.commit()
    return task_out(t)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db.delete(get_task(db, task_id)); db.commit()


@app.get("/tasks/{task_id}/lint")
def lint(task_id: int, db: Session = Depends(get_db)):
    t = get_task(db, task_id)
    return lint_task(t.prompt, t.checks)


# ---- Running and verifying ----
@app.post("/runs", status_code=202)
def start_runs(body: RunRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    get_task(db, body.task_id)
    runs = [Run(task_id=body.task_id, model=m.strip()) for m in body.models if m.strip()]
    db.add_all(runs); db.commit()
    for r in runs:
        bg.add_task(execute_run, r.id)
    return [run_out(r) for r in runs]


@app.get("/runs")
def list_runs(task_id: int | None = None, db: Session = Depends(get_db)):
    q = select(Run).order_by(Run.id.desc()).limit(200)
    if task_id:
        q = q.where(Run.task_id == task_id)
    return [run_out(r) for r in db.scalars(q)]


# ---- Benchmark comparison ----
@app.get("/benchmarks")
def benchmarks(db: Session = Depends(get_db)):
    runs = list(db.scalars(select(Run).where(Run.status.in_(["done", "error"]))))
    by_model, matrix = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for r in runs:
        by_model[r.model].append(r)
        matrix[r.task_id][r.model].append(r.score)
    models = []
    for m, rs in by_model.items():
        ok = [r for r in rs if r.status == "done"]
        models.append({
            "model": m, "runs": len(rs), "errors": len(rs) - len(ok),
            "mean_score": round(statistics.fmean(r.score for r in ok), 3) if ok else 0,
            "pass_rate": round(sum(r.score == 1 for r in ok) / len(ok), 3) if ok else 0,
            "p50_latency_ms": int(statistics.median(r.latency_ms for r in ok)) if ok else 0,
        })
    names = {t.id: t.name for t in db.scalars(select(Task))}
    tasks = [{"task_id": tid, "name": names.get(tid, str(tid)),
              "scores": {m: round(statistics.fmean(s), 3) for m, s in per.items()}} for tid, per in matrix.items()]
    return {"models": sorted(models, key=lambda x: -x["mean_score"]), "tasks": tasks}
