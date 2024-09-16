import ipaddress as ipa
import json
import random
from pathlib import Path
from os import PathLike
from pathlib import PosixPath
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import networkx as nx
import yaml
from tqdm import tqdm

from cyberwheel.network.host import Host, HostType
from cyberwheel.network.network_object import (FirewallRule, NetworkObject,
                                               Route)
from cyberwheel.network.router import Router
from cyberwheel.network.service import Service
from cyberwheel.network.subnet import Subnet


class Network:
    """A class to represent a computer network. The Network class allows you to
    add nodes (subnets, routers, hosts), connect them, and perform operations
    like scanning and ping sweeps. It also handles firewall rules and traffic
    checking.

    代码定义了一个`Network`类，该类使用基于图的结构通过NetworkX表示网络基础设施。这个类支持添加路由器、子网和主机等操作，以及在它们之间建立连接和断开连接。
    代码包括各种实用方法，用于管理网络配置、检查连通性、隔离主机和扫描子网以查找活动主机。

    以下是类的关键功能的总结：

    ### 初始化和配置
    - **初始化**：`Network`类使用网络名称、图、诱饵、断开连接的节点和隔离的主机等参数进行初始化。如果未提供图，则创建一个默认的有向图。
    - **从YAML加载**：`create_network_from_yaml` 方法允许从YAML配置文件构建网络。该方法解析文件中的路由器、子网、主机、防火墙规则、服务和接口，并相应地构建网络图。

    ### 节点管理
    - **添加节点**：使用`add_node`、`add_subnet`、`add_router`和`add_host`方法向图中添加不同类型的网络对象（子网、路由器、主机）。
    - **移除节点**：`remove_node`方法从图中移除一个节点。
    - **连接节点**：`connect_nodes`方法在两个节点之间添加一条边，表示连接。
    - **断开连接节点**：`disconnect_nodes`方法移除两个节点之间的边，有效地断开它们。

    ### 主机管理
    - **主机操作**：方法如`get_hosts`、`get_nondecoy_hosts`、`get_host_names`和`get_all_hosts_on_subnet`允许从网络中检索各种类型的主机。
    - **主机隔离**：`isolate_host`方法通过从其子网断开连接来隔离主机。
    - **主机状态**：类包括更新和检查主机被破坏状态的方法。

    ### 连通性和路径查找
    - **查找路径**：`find_path_between_hosts`方法尝试找到网络中两个主机之间的最短路径。`find_host_with_longest_path`方法识别从给定源主机出发路径最长的主机。
    - **可达性**：`is_subnet_reachable`方法检查两个子网之间是否有路径。
    - **流量允许**：`is_traffic_allowed`方法根据防火墙规则评估是否应该允许两个网络对象之间的网络流量。

    ### 可视化
    - **网络可视化**：`draw`方法生成网络图的视觉表示，根据节点类型进行颜色编码，并将图像保存到文件。

    ### 扫描和流量操作
    - **子网扫描**：`scan_subnet`方法扫描子网以查找活动主机和开放端口，尽管其实现不完整。
    - **主机扫描**：`scan_host`方法旨在返回给定主机上的开放端口。
    - **Ping扫描**：`ping_sweep_subnet`方法尝试ping所有子网主机，检查是否允许ICMP流量通过防火墙规则。

    ### 其他
    - **观察和动作空间**：像`get_action_space_size`这样的方法提供了与网络交互的实用工具，例如在模拟环境等更广泛的系统中。

    ### 创建网络
    从YAML文件创建网络：create_network_from_yaml() 方法通过解析YAML配置文件，动态创建网络结构，包括路由器、子网和主机等。


    ### 关键依赖
    - **NetworkX**：用于创建和操作网络图的库。
    - **Matplotlib**：用于可视化网络结构。
    - **YAML**：用于从YAML文件加载网络配置。
    - **TQDM**：在从YAML创建网络期间显示进度条。
    """

    def __init__(
        self,
        name: str = '',
        graph: Optional[nx.Graph] = None,
        decoys: Optional[List[str]] = None,
        disconnected_nodes: Optional[List[str]] = None,
        isolated_hosts: Optional[List[str]] = None,
    ) -> None:
        """Initialize the Network with a name and optionally a predefined
        graph, decoy nodes, disconnected nodes, and isolated hosts.

        :param name: Name of the network.
        :param graph: An existing graph, if any. Defaults to an empty directed graph.
        :param decoys: A list of decoy (honeypot) nodes.
        :param disconnected_nodes: A list of nodes that are disconnected from the main network.
        :param isolated_hosts: A list of hosts that are isolated (no connections).
        """
        self.name = name
        self.graph = (
            graph if graph else nx.DiGraph(name=name)
        )  # Initialize with an empty directed graph if none provided
        self.decoys = decoys if decoys else []
        self.disconnected_nodes = disconnected_nodes if disconnected_nodes else []
        self.isolated_hosts = isolated_hosts if isolated_hosts else []

    def __iter__(self):
        """Iterate over the nodes in the network graph."""
        return iter(self.graph)

    def __len__(self):
        """Return the number of nodes in the network graph."""
        return len(self.graph)

    def copy(self) -> 'Network':
        """Creates a copy of the network with the same name and a copy of the
        graph."""
        return Network(name=self.name, graph=self.graph.copy())

    def get_decoys(self) -> List:
        """Returns the list of decoy nodes in the network."""
        return self.decoys

    def num_decoys(self) -> int:
        """Returns the number of decoy nodes in the network."""
        return len(self.decoys)

    def get_disconnected(self) -> List:
        """Returns the list of disconnected nodes in the network."""
        return self.disconnected_nodes

    def get_connected(self) -> List['Host']:
        """Returns a list of connected hosts in the network that are not
        disconnected."""
        return [
            host for _, host in self.graph.nodes(data='data')
            if isinstance(host, Host) and not host.disconnected
        ]

    def num_disconnected(self) -> int:
        """Returns the number of disconnected nodes in the network."""
        return len(self.disconnected_nodes)

    def add_subnet(self, subnet: Subnet):
        """add subnet.

        Args:
            subnet (_type_): _description_
        """
        self.add_node(subnet)

    def add_router(self, router: Route):
        """add router.

        Args:
            router (_type_): _description_
        """
        self.add_node(router)

    def add_host(self, host: Host):
        """add host.

        Args:
            host (Host): _description_
        """
        self.add_node(host)

    def add_node(self, node: NetworkObject) -> None:
        """Add a network object (host, subnet, router) to the network graph.

        :param node: Network object to add.
        """
        self.graph.add_node(node.name, data=node)

    def remove_node(self, node: NetworkObject) -> None:
        """Remove a network object from the network graph.

        :param node: Network object to remove.
        :raises nx.NetworkXError: If the node is not in the graph.
        """
        try:
            self.graph.remove_node(node.name)
        except nx.NetworkXError as e:
            print(f'Node {node} does not exist in the network.')
            raise e

    def connect_nodes(self, node1: NetworkObject,
                      node2: NetworkObject) -> None:
        """Add an edge between two nodes in the network graph.

        :param node1: First node.
        :param node2: Second node.
        """
        self.graph.add_edge(node1.name, node2.name)

    def isolate_host(self, host: Host, subnet: Subnet) -> None:
        """Isolate a host from its subnet by removing the edge connecting them.

        :param host: Host to isolate.
        :param subnet: Subnet from which to isolate the host.
        """
        host.isolated = True
        self.disconnect_nodes(host.name, subnet.name)

    def disconnect_nodes(self, node1: NetworkObject,
                         node2: NetworkObject) -> None:
        """Disconnect two nodes in the network.

        :param node1: The first node.
        :param node2: The second node.
        """
        self.graph.remove_edge(node1, node2)
        self.disconnected_nodes.append((node1, node2))

    def is_subnet_reachable(self, subnet1: 'Subnet',
                            subnet2: 'Subnet') -> bool:
        """Checks if there is a path between two subnets in the network.

        :param subnet1: First subnet.
        :param subnet2: Second subnet.
        :return: True if there is a path, False otherwise.
        """
        return nx.has_path(self.graph, subnet1.name, subnet2.name)

    def get_random_host(self) -> 'Host':
        """Returns a random host from the network."""
        all_hosts = self.get_hosts()
        return random.choice(all_hosts) if all_hosts else None

    def get_random_user_host(self) -> Union['Host', None]:
        """Returns a random user host (workstation) from the network."""
        user_hosts = [
            host for host in self.get_hosts() if self.is_user_host(host)
        ]
        return random.choice(user_hosts) if user_hosts else None

    def is_user_host(self, host: 'Host') -> bool:
        """Checks if a host is a user host, typically a workstation."""
        return (host.host_type is not None and host.host_type.name is not None
                and 'workstation' in host.host_type.name.lower())

    def get_hosts(self) -> List['Host']:
        """Returns a list of all hosts in the network."""
        return [
            host for _, host in self.graph.nodes(data='data')
            if isinstance(host, Host)
        ]

    def get_host_names(self) -> List[str]:
        """Returns a list of all host names in the network."""
        return [
            host.name for _, host in self.graph.nodes(data='data')
            if isinstance(host, Host)
        ]

    def get_nondecoy_hosts(self) -> List['Host']:
        """Returns a list of all non-decoy hosts in the network."""
        return [
            host for _, host in self.graph.nodes(data='data')
            if isinstance(host, Host) and not host.decoy
        ]

    def update_host_compromised_status(self, host_name: str,
                                       is_compromised: bool) -> None:
        """Update the compromised status of a host.

        :param host: Name of the host.
        :param is_compromised: New compromised status.
        """
        try:
            host_obj = self.get_node_from_name(host_name)
            if host_obj and isinstance(host_obj, Host):
                host_obj.is_compromised = is_compromised
        except KeyError:
            return None  # Return None if host no found

    def check_compromised_status(self, host_name: str) -> Union[bool, None]:
        """Check the compromised status of a host.

        :param host_name: Name of the host.
        :return: Compromised status of the host.
        """
        host_obj = self.get_node_from_name(host_name)
        return (host_obj.is_compromised
                if host_obj and isinstance(host_obj, Host) else None)

    def find_path_between_hosts(self, source_host: str,
                                target_host: str) -> Union[List[str], None]:
        """Find the shortest path between two hosts in the network.

        :param source_host: Name of the source host.
        :param target_host: Name of the target host.
        :return: List of node names in the path, or None if no path exists.
        """
        if source_host not in self.graph or target_host not in self.graph:
            return None  # Source or target not found in the network

        try:
            shortest_path = nx.shortest_path(self.graph,
                                             source=source_host,
                                             target=target_host)

            new_path = []
            for node in shortest_path:
                node_data = self.graph.nodes[node].get('data')

                if isinstance(node_data, Subnet):  # If the node is a Subnet
                    connected_hosts = [
                        neighbor for neighbor in self.graph.neighbors(node)
                        if isinstance(self.graph.nodes[neighbor].get('data'),
                                      Host)
                    ]
                    if connected_hosts:
                        new_path.append(connected_hosts[0]
                                        )  # Replace subnet with connected host
                    else:
                        new_path.append(
                            node)  # No connected host found, keep the subnet
                else:
                    new_path.append(node)  # Keep non-subnet nodes unchanged

            return new_path

        except nx.NetworkXNoPath:
            return None  # No path found between the hosts

    def find_host_with_longest_path(self,
                                    source_host: str) -> Union[Host, None]:
        """Find the host with the longest path from the source host.

        :param source_host: Name of the source host.
        :return: Name of the host with the longest path, or None if no other hosts exist.
        """
        all_hosts = self.get_hosts()

        # Remove the source host from the list
        all_hosts.remove(source_host)

        if not all_hosts:
            return None  # No other hosts in the network

        longest_path_length = -1
        target_host = None

        for host in all_hosts:
            path = self.find_path_between_hosts(source_host, host)
            if path and len(path) > longest_path_length:
                longest_path_length = len(path)
                target_host = host

        return target_host

    def get_action_space_size(self) -> int:
        """Return the number of hosts in the network."""
        return len(self.get_hosts())

    def is_any_subnet_fully_compromised(self) -> bool:
        """Checks if any subnet is fully compromised."""
        all_subnets = self.get_all_subnets()
        for subnet in all_subnets:
            subnet_hosts = self.get_all_hosts_on_subnet(subnet)
            if all(host.is_compromised for host in subnet_hosts):
                return True
        return False

    def set_host_compromised(self, host_id: str, compromised: bool) -> None:
        """Set the compromised status of a host.

        :param host_id: Name of the host.
        :param compromised: New compromised status.
        """

        host_to_modify = self.get_node_from_name(host_id)
        if host_to_modify and isinstance(host_to_modify, Host):
            host_to_modify.is_compromised = compromised

    def draw(self,
             labels: bool = False,
             filename: str = 'networkx_graph.png') -> None:
        """Draw the network graph.

        :param labels: Whether to display node labels (default is False).
        :param filename: Filename to save the graph image (default is "networkx_graph.png").
        """
        color_map = {
            Host: {
                'workstation': 'green',
                'server': 'red',
                'decoy': 'blue',
            },
            Subnet: 'cyan',
            Router: 'orange',
        }
        colors = []

        for _, node in self.graph.nodes(data='data'):
            if isinstance(node, Host):
                if node.decoy:
                    colors.append(color_map[Host]['decoy'])
                else:
                    colors.append(color_map[Host].get(node.host_type.name,
                                                      'black'))
            elif isinstance(node, Subnet):
                colors.append(color_map[Subnet])
            elif isinstance(node, Router):
                colors.append(color_map[Router])
            else:
                colors.append('black')

        # clear
        plt.clf()
        nx.draw(
            self.graph,
            with_labels=labels,
            node_color=colors,
            node_size=30,
            font_size=12,
            font_color='black',
            font_weight='bold',
            edge_color='black',
        )

        # Display the graph
        if filename:
            plt.savefig(filename, format='png')
        else:
            plt.show()

    @classmethod
    def create_network_from_yaml(
        cls,
        network_config: Union[str, PathLike] = None,
        host_config='host_defs_services.yaml',
    ) -> 'Network':
        """Create a network instance from a YAML configuration file.

        :param network_config: Path to the network configuration YAML file.
        :param host_config: Path to the host configuration YAML file.
        :return: Network instance.
        """
        network_config = cls._get_network_config(network_config)
        config = cls._load_yaml_file(network_config)

        # Create Network instance
        network = cls(name=config['network'].get('name'))
        # Load host types
        conf_dir = Path("cyberwheel/resources/configs/host_definitions")
        conf_file = conf_dir.joinpath(host_config)
        types = cls._load_host_types(conf_file)

        # add router to network graph
        cls._build_routers(network, config['routers'])
        # cls._build_subnets(network, config['subnets'])
        cls._build_hosts(network, config['interfaces'], config['hosts'],
                         conf_file, types)

        network.initialize_interfacing()
        return network

    @staticmethod
    def _get_network_config(network_config):
        if network_config is None:
            config_dir = Path("cyberwheel/resources/configs/network")
            network_config: PosixPath = config_dir.joinpath(
                'example_config.yaml')
            print(
                f'Using default network config file ({network_config.absolute()})'
            )
        return network_config

    @staticmethod
    def _load_yaml_file(filepath):
        """Load the YAML config file."""
        with open(filepath, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)

    @staticmethod
    def _load_host_types(conf_file):
        with open(conf_file, '+r') as f:
            type_config = yaml.safe_load(f)
        types = type_config['host_types']
        return types

    @staticmethod
    def _build_routers(network: 'Network', routers_config: Any) -> None:
        """Add router to network graph.

        Args:
            network (Network): _description_
            routers_config (Any): _description_
        """
        # parse routers
        routers = tqdm(routers_config)
        routers.set_description('Building Routers')
        for r in routers:
            routers.set_description(f'Building Routers: {r}', refresh=True)
            router = Router(r, routers_config[r].get('firewall', []))
            network.add_router(router)

    @staticmethod
    def _build_subnets(network: 'Network', subnets_config: Any) -> None:
        """Add subnet to Network.

        Args:
            network (Network): _description_
            subnets_config (Any): _description_
        """
        subnets = tqdm(subnets_config)
        subnets.set_description('Building Subnets')
        for s in subnets:
            subnets.set_description(f'Building Subnets: {s}', refresh=True)
            router: Router = network.get_node_from_name(
                subnets_config[s]['router'])
            subnet = Subnet(
                s,
                subnets_config[s].get('ip_range', ''),
                router,
                subnets_config[s].get('firewall', []),
                dns_server=subnets_config[s].get('dns_server'),
            )
            # Add subnet to network graph
            network.add_subnet(subnet)
            network.connect_nodes(subnet.name, router.name)
            # Add subnet interface to router
            router.add_subnet_interface(subnet)
            # Set default route to router interface for this subnet
            subnet.set_default_route()
            # Assign router first available IP on each subnet
            # Routers have one interface for each connected subnet
            router.set_interface_ip(subnet.name, subnet.available_ips.pop(0))
            # Ensure subnet.dns_server is defined
            # Default to router IP if it's still None
            router_interface_ip = router.get_interface_ip(subnet.name)
            if subnet.dns_server is None and router_interface_ip is not None:
                subnet.set_dns_server(router_interface_ip)

    @staticmethod
    def _build_hosts(
        network: 'Network',
        interface_config: Dict[str, Any],
        hosts_config: Dict[str, Any],
        conf_file: str,
        types: Any,
    ):
        hosts = tqdm(hosts_config)
        hosts.set_description('Building Hosts')
        for host_name in hosts:
            val = hosts_config[host_name]
            fw_rules = []
            # Instantiate firewall rules, if defined
            if rules := val.get('firewall_rules'):
                for rule in rules:
                    fw_rules.append(
                        FirewallRule(
                            name=rule['name'],
                            src=rule.get('src'),
                            port=rule.get('port'),
                            prpto=rule.get('proto'),
                            desc=rule.get('desc'),
                        ))
            else:
                fw_rules.append(FirewallRule())

            # instantiate HostType if defined
            if type_str := val.get('type'):
                host_type = network.create_host_type_from_yaml(
                    type_str, conf_file, types)  # type: ignore
            else:
                host_type = None

            services = []
            if services_dict := val.get('services'):
                for service_id in services_dict:
                    service = services_dict[service_id]
                    services.append(
                        Service(
                            name=service['name'],
                            port=service['port'],
                            protocol=service.get('protocol'),
                            version=service.get('version'),
                            vulns=service.get('vulns'),
                            description=service.get('descscription'),
                            decoy=service.get('decoy'),
                        ))

            interfaces = []
            if host_name in interface_config:
                interfaces = interface_config[host_name]

            # instantiate host
            host = network.add_host_to_subnet(
                name=host_name,
                subnet=network.get_node_from_name(val['subnet']),
                host_type=host_type,
                firewall_rules=fw_rules,
                services=services,
                interfaces=interfaces,
            )
            if routes := val.get('routes'):
                host.add_routes_from_dict(routes)
        network.initialize_interfacing()
        return network

    def get_node_from_name(
            self, node: str) -> Union[NetworkObject, Host, Subnet, Router]:
        """Return network object by name.

        :param node: Node name of the object.
        :return: Network object.
        :raises KeyError: If the node is not found in the network.
        """
        try:
            return self.graph.nodes[node]['data']
        except KeyError as e:
            print(f'{node} not found in {self.name}')
            raise e

    def get_all_subnets(self) -> List[Subnet]:
        """Return a list of all subnets in the network."""
        nodes_tuple = self.graph.nodes(data='data')  # type: ignore
        subnets = [obj for _, obj in nodes_tuple if isinstance(obj, Subnet)]
        return subnets

    def get_all_routers(self) -> List[Router]:
        """Return a list of all routers in the network."""
        nodes_tuple = self.graph.nodes(data='data')  # type: ignore
        routers = [obj for _, obj in nodes_tuple if isinstance(obj, Router)]
        return routers

    def get_all_hosts_on_subnet(self, subnet: Subnet) -> List[Host]:
        """Return a list of all hosts connected to a specified subnet."""
        return subnet.get_connected_hosts()

    def _is_valid_port_number(self, port: Union[str, int]) -> bool:
        """Validate port number.

        :param port: Port number to validate.
        :return: True if valid, False otherwise.
        """
        if isinstance(port, str):
            if port.lower() == 'all':
                return True
            port = int(port)
        if port > 65535 or port < 1:
            return False
        return True

    def scan_subnet(self, src: Host, subnet: Subnet) -> Dict[str, List[int]]:
        """Scan a given subnet and return found IPs and open ports.

        :param src: Source host performing the scan.
        :param subnet: Subnet to scan.
        :return: Dictionary of found IPs and their open ports.
        """
        found_hosts = {}
        return found_hosts

    def scan_host(self, src: Host, ip: str) -> List[int]:
        """Scan a given host and return open ports.

        :param src: Source host performing the scan.
        :param ip: IP address of the target host.
        :return: List of open ports.
        """
        open_ports = []
        return open_ports

    def ping_sweep_subnet(self, src: Host, subnet: Subnet) -> List[str]:
        """Attempt to ping all hosts on a subnet.

        Hosts are only visible to ping if ICMP is allowed by the firewall(s).

        :param src: Source host performing the ping sweep.
        :param subnet: Subnet to ping sweep.
        :return: List of found IPs.
        """
        subnet_hosts = self.get_all_hosts_on_subnet(subnet)
        found_ips = []
        for host in subnet_hosts:
            if self.is_traffic_allowed(src, host, None, 'icmp'):
                found_ips.append(host.ip_address)
        return found_ips

    def is_traffic_allowed(
        self,
        src: NetworkObject,
        dest: NetworkObject,
        port: Union[str, int, None],
        proto: str = 'tcp',
    ) -> bool:
        """Check if network traffic should be allowed based on firewall rules.

        :param src: Source subnet or host of traffic.
        :param dest: Destination subnet or host of traffic.
        :param port: Destination port.
        :param proto: Protocol (i.e. tcp/udp/icmp, default = tcp).
        :return: True if traffic is allowed, False otherwise.
        :raises ValueError: If the port number is invalid.
        """
        # ICMP doesn't use ports (it's considered layer 3)
        if proto.lower() == 'icmp':
            pass
        elif not self._is_valid_port_number(port):
            raise ValueError(f'{port} is not a valid port number')

        def _does_src_match(src, rule: dict, type: str) -> bool:
            if src.name == rule['src'] or rule['src'] == 'all':
                return True
            if type == 'host':
                if (src.subnet.router.name == rule['src']
                        or src.subnet.name == rule['src']):
                    return True
            elif type == 'subnet':
                if src.router.name == rule['src']:
                    return True
            return False

        def _does_dest_match(dest, rule: dict, type: str) -> bool:
            if dest.name == rule['dest'] or rule['dest'] == 'all':
                return True
            if type == 'host':
                if (dest.subnet.router.name == rule['dest']
                        or dest.subnet.name == rule['dest']):
                    return True
            elif type == 'subnet':
                if dest.router.name == rule['dest']:
                    return True
            return False

        def _does_port_match(port: str, rule: dict) -> bool:
            if str(rule['port']) == port or str(rule['port']) == 'all':
                return True
            return False

        def _does_proto_match(proto: str, rule: dict) -> bool:
            if rule['proto'] == proto or rule['proto'] == 'all':
                return True
            return False

        def _check_rules(src, dest, port, proto, type: str) -> bool:
            for rule in dest.firewall_rules:
                if not _does_src_match(src, rule, type):
                    break
                if not _does_dest_match(dest, rule, type):
                    break
                if not _does_port_match(str(port), rule):
                    break
                if not _does_proto_match(proto, rule):
                    break
                return True
            return False

        if isinstance(dest, Host):
            subnet = dest.subnet
            router = subnet.router
            if not _check_rules(src, router, port, proto, 'host'):
                return False
            if not _check_rules(src, subnet, port, proto, 'host'):
                return False
            if not _check_rules(src, dest, port, proto, 'host'):
                return False
            return True
        elif isinstance(dest, Subnet):
            router = dest.router
            if not _check_rules(src, router, port, proto, 'subnet'):
                return False
            if not _check_rules(src, dest, port, proto, 'subnet'):
                return False
            return True
        elif isinstance(dest, Router):
            if not _check_rules(src, dest, port, proto, 'router'):
                return False
            return True

        return False

    def add_host_to_subnet(self, name: str, subnet: Subnet,
                           host_type: HostType, **kwargs) -> Host:
        """Create a host and add it to a specified subnet, assigning IP, DNS,
        and routes.

        :param name: Name of the host.
        :param subnet: Subnet to add the host to.
        :param host_type: Host type.
        :param kwargs: Additional keyword arguments.
        :return: Created host.
        """
        host = Host(
            name,
            subnet,
            host_type,
            firewall_rules=kwargs.get('firewall_rules', []),
            services=kwargs.get('services'),
        )
        self.add_node(host)
        self.connect_nodes(host.name, subnet.name)
        host.get_dhcp_lease()
        host.decoy = kwargs.get('decoy', False)
        return host

    def initialize_interfacing(self) -> None:
        """Initialize interfaces for hosts with multiple interfaces."""
        h_names = [h.name for h in self.get_hosts() if len(h.interfaces) > 0]
        for h in h_names:
            host = self.get_node_from_name(h)
            interface_hosts = []
            for i in host.interfaces:
                interface_hosts.append(self.get_node_from_name(i))
            host.interfaces = interface_hosts

    def remove_host_from_subnet(self, host: Host) -> None:
        """Remove a host from its subnet and release its DHCP lease.

        :param host: Host to remove.
        """
        if host.ip_address is not None:
            ip: Union[ipa.IPv4Address, ipa.IPv6Address] = host.ip_address
            host.subnet.available_ips.append(ip)
        if host in self.get_hosts():
            self.remove_node(host)
            host.subnet.remove_connected_host(host)

    def create_decoy_host(self, *args, **kwargs) -> Host:
        """Create decoy host and add it to subnet and self.graph.

        :param str *name:
        :param Subnet *subnet:
        :param str *type:
        :param list[Service] **services:
        :param IPv4Address | IPv6Address **dns_server:
        """
        host = self.add_host_to_subnet(*args, decoy=True, **kwargs)
        self.decoys.append(host)
        return host

    def remove_decoy_host(self, host: Host) -> None:
        """Remove a decoy host from the network.

        :param host: Decoy host to remove.
        """
        for _, h in self.graph.nodes(data='data'):
            if not isinstance(h, Host):
                continue
            if h.name == host.name:
                self.remove_host_from_subnet(host)
                break
        for i in range(len(self.decoys)):
            if self.decoys[i].name == host.name:
                break
        self.decoys.remove(i)

    def reset(self) -> None:
        """Reset the network to its initial state."""
        for decoy in self.decoys:
            self.remove_host_from_subnet(decoy)
        self.decoys = []

        for edge in self.disconnected_nodes:
            self.connect_nodes(edge[0], edge[1])
        self.disconnected_nodes = []

        self.isolated_hosts = []

        for host in self.get_hosts():
            host.command_history = []
            host.is_compromised = False
            host.isolated = False  # For isolate action
            host.restored = False

    @staticmethod
    def create_host_type_from_json(name: str,
                                   config_file: PathLike) -> HostType:
        """Return a matching HostType object from a JSON config file.

        :param name: Host type name to match against.
        :param config_file: JSON config file path.
        :raises HostTypeNotFoundError: If the host type is not found in the config file.
        :return: HostType object.
        """
        with open(config_file) as f:
            config = json.load(f)
        types: list = config['host_types']

        host_type = [t for t in types if t['type'].lower() == name.lower()]
        if not host_type:
            msg = f'Host type ({name}) not found in config file ({config_file})'
            raise HostTypeNotFoundError(value=name, message=msg)

        services_list = host_type[0]['services']
        service_objects = []
        for service in services_list:
            service_objects.append(
                Service(
                    name=name,
                    port=service.get('port'),
                    protocol=service.get('protocol'),
                    version=service.get('version'),
                    vulns=service.get('vulns'),
                    description=service.get('description'),
                    decoy=service.get('decoy'),
                ))

        decoy = host_type[0].get('decoy', False)
        os = host_type[0].get('os')

        return HostType(name=name,
                        services=service_objects,
                        decoy=decoy,
                        os=os)

    @staticmethod
    def create_host_type_from_yaml(name: str, config_file: PathLike,
                                   types: Dict[str, Any]) -> HostType:
        """Return a matching HostType object from a YAML config file.

        :param name: Host type name to match against.
        :param config_file: YAML config file path.
        :param types: Dictionary of host types.
        :raises HostTypeNotFoundError: If the host type is not found in the config file.
        :return: HostType object.
        """
        host_type = {}
        host_type_name = ''
        for k, v in types.items():
            if k == name.lower():
                host_type_name = k
                host_type = v

        if 'host_type' not in locals():
            msg = f'Host type ({name}) not found in config file ({config_file})'
            raise HostTypeNotFoundError(value=name, message=msg)

        services_list = host_type.get('services', [])

        windows_services = {}
        config_dir = Path("cyberwheel/resources/configs/services")
        config_file_path: PosixPath = config_dir.joinpath(
            'windows_exploitable_services.yaml')
        with open(config_file_path, 'r') as f:
            windows_services = yaml.safe_load(f)

        cve_list = set()
        running_services = []
        for service in services_list:
            temp_service = Service.create_service_from_yaml(
                windows_services, service)
            running_services.append(temp_service)
            cve_list.update(temp_service.vulns)
        decoy: bool = host_type.get('decoy', False)
        os: str = host_type.get('os', '')

        host_type = HostType(
            name=host_type_name,
            services=running_services,
            decoy=decoy,
            os=os,
            cve_list=cve_list,
        )

        return host_type


class HostTypeNotFoundError(Exception):
    """Exception raised when a specified host type is not found in the
    configuration file."""

    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)
