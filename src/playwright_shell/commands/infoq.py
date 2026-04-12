"""InfoQ CLI commands for article publishing operations."""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Annotated

import typer
from playwright.sync_api import Page

from playwright_shell.config import AutomationSettings
from playwright_shell.logging_utils import configure_logging, get_logger
from playwright_shell.services.auth import AuthManager
from playwright_shell.services.browser import BrowserSession
from playwright_shell.services.infoq import InfoQService

infoq_app = typer.Typer(help="InfoQ article publishing commands.")

# -- Common options ------------------------------------------------------------

AuthProfileOption = Annotated[
    str | None,
    typer.Option("--auth-profile", "-p", help="Authentication profile name."),
]

CdpUrlOption = Annotated[
    str | None,
    typer.Option("--cdp-url", help="CDP connection URL (default: http://127.0.0.1:9222)."),
]

JsonOption = Annotated[
    bool,
    typer.Option("--json", help="Output in JSON format."),
]

KeepOpenOption = Annotated[
    bool,
    typer.Option("--keep-open", help="Keep browser open after command completes (CDP mode)."),
]

_TARGET_URL_DEFAULT = "https://xie.infoq.cn/"


# -- Helpers -------------------------------------------------------------------

def _build_settings() -> AutomationSettings:
    return AutomationSettings()


def _create_browser(
    settings: AutomationSettings,
    auth_profile: str | None,
    cdp_url: str | None,
) -> BrowserSession:
    auth_manager = AuthManager(settings)
    browser_kwargs = auth_manager.browser_session_kwargs(auth_profile)
    if cdp_url:
        browser_kwargs["cdp_url"] = cdp_url
    browser = BrowserSession(settings, **browser_kwargs)
    browser.start()
    return browser


@contextmanager
def _infoq_browser(auth_profile: str | None, cdp_url: str | None, *, keep_open: bool = False):
    """Create browser session, run command, handle cleanup and keep-open hint."""
    settings = _build_settings()
    configure_logging(settings.log_level)
    browser = _create_browser(settings, auth_profile, cdp_url)
    try:
        yield browser, settings
    finally:
        if keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
        else:
            browser.close()


def _require_draft_page(browser: BrowserSession) -> Page:
    """Find the draft page or raise a helpful error."""
    service = InfoQService()
    page = service.find_draft_page(browser.context)
    if page is None:
        raise RuntimeError("No draft page found. Run 'start-create' first.")
    return page


# -- Commands ------------------------------------------------------------------

@infoq_app.command("start-create")
def start_create(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = _TARGET_URL_DEFAULT,
    keep_open: KeepOpenOption = False,
) -> None:
    """Open the InfoQ publish page and click the '立即创作' button.

    This command opens a new draft editor tab.
    """
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        service = InfoQService()
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)
        draft_page = service.start_create(publish_page)
        logger = get_logger("playwright_shell.infoq")
        logger.info("draft page opened", extra={"url": draft_page.url})
        typer.echo(f"draft_url\t{draft_page.url}")


@infoq_app.command("write-title")
def write_title(
    title: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article title in the draft editor."""
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.write_title(draft_page, title)
        get_logger("playwright_shell.infoq").info("title written", extra={"title": title})
        typer.echo(f"title\t{title}")


@infoq_app.command("write-body")
def write_body(
    body: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article body content in the draft editor."""
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.write_body(draft_page, body)
        get_logger("playwright_shell.infoq").info("body written")
        typer.echo("body\twritten")


@infoq_app.command("open-publish-dialog")
def open_publish_dialog(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Open the publish settings dialog in the draft editor."""
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.open_publish_dialog(draft_page)
        get_logger("playwright_shell.infoq").info("publish dialog opened")
        typer.echo("dialog\topened")


@infoq_app.command("fill-summary")
def fill_summary(
    summary: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article summary in the publish dialog.

    The publish dialog must be open (run 'open-publish-dialog' first).
    """
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.fill_summary(draft_page, summary)
        get_logger("playwright_shell.infoq").info("summary written", extra={"summary": summary})
        typer.echo(f"summary\t{summary}")


@infoq_app.command("add-tag")
def add_tag(
    tag: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Add a tag to the article in the publish dialog.

    The publish dialog must be open (run 'open-publish-dialog' first).
    """
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.add_tag(draft_page, tag)
        get_logger("playwright_shell.infoq").info("tag added", extra={"tag": tag})
        typer.echo(f"tag\t{tag}")


@infoq_app.command("confirm-publish")
def confirm_publish(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
) -> None:
    """Confirm and submit the article for publishing.

    This command closes the browser session after completion.
    """
    with _infoq_browser(auth_profile, cdp_url, keep_open=False) as (browser, _):
        draft_page = _require_draft_page(browser)
        service = InfoQService()
        service.confirm_publish(draft_page)
        logger = get_logger("playwright_shell.infoq")
        logger.info("article published", extra={"url": draft_page.url})
        typer.echo(f"published\t{draft_page.url}")


@infoq_app.command("list-articles")
def list_articles(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = _TARGET_URL_DEFAULT,
    json_output: JsonOption = False,
    keep_open: KeepOpenOption = False,
) -> None:
    """List published articles."""
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        service = InfoQService()
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)
        articles = service.list_articles(publish_page)
        get_logger("playwright_shell.infoq").info("articles listed", extra={"count": len(articles)})

        if json_output:
            typer.echo(json.dumps(
                [
                    {
                        "title": a.title,
                        "url": a.url,
                        "article_id": a.article_id,
                        "status": a.status,
                        "publish_time": a.publish_time,
                    }
                    for a in articles
                ],
                ensure_ascii=False,
                indent=2,
            ))
        else:
            for article in articles:
                typer.echo(f"{article.article_id}\t{article.title}\t{article.status}")


@infoq_app.command("delete-article")
def delete_article(
    article_id: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = _TARGET_URL_DEFAULT,
    keep_open: KeepOpenOption = False,
) -> None:
    """Delete an article by its ID."""
    with _infoq_browser(auth_profile, cdp_url, keep_open=keep_open) as (browser, _):
        service = InfoQService()
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)

        logger = get_logger("playwright_shell.infoq")
        success = service.delete_article(publish_page, article_id)
        if success:
            logger.info("article deleted", extra={"article_id": article_id})
            typer.echo(f"deleted\t{article_id}")
        else:
            logger.warning("article not found or delete failed",
                           extra={"article_id": article_id})
            typer.echo(f"not_found\t{article_id}", err=True)
            raise typer.Exit(1)
