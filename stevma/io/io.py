"""Input/output module"""

from pathlib import Path
from typing import Union

import yaml


def load_yaml(fname: Union[str, Path]) -> dict:
    """Load configuration file with YAML format

    Parameters
    ----------
    fname : `str / Path`
        YAML filename

    Returns
    -------
    `yaml.load`
    """

    if isinstance(fname, Path):
        fname = str(fname)

    with open(fname, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)
