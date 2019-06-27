import numpy as np

red = '\033[91m'
green = '\033[92m'
yellow = '\033[93m'
white = '\033[0m'
tab = '   '


def obs_equal(obs, other):
    if type(obs) == "int" and type(other) == "int":
        return obs == other

    elif type(obs).__name__ == "ndarray" and type(other).__name__ == "ndarray":
        return np.array_equal(obs, other)

    else:
        raise NotImplementedError("These observations cannot be compared")


def constrain_type(f):
    def decorated(*args, **kwargs):
        output = f(*args, **kwargs)
        class_annotation = f.__annotations__["return"]
        if not issubclass(type(output), class_annotation):
            raise TypeError("this class must return an object inheriting from " +
                            str(class_annotation.__name__) + " not " + str(type(output).__name__))

        return output

    return decorated

