import json
import os
import uuid
from typing import Dict, List, Tuple

import yaml


# Helper functions to initialize None values to appropriate types
def _initialize_dict(data: Dict, key: str) -> None:
    if data.get(key) is None:
        data[key] = {}


def _initialize_list(data: Dict, key: str) -> None:
    if data.get(key) is None:
        data[key] = []


def make_firewall(name: str = '',
                  src: str = '',
                  dest: str = '',
                  port: int = 0,
                  protocol: str = '') -> Tuple[str, str, str, int, str]:
    """Creates a tuple representing a firewall rule.

    Args:
        name (str): The name of the firewall rule.
        src (str): The source address.
        dest (str): The destination address.
        port (int): The port number.
        protocol (str): The protocol (e.g., TCP, UDP).

    Returns:
        Tuple[str, str, str, int, str]: A tuple containing firewall details.
    """
    return name, src, dest, port, protocol


class NetworkYAMLGenerator:
    """A class to help generate network configuration files using YAML or JSON.
    Supports adding routers, subnets, hosts, firewalls, and routes to a network
    configuration.

    Attributes:
        data (dict): The main data structure containing the network configuration.
        file_name (str): The base file name used when saving the network configuration.
    """

    # Add a YAML representer to handle None values as empty strings in YAML
    yaml.SafeDumper.add_representer(
        type(None),
        lambda dumper, value: dumper.represent_scalar('tag:yaml.org,2002:null',
                                                      ''),
    )

    def __init__(
        self,
        network_name: str = f'network-{uuid.uuid4().hex}',
        desc: str = 'default description',
    ) -> None:
        """Initializes the NetworkYAMLGenerator with a default network
        configuration.

        Args:
            network_name (str): The name of the network.
            desc (str): A description of the network.
        """
        self.data = {
            'network': {
                'name': network_name,
                'desc': desc
            },
            'routers': None,
            'subnets': None,
            'host_type_config': None,
            'hosts': None,
            'interfaces': None,
            'topology': None,
        }
        self.file_name = network_name

    def add_router(self, router_name: str, default_route: str = '') -> None:
        """Adds a router to the network configuration.

        Args:
            router_name (str): The name of the router.
            default_route (str): The default route for the router.

        Raises:
            KeyError: If the router already exists in the network.
        """
        _initialize_dict(self.data, 'routers')
        if router_name in self.data['routers']:
            raise KeyError(f"Router '{router_name}' already exists")

        self.data['routers'][router_name] = {
            'default_route': default_route if default_route else None,
            'routes_by_name': None,
            'routes': None,
            'firewall': None,
        }

    def add_route_to_router(self, router_name: str, dest: str,
                            via: str) -> None:
        """Adds a route to a router.

        Args:
            router_name (str): The name of the router.
            dest (str): The destination network or address.
            via (str): The next hop address.

        Raises:
            KeyError: If the router is not found in the network.
        """
        if not self.data['routers'].get(router_name):
            raise KeyError(f"Router '{router_name}' not found")
        self._add_route('routers', router_name, dest, via)

    def add_route_by_name(self, router_name: str, name: str) -> None:
        """Adds a route to a router by specifying the route name.

        Args:
            router_name (str): The name of the router.
            name (str): The name of the route.

        Raises:
            KeyError: If the router is not found in the network.
        """
        if not self.data['routers'].get(router_name):
            raise KeyError(f"Router '{router_name}' not found")
        _initialize_list(self.data['routers'][router_name], 'routes_by_name')
        self.data['routers'][router_name]['routes_by_name'].append(name)

    def add_firewall_to_router(
        self,
        router_name: str,
        name: str = '',
        src: str = '',
        dest: str = '',
        port: int = 0,
        protocol: str = '',
    ) -> None:
        """Adds a firewall rule to a router.

        Args:
            router_name (str): The name of the router.
            name (str): The name of the firewall rule.
            src (str): The source address.
            dest (str): The destination address.
            port (int): The port number.
            protocol (str): The protocol (e.g., TCP, UDP).

        Raises:
            KeyError: If the router is not found in the network.
        """
        if not self.data['routers'].get(router_name):
            raise KeyError(f"Router '{router_name}' not found")
        self._add_firewall_entry('routers', router_name, name, src, dest, port,
                                 protocol)

    def add_firewalls_to_router(
            self, router_name: str, firewalls: List[Tuple[str, str, str, int,
                                                          str]]) -> None:
        """Adds multiple firewall rules to a router.

        Args:
            router_name (str): The name of the router.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for firewall in firewalls:
            self.add_firewall_to_router(router_name, *firewall)

    def add_firewalls_to_multiple_routers(
            self, routers: List[str], firewalls: List[Tuple[str, str, str, int,
                                                            str]]) -> None:
        """Adds firewall rules to multiple routers.

        Args:
            routers (List[str]): A list of router names.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for router_name in routers:
            self.add_firewalls_to_router(router_name, firewalls)

    def add_subnet(
        self,
        subnet_name: str,
        router_name: str = '',
        ip_range: str = '',
        dns_server: str = '',
        default_route: str = '',
    ) -> None:
        """Adds a subnet to the network configuration.

        Args:
            subnet_name (str): The name of the subnet.
            router_name (str): The router associated with the subnet.
            ip_range (str): The IP range of the subnet.
            dns_server (str): The DNS server for the subnet.
            default_route (str): The default route for the subnet.

        Raises:
            KeyError: If the subnet already exists in the network.
        """
        _initialize_dict(self.data, 'subnets')
        if subnet_name in self.data['subnets']:
            raise KeyError(f"Subnet '{subnet_name}' already exists")

        self.data['subnets'][subnet_name] = {
            'router': router_name if router_name else None,
            'ip_range': ip_range if ip_range else None,
            'dns_server': dns_server if dns_server else None,
            'default_route': default_route if default_route else None,
            'firewall': None,
        }

    def add_firewall_to_subnet(
        self,
        subnet_name: str,
        name: str = '',
        src: str = '',
        dest: str = '',
        port: int = 0,
        protocol: str = '',
    ) -> None:
        """Adds a firewall rule to a subnet.

        Args:
            subnet_name (str): The name of the subnet.
            name (str): The name of the firewall rule.
            src (str): The source address.
            dest (str): The destination address.
            port (int): The port number.
            protocol (str): The protocol (e.g., TCP, UDP).

        Raises:
            KeyError: If the subnet is not found in the network.
        """
        if not self.data['subnets'].get(subnet_name):
            raise KeyError(f"Subnet '{subnet_name}' not found")
        self._add_firewall_entry('subnets', subnet_name, name, src, dest, port,
                                 protocol)

    def add_firewalls_to_subnet(
            self, subnet_name: str, firewalls: List[Tuple[str, str, str, int,
                                                          str]]) -> None:
        """Adds multiple firewall rules to a subnet.

        Args:
            subnet_name (str): The name of the subnet.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for firewall in firewalls:
            self.add_firewall_to_subnet(subnet_name, *firewall)

    def add_firewalls_to_multiple_subnets(
            self, subnets: List[str], firewalls: List[Tuple[str, str, str, int,
                                                            str]]) -> None:
        """Adds firewall rules to multiple subnets.

        Args:
            subnets (List[str]): A list of subnet names.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for subnet_name in subnets:
            self.add_firewalls_to_subnet(subnet_name, firewalls)

    def add_host(self, host_name: str, subnet: str, host_type: str) -> None:
        """Adds a host to a subnet.

        Args:
            host_name (str): The name of the host.
            subnet (str): The subnet the host belongs to.
            host_type (str): The type of the host (e.g., server, client).

        Raises:
            KeyError: If the host already exists in the network.
        """
        _initialize_dict(self.data, 'hosts')
        if host_name in self.data['hosts']:
            raise KeyError(f"Host '{host_name}' already exists")

        self.data['hosts'][host_name] = {
            'subnet': subnet,
            'type': host_type,
            'firewall': None,
            'routes': None,
        }

    def add_route_to_host(self, host_name: str, dest: str, via: str) -> None:
        """Adds a route to a host.

        Args:
            host_name (str): The name of the host.
            dest (str): The destination network or address.
            via (str): The next hop address.

        Raises:
            KeyError: If the host is not found in the network.
        """
        if not self.data['hosts'].get(host_name):
            raise KeyError(f"Host '{host_name}' not found")
        self._add_route('hosts', host_name, dest, via)

    def add_firewall_to_host(
        self,
        host_name: str,
        name: str = '',
        src: str = '',
        dest: str = '',
        port: int = 0,
        protocol: str = '',
    ) -> None:
        """Adds a firewall rule to a host.

        Args:
            host_name (str): The name of the host.
            name (str): The name of the firewall rule.
            src (str): The source address.
            dest (str): The destination address.
            port (int): The port number.
            protocol (str): The protocol (e.g., TCP, UDP).

        Raises:
            KeyError: If the host is not found in the network.
        """
        if not self.data['hosts'].get(host_name):
            raise KeyError(f"Host '{host_name}' not found")
        self._add_firewall_entry('hosts', host_name, name, src, dest, port,
                                 protocol)

    def add_firewalls_to_host(
            self, host_name: str, firewalls: List[Tuple[str, str, str, int,
                                                        str]]) -> None:
        """Adds multiple firewall rules to a host.

        Args:
            host_name (str): The name of the host.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for firewall in firewalls:
            self.add_firewall_to_host(host_name, *firewall)

    def add_firewalls_to_multiple_hosts(
            self, hosts: List[str], firewalls: List[Tuple[str, str, str, int,
                                                          str]]) -> None:
        """Adds firewall rules to multiple hosts.

        Args:
            hosts (List[str]): A list of host names.
            firewalls (List[Tuple[str, str, str, int, str]]): A list of firewall rules.
        """
        for host_name in hosts:
            self.add_firewalls_to_host(host_name, firewalls)

    def set_host_type_config(self, path: str) -> None:
        """Sets the host type configuration path.

        Args:
            path (str): The path to the host type configuration file.
        """
        self.data['host_type_config'] = path

    def add_interface(self, src: str, dest: str) -> None:
        """Adds an interface connection between two network components.

        Args:
            src (str): The source component.
            dest (str): The destination component.
        """
        _initialize_dict(self.data, 'interfaces')
        if src not in self.data['interfaces']:
            self.data['interfaces'][src] = []
        self.data['interfaces'][src].append(dest)

    def _add_route(self, index: str, index2: str, dest: str, via: str) -> None:
        """Internal method to add a route to a network component.

        Args:
            index (str): The primary key (e.g., 'routers', 'hosts').
            index2 (str): The specific component name.
            dest (str): The destination network or address.
            via (str): The next hop address.
        """
        _initialize_list(self.data[index][index2], 'routes')
        self.data[index][index2]['routes'].append({'dest': dest, 'via': via})

    def _add_firewall_entry(
        self,
        index: str,
        index2: str,
        name: str = '',
        src: str = '',
        dest: str = '',
        port: int = 0,
        protocol: str = '',
    ) -> None:
        """Internal method to add a firewall entry to a network component.

        Args:
            index (str): The primary key (e.g., 'routers', 'subnets', 'hosts').
            index2 (str): The specific component name.
            name (str): The name of the firewall rule.
            src (str): The source address.
            dest (str): The destination address.
            port (int): The port number.
            protocol (str): The protocol (e.g., TCP, UDP).
        """
        firewall_entry = {
            'name': name,
            'src': src,
            'dest': dest,
            'port': port,
            'proto': protocol,
        }
        _initialize_list(self.data[index][index2], 'firewall')
        self.data[index][index2]['firewall'].append(firewall_entry)

    def _generate_topology(self) -> None:
        """Internal method to generate the network topology based on routers,
        subnets, and hosts."""
        topology = {}
        for router in self.data['routers']:
            topology[router] = {}
            for subnet, subnet_data in self.data['subnets'].items():
                if subnet_data.get('router') == router:
                    topology[router][subnet] = [
                        host for host, host_data in self.data['hosts'].items()
                        if host_data['subnet'] == subnet
                    ]

        # Handle subnets without routers
        topology['no_router'] = {
            subnet: [
                host for host, host_data in self.data['hosts'].items()
                if host_data['subnet'] == subnet
            ]
            for subnet, subnet_data in self.data['subnets'].items()
            if not subnet_data.get('router')
        }

        self.data['topology'] = topology

    def output_yaml(self, path: str = '.') -> None:
        """Outputs the network configuration as a YAML file.

        Args:
            path (str): The directory path to save the file.
        """
        self._generate_topology()
        file_path = os.path.join(path, self.file_name + '.yaml')
        with open(file_path, 'w') as yaml_file:
            yaml.safe_dump(self.data, yaml_file)

    def output_json(self, path: str = '.') -> None:
        """Outputs the network configuration as a JSON file.

        Args:
            path (str): The directory path to save the file.
        """
        self._generate_topology()
        file_path = os.path.join(path, self.file_name + '.json')
        with open(file_path, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)
