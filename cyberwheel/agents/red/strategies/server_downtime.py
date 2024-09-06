"""The Server Downtime strategy is to find and attack all of the Servers it can
find in the network.

Once it finds a server, it will try to impact it. Once impacted, it will look
for another server.
"""

from typing import Dict, Optional, Tuple

from cyberwheel.agents.red.strategies.red_strategy import RedStrategy
from cyberwheel.network import Host


class ServerDowntime(RedStrategy):
    """Server Downtime Strategy.

    This strategy targets servers in the network. It continues to attack the
    current host if it is an unknown host or a server that has not been
    impacted yet. Once it finds an impacted server, it looks for another server
    to attack. If no unimpacted servers or unknown hosts are available, the
    strategy signifies failure by potentially assigning a high cost.
    """

    @classmethod
    def select_target(cls, agent_obj) -> Optional[Host]:
        """Selects the next target host based on the current state of the
        agent.

        - Continues attacking the current host if it is unknown or a server that
          has not been impacted yet.
        - Prioritizes attacking unimpacted servers.
        - If no unimpacted servers are found, it targets unknown hosts.
        - If neither is available, the strategy has failed.

        :param agent_obj: The agent object containing history and target lists.
        :return: The selected target host or None if no target is found.
        """
        current_host = agent_obj.current_host
        current_host_name = current_host.name
        current_host_type = agent_obj.history.hosts[current_host_name].type

        if (current_host_type == 'Unknown'
                or agent_obj.unimpacted_servers.check_membership(
                    current_host_name)):
            # Continue with the current host if it is unknown or an unimpacted server
            target_host = current_host
        elif agent_obj.unimpacted_servers.length() > 0:
            # Target a random unimpacted server
            target_host_name = agent_obj.unimpacted_servers.get_random()
            target_host = agent_obj.history.mapping.get(target_host_name)
        elif agent_obj.unknowns.length() > 0:
            # Target a random unknown host
            target_host_name = agent_obj.unknowns.get_random()
            target_host = agent_obj.history.mapping.get(target_host_name)
        else:
            # No suitable targets found
            target_host = None

        return target_host

    @classmethod
    def get_reward_map(cls) -> Dict[str, Tuple[int, int]]:
        """Provides the reward map for the Server Downtime strategy.

        The reward map defines rewards and penalties for different actions.

        :return: A dictionary mapping action names to (reward, penalty) tuples.
        """
        return {
            'pingsweep': (-1, 0),
            'portscan': (-1, 0),
            'discovery': (-2, 0),
            'lateral-movement': (-4, 0),
            'privilege-escalation': (-6, 0),
            'impact': (-8, -4),
        }
