import os
import time
import numpy as np

red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
white = '\033[0m'
tab = '   '


def sample_cdf(cum_probs):  # cumulative dictribution function
    rand = np.random.rand()
    return sum(cum_probs < rand)


def sample_pmf(probs):  # probability mass function
    probs = np.array(probs)
    assert sum(probs) >= 0.9999999, "this vector does not sum to 1. We need a proper probability mass function"
    return sample_cdf(probs.cumsum())


class SaveResults(object):

    def __init__(self, parameters):
        self.parameters = parameters
        self.dir_path = self.get_dir_path()
        self.file_results_name = None

    def get_dir_path(self):
        dir_name = "results/" + self.parameters["name"]
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        dir_name += "/" + \
                    time.asctime(time.localtime(time.time())).replace(" ", "_")
        os.mkdir(dir_name)

        return dir_name

    def write_message(self, message):
        f = open(self.file_results_name, "a")
        f.write(message)
        f.close()

    def write_reward(self, t, total_reward):
        f = open(self.file_results_name, "a")
        f.write("t = " + str(t) + " reward = " + str(total_reward) + "\n")
        f.close()

    def write_setting(self):
        """
        writes the parameters in a file
        """
        f = open(self.dir_path + "/" + "setting", "a")
        for key in self.parameters:
            f.write(key + " : " + str(self.parameters[key]) + "\n")
        f.write("\n" * 3)
        f.close()

    def set_file_results_name(self, seed):
        self.file_results_name = self.dir_path + "/" + "seed_" + str(seed)


class ShowRender(object):

    def __init__(self, env):
        self.env = env
        self.display_learning = True
        self.blurred_render = False
        self.gray_scale_render = False
        self.agent_view = False
        self.env.render(blurred_render=self.blurred_render,
                        gray_scale_render=self.gray_scale_render,
                        agent_render=self.agent_view)
        self.env.unwrapped.viewer.window.on_key_press = self.key_press
        self.env.unwrapped.viewer.window.on_key_release = self.key_release

    def display(self):
        if self.display_learning:
            self.env.render(blurred_render=self.blurred_render,
                            gray_scale_render=self.gray_scale_render,
                            agent_render=self.agent_view)

        else:
            self.env.unwrapped.viewer.window.dispatch_events()

    def key_press(self, key, mod):
        if key == ord("d"):
            self.display_learning = not self.display_learning

        if key == ord("b"):
            self.blurred_render = not self.blurred_render

        if key == ord("g"):
            self.gray_scale_render = not self.gray_scale_render

        if key == ord("a"):
            self.agent_view = not self.agent_view

        if key == ord(" "):
            self.agent_view = not self.agent_view
            self.blurred_render = self.agent_view
            self.gray_scale_render = not self.agent_view

    def key_release(self, key, mod):
        pass
