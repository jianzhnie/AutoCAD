import ipaddress as ipa
import random
from copy import deepcopy
from typing import List, Optional, Union

from cyberwheel.network.network_object import NetworkObject, Route
from cyberwheel.network.router import Router


class Subnet(NetworkObject):

    def __init__(
        self,
        name: str,
        ip_range: str,
        router: Router,
        firewall_rules: Optional[List[dict]] = None,
        **kwargs,
    ):
        """Initializes a Subnet object.

        :param str name: Name of the subnet.
        :param str ip_range: CIDR IP range (e.g., 192.168.0.0/24).
        :param Router router: Router object associated with this subnet.
        :param Optional[List[dict]] firewall_rules: List of firewall rules
               (empty rules mean allow all traffic).
        :param Optional[Union[ipa.IPv4Address, ipa.IPv6Address]] dns_server:
               Default DNS server for the subnet, if any.
        """
        super().__init__(name, firewall_rules or [])

        # Initialize IP network for the subnet
        try:
            self.ip_network = ipa.ip_network(ip_range, strict=False)
        except ValueError as e:
            raise ValueError(f'Invalid IP range: {ip_range}. Error: {e}')

        self.available_ips: List[Union[ipa.IPv4Address,
                                       ipa.IPv6Address]] = list(
                                           self.ip_network.hosts())
        self.connected_hosts: List = []  # List to store connected hosts
        self.router = router

        # Set DNS server if provided
        dns_server = kwargs.get('dns_server')
        if dns_server:
            try:
                self.dns_server = self.generate_ip_object(dns_server)
            except ValueError as e:
                raise ValueError(
                    f'Invalid DNS server IP: {dns_server}. Error: {e}')
        else:
            self.dns_server = None

        # Initialize the default route if the router interface is set
        self.default_route: Optional[Route] = None
        self.set_default_route()

    def __str__(self) -> str:
        return f'Subnet(name="{self.name}", ip_network="{self.ip_network}", router="{self.router.name}")'

    def __repr__(self) -> str:
        return (f'Subnet(name={self.name!r}, ip_network={self.ip_network!r}, '
                f'router={self.router!r}, dns_server={self.dns_server!r}, '
                f'firewall_rules={self.firewall_rules!r})')

    def __deepcopy__(self, memo: dict) -> 'Subnet':
        """Creates a deep copy of the Subnet object, including connected hosts.

        :param dict memo: Memo dictionary to prevent recursive copies.
        :return Subnet: Deep copied Subnet object.
        """
        new_subnet = Subnet(self.name, self.ip_range,
                            deepcopy(self.router, memo))
        memo[id(self)] = new_subnet
        new_subnet.connected_hosts = [
            deepcopy(host, memo) for host in self.connected_hosts
        ]
        return new_subnet

    def set_default_route(self) -> None:
        """Sets the default route for the subnet based on the router's
        interface IP address."""
        default_route_via = self.router.get_interface_ip(self.name)
        if default_route_via is None:
            return

        ip_version = default_route_via.version
        if ip_version == 4:
            self.default_route = Route(dest=ipa.ip_network('0.0.0.0/0'),
                                       via=default_route_via)
        elif ip_version == 6:
            self.default_route = Route(dest=ipa.ip_network('::/0'),
                                       via=default_route_via)

    def set_dns_server(self, ip: Union[ipa.IPv4Address,
                                       ipa.IPv6Address]) -> None:
        """Sets the DNS server for the subnet.

        :param Union[ipa.IPv4Address, ipa.IPv6Address] ip: IP address of the DNS server.
        """
        self.dns_server = ip

    def get_network_address(self) -> str:
        """Returns the network address of the subnet.

        :return str: Network address as a string.
        """
        return str(self.ip_network.network_address)

    def get_prefix_length(self) -> int:
        """Returns the prefix length of the subnet (e.g., 24 for
        192.168.0.0/24).

        :return int: Prefix length.
        """
        return self.ip_network.prefixlen

    def get_max_num_hosts(self) -> int:
        """Returns the maximum number of usable IP addresses in the subnet.

        :return int: Number of usable IP addresses.
        """
        return self.ip_network.num_addresses - 2

    def get_unassigned_ips(
            self) -> List[Union[ipa.IPv4Address, ipa.IPv6Address]]:
        """Returns the list of unassigned IP addresses in the subnet.

        :return List[Union[ipa.IPv4Address, ipa.IPv6Address]]: List of unassigned IP addresses.
        """
        return self.available_ips

    def get_num_unassigned_ips(self) -> int:
        """Returns the number of unassigned IP addresses in the subnet.

        :return int: Number of unassigned IP addresses.
        """
        return len(self.available_ips)

    def assign_dhcp_lease(self, host_obj) -> None:
        """Simulates a DHCP lease by assigning an IP address to a host and
        setting up its DNS and routes.

        :param Host host_obj: Host object requesting a DHCP lease.
        """
        if not self.available_ips:
            raise ValueError('No available IP addresses in the subnet.')

        # Assign a random IP address from the available pool
        ip_lease = random.choice(self.available_ips)
        self.available_ips.remove(ip_lease)

        # Update connected hosts list
        self.connected_hosts.append(host_obj)

        # Assign IP and DNS server to the host
        host_obj.set_ip(ip_lease)
        host_obj.set_dns(self.dns_server)

        # Assign a route for the subnet
        route = self.generate_route(self.ip_network, host_obj.ip_address)
        host_obj.add_route(route)

        # Assign default route if not already set
        if host_obj.default_route is None:
            host_obj.default_route = self.default_route

    def get_connected_hosts(self) -> List:
        """Returns the list of connected hosts.

        :return List: List of connected host objects.
        """
        return self.connected_hosts

    def remove_connected_host(self, host) -> None:
        """Removes a host from the list of connected hosts.

        :param Host host: Host object to remove.
        """
        self.connected_hosts = [
            h for h in self.connected_hosts if h.name != host.name
        ]

    def get_connected_hostnames(self) -> List[str]:
        """Returns the list of hostnames of connected hosts.

        :return List[str]: List of hostnames.
        """
        return [host.name for host in self.connected_hosts]

    def get_nexthop_from_routes(self):
        """Placeholder for a method to determine the next hop from routing
        tables."""
        raise NotImplementedError('This method needs to be implemented.')
