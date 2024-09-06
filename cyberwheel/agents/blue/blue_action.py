import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Set

from cyberwheel.network import Host, Network, Service, Subnet


def generate_id() -> str:
    """Returns a UUID4 as a string of hex digits."""
    return uuid.uuid4().hex


class BlueActionReturn:
    """The output of blue actions.

    Attributes:
        id (str): A string that identifies an action with a recurring reward. Should be the empty string otherwise.
        success (bool): Specifies if the action was completely successfully.
        recurring (int): An integer in the range `[-1,1]` specifying how this action affects recurring rewards.
                        `-1` means that this action removes a recurring reward.
                        `0` means this action does not affect recurring rewards.
                        `1` means that this action adds a recurring reward.
    """

    def __init__(self,
                 id: str = '',
                 success: bool = False,
                 recurring: int = 0) -> None:
        self.id = id
        self.success = success
        self.recurring = recurring


class BlueAction(ABC):
    """Base class for all blue actions.

    Attributes:
        network (Network): The environment's network.
        configs (Dict[str, Any]): Config information for the action.
    """

    def __init__(self, network: Network, configs: Dict[str, Any] = {}) -> None:
        self.network = network
        self.configs = configs

    @abstractmethod
    def execute(self, **kwargs) -> BlueActionReturn:
        """This method executes a blue action.

        Returns:
            BlueActionReturn: An instance of BlueActionReturn containing the result of the action.
        """
        raise NotImplementedError


class StandaloneAction(BlueAction):
    """A standalone action that does not require any specific target."""

    def __init__(self, network: Network, configs: Dict[str, Any]) -> None:
        super().__init__(network, configs)

    @abstractmethod
    def execute(self, **kwargs) -> BlueActionReturn:
        raise NotImplementedError


class HostAction(BlueAction):
    """An action that targets a specific host."""

    def __init__(self, network: Network, configs: Dict[str, Any]) -> None:
        super().__init__(network, configs)

    @abstractmethod
    def execute(self, host: Host, **kwargs) -> BlueActionReturn:
        raise NotImplementedError


class SubnetAction(BlueAction):
    """An action that targets a specific subnet."""

    def __init__(self, network: Network, configs: Dict[str, Any]) -> None:
        super().__init__(network, configs)

    @abstractmethod
    def execute(self, subnet: Subnet, **kwargs) -> BlueActionReturn:
        raise NotImplementedError

    def define_configs(self) -> None:
        """Defines the configuration for the subnet action."""
        self.decoy_info = self.configs['decoy_hosts']
        self.host_info = self.configs['host_definitions']
        self.service_info = self.configs['services']
        self.type = list(self.decoy_info.values())[0]['type']

    def define_services(self) -> None:
        """Defines the services and CVEs associated with the subnet action."""
        type_info = self.host_info['host_types'][self.type]
        self.services: Set[Service] = set()
        self.cves: Set[str] = set()
        for s in type_info['services']:
            service = Service.create_service_from_dict(self.service_info[s])
            self.services.add(service)
            self.cves.update(service.vulns)


class RangeAction(BlueAction):
    """An action that targets a range of indices."""

    def __init__(self, network: Network, configs: Dict[str, Any]) -> None:
        super().__init__(network, configs)

    @abstractmethod
    def execute(self, i: int, **kwargs) -> BlueActionReturn:
        raise NotImplementedError
