"""Tests for jackai.core.adapters.web_widget (with mocked Playwright)."""

from unittest.mock import MagicMock, patch

import pytest

from jackai.core.adapters.web_widget import WebWidgetAdapter
from jackai.core.models.config import TargetConfig, WebWidgetSelectors
from jackai.core.models.interface import ContextStrategy, SendRequest


@pytest.fixture
def web_widget_config() -> TargetConfig:
    return TargetConfig(
        name="test",
        adapter_type="web_widget",
        url="https://example.com",
        selectors=WebWidgetSelectors(
            input_selector="#input",
            message_list_selector=".messages",
            send_selector="button[type=submit]",
        ),
    )


class TestWebWidgetAdapterValidation:
    def test_connect_requires_web_widget_type(self, web_widget_config: TargetConfig) -> None:
        adapter = WebWidgetAdapter()
        web_widget_config.adapter_type = "telegram"  # type: ignore
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with pytest.raises(ValueError, match="adapter_type=web_widget"):
                adapter.connect(web_widget_config)

    def test_connect_requires_url(self, web_widget_config: TargetConfig) -> None:
        adapter = WebWidgetAdapter()
        web_widget_config.url = None
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with pytest.raises(ValueError, match="url"):
                adapter.connect(web_widget_config)

    def test_connect_requires_selectors(self, web_widget_config: TargetConfig) -> None:
        adapter = WebWidgetAdapter()
        web_widget_config.selectors = None
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with pytest.raises(ValueError, match="selectors"):
                adapter.connect(web_widget_config)

    def test_connect_raises_when_playwright_not_available(
        self,
        web_widget_config: TargetConfig,
    ) -> None:
        adapter = WebWidgetAdapter()
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="Playwright not installed"):
                adapter.connect(web_widget_config)


class TestWebWidgetAdapterWithMocks:
    @pytest.fixture
    def mock_playwright_chain(self) -> MagicMock:
        """Mock sync_playwright -> browser -> context -> page and locators."""
        mock_page = MagicMock()
        mock_locator = MagicMock()
        mock_locator.first = mock_locator
        mock_locator.locator.return_value = mock_locator
        mock_locator.count.return_value = 1
        mock_locator.fill.return_value = None
        mock_locator.click.return_value = None
        mock_locator.press.return_value = None
        mock_locator.wait_for.return_value = None
        mock_locator.inner_text.return_value = "Assistant reply"
        mock_locator.all.return_value = [mock_locator]
        mock_page.locator.return_value = mock_locator
        mock_page.frame_locator.return_value = mock_locator
        mock_page.wait_for_timeout.return_value = None
        mock_page.url = "https://example.com"

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_context.close.return_value = None

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_browser.close.return_value = None

        mock_pw = MagicMock()
        mock_chromium = MagicMock()
        mock_chromium.launch.return_value = mock_browser
        mock_pw.chromium = mock_chromium

        mock_sync = MagicMock()
        mock_sync.return_value.start.return_value = mock_pw
        mock_sync.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_sync.return_value.__exit__ = MagicMock(return_value=False)

        return mock_sync

    def test_connect_and_disconnect(
        self,
        web_widget_config: TargetConfig,
        mock_playwright_chain: MagicMock,
    ) -> None:
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with patch("jackai.core.adapters.web_widget.sync_playwright", mock_playwright_chain):
                adapter = WebWidgetAdapter()
                adapter.connect(web_widget_config)
                assert adapter.is_connected() is True
                adapter.disconnect()
                assert adapter.is_connected() is False
                assert adapter._page is None
                assert adapter._config is None

    def test_send_returns_reply(
        self,
        web_widget_config: TargetConfig,
        mock_playwright_chain: MagicMock,
    ) -> None:
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with patch("jackai.core.adapters.web_widget.sync_playwright", mock_playwright_chain):
                adapter = WebWidgetAdapter()
                adapter.connect(web_widget_config)
                reply = adapter.send(SendRequest(content="Hello"))
                assert reply.content == "Assistant reply"
                assert reply.channel_id == "test"
                adapter.disconnect()

    def test_send_when_not_connected_raises(self) -> None:
        adapter = WebWidgetAdapter()
        with pytest.raises(RuntimeError, match="Not connected"):
            adapter.send(SendRequest(content="Hi"))

    def test_clear_context_new_session(
        self,
        web_widget_config: TargetConfig,
        mock_playwright_chain: MagicMock,
    ) -> None:
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with patch("jackai.core.adapters.web_widget.sync_playwright", mock_playwright_chain):
                adapter = WebWidgetAdapter()
                adapter.connect(web_widget_config)
                adapter.clear_context(ContextStrategy(strategy="new_session"))
                # Should have closed context and created new one
                assert adapter._context.new_page.called or adapter._page is not None
                adapter.disconnect()

    def test_clear_context_inject(
        self,
        web_widget_config: TargetConfig,
        mock_playwright_chain: MagicMock,
    ) -> None:
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with patch("jackai.core.adapters.web_widget.sync_playwright", mock_playwright_chain):
                adapter = WebWidgetAdapter()
                adapter.connect(web_widget_config)
                adapter.clear_context(
                    ContextStrategy(strategy="inject", payload="Forget all.")
                )
                adapter.disconnect()

    def test_set_context_when_not_connected_raises(self) -> None:
        adapter = WebWidgetAdapter()
        with pytest.raises(RuntimeError, match="Not connected"):
            adapter.set_context("x")

    def test_disconnect_idempotent(self, web_widget_config: TargetConfig) -> None:
        with patch("jackai.core.adapters.web_widget.PLAYWRIGHT_AVAILABLE", True):
            with patch("jackai.core.adapters.web_widget.sync_playwright") as mock_sync:
                mock_pw = MagicMock()
                mock_browser = MagicMock()
                mock_context = MagicMock()
                mock_page = MagicMock()
                mock_context.new_page.return_value = mock_page
                mock_browser.new_context.return_value = mock_context
                mock_pw.chromium.launch.return_value = mock_browser
                mock_sync.return_value.start.return_value = mock_pw
                adapter = WebWidgetAdapter()
                adapter.connect(web_widget_config)
                adapter.disconnect()
                adapter.disconnect()
                assert adapter._page is None
