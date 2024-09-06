from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from cyberwheel.detectors.alert import Alert
from cyberwheel.network import Host, Service, Subnet

# Type aliases for better readability
Targets = Union[List[Host], List[Subnet]]
Destination = Union[Host, Service]
Source = Optional[Host]


class RedActionResults:
    """A class for handling the results of a red action.

    This class provides feedback to both the red and blue agents. The red agent
    uses `discovered_hosts` and `attack_success` for determining its next action
    and potentially for training. The blue agent uses `detector_alert` in the form
    of an observation vector created later by a `Detector` and an `AlertsConversion`.

    Important member variables:
    - `discovered_hosts`: List of hosts discovered by this attack.
    - `detector_alert`: The alert to be passed to the detector. Contains all the information the detector can get.
    - `attack_success`: Feedback for the red agent indicating whether the attack worked or not.
    - `metadata`: Metadata associated with the red action. For example, a Reconnaissance action may add host vulnerabilities to the metadata.
    """

    def __init__(self, src_host: Host, target_host: Host):
        self.discovered_hosts: List[Host] = []
        self.detector_alert: Alert = Alert(None, [], [])
        self.attack_success: bool = False
        self.metadata: Dict[str, Any] = {}
        self.src_host: Host = src_host
        self.target_host: Host = target_host
        self.cost: int = 0

    def add_host(self, host: Host) -> None:
        """Adds a host to the list of hosts discovered by this action."""
        self.discovered_hosts.append(host)

    def modify_alert(self,
                     dst: Union[Host, Service],
                     src: Optional[Host] = None) -> None:
        """Modifies the RedActionResults' alert by adding to either
        alert.dst_hosts or alert.services."""
        if isinstance(dst, Host):
            if dst:  # Only add the host if it's not None.
                self.detector_alert.add_dst_host(dst)
            if src:
                self.detector_alert.add_src_host(src)
        elif isinstance(dst, Service):
            self.detector_alert.add_service(dst)
        else:
            raise TypeError(
                f'RedActionResults.modify_alert(): dst needs to be Host or Service, not {type(dst)}'
            )

    def add_successful_action(self) -> None:
        """Marks the action as successful."""
        self.attack_success = True

    def add_metadata(self, key: str, value: Any) -> None:
        """Adds metadata to the action result."""
        if key in self.metadata:
            self.metadata[key].update(value)
        else:
            self.metadata[key] = value

    def set_cost(self, cost: int) -> None:
        """Sets the cost associated with the action."""
        self.cost = cost

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RedActionResults):
            return NotImplemented
        return (self.discovered_hosts == other.discovered_hosts
                and self.detector_alert == other.detector_alert
                and self.attack_success == other.attack_success)


class ARTAction(ABC):
    """Base class for defining Atomic Red Team (ART) actions.

    New ART actions should inherit from this class and define the sim_execute()
    method.
    """

    def __init__(self, src_host: Host, target_host: Host) -> None:
        self.src_host: Host = src_host
        self.target_host: Host = target_host
        self.action_results: RedActionResults = RedActionResults(
            src_host, target_host)
        self.name: str = ''

    @abstractmethod
    def sim_execute(self) -> RedActionResults | NotImplementedError:
        """Executes the simulated action.

        Should be implemented by subclasses to define specific red team
        actions.
        """
        pass

    def get_techniques(self) -> List[str]:
        """Returns a list of techniques associated with this action."""
        return getattr(self, 'techniques', [])

    @classmethod
    def get_name(cls) -> str:
        """Returns the name of the action."""
        return cls.name
