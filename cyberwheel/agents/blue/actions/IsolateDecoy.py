from typing import Any, Dict, List, Tuple

from cyberwheel.agents.blue.blue_action import (BlueActionReturn,
                                                StandaloneAction)
from cyberwheel.network import Host, Network, Subnet


class IsolateDecoy(StandaloneAction):
    """Action to isolate a decoy host within the network."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the IsolateDecoy action.

        :param network: The network where the decoy host resides.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments, including 'isolate_data'.
        """
        super().__init__(network, configs)
        # Expecting 'isolate_data' to be a list of tuples (Host, Subnet)
        self.isolate_data: List[Tuple[Host, Subnet]] = kwargs.get(
            'isolate_data', [])

    def execute(self, i: int, **kwargs) -> BlueActionReturn:
        """Executes the action to isolate a decoy host.

        :param i: The index of the host in the isolate_data list to isolate.
        :param kwargs: Additional keyword arguments.
        :return: BlueActionReturn indicating success or failure of the isolation.
        """
        # Check if the index is within the valid range of isolate_data
        if i >= len(self.isolate_data):
            return BlueActionReturn(id='', success=False)

        host, subnet = self.isolate_data[i]

        # Check if the host is already isolated
        if host.isolated:
            return BlueActionReturn(id='', success=False)

        # Isolate the host within the subnet
        self.network.isolate_host(host, subnet)
        return BlueActionReturn(id='', success=True)
