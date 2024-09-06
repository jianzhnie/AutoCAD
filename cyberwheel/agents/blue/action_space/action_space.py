from abc import ABC, abstractmethod
from typing import Dict, Tuple

from gymnasium import Space, spaces
from gymnasium.core import ActType

from cyberwheel.agents.blue.blue_action import BlueAction
from cyberwheel.network import Network


class ASReturn:
    """A class to encapsulate the return values from the ActionSpace's
    select_action method.

    Attributes:
        name (str): The name of the action.
        action (BlueAction): The BlueAction instance to be executed.
        args (tuple): Positional arguments for the action.
        kwargs (dict): Keyword arguments for the action.
    """

    def __init__(self,
                 name: str,
                 action: BlueAction,
                 args: Tuple = (),
                 kwargs: Dict = {}) -> None:
        self.name = name
        self.action = action
        self.args = args
        self.kwargs = kwargs


class ActionSpace(ABC):
    """A base class for converting the output of `gym.Space.sample()` to a blue
    action.

    This class must be subclassed to implement the following abstract methods:
    - `select_action()`: Method for handling which method the blue agent selects.
    - `add_action()`: Method for adding an action.
    - `get_shape()`: Method for getting the shape of the action space.
    - `create_action_space()`: Creates a gym.Space representation of the action space.

    Attributes:
        network (Network): The network instance.
        hosts (list): List of hosts in the network.
        subnets (list): List of subnets in the network.
        num_hosts (int): Number of hosts in the network.
        num_subnets (int): Number of subnets in the network.
    """

    def __init__(self, network: Network) -> None:
        self.network = network
        self.hosts = network.get_hosts()
        self.subnets = network.get_all_subnets()
        self.num_hosts = len(self.hosts)
        self.num_subnets = len(self.subnets)

    @abstractmethod
    def select_action(self, action: ActType, **kwargs) -> ASReturn:
        """Selects which action to perform based on the value of `action`.

        Args:
            action (ActType): The action sampled from the action space.
            **kwargs: Additional keyword arguments that may be necessary for selecting the action.

        Returns:
            ASReturn: An instance of ASReturn containing the name, action, args, and kwargs.
        """
        pass

    @abstractmethod
    def add_action(self, name: str, action: BlueAction, **kwargs) -> None:
        """Adds an action to this `ActionSpace`.

        Args:
            name (str): The name of the action.
            action (BlueAction): The BlueAction instance to be added.
            **kwargs: Additional keyword arguments that may be necessary for adding the action.
        """
        pass

    @abstractmethod
    def get_shape(self) -> Tuple[int, ...]:
        """Returns the shape of the action space.

        Returns:
            Tuple[int, ...]: A tuple representing the shape of the action space.
        """
        pass

    @abstractmethod
    def create_action_space(self) -> Space:
        """Creates a gym.Space representation of the action space.

        Returns:
            Space: An instance of gym.Space representing the action space.
        """
        pass

    def finalize(self) -> None:
        """Called by the dynamic blue agent after it finishes adding actions.

        This method can be overwritten to perform any operations necessary to
        finalize the converter's setup.
        """
        pass


class SimpleActionSpace(ActionSpace):
    """A simple implementation of the ActionSpace class.

    Attributes:
        actions (Dict[str, BlueAction]): A dictionary mapping action names to BlueAction instances.
    """

    def __init__(self, network: Network) -> None:
        super().__init__(network)
        self.actions: Dict[str, BlueAction] = {}

    def select_action(self, action: ActType, **kwargs) -> ASReturn:
        """Selects an action based on the sampled action.

        Args:
            action (ActType): The action sampled from the action space.
            **kwargs: Additional keyword arguments (not used in this implementation).

        Returns:
            ASReturn: An instance of ASReturn containing the selected action.

        Raises:
            ValueError: If the action name is not found in the action space.
        """
        action_name = action[0]
        if action_name in self.actions:
            return ASReturn(action_name, self.actions[action_name])
        else:
            raise ValueError(
                f'Action {action_name} not found in action space.')

    def add_action(self, name: str, action: BlueAction, **kwargs) -> None:
        """Adds an action to the action space.

        Args:
            name (str): The name of the action.
            action (BlueAction): The BlueAction instance to be added.
            **kwargs: Additional keyword arguments (not used in this implementation).
        """
        self.actions[name] = action

    def get_shape(self) -> Tuple[int, ...]:
        """Returns the shape of the action space.

        Returns:
            Tuple[int, ...]: A tuple representing the shape of the action space.
        """
        return (len(self.actions), )

    def create_action_space(self) -> Space:
        """Creates a gym.Space representation of the action space.

        Returns:
            Space: An instance of gym.Space representing the action space.
        """
        return spaces.Discrete(len(self.actions))
