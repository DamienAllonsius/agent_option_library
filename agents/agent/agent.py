"""
This library can be connected to a gym environment or any kind of environment as long as it has the following methods:
- env.reset
- env.step
"""
import numpy as np

from agents.utils.utils import SaveResults
from abc import ABCMeta, abstractmethod
from tqdm import tqdm
from agents.policies.agent.agent_policy import PolicyAbstractAgent
from agents.options.options import OptionAbstract
from agents.options.options_explore import OptionExploreAbstract


class AbstractAgent(metaclass=ABCMeta):
    """
    Very general abstract skeleton for Agent class for any kind of purpose
    """

    @abstractmethod
    def reset(self, initial_state):
        """
        resets the state space parameter.
        :param initial_state: an element of the state space
        :return: void
        """
        raise NotImplementedError()

    @abstractmethod
    def act(self, *args, **kwargs):
        """
        makes an action
        :param args:
        :param kwargs:
        :return: an element of the action space
        """
        raise NotImplementedError()

    @abstractmethod
    def update_agent(self, *args, **kwargs):
        """
        updates the agent parameters (the policy for instance)
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def train_agent(self, *args, **kwargs):
        """
        Performs the training phase
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def simulate_agent(self, *args, **kwargs):
        """
        Performs the simulation phase
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()


class AbstractAgentOption(AbstractAgent):
    """
    Abstract Agent class with the Options framework
    """

    def __init__(self, action_space, parameters):
        """
        initialize the agent's parameters.
        :param action_space:
        :param parameters:
        """

        self.action_space = action_space
        self.parameters = parameters
        self.option_list = []
        self.score = 0

        self.policy = self.get_policy()
        self.explore_option = self.get_explore_option()

        AbstractAgentOption.check_type(self.policy, PolicyAbstractAgent)
        AbstractAgentOption.check_type(self.explore_option, OptionExploreAbstract)
        AbstractAgentOption.check_type(self.get_option(), OptionAbstract)

    def __len__(self):
        return len(self.option_list)

    @staticmethod
    def check_type(object1, object2):
        """
        check that object1 inherits from object2
        :param object1: the child class
        :param object2: the parent class
        :return:
        """
        if not issubclass(type(object1), object2):
            raise TypeError("this class must return an object inheriting from " +
                            object2.__name__ + " not " + type(object1).__name__)

    def reset(self, initial_state):
        self.score = 0
        self.policy.reset(initial_state)

    def _train_simulate_agent(self, environment, train_episode=None):
        """
        Method used to train or simulate the agent

        a) choose an option
        b) option acts and updates
        c) if a new state is found then update agent

        :param environment:
        :param train_episode: the episode of training.
        :return:
        """
        # The initial observation
        obs = environment.reset()
        o_r_d_i = [obs]

        # Reset all the parameters
        self.reset(o_r_d_i[0]["agent"])
        done = False
        current_option = None

        # Render the current state
        self.display_state(environment, train_episode)

        while not done:
            # If no option is activated then choose one
            if current_option is None:
                current_option = self.act(o_r_d_i, train_episode)

            # choose an action
            action = current_option.act()

            # make an action and display the state space
            # todo record the learning curve
            o_r_d_i = environment.step(action)

            self.display_state(environment, train_episode)

            # update the option
            current_option.update_option(o_r_d_i, action, train_episode)

            # check if the option ended
            end_option = current_option.check_end_option(o_r_d_i[0]["agent"])

            # If the option is done, update the agent
            if end_option:
                self.update_agent(o_r_d_i, current_option, train_episode)
                done = self.check_end_agent(o_r_d_i, current_option, train_episode)
                current_option = None

    def act(self, o_r_d_i, train_episode=None):
        """
        the action for an Agent in the Option framework corresponds to
        1) choose an option in option_list
        2) reset the parameters of this option
        3) return the index corresponding to this option

        :return: an option
        """
        best_option_index, terminal_state = self.policy.find_best_action(train_episode)

        if terminal_state is None:

            # in this case : explore
            self.explore_option.reset(self.policy.get_current_state())

            return self.explore_option

        else:  # in this case, activate an option from the list self.option_set

            # get the information from the environment that the option needs to reset
            option_states = self.get_option_states(o_r_d_i, terminal_state)

            # set the parameters  of the option with that states
            self.option_list[best_option_index].reset(*option_states)

            return self.option_list[best_option_index]

    def update_agent(self, o_r_d_i, option, train_episode=None):
        """
        updates the agent parameters.
        In testing mode, updates
        - score
        In learning mode, updates
        - policy
        - option
        :param o_r_d_i : Observation, Reward, Done, Info given by function step
        :param option: the index of the option that did the last action
        :param train_episode: the number of the current training episode
        :return : void
        """

        if train_episode is None:  # in simulate mode
            # compute total score
            self.score = self.compute_total_score(o_r_d_i, option, train_episode)

        else:  # in training mode
            self._update_policy(o_r_d_i, option.index, train_episode)

            # add a new option if necessary
            if self.policy.max_number_successors() > len(self):
                self.option_list.append(self.get_option())

    def _update_policy(self, o_r_d_i, option_index, train_episode):
        """
        updates the policy only if the current option activated is not an explore option, that is :
        option_index is not None
        :param o_r_d_i:
        :param option_index:
        :param train_episode:
        :return:
        """
        # update the q value only if the option is not the explore_option
        if option_index is not None:

            # first, compute the total reward to update the policy
            total_reward = self.compute_total_reward(o_r_d_i, option_index, train_episode)
            # then, update the policy
            self.policy.update(o_r_d_i[0]["agent"], total_reward, option_index)

    def train_agent(self, environment, seed=0):
        """
        Method used to train the RL agent. It calls function _train_simulate_agent with the current training episode
        :return: Nothing
        """
        # set the seeds
        np.random.seed(seed)
        environment.seed(seed)

        for t in tqdm(range(1, self.parameters["number_episodes"])):
            self._train_simulate_agent(environment, t)

    def simulate_agent(self, environment, seed=0):
        """
        Method used to train the RL agent.
        It calls _train_simulate_agent method with parameter "train_episode" set to None
        :return: Nothing
        """
        # set the seeds
        np.random.seed(seed)
        environment.seed(seed)

        # prepare the file for the results
        save_results = SaveResults(self.parameters)
        save_results.write_setting()
        save_results.set_file_results_name(seed)

        # simulate
        self._train_simulate_agent(environment)

        # write the results and write that the experiment went well
        save_results.write_reward(self.parameters["number_episodes"], self.score)
        save_results.write_message("Experiment complete.")

    @staticmethod
    @abstractmethod
    def display_state(environment, train_episode):
        raise NotImplementedError()

    @abstractmethod
    def get_option_states(self, *args, **kwargs):
        """
        Returns the information needed for the option to reset
        """
        raise NotImplementedError()

    @abstractmethod
    def compute_total_score(self, o_r_d_i, option, train_episode):
        """
        This function highly depends on the environment.
        :return: a float corresponding of the score of the agent accumulated so far
        """
        raise NotImplementedError()

    @abstractmethod
    def compute_total_reward(self, o_r_d_i, option, train_episode):
        """
        This function highly depends on the environment.
        :return: a float corresponding of the current reward of the agent
        """
        raise NotImplementedError()

    @abstractmethod
    def check_end_agent(self, o_r_d_i, option, train_episode):
        """
        Check if the current episode is over or not. The output of this function will update the variable "done" in
        method self._train_simulate_agent
        :param o_r_d_i:
        :param option:
        :param train_episode:
        :return: True iff the agent is done.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_current_state(self):
        raise NotImplementedError()

    @abstractmethod
    def get_option(self) -> OptionAbstract:
        """
        Updates the list: self.option_list
        This method depends on the kind of option we want to use.
        :return: void
        """
        raise NotImplementedError()

    @abstractmethod
    def get_explore_option(self) -> OptionExploreAbstract:
        raise NotImplementedError()

    @abstractmethod
    def get_policy(self) -> PolicyAbstractAgent:
        """
        :return: An instance of a class which inherits from PolicyAbstract
        """
        raise NotImplementedError()