import unittest

from cyberwheel.agents.red.actions import RedActionResults
from cyberwheel.detectors import Alert
from cyberwheel.network import Network


class TestRedActionResult(unittest.TestCase):

    def setUp(self):
        self.network = Network.create_network_from_yaml(
            'network/example_config.yaml')
        self.action_result = RedActionResults()
        self.host = self.network.get_hosts()[0]
        self.service = self.host.services[0]
        self.alert = Alert()

    def test_red_action_result_add_host(self):
        self.action_result.add_host(self.host)
        self.assertListEqual(self.action_result.discovered_hosts, [self.host])

    def test_red_action_result_modify_alert_host(self):
        self.alert.add_dst_host(self.host)
        self.action_result.modify_alert(self.host)
        self.assertEqual(self.action_result.detector_alert, self.alert)

    def test_red_action_result_modify_alert_service(self):
        self.alert.add_service(self.service)
        self.action_result.modify_alert(self.service)
        self.assertEqual(self.action_result.detector_alert, self.alert)

    def test_red_action_result_add_successful_action(self):
        self.action_result.add_successful_action(self.host)
        self.assertListEqual(self.action_result.attack_success, [self.host])


class TestRedAction(unittest.TestCase):

    def setUp(self):
        self.network = Network.create_network_from_yaml(
            'network/example_config.yaml')
        self.host = self.network.get_hosts()[0]
        self.src_host = self.network.get_hosts()[1]
        self.service = self.host.services[0]

    def test_sim_execute(self):
        true_result = RedActionResults()
        true_result.add_host(self.host)
        true_result.add_successful_action(self.host)
        true_result.modify_alert(self.host)
        true_result.modify_alert(self.service)


if __name__ == '__main__':
    unittest.main()
