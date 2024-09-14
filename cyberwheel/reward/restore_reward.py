import logging

from cyberwheel.reward.reward_base import Reward, RewardMap

logger = logging.getLogger(__name__)


class RestoreReward(Reward):
    """这段代码定义了一个名为RestoreReward的类， 它继承自Reward基类。这个类用于计算红蓝两方在某种对抗性场景中的奖励值。"""

    def __init__(
        self,
        red_rewards: RewardMap,
        blue_rewards: RewardMap,
    ) -> None:
        super().__init__(red_rewards, blue_rewards)

    def calculate_reward(
        self,
        red_action: str,
        blue_action: str,
        red_success: bool,
        blue_success: bool,
    ) -> float:
        """计算奖励值的函数。 根据红队和蓝队的行动成功与否，从各自的奖励字典中获取奖励值。
        如果红队成功，则从红队奖励字典中获取奖励值；否则，取相反数。 如果蓝队成功，则从蓝队奖励字典中获取奖励值；否则，取相反数。
        最后返回红队和蓝队奖励值的和。

        接收四个参数：红方行动、蓝方行动、红方是否成功、蓝方是否成功。

        Args:
            red_action (str): 红方行动
            blue_action (str): 蓝方行动
            red_success (bool): 红方是否成功
            blue_success (bool): 蓝方是否成功

        Returns:
            float: 奖励值
        """
        try:
            red_agent_reward = self.red_rewards[red_action][0] * (
                1 if red_success else -1)
            blue_agent_reward = self.blue_rewards[blue_action][0] * (
                1 if blue_success else -1)
        except KeyError as e:
            logger.error(f'Invalid action: {e}')
            raise ValueError(f'Invalid action: {e}')

        reward = red_agent_reward + blue_agent_reward
        logger.info(f'RestoreReward: {reward}')
        logger.debug(
            f'Calculated reward: {reward} (Red: {red_agent_reward}, Blue: {blue_agent_reward})'
        )
        return reward

    def reset(self) -> None:
        return
