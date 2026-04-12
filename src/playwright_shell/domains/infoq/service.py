"""InfoQ service layer for article publishing operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Locator, Page


@dataclass(slots=True)
class InfoqArticle:
    """Represents an InfoQ article."""

    title: str
    url: str
    article_id: str
    status: str
    publish_time: str | None


class InfoQService:
    """Service for InfoQ article publishing operations."""

    DRAFT_URL_PATTERN = "xie.infoq.cn/draft/"
    PUBLISH_URL = "https://xie.infoq.cn/"

    def is_on_draft_page(self, page: Page) -> bool:
        """Check if the page is on the InfoQ draft editor."""
        return self.DRAFT_URL_PATTERN in page.url

    def is_on_publish_page(self, page: Page) -> bool:
        """Check if the page is on the InfoQ publish/listing page."""
        return "xie.infoq.cn" in page.url and self.DRAFT_URL_PATTERN not in page.url

    def find_draft_page(self, context: BrowserContext) -> Page | None:
        """Find an open draft page tab in the browser context."""
        for page in context.pages:
            if not page.is_closed() and self.is_on_draft_page(page):
                return page
        return None

    def find_publish_page(self, context: BrowserContext) -> Page | None:
        """Find an open publish/listing page tab in the browser context."""
        for page in context.pages:
            if not page.is_closed() and self.is_on_publish_page(page):
                return page
        return None

    def wait_for_page_ready(self, page: Page, timeout_ms: int = 10_000) -> None:
        """Wait for page to be ready for interaction."""
        page.wait_for_load_state("domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            pass

    def find_create_button(self, page: Page) -> Locator:
        """Find the '立即创作' (Create Now) button."""
        candidates = [
            page.locator(".main-sidebar .Button_button_3onsJ").filter(has_text="立即创作"),
            page.locator(".btns .Button_button_3onsJ").filter(has_text="立即创作"),
            page.locator("div[gk-button]").filter(has_text="立即创作"),
            page.get_by_text("立即创作", exact=True),
            page.get_by_role("button", name="立即创作"),
            page.get_by_role("link", name="立即创作"),
        ]

        for candidate in candidates:
            try:
                target = candidate.first
                target.wait_for(state="visible", timeout=5_000)
                disabled = target.get_attribute("disabled")
                classes = target.get_attribute("class") or ""
                if disabled is None and "disabled" not in classes:
                    return target
            except PlaywrightTimeoutError:
                continue

        raise RuntimeError("Could not find an enabled InfoQ '立即创作' button.")

    def start_create(self, publish_page: Page) -> Page:
        """Click the create button and return the new draft page."""
        context = publish_page.context
        before_pages = [p for p in context.pages if not p.is_closed()]
        create_button = self.find_create_button(publish_page)

        try:
            with context.expect_page(timeout=5_000) as page_info:
                create_button.click()
            draft_page = page_info.value
        except PlaywrightTimeoutError:
            create_button.click()
            publish_page.wait_for_timeout(2_000)
            after_pages = [p for p in context.pages if not p.is_closed()]
            new_pages = [p for p in after_pages if p not in before_pages]
            draft_page = next(
                (p for p in reversed(new_pages) if self.DRAFT_URL_PATTERN in p.url),
                None,
            )
            if draft_page is None:
                draft_page = next(
                    p for p in reversed(after_pages) if self.DRAFT_URL_PATTERN in p.url
                )

        draft_page.bring_to_front()
        self._wait_for_draft_page(draft_page)
        return draft_page

    def _wait_for_draft_page(self, page: Page, max_attempts: int = 30) -> None:
        """Wait for draft page to navigate to correct URL."""
        for _ in range(max_attempts):
            if self.DRAFT_URL_PATTERN in page.url:
                page.wait_for_load_state("domcontentloaded")
                return
            page.wait_for_timeout(500)
        raise RuntimeError(f"InfoQ draft tab did not navigate to a draft URL: {page.url}")

    def write_title(self, draft_page: Page, title: str) -> None:
        """Fill in the article title."""
        title_input = draft_page.locator("input.draft-title")
        title_input.fill(title)

    def write_body(self, draft_page: Page, body: str) -> None:
        """Fill in the article body content."""
        editor = draft_page.locator("div.ProseMirror").first
        editor.click()
        editor.fill(body)
        draft_page.wait_for_timeout(500)

    def open_publish_dialog(self, draft_page: Page) -> None:
        """Open the publish settings dialog."""
        draft_page.locator(".submit-btn").click()
        draft_page.locator(".dialog-setting").wait_for(state="visible", timeout=10_000)

    def fill_summary(self, draft_page: Page, summary: str) -> None:
        """Fill in the article summary in the publish dialog."""
        dialog = draft_page.locator(".dialog-setting")
        dialog.wait_for(state="visible", timeout=10_000)
        summary_box = dialog.locator("textarea").first
        summary_box.click()
        summary_box.fill(summary)

    def add_tag(self, draft_page: Page, tag: str) -> None:
        """Add a tag in the publish dialog."""
        dialog = draft_page.locator(".dialog-setting")
        dialog.wait_for(state="visible", timeout=10_000)
        tag_input = dialog.locator("input[placeholder='输入标签，回车创建']").first
        tag_input.click()
        tag_input.fill(tag)
        tag_input.press("Enter")

        # Wait for tag to be confirmed (input cleared)
        for _ in range(10):
            current_value = tag_input.input_value().strip()
            if current_value == "":
                return
            tag_input.press("Enter")
            draft_page.wait_for_timeout(200)

        raise RuntimeError(f"Could not confirm InfoQ tag creation for: {tag}")

    def confirm_publish(self, draft_page: Page) -> None:
        """Confirm and submit the article for publishing."""
        dialog = draft_page.locator(".dialog-setting")
        dialog.wait_for(state="visible", timeout=10_000)
        confirm_button = dialog.locator(".dialog-footer-buttons .Button_button_3onsJ").filter(
            has_text="确定"
        )
        confirm_button.first.click()
        dialog.wait_for(state="hidden", timeout=10_000)

    def get_publish_dialog(self, draft_page: Page) -> Locator:
        """Get the publish dialog locator."""
        return draft_page.locator(".dialog-setting")

    def list_articles(self, publish_page: Page) -> list[InfoqArticle]:
        """List published articles from the publish page.

        Note: This method requires selector verification through page analysis.
        The current implementation uses common patterns but may need adjustment.
        """
        self.wait_for_page_ready(publish_page)

        articles: list[InfoqArticle] = []
        # Common article list item patterns
        article_items = publish_page.locator(
            "[class*='article-item'], [class*='articleItem'], .article-list li, .list-item"
        )

        try:
            article_items.first.wait_for(state="visible", timeout=5_000)
        except PlaywrightTimeoutError:
            return articles

        count = article_items.count()
        for i in range(count):
            item = article_items.nth(i)
            try:
                # Try to extract article info
                title_el = item.locator("a[href*='/article/'], h2 a, h3 a, .title a").first
                title = title_el.inner_text(timeout=1_000).strip()
                url = title_el.get_attribute("href") or ""

                # Extract article ID from URL
                article_id = ""
                if "/article/" in url:
                    article_id = url.split("/article/")[-1].split("?")[0]
                elif "/a/" in url:
                    article_id = url.split("/a/")[-1].split("?")[0]

                # Try to get status
                status_el = item.locator("[class*='status'], .status, .tag").first
                try:
                    status = status_el.inner_text(timeout=1_000).strip()
                except PlaywrightTimeoutError:
                    status = "published"

                # Try to get publish time
                time_el = item.locator("time, .time, [class*='date']").first
                try:
                    publish_time = time_el.inner_text(timeout=1_000).strip()
                except PlaywrightTimeoutError:
                    publish_time = None

                articles.append(InfoqArticle(
                    title=title,
                    url=url,
                    article_id=article_id,
                    status=status,
                    publish_time=publish_time,
                ))
            except PlaywrightTimeoutError:
                continue

        return articles

    def delete_article(self, publish_page: Page, article_id: str) -> bool:
        """Delete an article by its ID.

        Note: This method requires selector verification through page analysis.
        The current implementation uses common patterns but may need adjustment.
        """
        self.wait_for_page_ready(publish_page)

        # Try to find the article item by ID
        article_item = publish_page.locator(
            f"a[href*='{article_id}'], [data-id='{article_id}']"
        ).first

        try:
            article_item.wait_for(state="visible", timeout=5_000)
        except PlaywrightTimeoutError:
            return False

        # Find the parent article item container
        xpath = (
            "ancestor::*[contains(@class, 'article-item') "
            "or contains(@class, 'articleItem') or self::li]"
        )
        container = article_item.locator(f"xpath={xpath}").first

        # Try to find and click delete button
        delete_button = container.locator(
            "button:has-text('删除'), a:has-text('删除'), [class*='delete']"
        ).first

        try:
            delete_button.wait_for(state="visible", timeout=2_000)
            delete_button.click()

            # Handle confirmation dialog if present
            confirm_dialog = publish_page.locator(".dialog, .modal, [role='dialog']").first
            try:
                confirm_dialog.wait_for(state="visible", timeout=2_000)
                confirm_button = confirm_dialog.locator(
                    "button:has-text('确定'), button:has-text('确认'), button:has-text('删除')"
                ).first
                confirm_button.click()
                confirm_dialog.wait_for(state="hidden", timeout=5_000)
            except PlaywrightTimeoutError:
                pass

            return True
        except PlaywrightTimeoutError:
            return False