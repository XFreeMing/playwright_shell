from __future__ import annotations

from playwright_shell.config import AutomationSettings, load_task_file
from playwright_shell.logging_utils import get_logger
from playwright_shell.models import TaskSpec
from playwright_shell.services.auth import AuthManager
from playwright_shell.services.browser import BrowserSession
from playwright_shell.services.desktop import DesktopController
from playwright_shell.workflows.base import WorkflowContext
from playwright_shell.workflows.registry import build_workflow_registry


class AutomationRuntime:
    def __init__(self, settings: AutomationSettings) -> None:
        self.settings = settings
        self.registry = build_workflow_registry()
        self.auth_manager = AuthManager(settings)
        self.logger = get_logger("playwright_shell.runtime")

    def list_tasks(self) -> list[TaskSpec]:
        task_file = load_task_file(self.settings.task_file)
        return task_file.tasks

    def run_task(self, task_name: str) -> None:
        task_file = load_task_file(self.settings.task_file)
        task = task_file.get_task(task_name)
        workflow = self.registry.get(task.workflow)
        if workflow is None:
            raise KeyError(f"Workflow '{task.workflow}' is not registered.")

        browser_kwargs = self.auth_manager.browser_session_kwargs(task.auth_profile)
        browser = BrowserSession(self.settings, **browser_kwargs)
        desktop = DesktopController(self.settings)
        browser.start()
        try:
            context = WorkflowContext(
                settings=self.settings,
                logger=self.logger,
                browser=browser,
                desktop=desktop,
            )
            workflow.run(task, context)
        except Exception:
            browser.screenshot(f"failure-{task.name}")
            raise
        finally:
            browser.close()
