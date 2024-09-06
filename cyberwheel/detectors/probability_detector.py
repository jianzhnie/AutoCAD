import random
from typing import Dict, Iterable, List

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector
from cyberwheel.utils.file_utils import read_detector_yaml


class ProbabilityDetector(Detector):
    """A detector that identifies techniques with a certain probability of
    success.

    The detection probabilities for different techniques are defined in a YAML
    file. Based on these probabilities, the detector decides whether or not to
    generate an alert for a specific action.

    Attributes:
        name (str): The name of the detector. Default is 'ProbabilityDetector'.
        technique_probabilities (Dict[str, float]): A dictionary mapping techniques
        to their probabilities of detection.
    """

    name: str = 'ProbabilityDetector'

    def __init__(self, config: str) -> None:
        """Initializes the ProbabilityDetector with the detection probabilities
        from the YAML file.

        Args:
            config (str): The path to the YAML configuration file containing
            technique probabilities.
        """
        self.technique_probabilities: Dict[str,
                                           float] = read_detector_yaml(config)

    def obs(self, perfect_alerts: Iterable[Alert]) -> List[Alert]:
        """Observes and processes alerts, generating new alerts based on
        detection probabilities for specific techniques.

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            representing perfect information.

        Returns:
            List[Alert]: A list of alerts where actions were detected based on
            their associated techniques and probabilities.
        """
        alerts: List[Alert] = []

        for perfect_alert in perfect_alerts:
            for dst in perfect_alert.dst_hosts:
                detection_failed = True

                # If no techniques are defined in the YAML file, skip detection
                if not self.technique_probabilities:
                    continue

                # Identify techniques used in the alert that this detector supports
                techniques = set(perfect_alert.techniques) & set(
                    self.technique_probabilities.keys())

                # Check each technique to see if the action is detected based on probability
                for technique in techniques:
                    detection_probability = float(
                        self.technique_probabilities[technique])

                    # Determine if detection is successful based on probability
                    if random.random() <= detection_probability:
                        detection_failed = False
                        break  # Stop checking once detection is successful for any technique

                # If detection failed for all techniques, skip this alert
                if detection_failed:
                    continue

                # Generate a new alert if detection was successful
                new_alert = Alert(
                    src_host=perfect_alert.src_host,
                    dst_hosts=[dst],
                    services=perfect_alert.services,
                )
                alerts.append(new_alert)

        return alerts
