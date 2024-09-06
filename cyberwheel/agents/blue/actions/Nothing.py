from typing import Any, Dict

from cyberwheel.agents.blue.blue_action import (BlueActionReturn,
                                                StandaloneAction, generate_id)
from cyberwheel.network import Network


class Nothing(StandaloneAction):
    """A no-op action that does nothing but return a success with a generated
    ID."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the Nothing action.

        :param network: The network in which the action is performed.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments (unused).
        """
        super().__init__(network, configs)

    def execute(self, **kwargs) -> BlueActionReturn:
        """Executes the no-op action.

        :param kwargs: Additional keyword arguments (unused).
        :return: BlueActionReturn containing a generated ID and success status.
        """
        # Return a successful action with a generated unique ID
        return BlueActionReturn(id=generate_id(), success=True)
