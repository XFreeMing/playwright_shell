from playwright_shell.config import AutomationSettings
from playwright_shell.services.auth import AuthManager


def test_auth_manager_builds_profile_paths() -> None:
    manager = AuthManager(AutomationSettings())

    paths = manager.auth_paths("zhihu_default")

    assert paths.user_data_dir.as_posix().endswith(".chrome-custom")
    assert paths.storage_state_path.as_posix().endswith(
        "data/storage_states/zhihu_default.json"
    )


def test_auth_session_kwargs_use_profile_overrides() -> None:
    manager = AuthManager(AutomationSettings())

    kwargs = manager.browser_session_kwargs("bilibili_default")

    assert kwargs["base_url"] == "https://www.bilibili.com/"