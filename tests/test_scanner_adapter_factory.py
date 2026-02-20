"""Tests for jackai.scanner.adapter_factory."""

import pytest
from pathlib import Path

from jackai.models.config import TargetConfig, WebWidgetSelectors
from jackai.models.scanner import IdentifiedInteraction
from jackai.scanner.adapter_factory import (
    build_target_config_from_result,
    save_target_config,
    _safe_filename,
)


@pytest.fixture
def identified(web_widget_selectors: WebWidgetSelectors) -> IdentifiedInteraction:
    return IdentifiedInteraction(
        url="https://example.com/chat",
        widget_type="intercom",
        selectors=web_widget_selectors,
        confidence=0.9,
        frame=None,
    )


class TestBuildTargetConfigFromResult:
    def test_returns_target_config(self, identified: IdentifiedInteraction) -> None:
        config = build_target_config_from_result(
            identified, success=True, strategy_used="new_session"
        )
        assert isinstance(config, TargetConfig)
        assert config.adapter_type == "web_widget"
        assert config.url == identified.url
        assert config.selectors == identified.selectors
        assert config.recommended_context_strategy == "new_session"
        assert config.widget_type == "intercom"

    def test_name_derived_from_url_and_widget(self, identified: IdentifiedInteraction) -> None:
        config = build_target_config_from_result(
            identified, success=True, strategy_used="inject"
        )
        assert "example" in config.name or "discovered" in config.name
        assert config.recommended_context_strategy == "inject"

    def test_empty_strategy_uses_new_session(self, identified: IdentifiedInteraction) -> None:
        config = build_target_config_from_result(
            identified, success=False, strategy_used=""
        )
        assert config.recommended_context_strategy == "new_session"

    def test_custom_name(self, identified: IdentifiedInteraction) -> None:
        config = build_target_config_from_result(
            identified, success=True, strategy_used="new_session", name="my-target"
        )
        assert config.name == "my-target"


class TestSaveTargetConfig:
    def test_saves_yaml_file(
        self,
        identified: IdentifiedInteraction,
        tmp_config_dir: Path,
    ) -> None:
        config = build_target_config_from_result(
            identified, success=True, strategy_used="new_session"
        )
        path = save_target_config(config, config_dir=tmp_config_dir)
        assert Path(path).exists()
        assert path.endswith(".yaml") or "yaml" in path
        content = Path(path).read_text()
        assert "name" in content or "url" in content

    def test_creates_directory_if_missing(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "new" / "targets"
        config = TargetConfig(
            name="t",
            adapter_type="web_widget",
            url="https://x.com",
            selectors=WebWidgetSelectors(
                input_selector="#i",
                message_list_selector=".m",
            ),
        )
        path = save_target_config(config, config_dir=config_dir)
        assert config_dir.exists()
        assert Path(path).exists()

    def test_custom_filename(
        self,
        identified: IdentifiedInteraction,
        tmp_config_dir: Path,
    ) -> None:
        config = build_target_config_from_result(
            identified, success=True, strategy_used="new_session"
        )
        path = save_target_config(config, config_dir=tmp_config_dir, filename="custom.yaml")
        assert Path(path).name == "custom.yaml"
        assert Path(path).exists()


class TestSafeFilename:
    def test_safe_filename_domain(self) -> None:
        name = _safe_filename("https://sub.example.com/path", "intercom")
        assert "example" in name or "sub" in name
        assert " " not in name
        assert ".com" not in name or name.count(".") == 0  # domain dots replaced

    def test_safe_filename_widget_type(self) -> None:
        name = _safe_filename("https://x.com", "generic")
        assert "generic" in name or "discovered" in name
