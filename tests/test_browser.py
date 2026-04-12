from playwright_shell.config import AutomationSettings
from playwright_shell.services.browser import BrowserSession


def test_make_connector_chooses_cdp_for_cdp_mode() -> None:
    settings = AutomationSettings(browser_mode="cdp", cdp_url="http://127.0.0.1:9222")
    session = BrowserSession(settings)
    assert session.browser_mode == "cdp"


def test_make_connector_chooses_persistent_when_user_data_dir() -> None:
    settings = AutomationSettings(browser_mode="launch", user_data_dir="/tmp/test-data")
    session = BrowserSession(settings)
    assert session.browser_mode == "launch"
    assert session.user_data_dir is not None


def test_make_connector_chooses_standard_otherwise() -> None:
    settings = AutomationSettings(browser_mode="launch")
    session = BrowserSession(settings)
    assert session.browser_mode == "launch"
    assert session.user_data_dir is None


def test_resolve_cdp_endpoint_keeps_full_websocket_url() -> None:
    settings = AutomationSettings(browser_mode="cdp", cdp_url="ws://127.0.0.1:9222/devtools/browser/example")
    session = BrowserSession(settings)

    assert session._resolve_cdp_endpoint() == "ws://127.0.0.1:9222/devtools/browser/example"
