from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from playwright_shell.models import TaskSpec
from playwright_shell.services.page_analyzer import PageAnalyzer
from playwright_shell.workflows.base import Workflow, WorkflowContext

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class InfoqPublishWorkflow(Workflow):
    name = "infoq_publish"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        page = context.browser.open_page(
            task.inputs["target_url"],
            reuse_current=bool(task.inputs.get("reuse_current", False)),
        )
        self._wait_for_page_ready(page)

        button = self._find_create_button(page)
        button.scroll_into_view_if_needed()
        button.click()

        if task.inputs.get("analyze_after_click", True):
            label = task.inputs.get("label") or task.name
            artifacts = PageAnalyzer(context.settings).inspect(page, label=label)
            context.logger.info(
                "infoq publish artifacts saved",
                extra={
                    "task": task.name,
                    "report": str(artifacts.report_path),
                    "html": str(artifacts.html_path),
                    "screenshot": str(artifacts.screenshot_path),
                },
            )

        context.logger.info(
            "infoq publish create button clicked",
            extra={"task": task.name, "url": page.url},
        )

    def _wait_for_page_ready(self, page: Page) -> None:
        page.wait_for_load_state("domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            pass

    def _find_create_button(self, page: Page) -> Locator:
        candidates = [
            page.get_by_role("button", name="立即创作"),
            page.get_by_role("link", name="立即创作"),
            page.locator("text=立即创作"),
            page.locator("button").filter(has_text="立即创作"),
            page.locator("a").filter(has_text="立即创作"),
            page.locator("[class*='create'], [class*='publish'], [class*='write']").filter(
                has_text="立即创作"
            ),
        ]

        for candidate in candidates:
            try:
                candidate.first.wait_for(state="visible", timeout=5_000)
                return candidate.first
            except PlaywrightTimeoutError:
                continue

        raise RuntimeError("Could not find the InfoQ '立即创作' button.")