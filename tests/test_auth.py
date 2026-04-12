import json
import time

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


def test_storage_has_valid_cookies_returns_false_when_missing(tmp_path) -> None:
    manager = AuthManager(AutomationSettings())

    assert not manager._storage_has_valid_cookies("nonexistent_profile")


def test_storage_has_valid_cookies_returns_true_for_fresh_cookies(tmp_path) -> None:
    settings = AutomationSettings(storage_states_dir=tmp_path)
    manager = AuthManager(settings)
    storage_file = tmp_path / "test_profile.json"

    future = int(time.time()) + 3600
    storage_file.write_text(json.dumps({
        "cookies": [{"name": "session", "value": "abc", "expires": future}],
    }))

    assert manager._storage_has_valid_cookies("test_profile")


def test_storage_has_valid_cookies_returns_false_for_expired(tmp_path) -> None:
    settings = AutomationSettings(storage_states_dir=tmp_path)
    manager = AuthManager(settings)
    storage_file = tmp_path / "test_profile.json"

    past = int(time.time()) - 3600
    storage_file.write_text(json.dumps({
        "cookies": [{"name": "session", "value": "abc", "expires": past}],
    }))

    assert not manager._storage_has_valid_cookies("test_profile")