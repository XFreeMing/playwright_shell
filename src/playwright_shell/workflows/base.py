from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import TYPE_CHECKING

from playwright_shell.config import AutomationSettings
from playwright_shell.models import TaskSpec
from playwright_shell.services.browser import BrowserSession

if TYPE_CHECKING:
    from playwright_shell.services.desktop import DesktopController


@dataclass(slots=True)
class WorkflowContext:
    settings: AutomationSettings
    logger: Logger
    browser: BrowserSession
    _desktop: DesktopController | None = field(default=None, repr=False)

    @property
    def desktop(self) -> DesktopController:
        if self._desktop is None:
            from playwright_shell.services.desktop import DesktopController

            self._desktop = DesktopController(self.settings)
        return self._desktop


class Workflow(ABC):
    name: str

    @abstractmethod
    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        raise NotImplementedError
