from pathlib import Path

from playwright_shell.config import load_auth_file, load_task_file


def test_load_task_file_reads_example_tasks() -> None:
    task_file = load_task_file(Path("examples/tasks.yaml"))

    assert len(task_file.tasks) == 4
    assert task_file.get_task("geekbang_open_demo").workflow == "browse"
    assert task_file.get_task("comment_demo").workflow == "comment"
    assert task_file.get_task("comment_demo").auth_profile == "zhihu_default"


def test_load_auth_file_reads_example_profiles() -> None:
    auth_file = load_auth_file(Path("examples/auth_profiles.yaml"))

    assert len(auth_file.profiles) == 3
    assert auth_file.get_profile("zhihu_default").provider == "zhihu"

