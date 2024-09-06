"""这个代码实现了一个简单的网络路由和防火墙规则管理系统，使用了Python的pydantic库来进行数据验证。
它主要包含三个类：Route、RoutingTable和NetworkObject。"""

import ipaddress as ipa
from typing import Generator, Union

from pydantic import BaseModel

# ipaddress: 提供IP地址和网络操作的工具，这里用于处理IPv4和IPv6地址。
# pydantic: 一个数据验证库，BaseModel是它的基类，用于创建数据模型并进行验证。


class Route(BaseModel):
    """该类表示一个路由条目，包含目标网络(dest)和下一跳地址(via)。 属性：

    - dest：目标网络，可以是 IPv4 或 IPv6 网络对象。
    - via：下一跳地址，可以是 IPv4 或 IPv6 地址对象。
    """

    dest: Union[ipa.IPv4Network, ipa.IPv6Network]
    via: Union[ipa.IPv4Address, ipa.IPv6Address]

    def __hash__(self):
        # __hash__方法使得Route对象可以作为字典的键或存储在集合中。
        return hash((self.dest, self.via))


# Not using this just yet
class RoutingTable(BaseModel):
    """功能：管理路由条目的集合。

    属性：
        - routes：一个包含 Route 对象的集合，用于存储所有的路由条目。

    方法：
        - add_route：添加新的路由条目到路由表中。
        - get_routes：返回所有的路由条目。
        - iter_routes：以生成器的形式迭代路由条目，便于逐条处理。
    """

    routes: set[Route]

    def add_route(self, route: Route) -> None:
        self.routes.add(route)

    def get_routes(self) -> set[Route]:
        return self.routes

    def iter_routes(self) -> Generator[Route, None, None]:
        for route in self.routes:
            yield route


class FirewallRule(BaseModel):
    """功能：定义防火墙规则，包含规则名称、源地址、端口、协议和描述信息。

    Args:
        name：规则名称，默认值为 "allow all"。
        src：源地址，默认值为 "all"。
        port：端口号，默认值为 "all"。
        proto：协议类型，默认值为 "tcp"。
        desc：规则描述信息，默认为 None。

    方法：
        __eq__：用于比较两个 FirewallRule 对象是否相等，主要比较源地址、端口和协议字段。
    """

    name: str = 'allow all'
    src: str = 'all'
    port: Union[int, str] = 'all'
    proto: str = 'tcp'
    desc: Union[str, None] = None

    def __eq__(self, other) -> bool:
        if isinstance(other, FirewallRule):
            src_matched = self.src == other.src
            port_matched = self.port == other.port
            proto_matched = self.proto == other.proto
            return src_matched and port_matched and proto_matched
        return False


