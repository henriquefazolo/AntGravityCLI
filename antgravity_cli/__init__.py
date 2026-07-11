# AntGravity CLI Package
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("AntGravityCLI")
except PackageNotFoundError:
    __version__ = "1.2.8"

from . import config
from . import subagents
from . import utils
from . import parser
from . import runner
from . import repl
