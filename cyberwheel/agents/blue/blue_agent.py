from abc import ABC, abstractmethod

from cyberwheel.reward import RewardMap


class BlueAgentResult:
    """Represents the result of a blue agent's action.

    Attributes:
        name (str): The name of the blue action executed.
        id (str): The ID for a recurring reward.
        success (bool): Whether the action successfully executed or not.
        recurring (int): An integer describing how this action affected recurring rewards.
                        -1 removes the reward.
                        0 has no effect.
                        1 adds a new reward.
    """

    def __init__(self, name: str, id: str, success: bool,
                 recurring: int) -> None:
        self.name = name
        self.id = id
        self.success = success
        self.recurring = recurring


class BlueAgent(ABC):
    """Abstract base class for blue agents.

    Blue agents are responsible for taking actions within the environment and
    receiving rewards.
    """

    def __init__(self) -> None:
        """Initializes the BlueAgent."""
        pass

    @abstractmethod
    def act(self) -> BlueAgentResult:
        """Executes an action and returns the result.

        Returns:
            BlueAgentResult: The result of the action.
        """
        pass

    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        """Retrieves the reward map associated with the blue agent.

        Returns:
            RewardMap: The reward map.
        """
        pass
