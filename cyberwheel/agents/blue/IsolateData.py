from abc import ABC, abstractmethod
from typing import List, Tuple

from cyberwheel.network import Host, Subnet


class CustomSharedData(ABC):
    """An abstract base class for defining custom shared data to use with the
    dynamic blue agent.

    All custom shared data objects should implement a `clear()` method that
    resets the object's member variables to their default values. The `clear()`
    method is called whenever the environment resets.
    """

    @abstractmethod
    def clear(self) -> None:
        """Resets the object's member variables to their default values.

        This method must be implemented by any subclass of CustomSharedData.
        """
        raise NotImplementedError(
            "Subclasses must implement the 'clear' method.")


class IsolateData(CustomSharedData):
    """A shared data class that manages a list of decoy hosts and their
    associated subnets."""

    def __init__(self, **kwargs):
        """Initializes the IsolateData object with a maximum size and an empty
        decoy list.

        :param kwargs: Optional keyword arguments. 'size' specifies the maximum number of decoys.
        """
        self.size: int = kwargs.get('size', 10)
        self.decoys: List[Tuple[Host, Subnet]] = [
        ]  # List to store tuples of (decoy host, subnet)

    def __getitem__(self, k: int) -> Tuple[Host, Subnet]:
        """Gets the decoy-host-subnet pair at the specified index.

        :param k: The index of the decoy-host-subnet pair to retrieve.
        :return: A tuple containing the decoy host and its associated subnet.
        """
        return self.decoys[k]

    def __len__(self) -> int:
        """Returns the number of decoy-host-subnet pairs currently stored.

        :return: The number of stored decoys.
        """
        return len(self.decoys)

    def append_decoy(self, decoy: Host, subnet: Subnet) -> bool:
        """Appends a decoy host and its associated subnet to the list, if the
        list isn't full.

        :param decoy: The decoy host to add.
        :param subnet: The subnet associated with the decoy host.
        :return: True if the decoy was added, False if the list is full.
        """
        if len(self.decoys) >= self.size:
            return False
        self.decoys.append((decoy, subnet))
        return True

    def clear(self) -> None:
        """Clears all decoy-host-subnet pairs from the list."""
        self.decoys.clear()
