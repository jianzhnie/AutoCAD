from typing import Any, Dict, List

from cyberwheel.agents.blue.blue_action import BlueActionReturn, HostAction
from cyberwheel.network import Host, Network


class QuarantineHost(HostAction):
    """Action to quarantine a host by isolating it within the network."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the QuarantineHost action.

        :param network: The network where the host resides.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments, including 'quarantine_list'.
        """
        super().__init__(network, configs)
        # Initialize quarantine list from kwargs if provided
        self.quarantine_list: List[str] = kwargs.get('quarantine_list', [])

    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        """Executes the action to quarantine a host.

        :param host: The host to be quarantined.
        :param kwargs: Additional keyword arguments (unused).
        :return: BlueActionReturn indicating success or failure of the quarantine.
        """
        # Check if the host is already quarantined
        if host.name in self.quarantine_list:
            return BlueActionReturn(id='', success=False)

        # Isolate the host within the network
        self.network.isolate_host(host, host.subnet)
        # Add the host to the quarantine list
        self.quarantine_list.append(host.name)

        return BlueActionReturn(id='', success=True, recurring=0)


class RemoveQuarantineHost(HostAction):
    """Action to remove a host from quarantine by reconnecting it to the
    network."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the RemoveQuarantineHost action.

        :param network: The network where the host resides.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments, including 'quarantine_list'.
        """
        super().__init__(network, configs)
        # Initialize quarantine list from kwargs if provided
        self.quarantine_list: List[str] = kwargs.get('quarantine_list', [])

    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        """Executes the action to remove a host from quarantine.

        :param host: The host to be removed from quarantine.
        :param kwargs: Additional keyword arguments (unused).
        :return: BlueActionReturn indicating success or failure of the operation.
        """
        # Check if the host is not quarantined
        if host.name not in self.quarantine_list:
            return BlueActionReturn(id='', success=False)

        # Reconnect the host to the network
        self.network.connect_nodes(host.name, host.subnet.name)
        # Remove the host from the quarantine list
        self.quarantine_list.remove(host.name)

        return BlueActionReturn(id='', success=True)
