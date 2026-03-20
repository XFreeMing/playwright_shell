"""InfoQ CLI commands for article publishing operations."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from playwright_shell.config import AutomationSettings
from playwright_shell.logging_utils import configure_logging, get_logger
from playwright_shell.services.auth import AuthManager
from playwright_shell.services.browser import BrowserSession
from playwright_shell.services.infoq import InfoQService

infoq_app = typer.Typer(help="InfoQ article publishing commands.")


def build_settings() -> AutomationSettings:
    """Build automation settings."""
    return AutomationSettings()


def get_browser_session(
    settings: AutomationSettings,
    auth_profile: str | None,
    cdp_url: str | None,
) -> BrowserSession:
    """Create and start a browser session."""
    auth_manager = AuthManager(settings)
    browser_kwargs = auth_manager.browser_session_kwargs(auth_profile)
    if cdp_url:
        browser_kwargs["cdp_url"] = cdp_url
    browser = BrowserSession(settings, **browser_kwargs)
    browser.start()
    return browser


# Common options
AuthProfileOption = Annotated[
    str | None,
    typer.Option(
        "--auth-profile", "-p",
        help="Authentication profile name.",
    ),
]

CdpUrlOption = Annotated[
    str | None,
    typer.Option(
        "--cdp-url",
        help="CDP connection URL (default: http://127.0.0.1:9222).",
    ),
]

TabUrlOption = Annotated[
    str | None,
    typer.Option(
        "--tab-url",
        help="URL pattern to find an existing tab.",
    ),
]

JsonOption = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Output in JSON format.",
    ),
]

KeepOpenOption = Annotated[
    bool,
    typer.Option(
        "--keep-open",
        help="Keep browser open after command completes (CDP mode).",
    ),
]


@infoq_app.command("start-create")
def start_create(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = "https://xie.infoq.cn/",
    keep_open: KeepOpenOption = False,
) -> None:
    """Open the InfoQ publish page and click the '立即创作' button.

    This command opens a new draft editor tab.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)

        draft_page = service.start_create(publish_page)
        logger.info("draft page opened", extra={"url": draft_page.url})
        typer.echo(f"draft_url\t{draft_page.url}")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("write-title")
def write_title(
    title: str,
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article title in the draft editor.

    Use --tab-url to specify a URL pattern to find the draft tab.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.write_title(draft_page, title)
        logger.info("title written", extra={"title": title})
        typer.echo(f"title\t{title}")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("write-body")
def write_body(
    body: str,
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article body content in the draft editor.

    Use --tab-url to specify a URL pattern to find the draft tab.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.write_body(draft_page, body)
        logger.info("body written")
        typer.echo("body\twritten")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("open-publish-dialog")
def open_publish_dialog(
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Open the publish settings dialog in the draft editor."""
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.open_publish_dialog(draft_page)
        logger.info("publish dialog opened")
        typer.echo("dialog\topened")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("fill-summary")
def fill_summary(
    summary: str,
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Fill in the article summary in the publish dialog.

    The publish dialog must be open (run 'open-publish-dialog' first).
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.fill_summary(draft_page, summary)
        logger.info("summary written", extra={"summary": summary})
        typer.echo(f"summary\t{summary}")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("add-tag")
def add_tag(
    tag: str,
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    keep_open: KeepOpenOption = False,
) -> None:
    """Add a tag to the article in the publish dialog.

    The publish dialog must be open (run 'open-publish-dialog' first).
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.add_tag(draft_page, tag)
        logger.info("tag added", extra={"tag": tag})
        typer.echo(f"tag\t{tag}")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("confirm-publish")
def confirm_publish(
    tab_url: TabUrlOption = None,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
) -> None:
    """Confirm and submit the article for publishing.

    This command closes the browser session after completion.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        draft_page = service.find_draft_page(browser.context)
        if draft_page is None:
            raise RuntimeError("No draft page found. Run 'start-create' first.")

        service.confirm_publish(draft_page)
        logger.info("article published", extra={"url": draft_page.url})
        typer.echo(f"published\t{draft_page.url}")
    finally:
        browser.close()


@infoq_app.command("list-articles")
def list_articles(
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = "https://xie.infoq.cn/",
    json_output: JsonOption = False,
    keep_open: KeepOpenOption = False,
) -> None:
    """List published articles.

    Note: This command requires selector verification through page analysis.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)

        articles = service.list_articles(publish_page)
        logger.info("articles listed", extra={"count": len(articles)})

        if json_output:
            data = [
                {
                    "title": a.title,
                    "url": a.url,
                    "article_id": a.article_id,
                    "status": a.status,
                    "publish_time": a.publish_time,
                }
                for a in articles
            ]
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for article in articles:
                typer.echo(f"{article.article_id}\t{article.title}\t{article.status}")

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()


@infoq_app.command("delete-article")
def delete_article(
    article_id: str,
    auth_profile: AuthProfileOption = None,
    cdp_url: CdpUrlOption = None,
    target_url: str = "https://xie.infoq.cn/",
    keep_open: KeepOpenOption = False,
) -> None:
    """Delete an article by its ID.

    Note: This command requires selector verification through page analysis.
    """
    settings = build_settings()
    configure_logging(settings.log_level)
    logger = get_logger("playwright_shell.infoq")
    service = InfoQService()

    browser = get_browser_session(settings, auth_profile, cdp_url)
    try:
        publish_page = browser.open_page(target_url, reuse_current=True)
        service.wait_for_page_ready(publish_page)

        success = service.delete_article(publish_page, article_id)
        if success:
            logger.info("article deleted", extra={"article_id": article_id})
            typer.echo(f"deleted\t{article_id}")
        else:
            logger.warning("article not found or delete failed", extra={"article_id": article_id})
            typer.echo(f"not_found\t{article_id}", err=True)
            raise typer.Exit(1)

        if not keep_open:
            typer.echo("Use --keep-open to keep the browser session active.")
    finally:
        if not keep_open:
            browser.close()