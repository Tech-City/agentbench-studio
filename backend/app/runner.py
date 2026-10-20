import os
import time
from . import providers
from .checks import run_check, score
from .db import SessionLocal
from .models import Run


def judge(prompt: str) -> str:
    return providers.complete(os.getenv("JUDGE_MODEL", "mock:judge"), prompt)


def execute_run(run_id: int) -> None:
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        run.status = "running"
        db.commit()
        try:
            t0 = time.perf_counter()
            run.output = providers.complete(run.model, run.task.prompt)
            run.latency_ms = int((time.perf_counter() - t0) * 1000)
            run.results = [run_check(c, run.output, judge) for c in run.task.checks]
            run.score = score(run.results)
            run.status = "done"
        except Exception as e:
            run.status, run.error = "error", f"{type(e).__name__}: {e}"
        db.commit()
