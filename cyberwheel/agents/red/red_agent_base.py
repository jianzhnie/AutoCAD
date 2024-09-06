import random
from abc import ABC, abstractmethod
from ipaddress import IPv4Address, IPv6Address
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from cyberwheel.agents.red.actions import (ARTAction, ARTKillChainPhase,
                                           RedActionResults)
from cyberwheel.network import Host, Service, Subnet
from cyberwheel.reward import RewardMap


class RedAgent(ABC):
    """Base class for Red Agent.

    Defines the structure for any additional red agents to be added. This class
    serves as a blueprint for creating different types of Red Agents.
    """

    def __init__(self) -> None:
        """Initialize a RedAgent object.

        Since this is an abstract class, it does not implement specific
        functionality.
        """
        pass

    @abstractmethod
    def act(self) -> Type[ARTKillChainPhase]:
        """Define the behavior or action taken by the Red Agent.

        This method should be implemented by subclasses to determine the phase of the attack
        in the MITRE ATT&CK kill chain.

        Returns:
            Type[ARTKillChainPhase]: The next phase of the kill chain to execute.
        """
        pass

    @abstractmethod
    def handle_network_change(self) -> None:
        """Handle any network changes that might affect the Red Agent's
        actions.

        Subclasses should implement this method to define how the agent adjusts
        its strategy in response to changes in the network.
        """
        pass

    @abstractmethod
    def select_next_target(self) -> Tuple[Optional[Host], bool]:
        """Select the next target for the Red Agent.

        This method should be implemented by subclasses to decide which host to target next.
        The method can return None if no target is available.

        Returns:
            Tuple[Optional[Host], bool]: A tuple containing the selected Host (or None) and a boolean
                                         indicating if the selection was successful or not.
        """
        pass

    @abstractmethod
    def get_reward_map(self) -> RewardMap:
        """Get the reward map for the Red Agent.

        This method should be implemented by subclasses to return the reward structure that
        the agent uses to evaluate the success of its actions.

        Returns:
            RewardMap: The reward map used by the agent.
        """
        pass

    @abstractmethod
    def run_action(self) -> None:
        """Execute the current action for the Red Agent.

        Subclasses should implement this method to define the specific action
        that the agent will perform.
        """
        pass

    @abstractmethod
    def add_host_info(self) -> None:
        """Add information about a host to the Red Agent's knowledge base.

        Subclasses should implement this method to define how the agent
        collects and stores information about hosts.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the state of the Red Agent.

        This method should be implemented by subclasses to reset the agent to
        its initial state, clearing any internal state or data in preparation
        for a new run.
        """
        pass


class KnownHostInfo:
    """Defines the Red Agent's knowledge of a given host.

    Attributes:
        last_step (int): Index of the last step of the kill chain executed on this host. Default is -1.
        ports_scanned (bool): Whether the host has been port scanned.
        ping_sweeped (bool): Whether the host's subnet has been ping swept.
        ip_address (Optional[Union[IPv4Address, IPv6Address]]): IP address of the host.
        type (str): The known type of the host. Options are 'Unknown', 'User', or 'Server'. Default is 'Unknown'.
        services (List[Service]): The known services on the host.
        vulnerabilities (List[str]): The known vulnerabilities on the host.
        routes (Optional): The routing information for the host (defaults to None).
        impacted (bool): Whether the host has been impacted by an attack.
    """

    def __init__(
        self,
        last_step: int = -1,
        scanned: bool = False,
        sweeped: bool = False,
        ip_address: Optional[Union[IPv4Address, IPv6Address]] = None,
        type: str = 'Unknown',
        services: Optional[List[Service]] = None,
        vulnerabilities: Optional[List[str]] = None,
    ) -> None:
        """Initialize a KnownHostInfo object.

        Args:
            last_step (int): The last step executed on the host. Default is -1.
            scanned (bool): Whether the host has been port scanned. Default is False.
            sweeped (bool): Whether the host's subnet has been ping swept. Default is False.
            ip_address (Optional[Union[IPv4Address, IPv6Address]]): The IP address of the host.
            type (str): The known type of the host. Default is 'Unknown'.
            services (Optional[List[Service]]): The known services on the host. Default is an empty list.
            vulnerabilities (Optional[List[str]]): The known vulnerabilities on the host. Default is an empty list.
        """
        self.last_step = last_step
        self.ports_scanned = scanned
        self.ping_sweeped = sweeped
        self.ip_address = ip_address
        self.type = type
        self.services = services if services is not None else []
        self.vulnerabilities = vulnerabilities if vulnerabilities is not None else []
        self.routes = None  # TODO: If route not set, defaults to Router and local Subnet-level network
        self.impacted = False

    def scan(self) -> None:
        """Mark the host as port scanned."""
        self.ports_scanned = True

    def is_scanned(self) -> bool:
        """Check if the host has been port scanned.

        Returns:
            bool: True if the host has been port scanned, False otherwise.
        """
        return self.ports_scanned

    def update_killchain_step(self) -> None:
        """Increment the last step of the kill chain executed on this host."""
        self.last_step += 1

    def get_next_step(self) -> int:
        """Get the next step of the kill chain for this host.

        Returns:
            int: The next step in the kill chain.
        """
        return self.last_step + 1


