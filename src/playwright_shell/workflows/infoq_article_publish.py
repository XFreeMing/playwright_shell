from __future__ import annotations

from typing import TYPE_CHECKING

from playwright_shell.models import TaskSpec
from playwright_shell.services.infoq import InfoQService
from playwright_shell.services.page_analyzer import PageAnalyzer
from playwright_shell.workflows.base import Workflow, WorkflowContext

if TYPE_CHECKING:
    from playwright.sync_api import Page


class InfoqArticlePublishWorkflow(Workflow):
    name = "infoq_article_publish"

    def __init__(self) -> None:
        self._service = InfoQService()

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        publish_page = context.browser.open_page(
            task.inputs["target_url"],
            reuse_current=bool(task.inputs.get("reuse_current", False)),
        )
        self._service.wait_for_page_ready(publish_page)

        draft_page = self._service.start_create(publish_page)
        self._service.wait_for_page_ready(draft_page)

        self._service.write_title(draft_page, task.inputs["article_title"])
        self._service.write_body(draft_page, task.inputs["article_body"])

        self._service.open_publish_dialog(draft_page)
        self._fill_publish_settings(task, draft_page)
        self._service.confirm_publish(draft_page)

        if task.inputs.get("analyze_after_publish", True):
            label = task.inputs.get("label") or task.name
            artifacts = PageAnalyzer(context.settings).inspect(draft_page, label=label)
            context.logger.info(
                "infoq article publish artifacts saved",
                extra={
                    "task": task.name,
                    "report": str(artifacts.report_path),
                    "html": str(artifacts.html_path),
                    "screenshot": str(artifacts.screenshot_path),
                },
            )

        context.logger.info(
            "infoq article publish confirmed",
            extra={"task": task.name, "url": draft_page.url},
        )

    def _fill_publish_settings(self, task: TaskSpec, draft_page: Page) -> None:
        """Fill in publish settings (summary and tags)."""
        summary = task.inputs.get("article_summary")
        if summary:
            self._service.fill_summary(draft_page, summary)

        for tag in task.inputs.get("article_tags", []):
            self._service.add_tag(draft_page, tag)