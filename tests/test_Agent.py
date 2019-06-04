import unittest
from agents.examples.agent_example import AgentOptionMontezuma
from agents.examples.policy_examples_agent import QGraph
from agents.examples.options_examples import OptionQArray
import numpy as np


class AgentMontezumaTest(unittest.TestCase):

    def setUp(self):
        np.random.seed(0)
        self.parameters = {"probability_random_action_option": 0.1,
                           "probability_random_action_agent": 0.1,
                           "reward_end_option": 10,
                           "penalty_end_option": -10,
                           "penalty_option_action": -1,
                           "learning_rate": 0.1}

        self.action_space = range(4)

        self.agent = AgentOptionMontezuma(action_space=self.action_space, parameters=self.parameters)
        self.q = QGraph(parameters=self.parameters)
        self.q._update_states("state 0")
        self.q._update_states("state 1")
        self.q._update_states("state 2")
        self.q._update_states("state 0")
        self.q._update_states("state 3")
        self.q._update_states("state 4")
        self.q._update_states("state 4")
        self.q._update_states("state 4")
        self.q._update_states("state 5")
        self.q.values = list(map(lambda x: np.random.rand(len(x)), self.q.state_graph))

        self.o_r_d_i1 = [{"agent": "state 2", "option": "initial state option"}, 10, False, None]
        self.o_r_d_i2 = [{"agent": "state 0", "option": "state0 option"}, 0, True, None]

        self.agent.policy = self.q
        self.agent.option_list = list()
        for k in range(self.q.max_number_successors()):
            self.agent.option_list.append(self.agent.get_option())

    def test_act(self):
        self.agent.policy.parameters["probability_random_action_agent"] = 1
        option = self.agent.act(self.o_r_d_i1, train_episode=1)
        self.assertEqual(type(option).__name__, "OptionRandomExplore")
        self.assertEqual(option.initial_state, self.q.get_current_state())

        self.agent.policy.parameters["probability_random_action_agent"] = 0
        option = self.agent.act(self.o_r_d_i1, train_episode=0)
        self.assertEqual(type(option).__name__, "OptionQArray")

        # are the current states updated before to activate the option ?
        self.assertEqual(option.initial_state, self.o_r_d_i1[0]["agent"])
        self.assertEqual(option.policy.state_list[option.policy.current_state_index], self.o_r_d_i1[0]["option"])

        idmax = np.argmax(self.q.values[self.q.current_state_index])
        self.assertEqual(option.terminal_state, self.q.states[self.q.state_graph[self.q.current_state_index][idmax]])

    def test_update_policy(self):
        option_index = 0
        import copy
        v_copy = copy.deepcopy(list(self.q.values.copy()))

        self.agent._update_policy(self.o_r_d_i1, None, None)
        for k in range(len(v_copy)):
            self.assertListEqual(list(self.q.values[k]), list(v_copy[k]))

        v_copy[self.q.current_state_index][option_index] *= (1 - self.parameters["learning_rate"])
        state_index = self.q.states.index(self.o_r_d_i1[0]["agent"])
        best_value = np.max(v_copy[state_index])
        total_reward = self.agent.compute_total_reward(self.o_r_d_i1, self.agent.option_list[option_index],0)
        v_copy[self.q.current_state_index][option_index] += self.parameters["learning_rate"] * (total_reward +
                                                                                                best_value)

        self.agent._update_policy(self.o_r_d_i1, option_index, None)
        for k in range(len(v_copy)):
            self.assertListEqual(list(self.agent.policy.values[k]), list(v_copy[k]))

        self.assertEqual(self.agent.policy.get_current_state(), self.o_r_d_i1[0]["agent"])

    def test_update_agent(self):
        n = self.q.max_number_successors() - 1
        self.agent.option_list = list()
        for k in range(n):
            self.agent.option_list.append(self.agent.get_option())

        self.assertEqual(len(self.agent.option_list), n)

        option_index = 1
        total_reward = self.agent.compute_total_reward(self.o_r_d_i1, self.agent.option_list[option_index], None)
        self.agent.policy._update_states("state 0")
        current_idx = self.agent.policy.current_state_index
        val = self.agent.policy.values[self.agent.policy.current_state_index][option_index]

        best_val = np.max(self.agent.policy.values[self.agent.policy.states.index(self.o_r_d_i1[0]["agent"])])

        val *= (1 - self.parameters["learning_rate"])
        val += self.parameters["learning_rate"]*(total_reward + best_val)

        self.agent.update_agent(self.o_r_d_i1, self.agent.option_list[1], 1)
        self.assertEqual(len(self.agent.option_list), n+1)

        self.assertEqual(val, self.agent.policy.values[current_idx][option_index])

    def test_get_option_state(self):
        self.agent.update_agent(self.o_r_d_i1, self.agent.option_list[0], 1)
        option_states = self.agent.get_option_states(self.o_r_d_i1, "terminal state")

        self.assertEqual(option_states, (self.o_r_d_i1[0]["agent"], self.o_r_d_i1[0]["option"], "terminal state"))
        self.assertEqual(option_states, (self.agent.policy.get_current_state(), self.o_r_d_i1[0]["option"], "terminal state"))
        self.assertEqual(option_states, (self.agent.get_current_state(), self.o_r_d_i1[0]["option"], "terminal state"))

    def test_get_current_state(self):
        self.assertEqual(self.agent.get_current_state(), "state 5")

        self.agent.update_agent(self.o_r_d_i1, self.agent.option_list[0], 1)
        self.assertEqual(self.agent.get_current_state(), "state 2")

        self.agent.update_agent(self.o_r_d_i2, self.agent.option_list[0], 1)
        self.assertEqual(self.agent.get_current_state(), "state 0")