import random
from typing import Iterable, List

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector


class CoinFlipDetector(Detector):
    """A detector that randomly decides whether to keep all alerts or discard
    them based on a coin flip (50/50 chance).

    Attributes:
        name (str): The name of the detector. Default is 'CoinFlipDetector'.
    """

    name: str = 'CoinFlipDetector'

    def obs(self, perfect_alerts: Iterable[Alert]) -> List[Alert]:
        """Observes alerts and randomly decides to either return all or none of
        them.

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            representing perfect information.

        Returns:
            List[Alert]: All alerts if the coin flip is heads (1), or an empty
            list if tails (0).
        """
        flip = random.randint(0, 1)
        if flip:
            return list(perfect_alerts)
        return []


class DecoyDetector(Detector):
    """A detector that generates alerts only for hosts that interact with
    decoys.

    Attributes:
        name (str): The name of the detector. Default is 'DecoyDetector'.
    """

    name: str = 'DecoyDetector'

    def obs(self, perfect_alerts: Iterable[Alert]) -> List[Alert]:
        """Observes alerts and generates new alerts for actions where a host
        interacts with a decoy.

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            representing perfect information.

        Returns:
            List[Alert]: A list of alerts where the destination host is a decoy.
        """
        alerts: List[Alert] = [
            Alert(
                src_host=perfect_alert.src_host,
                dst_hosts=[host],
                services=perfect_alert.services,
            ) for perfect_alert in perfect_alerts
            for host in perfect_alert.dst_hosts if host.decoy
        ]
        return alerts


class PerfectDetector(Detector):
    """A detector that passes through all alerts without modification.

    Attributes:
        name (str): The name of the detector. Default is 'PerfectDetector'.
    """

    name: str = 'PerfectDetector'

    def obs(self, perfect_alerts: Iterable[Alert]) -> List[Alert]:
        """Observes and returns all alerts without filtering or modification.

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            representing perfect information.

        Returns:
            List[Alert]: A list containing all the alerts, unchanged.
        """
        return list(perfect_alerts)
