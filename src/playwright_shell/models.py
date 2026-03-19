from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    name: str
    workflow: str
    enabled: bool = True
    description: str | None = None
    auth_profile: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


class TaskFile(BaseModel):
    tasks: list[TaskSpec] = Field(default_factory=list)

    def get_task(self, name: str) -> TaskSpec:
        for task in self.tasks:
            if task.name == name:
                return task
        raise KeyError(f"Task '{name}' was not found.")

    def enabled_tasks(self) -> list[TaskSpec]:
        return [task for task in self.tasks if task.enabled]


class CollectResult(BaseModel):
    task_name: str
    items: list[dict[str, str]] = Field(default_factory=list)
    output_path: Path


class AuthProfileSpec(BaseModel):
    name: str
    provider: str
    enabled: bool = True
    base_url: str | None = None
    login_url: str | None = None
    logged_in_selector: str | None = None
    logged_out_selector: str | None = None
    login_timeout_seconds: int = 300
    description: str | None = None


class AuthFile(BaseModel):
    profiles: list[AuthProfileSpec] = Field(default_factory=list)

    def get_profile(self, name: str) -> AuthProfileSpec:
        for profile in self.profiles:
            if profile.name == name:
                return profile
        raise KeyError(f"Auth profile '{name}' was not found.")