class KnownSubnetInfo:
    """Defines the Red Agent's knowledge of a given subnet.

    Attributes:
        scanned (bool): Whether the subnet has been ping swept.
        connected_hosts (List[KnownHostInfo]): List of hosts in the subnet.
        available_ips (List[str]): The IP addresses available for the subnet to distribute.
    """

    def __init__(self, scanned: bool = False) -> None:
        """Initialize a KnownSubnetInfo object.

        Args:
            scanned (bool): Whether the subnet has been ping swept. Default is False.
        """
        self.scanned = scanned
        self.connected_hosts: List[KnownHostInfo] = []
        self.available_ips: List[str] = []

    def scan(self) -> None:
        """Mark the subnet as ping swept."""
        self.scanned = True

    def is_scanned(self) -> bool:
        """Check if the subnet has been ping swept.

        Returns:
            bool: True if the subnet has been ping swept, False otherwise.
        """
        return self.scanned


class AgentHistory:
    """Defines the history of the red agent throughout the game.

    Attributes:
        history (List[Dict[str, Any]]): List of metadata detailing red agent actions. Grows with each step.
        red_action_history (List[RedActionResults]): List of action results for every given step.
        mapping (Dict[str, Union[Host, Subnet]]): Mapping from host/subnet name to Host/Subnet object for information gathering.
        hosts (Dict[str, KnownHostInfo]): Dictionary of hostnames mapped to KnownHostInfo objects.
        subnets (Dict[str, KnownSubnetInfo]): Dictionary of subnet names mapped to KnownSubnetInfo objects.
        step (int): The last step of the simulation.
    """

    def __init__(self, initial_host: Host) -> None:
        """Initialize an AgentHistory object.

        Args:
            initial_host (Host): The initial entry host for the red agent to establish a foothold on the network.
        """
        self.history: List[Dict[str, Any]] = [
        ]  # List of step information detailing actions by step
        self.red_action_history: List[RedActionResults] = []
        self.mapping: Dict[str, Union[Host, Subnet]] = {}
        self.hosts: Dict[str, KnownHostInfo] = {}
        self.subnets: Dict[str, KnownSubnetInfo] = {}
        self.step: int = -1

        # Initialize with the initial host's information
        self.hosts[initial_host.name] = KnownHostInfo(
            ip_address=initial_host.ip_address)
        self.subnets[initial_host.subnet.name] = KnownSubnetInfo()
        self.mapping[initial_host.name] = initial_host
        self.mapping[initial_host.subnet.name] = initial_host.subnet

    def update_step(
        self,
        action: Type[ARTAction],
        red_action_results: RedActionResults,
    ) -> None:
        """Updates the history of the red agent at a given step with action and
        RedActionResults metadata.

        Args:
            action (Type[ARTAction]): The action taken by the red agent.
            red_action_results (RedActionResults): The results of the action.
        """
        self.step += 1
        target_host_metadata = red_action_results.metadata[
            red_action_results.target_host.name]
        techniques = {
            'mitre_id': target_host_metadata['mitre_id'],
            'technique': target_host_metadata['technique'],
            'commands': target_host_metadata['commands'],
        }
        self.history.append({
            'step': self.step,
            'action': action.__name__,
            'src_host': red_action_results.src_host.name,
            'target_host': red_action_results.target_host.name,
            'techniques': techniques,
            'success': red_action_results.attack_success,
        })
        self.red_action_history.append(red_action_results)

    def recent_history(self) -> RedActionResults:
        """Get the most recent action result.

        Returns:
            RedActionResults: The most recent action result.
        """
        return self.red_action_history[-1]


class HybridSetList:
    """Defines a Hybrid Set/List object.

    This class combines the O(1) time complexity of set membership checks with
    the O(1) time complexity of list operations like random.choice().
    """

    def __init__(self) -> None:
        """Initialize a HybridSetList object."""
        self.data_set: set = set()
        self.data_list: List[Any] = []

    def add(self, value: Any) -> None:
        """Add a value to the set/list if it is not already present.

        Args:
            value (Any): The value to add.
        """
        if value not in self.data_set:
            self.data_set.add(value)
            self.data_list.append(value)

    def remove(self, value: Any) -> None:
        """Remove a value from the set/list if it is present.

        Args:
            value (Any): The value to remove.
        """
        if value in self.data_set:
            self.data_set.remove(value)
            self.data_list.remove(value)

    def get_random(self) -> Any:
        """Get a random value from the list.

        Returns:
            Any: A random value from the list.
        """
        return random.choice(self.data_list)

    def check_membership(self, value: Any) -> bool:
        """Check if a value is in the set.

        Args:
            value (Any): The value to check.

        Returns:
            bool: True if the value is in the set, False otherwise.
        """
        return value in self.data_set

    def length(self) -> int:
        """Get the number of elements in the set.

        Returns:
            int: The number of elements in the set.
        """
        return len(self.data_set)
