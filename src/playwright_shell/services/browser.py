from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from playwright_shell.config import AutomationSettings


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
        browser_launcher = getattr(self._playwright, self.settings.browser_type)

        if self.browser_mode == "cdp":
            self._browser = browser_launcher.connect_over_cdp(self._resolve_cdp_endpoint())
            if self._browser.contexts:
                self._context = self._browser.contexts[0]
                self._external_context = True
            else:
                self._context = self._browser.new_context(base_url=self.base_url)
            self._context.set_default_timeout(self.settings.timeout_ms)
            return

        if self.user_data_dir is not None:
            self._context = browser_launcher.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.settings.headless,
                slow_mo=self.settings.slow_mo_ms,
                accept_downloads=True,
                base_url=self.base_url,
            )
            self._context.set_default_timeout(self.settings.timeout_ms)
            return

        self._browser = browser_launcher.launch(
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo_ms,
        )
        context_kwargs: dict[str, Any] = {
            "accept_downloads": True,
        }
        if self.base_url:
            context_kwargs["base_url"] = self.base_url
        if self.storage_state_path:
            context_kwargs["storage_state"] = str(self.storage_state_path)
        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self.settings.timeout_ms)

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
                f"Could not discover Chrome CDP websocket from {version_url}."
            ) from error

        websocket_url = payload.get("webSocketDebuggerUrl")
        if not websocket_url:
            raise RuntimeError(
                f"Chrome DevTools endpoint {version_url} did not return webSocketDebuggerUrl."
            )
        return str(websocket_url)

    def save_storage_state(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.context.storage_state(path=str(path))
        return path

    def close(self) -> None:
        if self._context is not None and not self._external_context:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        self._context = None
        self._external_context = False
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
