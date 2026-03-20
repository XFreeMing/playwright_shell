from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from playwright_shell.config import AutomationSettings, load_auth_file
from playwright_shell.logging_utils import get_logger
from playwright_shell.models import AuthProfileSpec
from playwright_shell.services.browser import BrowserSession


@dataclass(slots=True)
class AuthPaths:
    user_data_dir: Path
    storage_state_path: Path


class AuthProvider:
    def __init__(
        self,
        name: str,
        *,
        base_url: str | None = None,
        login_url: str | None = None,
        logged_in_selector: str | None = None,
        logged_out_selector: str | None = None,
    ) -> None:
        self.name = name
        self.default_base_url = base_url
        self.default_login_url = login_url
        self.default_logged_in_selector = logged_in_selector
        self.default_logged_out_selector = logged_out_selector

    def base_url(self, profile: AuthProfileSpec) -> str | None:
        return profile.base_url or self.default_base_url

    def login_url(self, profile: AuthProfileSpec) -> str:
        login_url = profile.login_url or self.default_login_url
        if not login_url:
            raise ValueError(
                f"Auth profile '{profile.name}' must define login_url "
                "or use a provider with a default login URL."
            )
        return login_url

    def logged_in_selector(self, profile: AuthProfileSpec) -> str | None:
        return profile.logged_in_selector or self.default_logged_in_selector

    def logged_out_selector(self, profile: AuthProfileSpec) -> str | None:
        return profile.logged_out_selector or self.default_logged_out_selector

    def is_authenticated(self, session: BrowserSession, profile: AuthProfileSpec) -> bool:
        page = session.page
        target_url = self.base_url(profile) or self.login_url(profile)
        page.goto(target_url, wait_until="domcontentloaded")

        logged_in_selector = self.logged_in_selector(profile)
        logged_out_selector = self.logged_out_selector(profile)

        if logged_in_selector:
            return page.locator(logged_in_selector).first.is_visible(timeout=3_000)
        if logged_out_selector:
            try:
                return not page.locator(logged_out_selector).first.is_visible(timeout=3_000)
            except PlaywrightTimeoutError:
                return True
        raise ValueError(
            f"Auth profile '{profile.name}' must define logged_in_selector or logged_out_selector."
        )

    def wait_until_authenticated(
        self,
        session: BrowserSession,
        profile: AuthProfileSpec,
    ) -> None:
        page = session.page
        page.goto(self.login_url(profile), wait_until="domcontentloaded")
        logged_in_selector = self.logged_in_selector(profile)
        logged_out_selector = self.logged_out_selector(profile)
        timeout_ms = profile.login_timeout_seconds * 1_000

        if logged_in_selector:
            page.locator(logged_in_selector).first.wait_for(state="visible", timeout=timeout_ms)
            return
        if logged_out_selector:
            page.locator(logged_out_selector).first.wait_for(state="detached", timeout=timeout_ms)
            return
        raise ValueError(
            f"Auth profile '{profile.name}' must define logged_in_selector or logged_out_selector."
        )


def build_auth_provider_registry() -> dict[str, AuthProvider]:
    providers = [
        AuthProvider(
            "generic",
            logged_in_selector="body",
        ),
        AuthProvider(
            "zhihu",
            base_url="https://www.zhihu.com/",
            login_url="https://www.zhihu.com/signin",
            logged_in_selector="button[aria-label='Open Profile Menu'], a[href='/creator']",
            logged_out_selector="input[name='username'], input[name='account']",
        ),
        AuthProvider(
            "bilibili",
            base_url="https://www.bilibili.com/",
            login_url="https://passport.bilibili.com/login",
            logged_in_selector=".header-avatar-wrap, .bili-avatar, a[href*='space.bilibili.com']",
            logged_out_selector="input[placeholder*='账号'], input[placeholder*='手机号']",
        ),
        AuthProvider(
            "infoq",
            base_url="https://www.infoq.cn/",
            login_url="https://www.infoq.cn/",
            logged_in_selector="a[href*='/profile/'], .user-avatar, .header-avatar",
            logged_out_selector="text=登录, text=注册",
        ),
    ]
    return {provider.name: provider for provider in providers}


class AuthManager:
    def __init__(self, settings: AutomationSettings) -> None:
        self.settings = settings
        self.logger = get_logger("playwright_shell.auth")
        self.providers = build_auth_provider_registry()

    def _auth_file(self) -> list[AuthProfileSpec]:
        auth_file = load_auth_file(self.settings.auth_file)
        return [profile for profile in auth_file.profiles if profile.enabled]

    def list_profiles(self) -> list[AuthProfileSpec]:
        return self._auth_file()

    def get_profile(self, profile_name: str) -> AuthProfileSpec:
        auth_file = load_auth_file(self.settings.auth_file)
        profile = auth_file.get_profile(profile_name)
        if not profile.enabled:
            raise ValueError(f"Auth profile '{profile_name}' is disabled.")
        return profile

    def get_provider(self, profile: AuthProfileSpec) -> AuthProvider:
        provider = self.providers.get(profile.provider)
        if provider is None:
            raise KeyError(f"Auth provider '{profile.provider}' is not registered.")
        return provider

    def auth_paths(self, profile_name: str) -> AuthPaths:
        slug = profile_name.replace("/", "_").replace(" ", "_")
        return AuthPaths(
            user_data_dir=self.settings.shared_user_data_dir,
            storage_state_path=self.settings.storage_states_dir / f"{slug}.json",
        )

    def browser_session_kwargs(self, profile_name: str | None) -> dict[str, Path | str]:
        if not profile_name:
            return {}
        profile = self.get_profile(profile_name)
        provider = self.get_provider(profile)
        paths = self.auth_paths(profile_name)
        return {
            "base_url": provider.base_url(profile),
            "user_data_dir": paths.user_data_dir,
            "storage_state_path": paths.storage_state_path,
        }

    def login(self, profile_name: str) -> Path:
        profile = self.get_profile(profile_name)
        provider = self.get_provider(profile)
        paths = self.auth_paths(profile_name)
        browser = BrowserSession(
            self.settings,
            base_url=provider.base_url(profile),
            user_data_dir=paths.user_data_dir,
        )
        browser.start()
        try:
            self.logger.info("waiting for manual login", extra={"profile": profile_name})
            provider.wait_until_authenticated(browser, profile)
            browser.save_storage_state(paths.storage_state_path)
            return paths.storage_state_path
        finally:
            browser.close()

    def is_authenticated(self, profile_name: str) -> bool:
        profile = self.get_profile(profile_name)
        provider = self.get_provider(profile)
        paths = self.auth_paths(profile_name)
        if not paths.user_data_dir.exists():
            return False

        browser = BrowserSession(
            self.settings,
            base_url=provider.base_url(profile),
            user_data_dir=paths.user_data_dir,
        )
        browser.start()
        try:
            return provider.is_authenticated(browser, profile)
        except PlaywrightTimeoutError:
            return False
        finally:
            browser.close()