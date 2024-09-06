"""The DFS Impact strategy is to attack the current host until it's impacted,
move to another random unimpacted host, and repeat."""

import random
from typing import Dict, Optional, Tuple

from cyberwheel.agents.red.strategies.red_strategy import RedStrategy
from cyberwheel.network import Host


class DFSImpact(RedStrategy):
    """Depth-First Search (DFS) Impact Strategy.

    The strategy focuses on attacking the current host until it is impacted,
    then moving to a random unimpacted host, and repeating the process.
    """

    @classmethod
    def select_target(cls, agent_obj) -> Optional[Host]:
        """Selects the next target host based on the current state of the
        agent.

        If the current host has been impacted, the method chooses a random
        unimpacted host. Otherwise, it continues attacking the current host.

        :param agent_obj: The agent object containing history and current host information.
        :return: The next target host or None if no target is found.
        """
        current_host_name = agent_obj.current_host.name
        history = agent_obj.history.hosts
        killchain_length = len(agent_obj.killchain)

        if history[current_host_name].last_step == killchain_length - 1:
            unimpacted_hosts = [
                h for h, info in history.items()
                if info.last_step < killchain_length - 1
            ]
            if unimpacted_hosts:
                target_host_name = random.choice(unimpacted_hosts)
                target_host = agent_obj.history.mapping.get(target_host_name)
                return target_host
        return agent_obj.current_host

    @classmethod
    def get_reward_map(cls) -> Dict[str, Tuple[int, int]]:
        """Provides the reward map for the strategy.

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
