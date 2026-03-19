from __future__ import annotations

from pathlib import Path

from playwright_shell.models import TaskSpec
from playwright_shell.workflows.base import Workflow, WorkflowContext


class DownloadWorkflow(Workflow):
    name = "download"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        page = context.browser.page
        page.goto(task.inputs["target_url"])

        trigger = task.inputs["download_trigger"]
        with page.expect_download() as download_info:
            page.locator(trigger).click()

        download = download_info.value
        suggested_name = task.inputs.get("filename") or download.suggested_filename
        destination = Path(context.settings.downloads_dir) / suggested_name
        download.save_as(str(destination))
        context.logger.info(
            "download workflow completed",
            extra={"task": task.name, "file": str(destination)},
        )
