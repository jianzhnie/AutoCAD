import json
from typing import Any, Dict, List

from cyberwheel.agents.blue.blue_action import (BlueActionReturn, SubnetAction,
                                                generate_id)
from cyberwheel.network import HostType, Network, Subnet


def get_host_types() -> List[Dict[str, Any]]:
    """Loads and returns host types from a JSON file.

    :return: A list of dictionaries containing host type definitions.
    """
    with open('resources/metadata/host_definitions.json', 'r') as f:
        host_defs = json.load(f)
    return host_defs['host_types']


class DeployDecoyHost(SubnetAction):
    """Action to deploy a decoy host within a given subnet."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the DeployDecoyHost action.

        :param network: The network in which the decoy host will be deployed.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(network, configs)
        self.define_configs()
        self.define_services()
        # Initialize decoy list from kwargs if provided
        self.decoy_list: List[str] = kwargs.get('decoy_list', [])

    def execute(self, subnet: Subnet, **kwargs) -> BlueActionReturn:
        """Executes the action to deploy a decoy host.

        :param subnet: The subnet where the decoy host will be deployed.
        :param kwargs: Additional keyword arguments.
        :return: BlueActionReturn containing the host name, success status, and an identifier.
        """
        name = generate_id()  # Generate a unique ID for the host

        # Determine the host type based on the 'type' attribute in configs
        if 'server' in self.configs.get('type', '').lower():
            host_type = HostType(name='Server',
                                 services=self.services,
                                 decoy=True,
                                 cve_list=self.cves)
        else:
            host_type = HostType(
                name='Workstation',
                services=self.services,
                decoy=True,
                cve_list=self.cves,
            )

        # Create the decoy host in the network
        self.host = self.network.create_decoy_host(name, subnet, host_type)
        # Append the host name to the decoy list
        self.decoy_list.append(name)

        return BlueActionReturn(id=name, success=True, recurring=1)


class IsolateDecoyHost(SubnetAction):
    """Action to isolate a decoy host within a given subnet."""

    def __init__(self, network: Network, configs: Dict[str, Any],
                 **kwargs) -> None:
        """Initializes the IsolateDecoyHost action.

        :param network: The network in which the decoy host will be isolated.
        :param configs: Configuration dictionary.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(network, configs)
        self.define_configs()
        self.define_services()
        # Initialize isolate data from kwargs if provided
        self.isolate_data: List[Any] = kwargs.get('isolate_data', [])

    def execute(self, subnet: Subnet, **kwargs) -> BlueActionReturn:
        """Executes the action to isolate a decoy host.

        :param subnet: The subnet where the decoy host will be isolated.
        :param kwargs: Additional keyword arguments.
        :return: BlueActionReturn containing the host name, success status, and an identifier.
        """
        name = generate_id()  # Generate a unique ID for the host

        # Define the host type as a decoy host
        host_type = HostType(name=name,
                             services=self.services,
                             decoy=True,
                             cve_list=self.cves)

        # Create the decoy host in the network
        self.host = self.network.create_decoy_host(name, subnet, host_type)

        # Isolate the decoy host and update isolate_data
        # TODO
        isolation_success = self.isolate_data.append_decoy(self.host, subnet)

        return BlueActionReturn(id=name,
                                success=isolation_success,
                                recurring=1)
