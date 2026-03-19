from __future__ import annotations

from playwright_shell.workflows.base import Workflow
from playwright_shell.workflows.browse import BrowseWorkflow
from playwright_shell.workflows.collect import CollectWorkflow
from playwright_shell.workflows.comment import CommentWorkflow
from playwright_shell.workflows.download import DownloadWorkflow


def build_workflow_registry() -> dict[str, Workflow]:
    workflows: list[Workflow] = [
        BrowseWorkflow(),
        CommentWorkflow(),
        CollectWorkflow(),
        DownloadWorkflow(),
    ]
    return {workflow.name: workflow for workflow in workflows}
