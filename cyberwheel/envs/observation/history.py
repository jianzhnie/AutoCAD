from typing import Dict, Iterable

import numpy as np

from cyberwheel.detectors.alert import Alert
from cyberwheel.envs.observation.observation import Observation
from cyberwheel.network import Host


class HistoryObservation(Observation):
    """A class for managing the observation vector based on historical alerts.

    Attributes:
        shape (int): The size of the observation vector.
        mapping (Dict[Host, int]): A mapping from Host objects to indices in the observation vector.
        obs_vec (np.ndarray): The observation vector that tracks the state of alerts.
    """

    def __init__(self, shape: int, mapping: Dict[Host, int]) -> None:
        """Initialize the HistoryObservation object.

        Args:
            shape (int): The size of the observation vector.
            mapping (Dict[Host, int]): A dictionary that maps Host objects to indices in the observation vector.
        """
        self.shape = shape
        self.mapping = mapping
        self.obs_vec = np.zeros(shape)

    def create_obs_vector(self, alerts: Iterable[Alert]) -> np.ndarray:
        """Create and update the observation vector based on the given alerts.

        Args:
            alerts (Iterable[Alert]): A collection of Alert objects to process.

        Returns:
            np.ndarray: The updated observation vector.
        """
        # Refresh the non-history portion of the obs_vec
        obs_length = len(self.obs_vec)
        barrier = obs_length // 2

        # Reset the first half of the observation vector
        self.obs_vec[:barrier] = 0

        for alert in alerts:
            alerted_host = alert.src_host
            # Ensure alerted_host is not None and exists in the mapping
            if alerted_host is not None and alerted_host.name in self.mapping:
                index = self.mapping[alerted_host.name]
                self.obs_vec[index] = 1
                self.obs_vec[index + barrier] = 1

        return self.obs_vec

    def reset_obs_vector(self) -> np.ndarray:
        """Reset the observation vector to its initial state.

        Returns:
            np.ndarray: The reset observation vector, filled with zeros.
        """
        self.obs_vec = np.zeros(self.shape)
        return self.obs_vec
