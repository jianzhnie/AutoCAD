from typing import Any, Dict

from cyberwheel.agents.blue.blue_action import BlueActionReturn, SubnetAction
from cyberwheel.network import Network, Subnet


class RemoveDecoyHost(SubnetAction):
    """Action to remove a decoy host from a given subnet in the network."""

    def __init__(self, network: Network, configs: Dict[str, Any]) -> None:
        """Initializes the RemoveDecoyHost action.

        :param network: The network where the action is to be performed.
        :param configs: Configuration dictionary.
        """
        super().__init__(network, configs)

    def execute(self, subnet: Subnet, **kwargs) -> BlueActionReturn:
        """Executes the action to remove a decoy host from the subnet.

        :param subnet: The subnet from which to remove the decoy host.
        :param kwargs: Additional keyword arguments (unused).
        :return: BlueActionReturn indicating the success or failure of the operation.
        """
        success = False
        host_id = ''

        # Iterate over the hosts connected to the subnet and find the decoy host
        for host in subnet.get_connected_hosts():
            if host.decoy:
                # Remove the decoy host from the subnet
                self.network.remove_host_from_subnet(host)
                success = True
                host_id = host.name
                break

        # Return the result of the action
        return BlueActionReturn(id=host_id, success=success, recurring=-1)
