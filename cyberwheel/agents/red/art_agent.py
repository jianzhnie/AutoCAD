from typing import Any, Dict, List, Optional, Tuple, Type

from cyberwheel.agents.red.actions import (ARTDiscovery, ARTImpact,
                                           ARTKillChainPhase,
                                           ARTLateralMovement, ARTPingSweep,
                                           ARTPortScan, ARTPrivilegeEscalation,
                                           RedActionResults, art_techniques)
from cyberwheel.agents.red.red_agent_base import (AgentHistory, HybridSetList,
                                                  KnownHostInfo,
                                                  KnownSubnetInfo, RedAgent)
from cyberwheel.agents.red.strategies import RedStrategy, ServerDowntime
from cyberwheel.network import Host, Network
from cyberwheel.reward import RewardMap


class ARTAgent(RedAgent):
    """An Atomic Red Team (ART) Red Agent that uses a defined Killchain to
    attack hosts in a particular order.

    Before going down the killchain on a host, the agent must Pingsweep the host's subnet and Portscan the host.
    These actions are defined to specific ART Techniques, and always succeed. After portscanning, the agent can start
    attacking down the killchain on a host.
    The KillChain in this case:
    1. ARTDiscovery - Chooses a 'discovery' Atomic Red Team technique to attack the host. Also exposes the Host's CVEs to the attacker.
    2. ARTPrivilegeEscalation - Chooses a 'privilege-escalation' Atomic Red Team technique to attack the host. Also escalates its privileges to 'root'
    3. ARTImpact - Chooses an 'impact' Atomic Red Team technique to attack the host.

    General Logic:
    - The agent will start on a given Host, with its CVEs, ports, subnet, and vulnerabilities already scanned.
    - At each step the agent will
        - Determine which Host is its target_host with its given red strategy (ServerDowntime by default)
        - Run a Pingsweep on the target_host's subnet if not already scanned
        - Run a Portscan on target_host, revealing services and vulnerabilities, if not already scanned
        - Run LateralMovement to hack into target_host if not already physically on target_host
        - On target_host, the agent will run the next step of the Killchain.
            - For example, if it has already run Discovery on the target_host, it will run PrivilegeEscalation

    Important member variables:

    * `entry_host`: required
        - The host for the red agent to start on. The agent will have info on the Host's ports, subnet (list of other hosts in subnet), and CVEs.
        - NOTE: This will be used as the initial value of the class variable `current_host`. This will track which Host the red agent is currently on.

    * `name`: optional
        - Name of the Agent.
        - Default: 'ARTAgent'

    * `network`: required
        - The network that the red agent will explore.

    * `killchain`: optional
        - The sequence of Actions the Red Agent will take on a given Host.
        - Default: [ARTDiscovery, ARTPrivilegeEscalation, ARTImpact]
        - NOTE: This is currently only tested with the default Killchain.

    * `red_strategy`: optional
        - The logic that the red agent will use to select it's next target.
        - This is implemented as separate class to allow modularity in red agent implementations.
        - Default: ServerDowntime

    * `service_mapping`: optional
        - A mapping that is initialized with a network, dictating with a bool, whether a given Technique will be valid on a given Host.
        - This is generated and passed before initialization to avoid checking for CVEs for every environment if running parallel.
        - Default: {} (if empty, will generate during __init__())


    The agent follows these steps:
        1. Pingsweep the target host's subnet if not already scanned.
        2. Portscan the target host to reveal services and vulnerabilities if not already scanned.
        3. Perform lateral movement if not already on the target host.
        4. Execute the next phase of the kill chain on the target host (Discovery, Privilege Escalation, Impact).

    Attributes:
        name (str): Name of the Agent.
        killchain (List[Type[ARTKillChainPhase]]): Sequence of actions the Red Agent will take on a given Host.
        current_host (Host): The host where the agent is currently located.
        history (AgentHistory): Tracks the agent's history on the network.
        network (Network): The network that the red agent will explore.
        unimpacted_servers (HybridSetList): Set of servers that have not been impacted.
        unknowns (HybridSetList): Set of unknown hosts.
        strategy (RedStrategy): Strategy for selecting the next target.
        services_map (Dict[str, Dict[Type[ARTKillChainPhase], List[str]]]): Mapping of host services and valid techniques.
    """

    def __init__(
        self,
        entry_host: Host,
        network: Network,
        name: str = 'ARTAgent',
        killchain: Optional[List[Type[ARTKillChainPhase]]] = None,
        red_strategy: Optional[RedStrategy] = None,
        service_mapping: Optional[Dict[str, Dict[Type[ARTKillChainPhase],
                                                 List[str]]]] = None,
    ):
        """Initialize the ARTAgent with the specified parameters.

        Args:
            entry_host (Host): The host for the red agent to start on.
            network (Network): The network that the red agent will explore.
            name (str): Name of the Agent.
            killchain (List[Type[ARTKillChainPhase]]): Sequence of actions the Red Agent will take on a given Host.
            red_strategy (RedStrategy): Logic that the red agent will use to select its next target.
            service_mapping (Dict[str, Dict[Type[ARTKillChainPhase], List[str]]]): Mapping of host services and valid techniques.
        """
        self.name: str = name
        self.killchain: List[Type[ARTKillChainPhase]] = killchain or [
            ARTDiscovery,
            ARTPrivilegeEscalation,
            ARTImpact,
        ]
        self.current_host: Host = entry_host
        self.history: AgentHistory = AgentHistory(initial_host=entry_host)
        self.network: Network = network
        self.initial_host_names: set[str] = set(self.network.get_host_names())
        self.unimpacted_servers: HybridSetList = HybridSetList()
        self.unknowns: HybridSetList = HybridSetList()
        self.strategy: RedStrategy = red_strategy or ServerDowntime()
        self.all_kcps: List[
            Type[ARTKillChainPhase]] = self.killchain + [ARTLateralMovement]

        self.services_map: Dict[str,
                                Dict[Type[ARTKillChainPhase], List[str]]] = (
                                    service_mapping if service_mapping else
                                    self._initialize_service_mapping())

        self.tracked_hosts: set[str] = set(self.services_map.keys())

    def _initialize_service_mapping(
        self, ) -> Dict[str, Dict[Type[ARTKillChainPhase], List[str]]]:
        """Initialize the service mapping for all hosts in the network."""
        service_mapping = {}
        for host in self.network.get_all_hosts():
            service_mapping[host.name] = self.get_valid_techniques_by_host(
                host, self.all_kcps)
        return service_mapping

    @classmethod
    def get_service_map(
        cls, network: Network
    ) -> Dict[str, Dict[Type[ARTKillChainPhase], List[str]]]:
        """Generate the service mapping for all hosts in the network."""
        killchain = [
            ARTDiscovery,
            ARTPrivilegeEscalation,
            ARTImpact,
            ARTLateralMovement,
        ]
        service_mapping = {}
        for host in network.get_hosts():
            service_mapping[host.name] = cls.get_valid_techniques_by_host(
                host, killchain)
        return service_mapping

    @staticmethod
    def get_valid_techniques_by_host(
        host: Host, all_kcps: List[Type[ARTKillChainPhase]]
    ) -> Dict[Type[ARTKillChainPhase], List[str]]:
        """Get valid techniques for a given host and kill chain phases."""
        valid_techniques = {}
        for kcp in all_kcps:
            valid_techniques[kcp] = []
            kcp_valid_techniques = kcp.validity_mapping[host.os][
                kcp.get_name()]
            for mid in kcp_valid_techniques:
                technique = art_techniques.technique_mapping[mid]
                if len(host.host_type.cve_list & technique.cve_list) > 0:
                    valid_techniques[kcp].append(mid)
        return valid_techniques

    def handle_network_change(self) -> None:
        """Check and handle any newly added hosts in the network."""
        current_hosts = set(self.network.get_host_names())
        new_hosts = current_hosts - self.tracked_hosts

        for host_name in new_hosts:
            new_host: Host = self.network.get_node_from_name(host_name)
            self.services_map[
                new_host.name] = self.get_valid_techniques_by_host(
                    new_host, self.all_kcps)
            self.tracked_hosts.add(new_host.name)

            # Add new host to history if subnet is already scanned
            scanned_subnets = {
                self.history.mapping[s]
                for s, v in self.history.subnets.items() if v.is_scanned()
            }
            if new_host.subnet in scanned_subnets:
                self.history.mapping[new_host.name] = new_host
                self.history.hosts[new_host.name] = KnownHostInfo()
                self.unknowns.add(new_host.name)

    def select_next_target(self) -> Host:
        """Select the next target host based on the red strategy."""
        return self.strategy.select_target(self)

    def run_action(
            self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """Execute the appropriate action based on the target host's state.

        Args:
            target_host (Host): The target host of the attack.

        Returns:
            Tuple[RedActionResults, Type[ARTKillChainPhase]]: Results of the action and the action type.
        """
        host_info = self.history.hosts[target_host.name]
        step = min(host_info.get_next_step(), len(self.killchain) - 1)

        if not host_info.ping_sweeped:
            return self._ping_sweep(target_host)
        elif not host_info.ports_scanned:
            return self._port_scan(target_host)
        elif self.current_host.name != target_host.name:
            return self._lateral_move(target_host)

        action = self.killchain[step]
        return action(
            self.current_host, target_host,
            self.services_map[target_host.name][action]).sim_execute(), action

    def _ping_sweep(
            self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """Perform a ping sweep on the target host's subnet."""
        action_results = ARTPingSweep(self.current_host,
                                      target_host).sim_execute()
        if action_results.attack_success:
            for host in target_host.subnet.connected_hosts:
                # Create Red Agent History for host if not in there
                if host.name not in self.history.hosts:
                    self.history.hosts[host.name] = KnownHostInfo(sweeped=True)
                    self.unknowns.add(host.name)
                else:
                    self.history.hosts[host.name].ping_sweeped = True

                if host.name not in self.history.mapping:
                    self.history.mapping[host.name] = host

        return action_results, ARTPingSweep

    def _port_scan(
            self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """Perform a port scan on the target host."""
        action_results = ARTPortScan(self.current_host,
                                     target_host).sim_execute()
        if action_results.attack_success:
            self.history.hosts[target_host.name].ports_scanned = True
        return action_results, ARTPortScan

    def _lateral_move(
            self, target_host: Host
    ) -> Tuple[RedActionResults, Type[ARTKillChainPhase]]:
        """Perform lateral movement to the target host."""
        action_results = ARTLateralMovement(
            self.current_host,
            target_host,
            self.services_map[target_host.name][ARTLateralMovement],
        ).sim_execute()
        if action_results.attack_success:
            self.current_host = target_host
        return action_results, ARTLateralMovement

    def act(self) -> Type[ARTKillChainPhase]:
        """Executes the red agent's action at each step of the simulation.

        This method:
        1. Handles any newly added hosts.
        2. Selects the next target host.
        3. Runs an action on the target host based on the kill chain.
        4. Updates metadata and history based on the action's outcome.

        Returns:
            Type[ARTKillChainPhase]: The type of action performed.
        """
        # Handle any changes in the network, such as new decoy hosts.
        self.handle_network_change()

        # Select the next target host based on the agent's strategy.
        target_host = self.select_next_target()

        # Run the appropriate action on the target host.
        action_results, action = self.run_action(target_host)
        success = action_results.attack_success

        # List of actions that do not require updating the kill chain step.
        no_update = [ARTLateralMovement, ARTPingSweep, ARTPortScan]

        if success:
            # Update the kill chain step if the action requires it.
            if action not in no_update:
                self.history.hosts[target_host.name].update_killchain_step()

            # Add host information to the agent's history based on action metadata.
            for h_name, metadata in action_results.metadata.items():
                self.add_host_info(h_name, metadata)

            # Handle specific actions like Impact, updating the server status.
            if action == ARTImpact:
                self.history.hosts[target_host.name].impacted = True
                if self.history.hosts[target_host.name].type == 'Server':
                    self.unimpacted_servers.remove(target_host.name)

        # Update the agent's history with the action and results.
        self.history.update_step(action, action_results)
        return action

    def add_host_info(self, host_name: str, metadata: Dict[str, Any]) -> None:
        """Adds metadata to the Red Agent's history/knowledge.

        This method processes metadata, which can include host type, IP address,
        and subnet scanning information. It updates the agent's internal state
        and knowledge about the network.

        Args:
            host_name (str): The name of the host to update.
            metadata (Dict[str, Any]): Metadata in JSON format with key-value pairs.

        Supported Metadata Keys:
            - `ip_address`: str
                - Adds newly found Host with IP address to Red Agent view.
            - `type`: str
                - Adds the Host type (e.g., Server, User) to history.
            - `subnet_scanned`: Subnet
                - Updates subnet information, including connected hosts and available IPs.
        """
        for key, value in metadata.items():
            if key == 'type':
                # Update the host type and associated metadata.
                host_type = value
                known_type = 'Unknown'
                if 'server' in host_type.lower():
                    known_type = 'Server'
                    self.unimpacted_servers.add(host_name)
                    self.unknowns.remove(host_name)
                elif 'workstation' in host_type.lower():
                    known_type = 'User'
                    self.unknowns.remove(host_name)
                self.history.hosts[host_name].type = known_type

            elif key == 'subnet_scanned':
                # Update subnet information in the agent's history.
                subnet = value
                if subnet.name not in self.history.subnets:
                    self.history.mapping[subnet.name] = subnet
                    self.history.subnets[subnet.name] = KnownSubnetInfo(
                        scanned=True)
                    self.history.subnets[
                        subnet.name].connected_hosts = subnet.connected_hosts
                    self.history.subnets[
                        subnet.name].available_ips = subnet.available_ips
                    self.history.subnets[subnet.name].scan()
                elif subnet.name not in self.history.mapping:
                    self.history.mapping[subnet.name] = subnet
                    self.history.subnets[subnet.name] = KnownSubnetInfo(
                        scanned=False)

                # Add newly discovered hosts to the agent's knowledge.
                for host in subnet.connected_hosts:
                    if host.name not in self.history.hosts:
                        self.history.mapping[host.name] = host
                        self.history.hosts[host.name] = KnownHostInfo()
                        self.unknowns.add(host.name)

            elif key == 'ip_address':
                # Update host IP address information.
                if host_name not in self.history.hosts:
                    self.history.hosts[host_name] = KnownHostInfo(
                        ip_address=value.ip_address)
                    self.unknowns.add(host_name)
                    self.history.mapping[host_name] = value

    def get_reward_map(self) -> RewardMap:
        """Retrieve the reward mapping for the red agent.

        The reward map defines the cost and value of different actions based
        on the agent's strategy. For example, Impact might have a high cost
        compared to Discovery.

        Returns:
            RewardMap: The reward map defining action values.
        """
        return self.strategy.get_reward_map()

    def reset(self, entry_host: Host, network: Network) -> None:
        """Reset the red agent to its initial state, effectively restarting the
        simulation.

        This method reinitializes the agent's network, current host, history,
        and lists of unimpacted servers and unknown hosts.

        Args:
            entry_host (Host): The initial entry point host for the agent.
            network (Network): The network the agent will operate within.
        """
        self.network = network
        self.current_host = entry_host
        self.history = AgentHistory(initial_host=entry_host)
        self.initial_host_names = set(self.network.get_host_names())
        self.unimpacted_servers = HybridSetList()
        self.unknowns = HybridSetList()
