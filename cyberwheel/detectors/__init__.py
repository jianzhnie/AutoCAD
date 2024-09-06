from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector
from cyberwheel.detectors.handler import DetectorHandler
from cyberwheel.detectors.isolate_detector import IsolateDetector
from cyberwheel.detectors.probability_detector import ProbabilityDetector
from cyberwheel.detectors.example_detectors import (
    CoinFlipDetector,
    DecoyDetector,
    PerfectDetector,
)


__all__ = [
    "Alert",
    "Detector",
    "DetectorHandler",
    "IsolateDetector",
    "ProbabilityDetector",
    "CoinFlipDetector",
    "DecoyDetector",
    "PerfectDetector",
]

detetctor_maping = {
    "CoinFlipDetector": CoinFlipDetector,
    "DecoyDetector": DecoyDetector,
    "PerfectDetector": PerfectDetector,
}