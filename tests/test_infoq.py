"""Tests for InfoQ service layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from playwright_shell.services.infoq import InfoQService, InfoqArticle


class TestInfoqArticle:
    """Tests for InfoqArticle dataclass."""

    def test_article_creation(self) -> None:
        """Test creating an InfoqArticle instance."""
        article = InfoqArticle(
            title="Test Article",
            url="https://xie.infoq.cn/article/test-123",
            article_id="test-123",
            status="published",
            publish_time="2024-01-01",
        )
        assert article.title == "Test Article"
        assert article.url == "https://xie.infoq.cn/article/test-123"
        assert article.article_id == "test-123"
        assert article.status == "published"
        assert article.publish_time == "2024-01-01"

    def test_article_with_none_publish_time(self) -> None:
        """Test creating an InfoqArticle with None publish_time."""
        article = InfoqArticle(
            title="Test Article",
            url="https://xie.infoq.cn/article/test-123",
            article_id="test-123",
            status="draft",
            publish_time=None,
        )
        assert article.publish_time is None


class TestInfoQService:
    """Tests for InfoQService."""

    @pytest.fixture
    def service(self) -> InfoQService:
        """Create an InfoQService instance."""
        return InfoQService()

    @pytest.fixture
    def mock_page(self) -> MagicMock:
        """Create a mock Page."""
        return MagicMock()

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create a mock BrowserContext."""
        return MagicMock()

    def test_is_on_draft_page_true(self, service: InfoQService, mock_page: MagicMock) -> None:
        """Test is_on_draft_page returns True for draft URLs."""
        mock_page.url = "https://xie.infoq.cn/draft/abc123"
        assert service.is_on_draft_page(mock_page) is True

    def test_is_on_draft_page_false(self, service: InfoQService, mock_page: MagicMock) -> None:
        """Test is_on_draft_page returns False for non-draft URLs."""
        mock_page.url = "https://xie.infoq.cn/article/abc123"
        assert service.is_on_draft_page(mock_page) is False

    def test_is_on_publish_page_true(self, service: InfoQService, mock_page: MagicMock) -> None:
        """Test is_on_publish_page returns True for publish URLs."""
        mock_page.url = "https://xie.infoq.cn/"
        assert service.is_on_publish_page(mock_page) is True

    def test_is_on_publish_page_false_for_draft(
        self, service: InfoQService, mock_page: MagicMock
    ) -> None:
        """Test is_on_publish_page returns False for draft URLs."""
        mock_page.url = "https://xie.infoq.cn/draft/abc123"
        assert service.is_on_publish_page(mock_page) is False

    def test_is_on_publish_page_false_for_other(
        self, service: InfoQService, mock_page: MagicMock
    ) -> None:
        """Test is_on_publish_page returns False for non-InfoQ URLs."""
        mock_page.url = "https://example.com/"
        assert service.is_on_publish_page(mock_page) is False

    def test_find_draft_page_found(
        self, service: InfoQService, mock_context: MagicMock, mock_page: MagicMock
    ) -> None:
        """Test find_draft_page finds a draft page."""
        mock_page.url = "https://xie.infoq.cn/draft/abc123"
        mock_page.is_closed.return_value = False
        mock_context.pages = [mock_page]

        result = service.find_draft_page(mock_context)
        assert result == mock_page

    def test_find_draft_page_not_found(
        self, service: InfoQService, mock_context: MagicMock
    ) -> None:
        """Test find_draft_page returns None when no draft page exists."""
        mock_context.pages = []
        result = service.find_draft_page(mock_context)
        assert result is None

    def test_find_draft_page_skips_closed(
        self, service: InfoQService, mock_context: MagicMock, mock_page: MagicMock
    ) -> None:
        """Test find_draft_page skips closed pages."""
        mock_page.url = "https://xie.infoq.cn/draft/abc123"
        mock_page.is_closed.return_value = True
        mock_context.pages = [mock_page]

        result = service.find_draft_page(mock_context)
        assert result is None

    def test_find_publish_page_found(
        self, service: InfoQService, mock_context: MagicMock, mock_page: MagicMock
    ) -> None:
        """Test find_publish_page finds a publish page."""
        mock_page.url = "https://xie.infoq.cn/"
        mock_page.is_closed.return_value = False
        mock_context.pages = [mock_page]

        result = service.find_publish_page(mock_context)
        assert result == mock_page

    def test_draft_url_pattern_constant(self, service: InfoQService) -> None:
        """Test that DRAFT_URL_PATTERN is correctly defined."""
        assert service.DRAFT_URL_PATTERN == "xie.infoq.cn/draft/"

    def test_publish_url_constant(self, service: InfoQService) -> None:
        """Test that PUBLISH_URL is correctly defined."""
        assert service.PUBLISH_URL == "https://xie.infoq.cn/"


class TestInfoQServiceIntegration:
    """Integration-style tests with more complex mocking."""

    @pytest.fixture
    def service(self) -> InfoQService:
        """Create an InfoQService instance."""
        return InfoQService()

    def test_write_title_calls_fill(self, service: InfoQService) -> None:
        """Test write_title calls locator fill with correct value."""
        mock_page = MagicMock()
        mock_locator = MagicMock()
        mock_page.locator.return_value = mock_locator

        service.write_title(mock_page, "Test Title")

        mock_page.locator.assert_called_once_with("input.draft-title")
        mock_locator.fill.assert_called_once_with("Test Title")

    def test_write_body_calls_fill(self, service: InfoQService) -> None:
        """Test write_body clicks and fills the ProseMirror editor."""
        mock_page = MagicMock()
        mock_editor = MagicMock()
        mock_page.locator.return_value.first = mock_editor

        service.write_body(mock_page, "Test Body")

        mock_page.locator.assert_called_once_with("div.ProseMirror")
        mock_editor.click.assert_called_once()
        mock_editor.fill.assert_called_once_with("Test Body")

    def test_open_publish_dialog_clicks_submit(self, service: InfoQService) -> None:
        """Test open_publish_dialog clicks submit button."""
        mock_page = MagicMock()
        mock_dialog = MagicMock()
        mock_page.locator.side_effect = [MagicMock(), mock_dialog]

        service.open_publish_dialog(mock_page)

        # First call is .submit-btn click, second is .dialog-setting wait_for
        assert mock_page.locator.call_count >= 1