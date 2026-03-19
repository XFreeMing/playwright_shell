from playwright_shell.workflows.registry import build_workflow_registry


def test_registry_contains_expected_workflows() -> None:
    registry = build_workflow_registry()

    assert {"browse", "comment", "collect", "download"}.issubset(registry)