from pathlib import Path

from playwright_shell.config import (
    _PROJECT_ROOT,
    AutomationSettings,
    load_auth_file,
    load_task_file,
)


def test_load_task_file_reads_example_tasks() -> None:
    task_file = load_task_file(Path("examples/tasks.yaml"))

    assert len(task_file.tasks) == 6
    assert task_file.get_task("geekbang_open_demo").workflow == "browse"
    assert task_file.get_task("infoq_publish_create_demo").workflow == "infoq_publish"
    assert task_file.get_task("infoq_publish_create_demo").auth_profile == "infoq_default"
    assert task_file.get_task("infoq_publish_article_demo").workflow == "infoq_article_publish"
    assert task_file.get_task("infoq_publish_article_demo").auth_profile == "infoq_default"
    assert task_file.get_task("comment_demo").workflow == "comment"
    assert task_file.get_task("comment_demo").auth_profile == "zhihu_default"


def test_load_auth_file_reads_example_profiles() -> None:
    auth_file = load_auth_file(Path("examples/auth_profiles.yaml"))

    assert len(auth_file.profiles) == 4
    assert auth_file.get_profile("zhihu_default").provider == "zhihu"
    assert auth_file.get_profile("infoq_default").provider == "infoq"


def test_settings_defaults_resolve_to_absolute_paths() -> None:
    settings = AutomationSettings()

    assert settings.task_file.is_absolute()
    assert settings.auth_file.is_absolute()
    assert settings.task_file.parent.name == "examples"
    assert settings.auth_file.parent.name == "examples"
    # Both resolve relative to the project root (not cwd).
    assert settings.task_file.parent.parent == _PROJECT_ROOT


def test_output_dirs_resolved_relative_to_cwd() -> None:
    settings = AutomationSettings()

    assert settings.downloads_dir.is_absolute()
    assert settings.screenshot_dir.is_absolute()
    # When not overridden, they are made absolute relative to cwd.
    assert settings.downloads_dir == Path.cwd() / "data" / "downloads"

