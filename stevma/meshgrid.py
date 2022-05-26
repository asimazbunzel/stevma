"""Module to manage the grid of different models of simulations of stellar evolution

Throughout the module, it is assumed that the grid is stored in a dictionary. Each key of the
dictionary must be a valid MESA namelist (see mesa/__init__.py for a list of valid options).
Each of them present in the dictionary is a dictionary in itself, such that the parameters that
are varied in the grid are keys of them and should contain lists or numbers or booleans\
"""

from stevma.io.logger import logger
from stevma.mesa import _defaultStarNamelists, _defaultBinaryNamelists
from stevma.mesa.mesa import get_mesa_defaults


def check_for_valid_namelist_options(d: dict = {}, mesa_dir: str = "") -> bool:
    """Function that checks whether a dictionary contains valid namelists of MESA as well
    as valid name of options

    Parameters
    ----------
    d : `dict`
        Dictionary with MESA options for the meshgrid

    Returns
    -------
    is_okay : `bool`
        Flag that is True when everything is OK and False when some item in the dictionary is not a
        valid MESA namelist or option
    """

    # need MESA defaults parameters to check whether the arguments of the meshgrid are valid
    _MESADefaults = get_mesa_defaults(mesa_dir=mesa_dir)

    # check that each key in the dict grid is actually a valid namelist
    namelists = [namelist for namelist in _defaultStarNamelists]
    namelists.extend(([namelist for namelist in _defaultBinaryNamelists]))

    is_okay = True
    for key in d.keys():
        if key not in namelists:
            logger.critical(f"namelist `{key}` not present in MESA source code")
            is_okay = False
            break
        else:
            tmpDict = d[key]
            for subkey in tmpDict.keys():
                if subkey not in _MESADefaults.get(key):
                    logger.critical(
                        f"option `{subkey}` not valid (not found in MESA defaults)"
                    )
                    is_okay = False
                    break

    return is_okay


def get_number_of_gridpoints(d: dict = {}) -> int:
    """Get the number of points in the meshgrid

    Parameters
    ----------
    d : `dict`
        Dictionary with meshgrid points

    Returns
    -------
    n : `int`
        Number of models to evolve with the stellar evolutionary code
    """
    n = 1

    # we assume that there dictionary has one key with the namelist of MESA
    # which is in itself another dictionary with the actual gridpoints
    for namelist in d.keys():
        options = d[namelist]
        for option in options.keys():
            if isinstance(options[option], list):
                n *= len(options[option])
            else:
                logger.debug(f"{option} contains only one element")

    return n
