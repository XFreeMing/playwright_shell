from playwright_shell.config import AutomationSettings
from playwright_shell.services.browser import BrowserSession


def test_resolve_cdp_endpoint_keeps_full_websocket_url() -> None:
    session = BrowserSession(
        AutomationSettings(),
        cdp_url="ws://127.0.0.1:9222/devtools/browser/example",
    )

    assert session._resolve_cdp_endpoint() == "ws://127.0.0.1:9222/devtools/browser/example"