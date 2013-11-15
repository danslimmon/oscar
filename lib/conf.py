import yaml

class Conf:
    def __init__(self):
        self._conf_dict = yaml.load(open('/etc/oscar.yaml').read())

    def get(self):
        return self._conf_dict


c = Conf()
def get():
    return c.get()
