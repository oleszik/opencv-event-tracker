"""Foreground-based moving-object detection."""

import cv2
import numpy as np

from .config import DetectionConfig
from .models import Detection


class MotionDetector:
    def __init__(self, config: DetectionConfig) -> None:
        self.config = config
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=config.history, varThreshold=config.threshold, detectShadows=True
        )

    def detect(self, frame: np.ndarray) -> tuple[list[Detection], np.ndarray]:
        blurred = cv2.GaussianBlur(frame, (self.config.blur_size, self.config.blur_size), 0)
        mask = self.subtractor.apply(blurred, learningRate=self.config.learning_rate)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=self.config.morph_iterations)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = [
            Detection(cv2.boundingRect(contour))
            for contour in contours
            if cv2.contourArea(contour) >= self.config.min_area
        ]
        return sorted(detections, key=lambda item: item.bbox[0]), mask
