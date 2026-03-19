from __future__ import annotations

from playwright_shell.models import TaskSpec
from playwright_shell.workflows.base import Workflow, WorkflowContext


class CommentWorkflow(Workflow):
    name = "comment"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        page = context.browser.page
        target_url = task.inputs["target_url"]
        comment_box = task.inputs["comment_box"]
        comment_text = task.inputs["comment_text"]

        page.goto(target_url)
        page.locator(comment_box).fill(comment_text)

        if task.inputs.get("use_desktop_submit"):
            context.desktop.hotkey("ctrl", "enter")
        elif submit_button := task.inputs.get("submit_button"):
            page.locator(submit_button).click()

        context.logger.info("comment workflow completed", extra={"task": task.name})
