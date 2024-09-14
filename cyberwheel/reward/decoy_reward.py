from enum import Enum
from typing import List, Tuple

from cyberwheel.reward.reward_base import (RecurringAction, Reward, RewardMap,
                                           calc_quadratic)


class ActionType(Enum):
    ADD = 1
    REMOVE = -1
    NO_CHANGE = 0


class DecoyReward(Reward):

    def __init__(
            self,
            red_rewards: RewardMap,
            blue_rewards: RewardMap,
            r: Tuple[int, int] = (0, 10),
            scaling_factor: float = 10.0,
    ) -> None:
        """Increases the negative reward if the number of recurring actions is
        less than `r[0]` or greater than `r[1]`. If this number falls within
        the range, the sum of the recurring rewards is calculated normally.
        Otherwise, the cost of these actions increases scaling based on how far
        it is from the range. This is meant to prevent two things:

        1. the agent always choosing to do nothing instead of deploying hosts.
        2. the agent spamming decoys (20 decoys on a network of a dozen or so hosts is a bit absurd)

        It is important to note that the number of recurring actions is not strictly bound to `range`. The agent could
        create fewer or more recurring actions.

        `scaling_factor` impacts how much being outside `r` affects the reward


        Initialize DecoyReward.

        :param red_rewards: Reward map for red team actions
        :param blue_rewards: Reward map for blue team actions
        :param r: Range for number of recurring actions
        :param scaling_factor: Factor to scale rewards outside the range
        """

        super().__init__(red_rewards, blue_rewards)
        self.blue_recurring_actions: List[RecurringAction] = []
        self.red_recurring_actions = List[Tuple[RecurringAction, bool]] = []
        self.range = r
        self.scaling_factor = scaling_factor

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: bool,
        blue_success: bool,
        red_action_alerted: bool,
    ) -> float:
        """Calculate the reward for a single action."""
        r = self.calculate_red_reward(red_action, red_success, red_action_alerted)
        b = self.calculate_blue_reward(blue_action, blue_success)
        return r + b + self.sum_recurring_blue() + self.sum_recurring_red()

    def calculate_red_reward(self, action: str, success: bool, alerted: bool) -> float:
        """Calculate the reward for a red team action."""
        if alerted:
            return abs(self.red_rewards[action][0]) * self.scaling_factor * 10
        return self.red_rewards[action][0] if success else 0

    def calculate_blue_reward(self, action: str, success: bool) -> float:
        """Calculate the reward for a blue team action."""
        return self.blue_rewards[action][0] if success else -100 * self.scaling_factor

    def sum_recurring_blue(self) -> float:
        """Calculate the sum of recurring blue actions rewards."""
        sum_reward = sum(
            self.blue_rewards[ra.action][1] for ra in self.blue_recurring_actions
        )

        num_actions = len(self.blue_recurring_actions)
        if num_actions > self.range[1]:
            sum_reward -= calc_quadratic(
                num_actions - self.range[1], a=self.scaling_factor
            )
        elif num_actions < self.range[0]:
            sum_reward -= calc_quadratic(
                self.range[0] - num_actions, a=self.scaling_factor
            )

        return sum_reward if num_actions > 0 else -100

    def sum_recurring_red(self) -> float:
        sum = 0
        for ra in self.red_recurring_actions:
            if ra[1]:
                sum -= self.red_rewards[
                    ra[0].action][1] * self.scaling_factor * 10
            else:
                sum += self.red_rewards[ra[0].action][1]
        return sum

    def add_recurring_blue_action(self, id: str, action: str) -> None:
        """Add a recurring blue action."""
        self.blue_recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_blue_action(self, name: str) -> None:
        """Remove a recurring blue action."""
        self.blue_recurring_actions = [
            ra for ra in self.blue_recurring_actions if ra.id != name
        ]

    def add_recurring_red_impact(self, red_action: str, is_decoy: bool) -> None:
        """Add a recurring red impact."""
        self.red_recurring_actions.append(
            (RecurringAction('', red_action), is_decoy))

    def handle_blue_action_output(
        self, blue_action: str, rec_id: str, success: bool, recurring: ActionType
    ) -> None:
        """Handle the output of a blue action."""
        if not success:
            return
        if recurring == ActionType.REMOVE:
            self.remove_recurring_blue_action(rec_id)
        elif recurring == ActionType.ADD:
            self.add_recurring_blue_action(rec_id, blue_action)
        elif recurring != ActionType.NO_CHANGE:
            raise ValueError('recurring must be either -1, 0, or 1')

    def handle_red_action_output(self, red_action: str, is_decoy: bool) -> None:
        """Handle the output of a red action."""
        if 'impact' in red_action.lower():
            self.add_recurring_red_impact(red_action.lower(), is_decoy)

    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_actions = []
