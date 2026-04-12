from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from playwright_shell.config import AutomationSettings


class _BrowserConnector(ABC):
    """Strategy for launching/connecting to a browser."""

    @abstractmethod
    def connect(
        self,
        launcher,
        settings: AutomationSettings,
        base_url: str | None,
        storage_state_path: Path | None,
    ) -> tuple[Browser | None, BrowserContext, bool]:
        """Return (browser, context, external_context)."""


class _CdpConnector(_BrowserConnector):
    """Connect to an existing Chrome via CDP."""

    def __init__(self, cdp_url: str) -> None:
        self.cdp_url = cdp_url

    def connect(
        self,
        launcher,
        settings: AutomationSettings,
        base_url: str | None,
        storage_state_path: Path | None,
    ) -> tuple[Browser | None, BrowserContext, bool]:
        del storage_state_path  # not used in CDP mode
        browser = launcher.connect_over_cdp(self._resolve_cdp_endpoint())
        if browser.contexts:
            context = browser.contexts[0]
            external = True
        else:
            context = browser.new_context(base_url=base_url)
            external = False
        context.set_default_timeout(settings.timeout_ms)
        return browser, context, external

    def _resolve_cdp_endpoint(self) -> str:
        if self.cdp_url.startswith("ws://") or self.cdp_url.startswith("wss://"):
            parsed = urlparse(self.cdp_url)
            if parsed.path and parsed.path not in {"", "/"}:
                return self.cdp_url
            discovery_base = f"http://{parsed.netloc}"
        else:
            discovery_base = self.cdp_url.rstrip("/")

        version_url = urljoin(f"{discovery_base}/", "json/version")
        try:
            with urlopen(version_url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Could not discover Chrome CDP websocket from {version_url}.",
            ) from error

        websocket_url = payload.get("webSocketDebuggerUrl")
        if not websocket_url:
            raise RuntimeError(
                f"Chrome DevTools endpoint {version_url} did not return webSocketDebuggerUrl.",
            )
        return str(websocket_url)


class _PersistentContextConnector(_BrowserConnector):
    """Launch browser with a persistent user data directory."""

    def __init__(self, user_data_dir: Path) -> None:
        self.user_data_dir = user_data_dir

    def connect(
        self,
        launcher,
        settings: AutomationSettings,
        base_url: str | None,
        storage_state_path: Path | None,
    ) -> tuple[None, BrowserContext, bool]:
        del storage_state_path  # not used with persistent context
        context = launcher.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
            accept_downloads=True,
            base_url=base_url,
        )
        context.set_default_timeout(settings.timeout_ms)
        return None, context, False


class _StandardLauncher(_BrowserConnector):
    """Launch a fresh browser and create a new context."""

    def connect(
        self,
        launcher,
        settings: AutomationSettings,
        base_url: str | None,
        storage_state_path: Path | None,
    ) -> tuple[Browser, BrowserContext, bool]:
        browser = launcher.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
        )
        kwargs: dict[str, str] = {"accept_downloads": True}
        if base_url:
            kwargs["base_url"] = base_url
        if storage_state_path:
            kwargs["storage_state"] = str(storage_state_path)
        context = browser.new_context(**kwargs)
        context.set_default_timeout(settings.timeout_ms)
        return browser, context, False


class BrowserSession:
    def __init__(
        self,
        settings: AutomationSettings,
        *,
        browser_mode: str | None = None,
        base_url: str | None = None,
        storage_state_path: Path | None = None,
        user_data_dir: Path | None = None,
        cdp_url: str | None = None,
    ) -> None:
        self.settings = settings
        self.browser_mode = browser_mode if browser_mode is not None else settings.browser_mode
        self.base_url = base_url if base_url is not None else settings.base_url
        self.storage_state_path = (
            storage_state_path if storage_state_path is not None else settings.storage_state_path
        )
        self.user_data_dir = user_data_dir if user_data_dir is not None else settings.user_data_dir
        self.cdp_url = cdp_url if cdp_url is not None else settings.cdp_url
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._external_context = False

    def start(self) -> None:
        self.settings.ensure_directories()
        self._playwright = sync_playwright().start()
        launcher = getattr(self._playwright, self.settings.browser_type)
        connector = self._make_connector()
        self._browser, self._context, self._external_context = connector.connect(
            launcher, self.settings, self.base_url, self.storage_state_path,
        )

    def _make_connector(self) -> _BrowserConnector:
        if self.browser_mode == "cdp":
            return _CdpConnector(self.cdp_url)
        if self.user_data_dir is not None:
            return _PersistentContextConnector(self.user_data_dir)
        return _StandardLauncher()

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Browser session is not started.")
        return self._context

    @property
    def page(self) -> Page:
        pages = [page for page in self.context.pages if not page.is_closed()]
        if pages:
            return pages[-1]
        return self.context.new_page()

    def new_page(self) -> Page:
        return self.context.new_page()

    def open_page(self, url: str, *, reuse_current: bool = False) -> Page:
        page = self.page if reuse_current else self.new_page()
        page.goto(url, wait_until="domcontentloaded")
        return page

    def screenshot(self, name: str) -> Path:
        path = self.settings.screenshot_dir / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def save_storage_state(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(path))
        return path

    def close(self) -> None:
        if self._context is not None and not self._external_context:
            self._context.close()
        # In CDP mode the browser is shared — disconnect instead of closing
        # so OpenClaw Chrome keeps running.
        if self._browser is not None:
            if self.browser_mode == "cdp":
                self._browser.disconnect()
            else:
                self._browser.close()
        self._context = None
        self._browser = None
        self._external_context = False
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
