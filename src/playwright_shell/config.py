from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from playwright_shell.models import AuthFile, TaskFile

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _default_task_file() -> Path:
    return _PROJECT_ROOT / "examples" / "tasks.yaml"


def _default_auth_file() -> Path:
    return _PROJECT_ROOT / "examples" / "auth_profiles.yaml"


class AutomationSettings(BaseSettings):
    browser_type: str = "chromium"
    browser_mode: str = "cdp"
    headless: bool = False
    base_url: str | None = None
    task_file: Path = Field(default_factory=_default_task_file)
    auth_file: Path = Field(default_factory=_default_auth_file)
    downloads_dir: Path = Path("data/downloads")
    screenshot_dir: Path = Path("data/screenshots")
    page_analysis_dir: Path = Path("data/page_analysis")
    profiles_dir: Path = Path("data/profiles")
    storage_states_dir: Path = Path("data/storage_states")
    chrome_executable_path: Path = Path("/opt/google/chrome/chrome")
    shared_user_data_dir: Path = Path.home() / ".chrome-custom"
    cdp_url: str = "http://127.0.0.1:9222"
    remote_debugging_port: int = 9222
    openclaw_config_path: Path = Path.home() / ".openclaw" / "openclaw.json"
    storage_state_path: Path | None = None
    user_data_dir: Path | None = None
    timeout_ms: int = 30_000
    slow_mo_ms: int = 0
    pyautogui_pause: float = Field(default=0.2, ge=0.0)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PS_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_output_dirs(self) -> "AutomationSettings":
        """Make output dirs absolute relative to cwd if they are relative."""
        if not self.downloads_dir.is_absolute():
            self.downloads_dir = Path.cwd() / self.downloads_dir
        if not self.screenshot_dir.is_absolute():
            self.screenshot_dir = Path.cwd() / self.screenshot_dir
        if not self.page_analysis_dir.is_absolute():
            self.page_analysis_dir = Path.cwd() / self.page_analysis_dir
        if not self.profiles_dir.is_absolute():
            self.profiles_dir = Path.cwd() / self.profiles_dir
        if not self.storage_states_dir.is_absolute():
            self.storage_states_dir = Path.cwd() / self.storage_states_dir
        return self

    def ensure_directories(self) -> None:
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.page_analysis_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.storage_states_dir.mkdir(parents=True, exist_ok=True)


def load_task_file(path: Path) -> TaskFile:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return TaskFile.model_validate(payload)


def load_auth_file(path: Path) -> AuthFile:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return AuthFile.model_validate(payload)
