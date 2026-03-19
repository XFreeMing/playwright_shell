from __future__ import annotations

from pathlib import Path

from playwright_shell.models import CollectResult, TaskSpec
from playwright_shell.workflows.base import Workflow, WorkflowContext


class CollectWorkflow(Workflow):
    name = "collect"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        page = context.browser.page
        page.goto(task.inputs["target_url"])

        item_selector = task.inputs["item_selector"]
        field_selectors: dict[str, str] = task.inputs.get("fields", {})
        items: list[dict[str, str]] = []

        for item in page.locator(item_selector).all():
            record: dict[str, str] = {}
            for field_name, selector in field_selectors.items():
                locator = item.locator(selector).first
                if field_name.lower().endswith("link"):
                    value = locator.get_attribute("href") or ""
                else:
                    value = locator.inner_text().strip()
                record[field_name] = value
            items.append(record)

        output_path = Path(task.inputs.get("output_path", f"data/collect/{task.name}.json"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result = CollectResult(task_name=task.name, items=items, output_path=output_path)
        output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        context.logger.info(
            "collect workflow completed",
            extra={"task": task.name, "items": len(items)},
        )
