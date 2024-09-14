from abc import ABC, abstractmethod
from typing import Dict, NewType, Tuple, Union

RewardMap = NewType("RewardMap", Dict[str, Tuple[Union[int, float], Union[int, float]]])


def calc_quadratic(x: float, a: float = 0.0, b: float = 0.0, c: float = 0.0) -> float:
    return a * x**2 + b * x + c


class RecurringAction:
    def __init__(self, id: str, action: str) -> None:
        self.id = id
        self.action = action


class Reward(ABC):
    def __init__(self, red_rewards: RewardMap, blue_rewards: RewardMap) -> None:
        self.red_rewards = red_rewards
        self.blue_rewards = blue_rewards

    @abstractmethod
    def calculate_reward(self) -> Union[int, float]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass
