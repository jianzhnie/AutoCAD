from typing import Any, Tuple

from pydantic import BaseModel, validator


class PrivilegeValueError(ValueError):
    """Custom exception raised when an invalid privilege level is provided."""

    def __init__(self, value: str, message: str) -> None:
        """Initializes the PrivilegeValueError.

        Args:
            value (str): The invalid privilege value.
            message (str): The error message.
        """
        self.value = value
        self.message = message
        super().__init__(message)


class Process(BaseModel):
    """Represents a process in the system with a name and privilege level."""

    name: str
    privilege: str = 'user'

    def __key(self) -> Tuple[str, str]:
        """Returns a unique key for hashing and equality comparison.

        Returns:
            Tuple[str, str]: A tuple containing the process name and privilege level.
        """
        return (self.name, self.privilege)

    def __hash__(self) -> int:
        """Returns the hash of the process based on its unique key.

        Returns:
            int: The hash value of the process.
        """
        return hash(self.__key())

    def __eq__(self, other: Any) -> bool:
        """Checks equality between this process and another process.

        Args:
            other (Any): The other object to compare with.

        Returns:
            bool: True if both processes have the same name and privilege, False otherwise.
        """
        if isinstance(other, Process):
            name_matched: bool = self.name == other.name
            privilege_matched: bool = self.privilege == other.privilege
            return name_matched and privilege_matched
        return False

    @validator('privilege')
    @classmethod
    def validate_privilege(cls, privilege: str) -> str:
        """Validates the privilege level.

        Args:
            privilege (str): The privilege level to validate.

        Raises:
            PrivilegeValueError: If the privilege level is not 'user' or 'root'.

        Returns:
            str: The validated privilege level.
        """
        if privilege not in ['user', 'root']:
            raise PrivilegeValueError(
                value=privilege,
                message="Privilege level should be either 'user' or 'root'.",
            )
        return privilege

    def escalate_privilege(self) -> None:
        """Escalates the privilege level of the process to 'root'."""
        self.privilege = 'root'


# Example usage of the Process class
if __name__ == '__main__':
    try:
        # Create a process with default 'user' privilege
        process1 = Process(name='process1')
        print(f'Process: {process1.name}, Privilege: {process1.privilege}')

        # Escalate privilege to 'root'
        process1.escalate_privilege()
        print(f'Process: {process1.name}, Privilege: {process1.privilege}')

        # Create a process with an invalid privilege level
        # This will raise a PrivilegeValueError
        process2 = Process(name='process2', privilege='admin')
    except PrivilegeValueError as e:
        print(f'Error: {e.message} (Invalid privilege: {e.value})')

    # Demonstrating equality and hashing
    process3 = Process(name='process3')
    process4 = Process(name='process3', privilege='user')

    # Check equality between process3 and process4
    print(f'Processes equal: {process3 == process4}')  # True

    # Check the hash values
    print(f'Hash of process3: {hash(process3)}')
    print(f'Hash of process4: {hash(process4)}')
