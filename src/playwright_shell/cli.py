from __future__ import annotations

from pathlib import Path

import typer

from playwright_shell.commands.infoq import infoq_app
from playwright_shell.config import AutomationSettings
from playwright_shell.logging_utils import configure_logging
from playwright_shell.runtime import AutomationRuntime
from playwright_shell.services.auth import AuthManager
from playwright_shell.services.browser import BrowserSession
from playwright_shell.services.page_analyzer import PageAnalyzer

app = typer.Typer(help="Playwright shell for browser and desktop automation workflows.")
auth_app = typer.Typer(help="Manage persistent login profiles for different websites.")
app.add_typer(auth_app, name="auth")
app.add_typer(infoq_app, name="infoq")


def build_settings(task_file: Path | None = None) -> AutomationSettings:
    settings = AutomationSettings()
    if task_file is not None:
        settings.task_file = task_file
    return settings


@app.command("list-tasks")
def list_tasks(task_file: Path | None = None) -> None:
    settings = build_settings(task_file)
    configure_logging(settings.log_level)
    runtime = AutomationRuntime(settings)
    for task in runtime.list_tasks():
        status = "enabled" if task.enabled else "disabled"
        auth_profile = task.auth_profile or "-"
        typer.echo(f"{task.name}\t{task.workflow}\t{status}\t{auth_profile}")


@app.command()
def run(task_name: str, task_file: Path | None = None) -> None:
    settings = build_settings(task_file)
    configure_logging(settings.log_level)
    runtime = AutomationRuntime(settings)
    runtime.run_task(task_name)


@app.command()
def open(
    url: str,
    auth_profile: str | None = typer.Option(default=None),
    reuse_current: bool = typer.Option(
        default=False,
        help="Reuse the current tab instead of a new tab.",
    ),
    analyze: bool = typer.Option(
        default=True,
        help="Capture page analysis report, HTML, and screenshot.",
    ),
    label: str | None = typer.Option(
        default=None,
        help="Optional output label for saved analysis files.",
    ),
) -> None:
    settings = build_settings()
    configure_logging(settings.log_level)
    auth_manager = AuthManager(settings)
    browser_kwargs = auth_manager.browser_session_kwargs(auth_profile)
    browser = BrowserSession(settings, **browser_kwargs)
    browser.start()
    try:
        page = browser.open_page(url, reuse_current=reuse_current)
        typer.echo(f"opened\t{page.url}")
        typer.echo(f"title\t{page.title()}")
        if analyze:
            analyzer = PageAnalyzer(settings)
            artifacts = analyzer.inspect(page, label=label)
            typer.echo(f"report\t{artifacts.report_path}")
            typer.echo(f"html\t{artifacts.html_path}")
            typer.echo(f"screenshot\t{artifacts.screenshot_path}")
    finally:
        browser.close()


@auth_app.command("list")
def list_auth_profiles() -> None:
    settings = build_settings()
    configure_logging(settings.log_level)
    manager = AuthManager(settings)
    for profile in manager.list_profiles():
        typer.echo(f"{profile.name}\t{profile.provider}\t{profile.description or ''}")


@auth_app.command("login")
def login(profile_name: str) -> None:
    settings = build_settings()
    configure_logging(settings.log_level)
    manager = AuthManager(settings)
    typer.echo(f"Attach to OpenClaw browser and complete login for profile: {profile_name}")
    storage_path = manager.login(profile_name)
    typer.echo(f"Login state saved: {storage_path}")


@auth_app.command("status")
def auth_status(profile_name: str) -> None:
    settings = build_settings()
    configure_logging(settings.log_level)
    manager = AuthManager(settings)
    authenticated = manager.is_authenticated(profile_name)
    state = "authenticated" if authenticated else "not-authenticated"
    typer.echo(f"{profile_name}\t{state}")


if __name__ == "__main__":
    app()
