from cyberwheel.reward.recurring_reward import RecurringReward
from cyberwheel.reward.reward_base import RewardMap


class StepDetectedReward(RecurringReward):
    """这段代码定义了一个名为StepDetectedReward的类， 用于计算蓝队(防御方)在检测到红队(攻击方)行动时的奖励."""

    def __init__(
        self,
        blue_rewards: RewardMap,
        max_steps: int,
    ) -> None:
        """Increases the reward the earlier that the red agent is detected. So
        the best reward it can get is one in which the blue agent immediately
        detects the red agent's actions. The worst reward it can get is one in
        which the blue agent detects the red agent at the final step of the
        episode.

        Reward Function: max_steps / n, where n is the number of steps
        """
        self.reward_function = max_steps * 10
        self.min_decoys = 1
        self.decoy_penalty = -100
        self.initial_step = float('inf')

        super().__init__(
            red_rewards={},
            blue_rewards=blue_rewards,
        )

    def calculate_reward(self, red_action_alerted: bool,
                         step_detected: int) -> float:
        """
        - 如果检测到红队行动且当前步骤小于之前记录的步骤,更新step_detected并计算奖励。
        - 如果蓝队没有部署至少一个防御措施,则给予 -100 的惩罚。
        - 最后加上蓝队的循环行动奖励。

        Args:
            red_action_alerted (bool): 是否检测到红队行动
            step_detected (int): 当前步骤

        Returns:
            float: 奖励
        """
        reward = 0
        if red_action_alerted and step_detected < self.step_detected:
            self.step_detected = step_detected
            reward += self.reward_function / self.step_detected

        # Should deploy at least 1 decoy
        if len(self.blue_recurring_actions) < self.min_decoys:
            reward += self.decoy_penalty
        return reward + self.sum_recurring_blue()

    def reset(self, ) -> None:
        self.step_detected = self.initial_step
        self.blue_recurring_actions = []
