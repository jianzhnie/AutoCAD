from typing import Any, Dict, Optional

from cyberwheel.network import Network


class Cyberwheel:
    """Cyberwheel is a class that handles the initialization and management of
    a network. It can create a network either from a YAML configuration file or
    use an existing network object.

    Args:
        **kwargs: Keyword arguments that can include:
            - config_file_path: Optional[str], the path to the YAML configuration file to create the network.
            - network: Optional[Network], an existing network object to use instead of creating one from YAML.

    Attributes:
        config_file_path (Optional[str]): The path to the YAML configuration file, if provided.
        network (Network): The network object, either created from YAML or provided directly.
        evaluation (bool): A flag indicating whether evaluation mode is active.
    """

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        # Retrieve the config_file_path if provided in kwargs, otherwise default to None
        self.config_file_path: Optional[str] = kwargs.get('config_file_path')

        # Retrieve the network object if provided in kwargs, otherwise create from YAML
        network: Optional[Network] = kwargs.get('network', None)

        if network is None:
            # If no network object is provided, create one from the YAML configuration file
            if self.config_file_path is None:
                raise ValueError(
                    'config_file_path must be provided if no network object is passed.'
                )
            print('Creating network from YAML configuration.')
            self.network = Network.create_network_from_yaml(
                self.config_file_path)
        else:
            # Use the provided network object
            self.network = network

        # Evaluation flag initialization
        self.evaluation = False

    @classmethod
    def create_from_yaml(cls, config_file_path: str) -> 'Cyberwheel':
        """Class method to create a Cyberwheel instance from a YAML
        configuration file.

        Args:
            config_file_path (str): The path to the YAML configuration file.

        Returns:
            Cyberwheel: A new instance of Cyberwheel initialized with the network from the YAML file.
        """
        return cls(config_file_path=config_file_path)
