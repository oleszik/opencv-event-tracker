"""YAML configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised for invalid user configuration."""


@dataclass(slots=True)
class DetectionConfig:
    min_area: int = 500
    history: int = 200
    threshold: int = 20
    learning_rate: float = -1.0
    blur_size: int = 5
    morph_iterations: int = 2


@dataclass(slots=True)
class TrackingConfig:
    max_distance: float = 70.0
    max_missing_frames: int = 8
    history_length: int = 30


@dataclass(slots=True)
class EventsConfig:
    cooldown_seconds: float = 1.0
    screenshots: bool = True
    screenshot_types: list[str] = field(default_factory=lambda: ["zone_enter", "line_cross"])


@dataclass(slots=True)
class OutputConfig:
    directory: str = "output"
    save_video: bool = True
    save_events: bool = True
    csv: bool = False
    display: bool = False


@dataclass(slots=True)
class ZoneConfig:
    name: str
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(slots=True)
class LineConfig:
    name: str
    start: tuple[int, int]
    end: tuple[int, int]


@dataclass(slots=True)
class AppConfig:
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    events: EventsConfig = field(default_factory=EventsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    zones: list[ZoneConfig] = field(default_factory=list)
    lines: list[LineConfig] = field(default_factory=list)


def _section(data: dict[str, Any], name: str, cls: type[Any]) -> Any:
    raw = data.get(name, {})
    if not isinstance(raw, dict):
        raise ConfigError(f"'{name}' must be a mapping")
    try:
        return cls(**raw)
    except TypeError as exc:
        raise ConfigError(f"Invalid '{name}' settings: {exc}") from exc


def load_config(path: Path) -> AppConfig:
    if not path.is_file():
        raise ConfigError(f"Configuration file does not exist: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a mapping")
    try:
        zones = [ZoneConfig(**item) for item in data.get("zones", [])]
        lines = [
            LineConfig(item["name"], tuple(item["start"]), tuple(item["end"]))
            for item in data.get("lines", [])
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid zone or line configuration: {exc}") from exc
    config = AppConfig(
        detection=_section(data, "detection", DetectionConfig),
        tracking=_section(data, "tracking", TrackingConfig),
        events=_section(data, "events", EventsConfig),
        output=_section(data, "output", OutputConfig),
        zones=zones,
        lines=lines,
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.detection.min_area <= 0:
        raise ConfigError("detection.min_area must be greater than zero")
    if config.detection.blur_size < 1 or config.detection.blur_size % 2 == 0:
        raise ConfigError("detection.blur_size must be a positive odd integer")
    if config.tracking.max_distance <= 0 or config.tracking.max_missing_frames < 0:
        raise ConfigError("tracking distances must be positive and missing frames non-negative")
    if config.events.cooldown_seconds < 0:
        raise ConfigError("events.cooldown_seconds cannot be negative")
    names: set[str] = set()
    for zone in config.zones:
        if not zone.name or zone.name in names:
            raise ConfigError(f"Zone names must be non-empty and unique: {zone.name!r}")
        names.add(zone.name)
        if zone.x1 >= zone.x2 or zone.y1 >= zone.y2:
            raise ConfigError(f"Zone '{zone.name}' must have increasing coordinates")
    names.clear()
    for line in config.lines:
        if not line.name or line.name in names or line.start == line.end:
            raise ConfigError(f"Line names must be unique and endpoints distinct: {line.name!r}")
        names.add(line.name)
