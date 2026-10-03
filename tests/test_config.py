from pathlib import Path

import pytest

from opencv_event_tracker.config import ConfigError, load_config


def test_demo_config_loads() -> None:
    config = load_config(Path("examples/demo.yaml"))
    assert config.zones[0].name == "center_zone"
    assert config.lines[0].start == (321, 40)


def test_invalid_config_has_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("detection:\n  min_area: 0\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="min_area"):
        load_config(path)


def test_missing_config() -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        load_config(Path("missing.yaml"))
