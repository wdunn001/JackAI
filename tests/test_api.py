"""Tests for FastAPI routes (jackai.api.app)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from jackai.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


class TestGetTargets:
    def test_get_targets_returns_list(self, client: TestClient) -> None:
        r = client.get("/api/targets")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_get_targets_empty_when_no_config(self, client: TestClient) -> None:
        r = client.get("/api/targets")
        assert r.status_code == 200
        assert r.json() == []


class TestChannels:
    def test_get_channels_returns_list(self, client: TestClient) -> None:
        r = client.get("/api/channels")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_connect_404_when_target_not_found(self, client: TestClient) -> None:
        r = client.post("/api/channels/nonexistent/connect")
        assert r.status_code == 404

    def test_disconnect_no_op_when_not_connected(self, client: TestClient) -> None:
        r = client.post("/api/channels/any/disconnect")
        assert r.status_code == 200

    def test_chat_returns_empty_replies_when_none_connected(self, client: TestClient) -> None:
        r = client.post("/api/chat", json={"channel_ids": ["x"], "message": "hi"})
        assert r.status_code == 200
        assert r.json()["replies"] == []


class TestScanScrape:
    def test_scrape_requires_seeds(self, client: TestClient) -> None:
        r = client.post("/api/scan/scrape", json={})
        assert r.status_code == 422  # validation error

    def test_scrape_returns_urls(self, client: TestClient) -> None:
        r = client.post(
            "/api/scan/scrape",
            json={"seeds": ["https://example.com"], "crawl_depth": 0, "use_sitemap": False},
        )
        assert r.status_code == 200
        data = r.json()
        assert "urls" in data
        assert isinstance(data["urls"], list)
        assert len(data["urls"]) >= 1

    def test_scrape_multiple_seeds(self, client: TestClient) -> None:
        r = client.post(
            "/api/scan/scrape",
            json={"seeds": ["https://example.com", "https://example.org"]},
        )
        assert r.status_code == 200
        assert len(r.json()["urls"]) >= 2


class TestScanIdentify:
    def test_identify_with_url(self, client: TestClient) -> None:
        r = client.post("/api/scan/identify", json={"url": "https://example.com"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_identify_with_urls(self, client: TestClient) -> None:
        r = client.post(
            "/api/scan/identify",
            json={"urls": ["https://example.com"]},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_identify_missing_body_returns_400(self, client: TestClient) -> None:
        r = client.post("/api/scan/identify", json={})
        assert r.status_code == 400


class TestScanTestWipe:
    def test_test_wipe_accepts_identified_interaction(self, client: TestClient) -> None:
        body = {
            "url": "https://example.com",
            "widget_type": "generic",
            "selectors": {
                "input_selector": "#input",
                "message_list_selector": ".messages",
                "send_selector": "button[type=submit]",
            },
            "confidence": 0.8,
            "frame": None,
        }
        r = client.post("/api/scan/test-wipe", json=body)
        # May 200 with result or 500 if Playwright fails
        assert r.status_code in (200, 500)
        if r.status_code == 200:
            data = r.json()
            assert "identified" in data
            assert "success" in data
            assert "strategy_used" in data
            assert "target_config" in data


class TestScanFull:
    def test_full_requires_seeds(self, client: TestClient) -> None:
        r = client.post("/api/scan/full", json={})
        assert r.status_code == 400

    def test_full_with_seeds_returns_results(self, client: TestClient) -> None:
        r = client.post(
            "/api/scan/full",
            json={"seeds": ["https://example.com"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "target_configs" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["target_configs"], list)


class TestScanSaveTarget:
    def test_save_target_accepts_config(self, tmp_path: Path) -> None:
        from jackai.infrastructure.tinydb_repositories import TinyDBTargetRepository
        db_path = tmp_path / "test.json"
        repo = TinyDBTargetRepository(db_path)
        with (
            patch("jackai.core.config_loader.get_target_repository", return_value=repo),
            patch("jackai.scanner.adapter_factory.get_target_repository", return_value=repo),
        ):
            app = create_app()
            c = TestClient(app)
            body = {
                "name": "test-save",
                "adapter_type": "web_widget",
                "url": "https://example.com",
                "selectors": {
                    "input_selector": "#i",
                    "message_list_selector": ".m",
                },
                "recommended_context_strategy": "new_session",
                "widget_type": "generic",
            }
            r = c.post("/api/scan/save-target", json=body)
        assert r.status_code == 200
        data = r.json()
        assert data["saved"] == "test-save"
        assert "targets" in data
        assert any(t.get("name") == "test-save" for t in data["targets"])