class NetworkObject:
    """Base class for host, subnet, and router objects. 功能：NetworkObject 是主类,
    表示网络中的一个对象（如主机、子网或路由器），管理该对象的路由条目和防火墙规则。

    属性：
        name：网络对象的名称。
        firewall_rules：防火墙规则列表。
        is_compromised：表示该网络对象是否被攻破，初始值为 False。
        default_route：默认路由，初始值为 None。
        routes：一个包含 Route 对象的集合，用于存储路由条目。

    方法：
        防火墙规则管理：
            add_firewall_rule：添加一条新的防火墙规则。
            add_firewall_rules：添加多条防火墙规则。
            remove_firewall_rule：移除指定名称的防火墙规则。

        IP和网络对象生成：
            generate_ip_object：从字符串生成一个 IP 地址对象。
            generate_ip_network_object：从字符串生成一个网络对象（IPv4 或 IPv6）。

        路由管理：
            generate_route：从目标网络和下一跳地址生成一个路由条目。
            generate_route_from_str：从字符串生成一个路由条目。
            add_route：将一个路由条目添加到当前对象的路由集合中。
            get_routes：返回该对象的所有路由条目。
            get_default_route：返回该对象的默认路由。
            add_routes_from_dict：从字典列表中批量添加路由条目。
            get_nexthop_from_routes：根据目的 IP 地址查询匹配的下一跳地址（选择最具体的匹配路由）。
    """

    def __init__(self, name, firewall_rules: Union[FirewallRule, None]):
        self.name = name
        # default to 'allow all' if no rules defined
        # this is antithetical to how firewalls work in the real world,
        # but seemed pragmatic in our case
        self.firewall_rules = firewall_rules
        self.is_compromised = False
        self.default_route = None
        self.routes = set()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NetworkObject):
            return self.name == other.name
        return False

    # 防火墙规则管理
    def add_firewall_rule(self, rule: FirewallRule) -> None:
        """添加/移除防火墙规则。 Adds new firewall rule.

        :param FirewallRule rule: firewall rule
        """
        self.firewall_rules.append(rule)

    def add_firewall_rules(self, rules: list[FirewallRule]) -> None:
        """# 用于从字符串生成IP地址和网络对象。 Adds new firewall rules.

        :param list[FirewallRule] rules: list of firewall rule(s)
        """
        self.firewall_rules.extend(rules)

    # TODO: refactor for FirewallRule
    def remove_firewall_rule(self, rule_name: str):
        """Removes an existing firewall rule.

        :param str rule_name: name of existing fw rule
        """
        updated_rules = [
            rule for rule in self.firewall_rules if rule.name != rule_name
        ]

        # update firewall rules
        self.firewall_rules = updated_rules

    # 生成IP地址和网络对象
    def generate_ip_object(self,
                           ip: str) -> Union[ipa.IPv4Address, ipa.IPv6Address]:
        try:
            return ipa.ip_address(ip)
        except ValueError as e:
            # TODO: raise custom exception here?
            raise e

    # 用于从字符串生成IP地址和网络对象。
    def generate_ip_network_object(
            self, net: str) -> Union[ipa.IPv4Network, ipa.IPv6Network]:
        try:
            return ipa.ip_network(net)
        except ValueError as e:
            # TODO: raise custom exception here?
            raise e

    # 生成路由
    def generate_route(
        self,
        dest_net: Union[ipa.IPv4Network, ipa.IPv6Network],
        via_ip: Union[ipa.IPv4Address, ipa.IPv6Address],
    ) -> Route:
        """根据目标网络和下一跳地址生成一个Route对象。

        Generate a Route object from dest network and nexthop IP

        :param IPv4Network | IPv6Network dest: destination network
        :param IPv4Address | IPv6Address via: next hop IP
        :raises ValueError:
        """
        return Route(dest=dest_net, via=via_ip)

    def generate_route_from_str(self, dest_net: str, via_ip: str) -> Route:
        """Generate a Route object from dest network and nexthop IP.

        :param str dest: destination network
        :param str via: next hop IP
        :raises ValueError:
        """
        try:
            dest: Union[ipa.IPv4Network,
                        ipa.IPv6Network] = ipa.ip_network(dest_net)
            via: Union[ipa.IPv4Address,
                       ipa.IPv6Address] = ipa.ip_address(via_ip)
        except ValueError as e:
            # TODO: raise custom exception?
            raise e
        return Route(dest=dest, via=via)

    # 路由管理
    def add_route(self, route: Route) -> None:
        self.routes.add(route)

    def get_routes(self):
        # should the default route be preppended to this list?
        routes = self.routes
        routes.add(self.default_route)
        return routes

    def get_default_route(self):
        return self.default_route

    def add_routes_from_dict(self, routes: list[dict]):
        for route in routes:
            # make sure 'dest' is an ip_network object
            try:
                if not isinstance(route['dest'], Union[ipa.IPv4Network,
                                                       ipa.IPv6Network]):
                    dest = self.generate_ip_network_object(route['dest'])
                else:
                    dest = route['dest']
            except ValueError as e:
                # TODO: custom exception here?
                raise e
            # make sure 'via' is an ip_address object
            try:
                if not isinstance(route['via'], Union[ipa.IPv4Address,
                                                      ipa.IPv6Address]):
                    via = self.generate_ip_object(route['via'])
                else:
                    via = route['via']
            except ValueError as e:
                # TODO: custom exception here?
                raise e
            self.add_route(route=Route(dest=dest, via=via))

    #  获取与目标IP匹配的下一跳地址（最具体的匹配）。
    def get_nexthop_from_routes(self, dest_ip: Union[ipa.IPv4Address,
                                                     ipa.IPv6Address]):
        """Return most specific route that matches dest_ip.

        :param (IPv4Address | IPv6Address) dest_ip: destination IP object
        :returns (IPv4Address | IPv6Address):
        """
        # sort routes
        routes = sorted(list(self.routes))

        # reverse list because ipaddress' logical operators are weird
        # and sort by subnet mask bits instead of number of ips in subnet
        # i.e. this should give us a list with smallest subnets first
        routes.reverse()

        # find most specific match in routes
        for route in routes:
            if dest_ip in route.dest.hosts():
                return route.via

        # return default_route if no matche
        return self.default_route.via  # type: ignore
