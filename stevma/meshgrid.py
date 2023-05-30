"""Module to manage the grid of different models of simulations of stellar evolution

Throughout the module, it is assumed that the grid is stored in a dictionary. Each key of the
dictionary must be a valid MESA namelist (see mesa/__init__.py for a list of valid options).
Each of them present in the dictionary is a dictionary in itself, such that the parameters that
are varied in the grid are keys of them and should contain lists or numbers or booleans\
"""

from typing import Any, Callable, Dict, List

import numpy as np

from stevma.io import logger
from stevma.mesa import get_mesa_defaults, mesa_namelists


def check_for_valid_namelist_options(d: Dict[Any, Any] = {}, mesa_dir: str = "") -> bool:
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
    namelists = [namelist for namelist in mesa_namelists.star_namelists]
    namelists.extend([namelist for namelist in mesa_namelists.binary_namelists])

    is_okay = True
    for key in d.keys():
        if key not in namelists:
            logger.critical(f"namelist `{key}` not present in MESA source code")
            is_okay = False
            break
        else:
            tmpDict = d[key]
            for subkey in tmpDict.keys():
                if subkey not in _MESADefaults.get(key):  # type: ignore
                    logger.critical(f"option `{subkey}` not valid (not found in MESA defaults)")
                    is_okay = False
                    break

    return is_okay


def create_meshgrid_from_dict(
    d: Dict[Any, Dict[str, Any]] = {}, conditions: List[Callable[..., bool]] = []
) -> Dict[Any, Any]:
    """Function that creates the meshgrid from a dictionary

    Parameters
    ----------
    d : `dict`
        Dictionary with different options of the meshgrid

    Returns
    -------
    meshgrid : `dict`
        Dictionary with the meshgrid
    """

    # get number of possible gridpoints (might be reduced later on)
    estimated_number_gridpoints = get_number_of_gridpoints(d)
    logger.debug(f"estimated number of gridpoints: {estimated_number_gridpoints}")

    # generate a list of identifiers based on the number of gridpoints. it starts with 0 and goes
    # up to (estimated_number_gridpoints - 1)
    identifiers = range(estimated_number_gridpoints)

    # dictionary that contains the actual runs, each key is a different run
    meshgrid: Dict[Any, Any] = dict()
    for k in identifiers:
        meshgrid.update({f"{k}": dict()})

    # create a tmp dict without namelists, but use them separately
    tmpDict = dict()
    option_names = []
    for namelist in d.keys():
        namelist_options = d.get(namelist)
        for option in namelist_options.keys():  # type: ignore
            option_names.append(option)

            values = namelist_options[option]  # type: ignore
            if not isinstance(values, list):
                try:
                    values = [values]
                except Exception as e:
                    logger.critical(f"{e}")

            tmpDict[option] = values

    # once the dictionary is set, use numpy to create the meshgrid
    tmpGrid = np.asarray(np.meshgrid(*list(tmpDict.values())))
    grid = np.column_stack([element.flatten() for element in tmpGrid])
    logger.debug(f"number of elements in the grid: {len(grid)}")

    # each element in the grid is then separated into different dictionaries, one for each case
    for k in range(len(grid)):
        row = grid[k]
        for j, name in enumerate(option_names):
            meshgrid.get(f"{k}").update({option_names[j]: row[j]})  # type: ignore
        logger.debug(f"meshgrid element ({k}): {meshgrid.get(f'{k}')}")

    # now we check some important stuff for binary evolution such as to avoid repeting simulations
    if len(conditions) > 0:
        keys_to_pop = []  # keys to remove from meshgrid are stored in this array
        for key in meshgrid.keys():
            tmpDict = meshgrid.get(key)  # type: ignore
            for k, condition in enumerate(conditions):
                if condition(tmpDict):
                    logger.debug(f"failed condition {k}: going to remove index {key} from meshgrid")
                    keys_to_pop.append(f"{key}")

        # pop keys that do not fulfill condition
        if len(keys_to_pop) > 0:
            for key in keys_to_pop:
                meshgrid.pop(key)

    return meshgrid


def get_number_of_gridpoints(d: Dict[Any, Any] = {}) -> int:
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
