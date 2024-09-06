"""Defines Base class for implementing Red Strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from cyberwheel.network import Host


class RedStrategy(ABC):
    """Base class for implementing Red strategies in a network security
    context.

    Subclasses should define specific strategies for selecting targets and
    computing reward maps.
    """

    @classmethod
    @abstractmethod
    def select_target(cls) -> Optional[Host]:
        """Selects a target host for the Red strategy.

        :return: The selected target host or None if no target is selected.
        """
        pass  # Abstract method, must be implemented by subclasses

    @classmethod
    @abstractmethod
    def get_reward_map(cls) -> Dict[str, Tuple[int, int]]:
        """Retrieves the reward map for the Red strategy.

        The reward map is a dictionary where the keys are strings representing
        specific criteria or actions, and the values are tuples containing
        reward and penalty values.

        :return: A dictionary mapping criteria/actions to (reward, penalty) tuples.
        """
        pass  # Abstract method, must be implemented by subclasses
