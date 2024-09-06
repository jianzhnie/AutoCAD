from typing import Any, Dict, Type, TypeVar, Union

from pydantic import BaseModel, PositiveInt, validator

# Type variable to allow class methods to return instances of subclasses
T = TypeVar('T', bound='Service')


class Vuln(BaseModel):
    """Represents a vulnerability with a name and an ID."""

    name: str
    id: str

    def __key(self) -> tuple[str, str]:
        """Generates a unique key for the Vuln instance.

        :return: Tuple of name and id.
        """
        return (self.name, self.id)

    def __hash__(self) -> int:
        """Allows Vuln to be used in sets or as dictionary keys."""
        return hash(self.__key())

    def __eq__(self, other: Any) -> bool:
        """Checks equality between two Vuln instances."""
        if isinstance(other, Vuln):
            return self.__key() == other.__key()
        return False

    # Validators for Vuln can be added here if needed


class PortValueError(ValueError):
    """Custom exception for invalid port values."""

    def __init__(self, value: int, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class ProtocolValueError(ValueError):
    """Custom exception for invalid protocol values."""

    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class Service(BaseModel):
    """Represents a network service with a name, port, protocol, and
    vulnerabilities."""

    name: str
    port: PositiveInt = 1  # Default port value for ICMP
    protocol: str = 'tcp'
    version: Union[str, None] = None
    vulns: set[str] = set()
    description: Union[str, None] = None
    decoy: Union[bool, None] = False

    def __key(self) -> tuple:
        """Generates a unique key for the Service instance.

        :return: Tuple of attributes that define the uniqueness of the service.
        """
        return (
            self.name,
            self.port,
            self.protocol,
            self.version,
            self.description,
            self.decoy,
        )

    def __hash__(self) -> int:
        """Allows Service to be used in sets or as dictionary keys."""
        return hash(self.__key())

    def __eq__(self, other: Any) -> bool:
        """Checks equality between two Service instances."""
        if isinstance(other, Service):
            port_matched: bool = self.port == other.port
            proto_matched: bool = self.protocol == other.protocol
            version_matched: bool = self.version == other.version
            return port_matched and proto_matched and version_matched
        return False

    @validator('port')
    @classmethod
    def validate_port(cls, port: PositiveInt) -> int:
        """Validates the port number.

        :param port: The port number to validate.
        :return: The validated port number.
        :raises PortValueError: If the port is out of the valid range.
        """
        if not (1 <= port <= 65535):
            raise PortValueError(value=port,
                                 message='Port should be between 1 and 65535')
        return port

    @validator('protocol')
    @classmethod
    def validate_protocol(cls, protocol: str) -> str:
        """Validates the protocol.

        :param protocol: The protocol to validate.
        :return: The validated protocol.
        :raises ProtocolValueError: If the protocol is not 'tcp', 'udp', or 'icmp'.
        """
        if protocol not in ['tcp', 'udp', 'icmp']:
            raise ProtocolValueError(
                value=protocol,
                message="Protocol should be 'tcp', 'udp', or 'icmp'")
        return protocol

    @classmethod
    def create_service_from_dict(cls: Type[T], service: Dict[str, Any]) -> T:
        """Creates a Service instance from a dictionary.

        :param service: The dictionary containing service attributes.
        :return: An instance of the Service class.
        """
        vulns = service.get('cve', [])
        return cls(
            name=service.get('name'),
            port=service.get('port', 1),
            protocol=service.get('protocol', 'tcp'),
            version=service.get('version'),
            vulns=vulns,
            description=service.get('description'),
            decoy=service.get('decoy'),
        )

    @classmethod
    def create_service_from_yaml(cls: Type[T], service_objs: list[Dict[str,
                                                                       Any]],
                                 service_str: str) -> T:
        """Creates a Service instance from a YAML configuration.

        :param service_objs: A list of dictionaries containing service objects.
        :param service_str: The key of the service object in the list.
        :return: An instance of the Service class.
        """
        service = service_objs.get(service_str, {})
        vulns = service.get('cve', set())

        return cls(
            name=service_str,
            port=service.get('port', 1),
            protocol=service.get('protocol', 'tcp'),
            version=service.get('version'),
            vulns=set(vulns),
            description=service.get('description'),
            decoy=service.get('decoy', False),
        )
