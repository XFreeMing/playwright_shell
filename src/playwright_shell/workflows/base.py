from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import Logger

from playwright_shell.config import AutomationSettings
from playwright_shell.models import TaskSpec
from playwright_shell.services.browser import BrowserSession
from playwright_shell.services.desktop import DesktopController


@dataclass(slots=True)
class WorkflowContext:
    settings: AutomationSettings
    logger: Logger
    browser: BrowserSession
    desktop: DesktopController


class Workflow(ABC):
    name: str

    @abstractmethod
    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        raise NotImplementedError
