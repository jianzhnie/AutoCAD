from abc import ABC, abstractmethod
from typing import Iterable

import numpy as np

from cyberwheel.detectors.alert import Alert
from cyberwheel.network import Host, Network


class Observation(ABC):
    """A base class for converting detector-produced alerts into blue
    observations.

    This class can be extended to create different observation vectors based on
    the specific needs of the detection system.
    """

    def __init__(self) -> None:
        self.network: Network = None  # Placeholder for the network object

    @abstractmethod
    def create_obs_vector(self, alerts: Iterable[Alert]) -> np.ndarray:
        """Abstract method that maps alerts to the blue observation space
        represented by a vector.

        Args:
            alerts (Iterable[Alert]): An iterable of Alert objects.

        Returns:
            np.ndarray: The observation vector based on the alerts.
        """
        pass

    def reset_obs_vector(self) -> np.ndarray:
        """Resets the observation vector and returns the initial state
        observation.

        Returns:
            np.ndarray: The reset observation vector, filled with zeros.
        """
        if hasattr(self, 'observation_vector'):
            self.observation_vector.fill(0)
            return self.observation_vector
        else:
            raise NotImplementedError(
                'reset_obs_vector should be implemented by subclasses.')

    def set_network(self, network: Network) -> None:
        """Sets the network object for the observation class.

        Args:
            network (Network): The network object to be set.
        """
        self.network = network


class TestObservation(Observation):
    """A simple test observation class that creates an observation vector based
    on whether each host in the network is a destination of any alert."""

    def create_obs_vector(self, alerts: Iterable[Alert]) -> np.ndarray:
        """Creates the observation vector based on alerts. Each host in the
        network is checked to see if it is a destination host in any alert.

        Args:
            alerts (Iterable[Alert]): An iterable of Alert objects.

        Returns:
            np.ndarray: The observation vector indicating which hosts are alert destinations.
        """
        # Ensure that the network is set
        if self.network is None:
            raise ValueError(
                'Network must be set using set_network() before creating the observation vector.'
            )

        # Count the number of hosts in the network
        num_hosts = sum(
            isinstance(data_object, Host)
            for _, data_object in self.network.graph.nodes(data='data'))

        # Initialize the observation vector
        observation_vector = np.zeros(num_hosts, dtype=np.int8)

        # Iterate through hosts and check if they are destination hosts in any alert
        index = 0
        for _, data_object in self.network.graph.nodes(data='data'):
            if isinstance(data_object, Host):
                for alert in alerts:
                    if data_object in alert.dst_hosts:
                        observation_vector[index] = 1
                index += 1

        # Save the vector for potential reset
        self.observation_vector = observation_vector

        return observation_vector
