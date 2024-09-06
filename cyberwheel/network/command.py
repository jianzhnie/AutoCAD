from typing import Literal


class InvalidPrivilegeError(ValueError):
    """Custom exception raised when an invalid privilege level is provided."""

    def __init__(self, value: str, message: str) -> None:
        self.value = value
        self.message = message
        super().__init__(message)


class Command:
    """Represents a command to be executed by a specific user with a certain
    privilege level."""

    def __init__(self,
                 executor: str,
                 content: str,
                 privilege: Literal['user', 'root'] = 'user') -> None:
        """Initializes the Command object.

        Args:
            executor (str): The name or ID of the executor (e.g., user or process).
            content (str): The command content to be executed.
            privilege (str): The privilege level required to execute the command ('user' or 'root').

        Raises:
            InvalidPrivilegeError: If the privilege level is not 'user' or 'root'.
        """
        self.executor = executor
        self.content = content
        self.privilege = self.validate_privilege(privilege)

    @staticmethod
    def validate_privilege(privilege: str) -> str:
        """Validates the privilege level.

        Args:
            privilege (str): The privilege level to validate.

        Raises:
            InvalidPrivilegeError: If the privilege level is not 'user' or 'root'.

        Returns:
            str: The validated privilege level.
        """
        if privilege not in ['user', 'root']:
            raise InvalidPrivilegeError(
                value=privilege,
                message="Privilege level should be either 'user' or 'root'.",
            )
        return privilege

    def __repr__(self) -> str:
        """Returns a string representation of the Command object.

        Returns:
            str: String representation of the command.
        """
        return f"Command(executor='{self.executor}', content='{self.content}', privilege='{self.privilege}')"


# Example usage of the Command class
if __name__ == '__main__':
    try:
        # Create a command with default 'user' privilege
        command1 = Command(executor='user1', content='ls')
        print(command1)

        # Create a command with 'root' privilege
        command2 = Command(executor='user2',
                           content='apt-get update',
                           privilege='root')
        print(command2)

        # Attempt to create a command with an invalid privilege level
        # This will raise an InvalidPrivilegeError
        command3 = Command(executor='user3',
                           content='rm -rf /',
                           privilege='admin')
    except InvalidPrivilegeError as e:
        print(f'Error: {e.message} (Invalid privilege: {e.value})')
