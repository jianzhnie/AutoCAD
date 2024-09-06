from typing import Any, Dict

from cyberwheel.agents.blue.blue_action import BlueActionReturn, HostAction
from cyberwheel.network import Host, Network


class Restore(HostAction):
    """Action to restore a host by removing malware and marking it as
    restored."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the Restore action.

        :param network: The network where the host resides.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments (unused).
        """
        super().__init__(network, configs)

    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        """Executes the restore action on the given host.

        :param host: The host to be restored.
        :param kwargs: Additional keyword arguments (unused).
        :return: BlueActionReturn indicating success or failure of the restoration.
        """
        # Check if the host has already been restored
        if host.restored:
            return BlueActionReturn(id='', success=False)

        # Remove the malware process from the host
        host.remove_process('malware.exe')
        # Mark the host as restored
        host.restored = True

        # Return a successful action result
        return BlueActionReturn(id='', success=True)
