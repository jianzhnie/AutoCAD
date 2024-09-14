from cyberwheel.reward.reward_base import Reward, RewardMap


class IsolateReward(Reward):
    """这段代码定义了一个名为IsolateReward的类，用于计算红蓝双方在网络隔离场景中的奖励。"""

    def __init__(
        self,
        red_rewards: RewardMap,
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

        Args:
            red_rewards (Dict[RedAction, float]): 红队行动对应的奖励值字典
        """

        self.red_rewards = red_rewards

    def calculate_reward(
        self,
        red_action: str,
        blue_success: bool,
        red_action_alerted: bool,
    ) -> float:
        """如果红队行动被检测到(alerted),使用奖励值的绝对值 如果蓝队(防守方)失败,额外减去100分 最后返回红队奖励和蓝队惩罚的总和.

        计算红队行动的奖励值

        Args:
            red_action (RedAction): 红队执行的行动
            blue_success (bool): 蓝队是否成功防御
            red_action_alerted (bool): 红队行动是否被检测到

        Returns:
            float: 计算得到的奖励值
        """

        reward = (abs(self.red_rewards[red_action])
                  if red_action_alerted else self.red_rewards[red_action])
        blue_penalty = -100 if not blue_success else 0
        return reward + blue_penalty

    def reset(self) -> None:
        self.blue_recurring_actions = []
        self.red_recurring_impacts = 0
