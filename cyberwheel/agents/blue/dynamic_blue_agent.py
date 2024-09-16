import builtins
import importlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from gymnasium import Space

from cyberwheel.agents.blue.action_space import ActionSpace
from cyberwheel.agents.blue.blue_agent import BlueAgent, BlueAgentResult
from cyberwheel.network import Network
from cyberwheel.reward import RewardMap


class ActionConfigInfo:
    """Holds configuration information for a blue action.

    Attributes:
        name (str): The name of the action.
        configs (List): List of configuration files for the action.
        immediate_reward (float): The immediate reward for the action.
        recurring_reward (float): The recurring reward for the action.
        action_space_args (Dict): Arguments for the action space.
        shared_data (List): List of shared data keys.
    """

    def __init__(
        self,
        name: str = '',
        configs: List = [],
        immediate_reward: float = 0.0,
        recurring_reward: float = 0.0,
        action_space_args: Dict = {},
        shared_data: List = [],
    ) -> None:
        self.name = name
        self.configs = configs
        self.immediate_reward = immediate_reward
        self.recurring_reward = recurring_reward
        self.shared_data = shared_data
        self.action_space_args = action_space_args

    def __str__(self) -> str:
        return (
            f'config: {self.configs}, immediate_reward: {self.immediate_reward}, '
            f'recurring_reward: {self.recurring_reward}, action_space_args: {self.action_space_args}'
        )


class DynamicBlueAgent(BlueAgent):
    """A dynamic blue agent that can load and execute blue actions based on a
    configuration file.

    Attributes:
        config (str): Path to the configuration file.
        network (Network): The network environment.
        configs (Dict[str, Any]): Dictionary to store configuration contents.
        action_space (ActionSpace): The action space for the agent.
        actions (List[Tuple]): List of tuples containing action classes and their configuration info.
        shared_data (Dict[str, Any]): Dictionary to store shared data between actions.
        reward_map (RewardMap): The reward map for the agent.
    """

    def __init__(self, config: str, network: Network) -> None:
        super().__init__()
        self.config = config
        self.network = network
        self.configs: Dict[str, Any] = {}
        self.action_space: ActionSpace = None
        self.actions: List[Tuple] = []
        self.shared_data: Dict[str, Any] = {}
        self.reward_map: RewardMap = {}

        self.from_yaml()
        self._init_blue_actions()
        self._init_reward_map()

    def from_yaml(self):
        """Loads the configuration from a YAML file and initializes the action
        space and actions."""
        with open(self.config, 'r') as r:
            contents = yaml.safe_load(r)

        # Get module import paths
        action_module_path = contents['action_module_path']
        if not isinstance(action_module_path, str):
            raise TypeError(
                'value for key "action_module_path" must be a string')
        as_module_path = contents['action_space_module_path']
        if not isinstance(as_module_path, str):
            raise TypeError(
                'value for key "action_space_module_path" must be a string')

        # Initialize the action space converter
        action_space = contents['action_space']
        as_module = action_space['module']
        as_class = action_space['class']
        as_args = action_space.get('args', {})
        import_path = '.'.join([as_module_path, as_module])
        m = importlib.import_module(import_path)
        self.action_space = getattr(m, as_class)(self.network, **as_args)

        # Get information needed to later initialize blue actions.
        for k, v in contents['actions'].items():
            module_name = v['module']
            class_name = v['class']
            configs = v.get('configs', {})
            shared_data = v.get('shared_data', [])

            import_path = '.'.join([action_module_path, module_name])
            m = importlib.import_module(import_path)
            class_ = getattr(m, class_name)
            action_info = ActionConfigInfo(
                k,
                configs,
                v['reward']['immediate'],
                v['reward']['recurring'],
                v['action_space_args'],
                shared_data,
            )
            self.actions.append((class_, action_info))

        # Set up data shared between actions
        if contents['shared_data'] is None:
            return
        for k, v in contents['shared_data'].items():
            if v in ('list', 'set', 'dict'):
                data_type = getattr(builtins, v)
                self.shared_data[k] = data_type()
            else:
                if 'module' not in v or 'class' not in v:
                    raise KeyError(
                        "If using custom object, 'module' and 'class' must be defined."
                    )
                a = importlib.import_module(v['module'])
                data_type = getattr(a, v['class'])
                kwargs = v.get('args', {})
                self.shared_data[k] = data_type(**kwargs)

    def _init_blue_actions(self) -> None:
        """Initializes the blue actions based on the configuration."""
        for action_class, action_info in self.actions:
            # Check configs and read them if they are new
            action_configs = {}
            for name, config in action_info.configs.items():
                if config not in self.configs:
                    conf_file = Path(f"cyberwheel/resources/configs/{name}").joinpath(
                        config
                    )
                    with open(conf_file, 'r') as f:
                        contents = yaml.safe_load(f)
                    self.configs[config] = contents
                    action_configs[name] = contents
                else:
                    action_configs[name] = self.configs[config]

            action_kwargs = {
                sd: self.shared_data[sd]
                for sd in action_info.shared_data
            }
            action = action_class(self.network, action_configs,
                                  **action_kwargs)

            self.action_space.add_action(action_info.name, action,
                                         **action_info.action_space_args)
        self.action_space.finalize()

    def _init_reward_map(self) -> None:
        """Initializes the reward map based on the configuration."""
        for _, action_config_info in self.actions:
            if action_config_info.name in self.reward_map:
                raise KeyError(
                    'error constructing reward map: action names should be unique'
                )
            self.reward_map[action_config_info.name] = (
                action_config_info.immediate_reward,
                action_config_info.recurring_reward,
            )

    def act(self, action: int) -> BlueAgentResult:
        """Executes an action and returns the result.

        Args:
            action (int): The action to execute.

        Returns:
            BlueAgentResult: The result of the action.
        """
        asc_return = self.action_space.select_action(action)
        result = asc_return.action.execute(*asc_return.args,
                                           **asc_return.kwargs)
        id = result.id
        success = result.success
        recurring = result.recurring
        return BlueAgentResult(asc_return.name, id, success, recurring)

    def get_reward_map(self) -> RewardMap:
        """Retrieves the reward map associated with the blue agent.

        Returns:
            RewardMap: The reward map.
        """
        return self.reward_map

    def get_action_space_shape(self) -> Tuple[int, ...]:
        """Retrieves the shape of the action space.

        Returns:
            Tuple[int, ...]: The shape of the action space.
        """
        return self.action_space.get_shape()

    def create_action_space(self) -> Space:
        """Creates a gym.Space representation of the action space.

        Returns:
            Space: The action space.
        """
        return self.action_space.create_action_space()

    def reset(self):
        """Resets the shared data."""
        for v in self.shared_data.values():
            v.clear()
