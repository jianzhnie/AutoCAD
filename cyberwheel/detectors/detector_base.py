from abc import ABC, abstractmethod
from typing import Iterable

from cyberwheel.detectors.alert import Alert


class Detector(ABC):
    """Abstract base class for defining detectors in the simulation.

    Detectors are responsible for observing and processing a sequence of
    alerts, performing some transformation or analysis on them, and
    returning the results.

    Attributes:
        name (str): The name of the detector. Default is 'Detector'.
    """

    name: str = 'Detector'

    def __init__(self) -> None:
        """Initializes the Detector.

        As an abstract class, it should not be instantiated directly. Instead,
        concrete subclasses should define the behavior for the `obs()` method.
        """
        super().__init__()

    @abstractmethod
    def obs(self, perfect_alerts: Iterable[Alert]) -> Iterable[Alert]:
        """Observes and processes a sequence of alerts.

        This method should be implemented by subclasses to define the
        specific transformation or analysis to be performed on the input
        alerts.

        Args:
            perfect_alerts (Iterable[Alert]): An iterable of `Alert` objects
            that the detector will process.

        Returns:
            Iterable[Alert]: The transformed or filtered sequence of alerts.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError('Subclasses must implement this method.')
