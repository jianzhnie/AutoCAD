from __future__ import annotations

import ipaddress as ipa
import random
from typing import List, Optional, Set, Union

from pydantic import BaseModel

from cyberwheel.network.command import Command
from cyberwheel.network.network_object import NetworkObject
from cyberwheel.network.process import Process
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet


class HostType(BaseModel):
    """Represents the type of a host in the network, defining its
    characteristics like services, processes, vulnerabilities, OS, and decoy
    status."""

    name: Optional[str] = None
    services: Set[Service] = set()
    processes: List[Process] = []
    cve_list: Set[str] = set()
    decoy: bool = False
    os: str = ''


class ArpEntry(BaseModel):
    """Represents a single ARP (Address Resolution Protocol) entry mapping an
    IP address to a MAC address."""

    mac: str
    ip: Union[ipa.IPv4Address, ipa.IPv6Address]


class ArpTable(BaseModel):
    """Represents an ARP table, which is a list of ARP entries mapping IP
    addresses to MAC addresses."""

    table: List[ArpEntry] = []


class Host(NetworkObject):
    """Represents a network host with various attributes like services,
    processes, and networking details.

    Allows managing services, processes, and command execution.
    """

    def __init__(self,
                 name: str,
                 subnet: Subnet,
                 host_type: Optional[HostType] = None,
                 **kwargs):
        """Initialize a Host object with a name, subnet, and optional host
        type.

        :param str name: The name of the host.
        :param Subnet subnet: The subnet to which the host is connected.
        :param HostType host_type: Optional host type, defining services and other attributes.
        :param kwargs: Additional arguments for initializing services or firewall rules.
        """
        super().__init__(name, kwargs.get('firewall_rules', []))
        self.subnet: Subnet = subnet
        self.host_type: Optional[HostType] = host_type
        self.services: List[Service] = kwargs.get('services', [])
        self.is_compromised: bool = False  # Default to not compromised
        self.mac_address: str = self._generate_mac_address()
        self.default_route: Optional[Union[ipa.IPv4Address,
                                           ipa.IPv6Address]] = None
        self.routes: Set[Union[ipa.IPv4Address, ipa.IPv6Address]] = set()
        self.decoy: bool = False
        self.os: str = 'windows'  # Can be 'windows', 'macos', or 'linux'
        self.isolated: bool = False  # For isolate action
        self.interfaces: List[str] = []
        self.restored: bool = False
        self.vulnerabilities: List[str] = []
        self.processes: List[Process] = []
        self.command_history: List[Command] = []
        self.dns_server: Optional[Union[ipa.IPv4Address,
                                        ipa.IPv6Address]] = None

        # Apply any HostType details if provided
        if self.host_type:
            self._apply_host_type(self.host_type)

    def __str__(self) -> str:
        return f'Host(name="{self.name}", subnet="{self.subnet.name}", host_type="{self.host_type}")'

    def __repr__(self) -> str:
        return (
            f'Host(name={self.name!r}, subnet={self.subnet!r}, host_type={self.host_type!r}, '
            f'firewall_rules={self.firewall_rules!r}, services={self.services!r}, '
            f'dns_server={self.dns_server!r})')

    def __deepcopy__(self, memo: dict) -> Host:
        """Creates a deep copy of the Host object."""
        new_host = Host(name=self.name,
                        subnet=self.subnet,
                        host_type=self.host_type)
        memo[id(self)] = new_host

        new_host.decoy = self.decoy
        new_host.interfaces = self.interfaces.copy()
        new_host.services = self.services.copy()
        new_host.mac_address = self.mac_address
        new_host.default_route = self.default_route
        new_host.routes = self.routes.copy()
        new_host.vulnerabilities = self.vulnerabilities.copy()
        new_host.processes = self.processes.copy()
        new_host.dns_server = self.dns_server
        new_host.ip_address = self.ip_address
        return new_host

    def __eq__(self, other: object) -> bool:
        """Compares two Host objects for equality based on their names."""
        if not isinstance(other, Host):
            return False
        return self.name == other.name

    def _apply_host_type(self, host_type: HostType) -> None:
        """Overrides and updates Host attributes from the defined HostType.

        :param HostType host_type: Host type to apply to this host instance.
        """
        # Using sets to join and deduplicate services
        deduped_services = []
        if self.services:
            host_type_services = set(host_type.services)
            host_services = set(self.services)
            deduped_services = list(host_services.union(host_type_services))

        self.services: list[Service] = deduped_services
        self.decoy: bool = host_type.decoy

    @staticmethod
    def _generate_mac_address() -> str:
        """Generates a random MAC address with a fixed prefix.

        :return: Randomly generated MAC address as a string.
        """

        def _generate_hextet() -> str:
            return '{:02x}'.format(random.randint(0, 255))

        mac_prefix = '46:6f:6f'
        return f'{mac_prefix}:{_generate_hextet()}:{_generate_hextet()}:{_generate_hextet()}'

    def set_ip(self, ip: Union[ipa.IPv4Address, ipa.IPv6Address]) -> None:
        """Manually sets the IP address of the host.

        :param Union[ipa.IPv4Address, ipa.IPv6Address] ip: IP address object.
        """
        self.ip_address = ip

    def set_ip_from_str(self, ip: str) -> None:
        """Manually sets the IP address of the host from a string.

        :param str ip: IP address in string format.
        :raises ValueError: If the IP address is invalid.
        """
        self.ip_address = self.generate_ip_object(ip)

    def set_dns(self, ip: Union[ipa.IPv4Address, ipa.IPv6Address]) -> None:
        """Manually sets the DNS IP address of the host.

        :param Union[ipa.IPv4Address, ipa.IPv6Address] ip: IP address object.
        """
        self.dns_server = ip

    def set_dns_from_str(self, ip: str) -> None:
        """Manually sets the DNS IP address of the host from a string.

        :param str ip: IP address in string format.
        :raises ValueError: If the IP address is invalid.
        """
        self.dns_server = self.generate_ip_object(ip)

    def get_dhcp_lease(self) -> None:
        """Obtains an IP lease from a DHCP server within the subnet."""
        self.subnet.assign_dhcp_lease(self)

    def define_services(self, services: List[Service]) -> None:
        """Defines the list of services running on the host.

        :param List[Service] services: List of Service objects.
        """
        self.services = services

    def get_services(self) -> List[Service]:
        """Retrieves the list of services running on the host.

        :return: List of Service objects.
        """
        return self.services

    def add_service(self, name: str, port: int, **kwargs) -> None:
        """Adds a service to the list of services running on the host.

        :param str name: Name of the service.
        :param int port: Port on which the service is running.
        :param kwargs: Additional service details like protocol, version, vulnerabilities, etc.
        """
        service = Service(
            name=name,
            port=port,
            protocol=kwargs.get('protocol', 'tcp'),
            version=kwargs.get('version', ''),
            vulns=kwargs.get('vulns', []),
            description=kwargs.get('desc', ''),
            decoy=kwargs.get('decoy', False),
        )

        if service not in self.services:
            self.services.append(service)
        else:
            # Update the existing service if it already exists
            for existing_service in self.services:
                if service == existing_service:
                    existing_service = service

    def remove_service(self, service_name: str) -> None:
        """Removes an existing service from the list of services running on the
        host.

        :param str service_name: Name of the service to remove (case-insensitive).
        """
        self.services = [
            service for service in self.services
            if service.name.lower() != service_name.lower()
        ]

    def add_process(self, process_name: str,
                    process_privilege_level: str) -> None:
        """Adds a process to the list of processes running on the host.

        :param str name: Name of the process.
        :param kwargs: Additional process details like PID, user, command, etc.
        """
        process = Process(
            name=process_name,
            privilege=process_privilege_level,
        )
        self.processes.append(process)

    def run_command(self, command_exector: Command, command_content: str,
                    privilege: str) -> None:
        """Adds a command to the host's command history.

        :param Command command: Command object representing the executed command.
        """
        command = Command(command_exector, command_content, privilege)
        self.command_history.append(command)

    def remove_process(self, process_name: str) -> None:
        """Removes an existing process from the list of processes running on
        the host.

        :param str process_name: Name of the process to remove (case-insensitive).
        """
        self.processes = [
            process for process in self.processes
            if process.name.lower() != process_name.lower()
        ]

    def kill_malicious_processes(self) -> None:
        """Removes all processes from the host, effectively killing any
        potentially malicious processes."""
        self.processes = []
