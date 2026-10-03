"""Validated video capture and output writer helpers."""

from pathlib import Path

import cv2


class VideoError(RuntimeError):
    """Raised when video I/O cannot be initialized."""


def open_capture(input_path: Path | None, camera: int | None) -> tuple[cv2.VideoCapture, str]:
    if input_path is not None:
        if not input_path.is_file():
            raise VideoError(f"Input video does not exist: {input_path}")
        source: str | int = str(input_path)
        label = str(input_path)
    elif camera is not None:
        source = camera
        label = f"camera:{camera}"
    else:
        raise VideoError("Specify exactly one input source: --input or --camera")
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        capture.release()
        kind = "camera" if camera is not None else "video"
        raise VideoError(f"Unable to open {kind} source: {label}")
    return capture, label


def create_writer(path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps if fps > 0 else 25.0, (width, height)
    )
    if not writer.isOpened():
        writer.release()
        raise VideoError(f"Unable to create annotated video: {path}")
    return writer
