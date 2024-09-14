from dataclasses import dataclass
from enum import Enum
from typing import List, Union

from cyberwheel.reward.reward_base import RecurringAction, Reward, RewardMap


class RecurringActionType(Enum):
    ADD = 1
    REMOVE = -1
    NO_CHANGE = 0


@dataclass
class RecurringReward(Reward):

    def __init__(
        self,
        red_rewards: RewardMap,
        blue_rewards: RewardMap,
    ) -> None:
        super().__init__(red_rewards, blue_rewards)
        self.blue_recurring_actions: List[RecurringAction] = []
        self.red_recurring_actions: List[RecurringAction] = []

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: bool,
        blue_success: bool,
        decoy: bool,
    ) -> float:
        red_agent_reward = (self.red_rewards[red_action][0]
                            if red_success and not decoy else 50)
        blue_agent_reward = self.blue_rewards[blue_action][
            0] if blue_success else -100

        if len(self.blue_recurring_actions) < 1:
            blue_agent_reward -= 100

        reward = (red_agent_reward + blue_agent_reward +
                  self.sum_recurring_blue() + self.sum_recurring_red())

        return reward

    def sum_recurring_blue(self) -> Union[int, float]:
        reward = sum(self.blue_rewards[ra.action][1]
                     for ra in self.blue_recurring_actions)
        return reward

    def sum_recurring_red(self) -> Union[int, float]:
        sum = 0
        for ra in self.red_recurring_actions:
            if ra[1]:
                sum -= self.red_rewards[ra[0].action][1] * 10
            else:
                sum += self.red_rewards[ra[0].action][1]
        return sum

    def add_recurring_blue_action(self, id: str, action: str) -> None:
        self.blue_recurring_actions.append(RecurringAction(id, action))

    def remove_recurring_blue_action(self, name: str) -> None:
        self.blue_recurring_actions = [
            ra for ra in self.blue_recurring_actions if ra.id != name
        ]

    def add_recurring_red_impact(self, red_action, is_decoy) -> None:
        self.red_recurring_actions.append(
            (RecurringAction('', red_action), is_decoy))

    def handle_blue_action_output(
        self,
        blue_action: str,
        rec_id: str,
        success: bool,
        recurring: RecurringActionType,
    ) -> None:
        if not success:
            return

        if recurring == RecurringActionType.REMOVE:
            self.remove_recurring_blue_action(rec_id)
        elif recurring == RecurringActionType.ADD:
            self.add_recurring_blue_action(rec_id, blue_action)
        elif recurring == RecurringActionType.NO_CHANGE:
            raise ValueError(
                'Invalid recurring action type, recurring must be either -1, 0, or 1'
            )

    def handle_red_action_output(self, red_action: str,
                                 is_decoy: bool) -> None:
        if 'impact' in red_action.lower():
            self.add_recurring_red_impact(red_action.lower(), is_decoy)
        return

    def reset(self) -> None:
        self.blue_recurring_actions.clear()
        self.red_recurring_actions.clear()
