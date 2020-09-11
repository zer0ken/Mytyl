import json

from utils import singleton

DEFAULT_PATH = './Mytyl/data/literals.json'
CONSTANT = '_constant_'
PATH = '_path_'
COG = '_cog_'
CHECK = '_check_'
EMOJI = '_emoji_'
BRIEF = '_brief_'
HELP = '_help_'
DEFAULT = '_default_'
PREFIX = '<P>'


def get_constant(name: str):
    return Literal().literals[CONSTANT].get(name)


def get_brief(name: str):
    return Literal().literals[BRIEF].get(name)


def get_help(name: str):
    return Literal().literals[HELP].get(name)


def get_path(name: str):
    return Literal().literals[PATH].get(name)


def get_cog(name: str):
    literal = Literal().literals[COG].get(name)
    return literal if literal is not None else Literal().literals[COG].get(DEFAULT)


def get_check(name: str):
    return Literal().literals[CHECK].get(name)


def get_emoji(name: str):
    literal = Literal().literals[EMOJI].get(name)
    return literal if literal is not None else Literal().literals[EMOJI].get(DEFAULT)


def literals(name: str = ''):
    l = Literal().literals
    return l.get(name) if name else l


def reload_literals():
    literal = Literal()
    literal.load()
    literal.format_all(literal.literals)


@singleton
class Literal:
    def __init__(self):
        self.literals: dict = dict()
        self.load()
        self.format_all(self.literals)

    def load(self):
        with open(DEFAULT_PATH, 'r', encoding='utf-8') as f:
            self.literals = json.load(f)

    def format_all(self, d):
        if isinstance(d, str):
            return d.replace(PREFIX, str(self.literals[CONSTANT]['default_prefix']))
        if isinstance(d, dict):
            for k, v in d.items():
                d[k] = self.format_all(v)
        if isinstance(d, list):
            for i in range(len(d)):
                d[i] = self.format_all(d[i])
        return d
