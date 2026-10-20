from typing import Any, Literal
from pydantic import BaseModel, Field
from .checks import TYPES

CheckType = Literal[tuple(TYPES)]  # type: ignore


class CheckSpec(BaseModel):
    type: CheckType
    value: Any = None
    label: str | None = None
    weight: float = Field(1, gt=0)


class TaskIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    checks: list[CheckSpec] = []


class RunRequest(BaseModel):
    task_id: int
    models: list[str] = Field(min_length=1)
