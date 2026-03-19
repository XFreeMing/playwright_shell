from __future__ import annotations

from playwright_shell.models import TaskSpec
from playwright_shell.services.page_analyzer import PageAnalyzer
from playwright_shell.workflows.base import Workflow, WorkflowContext


class BrowseWorkflow(Workflow):
    name = "browse"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        target_url = task.inputs["target_url"]
        reuse_current = bool(task.inputs.get("reuse_current", False))
        analyze = bool(task.inputs.get("analyze", True))
        label = task.inputs.get("label") or task.name

        page = context.browser.open_page(target_url, reuse_current=reuse_current)
        context.logger.info(
            "browse workflow opened page",
            extra={"task": task.name, "url": page.url},
        )

        if analyze:
            artifacts = PageAnalyzer(context.settings).inspect(page, label=label)
            context.logger.info(
                "browse workflow saved artifacts",
                extra={
                    "task": task.name,
                    "report": str(artifacts.report_path),
                    "html": str(artifacts.html_path),
                    "screenshot": str(artifacts.screenshot_path),
                },
            )