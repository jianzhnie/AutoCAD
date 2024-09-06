from typing import List, Tuple

from gymnasium import Space, spaces
from gymnasium.core import ActType

from cyberwheel.agents.blue.action_space import ActionSpace, ASReturn
from cyberwheel.agents.blue.blue_action import BlueAction
from cyberwheel.network import Network


class ActionRangeChecker:
    """A helper class to check if an action index falls within a specified
    range.

    Attributes:
        name (str): The name of the action.
        action (BlueAction): The BlueAction instance.
        type (str): The type of the action.
        lower_bound (int): The lower bound of the action range.
        upper_bound (int): The upper bound of the action range.
    """

    def __init__(
        self,
        name: str,
        action: BlueAction,
        type: str,
        lower_bound: int,
        upper_bound: int,
    ):
        self.name = name
        self.action = action
        self.type = type
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def check_range(self, index: int) -> bool:
        """Checks if the given index is within the specified range.

        Args:
            index (int): The index to check.

        Returns:
            bool: True if the index is within the range, False otherwise.
        """
        return self.lower_bound <= index < self.upper_bound


class DiscreteActionSpace(ActionSpace):
    """A concrete implementation of the ActionSpace class for discrete action
    spaces.

    Attributes:
        action_space_size (int): The total size of the action space.
        _action_checkers (List[_ActionRangeChecker]): List of action range checkers.
    """

    def __init__(self, network: Network) -> None:
        super().__init__(network)
        self.action_space_size: int = 0
        self.action_checkers: List[ActionRangeChecker] = []

    def select_action(self, action: ActType) -> ASReturn:
        """Selects an action based on the sampled action.

        Args:
            action (ActType): The action sampled from the action space.

        Returns:
            ASReturn: An instance of ASReturn containing the selected action.

        Raises:
            TypeError: If the provided action is not of type int.
            TypeError: If the action type is unknown.
        """
        try:
            action = int(action)
        except ValueError:
            raise TypeError(
                f'Provided action is of type {type(action)} and is unsupported by the chosen ActionSpaceConverter'
            )

        for ac in self.action_checkers:
            if not ac.check_range(action):
                continue
            name = ac.name
            if ac.type == 'standalone':
                return ASReturn(name, ac.action)
            elif ac.type == 'host':
                index = (action - ac.lower_bound) % self.num_hosts
                return ASReturn(name, ac.action, args=[self.hosts[index]])
            elif ac.type == 'subnet':
                index = (action - ac.lower_bound) % self.num_subnets
                return ASReturn(name, ac.action, args=[self.subnets[index]])
            elif ac.type == 'range':
                index = (action - ac.lower_bound) % (ac.upper_bound -
                                                     ac.lower_bound)
                return ASReturn(name, ac.action, args=[index])
            else:
                raise TypeError(f'Unknown action type: {ac.type}.')

    def add_action(self, name: str, action: BlueAction, **kwargs) -> None:
        """Adds an action to the action space.

        Args:
            name (str): The name of the action.
            action (BlueAction): The BlueAction instance to be added.
            **kwargs: Additional keyword arguments specifying the type and range of the action.

        Raises:
            ValueError: If the action type is invalid or if the range value is not greater than 0.
        """
        action_type = kwargs.get('type', '').lower()

        lower_bound = self.action_space_size
        if action_type == 'standalone':
            self.action_space_size += 1
        elif action_type == 'host':
            self.action_space_size += self.num_hosts
        elif action_type == 'subnet':
            self.action_space_size += self.num_subnets
        elif action_type == 'range':
            range_ = kwargs.get('range', 0)
            if range_ <= 0:
                raise ValueError('Value for range must be > 0')
            self.action_space_size += range_
        else:
            raise ValueError(
                "Action type must be 'host', 'subnet', 'standalone', or 'range'"
            )
        upper_bound = self.action_space_size
        self.action_checkers.append(
            ActionRangeChecker(name, action, action_type, lower_bound,
                               upper_bound))

    def get_shape(self) -> Tuple[int, ...]:
        """Returns the shape of the action space.

        Returns:
            Tuple[int, ...]: A tuple representing the shape of the action space.
        """
        return (self.action_space_size, )

    def create_action_space(self) -> Space:
        """Creates a gym.Space representation of the action space.

        Returns:
            Space: An instance of gym.Space representing the action space.
        """
        return spaces.Discrete(self.action_space_size)
