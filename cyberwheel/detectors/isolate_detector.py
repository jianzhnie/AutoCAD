from typing import Iterable, List

from cyberwheel.detectors.alert import Alert
from cyberwheel.detectors.detector_base import Detector


class IsolateDetector(Detector):
    """A detector that only generates alerts for hosts that access decoy hosts.

    This detector processes a sequence of alerts and filters out only those
    where the source host or destination host(s) are disconnected (i.e.,
    decoy hosts).

    Attributes:
        name (str): The name of the detector. Default is 'IsolateDetector'.
    """

    name: str = 'IsolateDetector'

    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        """Observes and filters alerts for hosts that interact with decoys.

        This method iterates over the given alerts and filters out alerts
        where either the source host or one of the destination hosts are
        marked as disconnected (indicating they are decoy hosts).

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            to be processed.

        Returns:
            List[Alert]: A list of alerts where interactions with decoys
            were detected.
        """
        alerts: List[Alert] = []

        for perfect_alert in perfect_alerts:
            # Check if the source host is disconnected (decoy)
            if perfect_alert.src_host.disconnected:
                alerts = [
                    perfect_alert
                ]  # Replace the list with a single alert if the source is a decoy
            else:
                # Check each destination host for disconnection
                for dst in perfect_alert.dst_hosts:
                    if dst.disconnected:
                        # Add an alert if the destination is a decoy
                        alerts.append(
                            Alert(perfect_alert.src_host, dst_hosts=[dst]))

        return alerts
