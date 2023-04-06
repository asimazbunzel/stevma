"""Module with utils functions and classes for a MESA model
"""

from typing import Any, Dict, Tuple, Union

import os
from collections import OrderedDict
from pathlib import Path

import numpy as np

from stevma.io import parse_fortran_value_to_python


class MESANamelists:
    """Namelists of MESA"""

    def __init__(self):
        self.star_namelists = ("star_job", "controls", "pgstar", "eos", "kap")
        self.binary_namelists = ("binary_job", "binary_controls")
        self.bin2dco_namelists = ("bin2dco_controls",)


class MESAMainNamelists:
    """Structure of the most important files for initializing a MESA simulation"""

    def __init__(self):
        self.namelists_for_mesabinary = {
            "binary_job": {
                "read_extra_binary_job_inlist1": True,
                "extra_binary_job_inlist1_name": "#{template}/inlist_project",
            },
            "binary_controls": {
                "read_extra_binary_controls_inlist1": True,
                "extra_binary_controls_inlist1_name": "#{template}/inlist_project",
            },
            "binary_pgstar": {
                "read_extra_binary_pgstar_inlist1": True,
                "extra_binary_pgstar_inlist1_name": "#{template}/inlist_project",
            },
        }

        self.namelists_for_mesabin2dco = {
            "bin2dco_controls": {
                "do_star_plus_star": False,
                "star_plus_star_filename": "inlist_star_plus_star",
                "star_plus_pm_filename": "inlist_star_plus_pm",
                "cc1_inlist_filename": "inlist_cc",
                "cc2_inlist_filename": "inlist_cc",
                "ce1_inlist_filename": "inlist_ce",
                "ce2_inlist_filename": "inlist_ce",
                "stop_after_plus_star": True,
                "do_kicks": False,
                "do_kicks_in_one_run": False,
                "natal_kicks_filename": "",
                "header_lines_to_skip_in_natal_kicks_file": 1,
                "star_info_at_cc_filename": "cc_data/star_at_core_collapse.data",
                "binary_info_at_cc_filename": "cc_data/binary_at_core_collapse.data",
                "add_kick_id_as_suffix": False,
                "termination_codes_folder": "termination_codes",
            },
        }

        self.namelists_for_mesastar = {
            "star_job": {
                "read_extra_star_job_inlist1": True,
                "extra_star_job_inlist1_name": "#{template}/inlist_project",
            },
            "eos": {
                "read_extra_eos_inlist1": True,
                "extra_eos_inlist1_name": "#{template}/inlist_project",
            },
            "kap": {
                "read_extra_kap_inlist1": True,
                "extra_kap_inlist1_name": "#{template}/inlist_project",
            },
            "controls": {
                "read_extra_controls_inlist1": True,
                "extra_controls_inlist1_name": "#{template}/inlist_project",
            },
            "pgstar": {
                "read_extra_pgstar_inlist1": True,
                "extra_pgstar_inlist1_name": "#{template}/inlist_project",
            },
        }


def namelist_defaults(fname: Union[str, Path]) -> Dict[Any, Any]:
    """Get default options for a certain namelist used by MESA

    Parameters
    ----------
    fname : `str / Path`
        Name of the file with the namelist options

    Returns
    -------
    options : `dict`
        Dictionary with options for a MESA namelist
    """

    # always use Path for files
    if isinstance(fname, str):
        fname = Path(fname)

    if not fname.is_file():
        raise FileNotFoundError(f"`{fname}` not found")

    with open(fname) as f:
        lines = [line.strip() for line in f.readlines() if len(line) > 0]

    options = OrderedDict()
    for k, line in enumerate(lines):
        if not line.startswith("!") and "=" in line:
            line = line.split("!", 1)[0]

            if len(line.split("=")) < 2:
                raise ValueError(f"error in line: {line}")
            elif len(line.split("=")) > 2:  # there is just one string in the defaults with two '='
                name, lval, rval = line.split("=")
                value = f"{lval}={rval}"
            else:
                name, value, *extra_words = line.split("=")

            options[name.strip()] = parse_fortran_value_to_python(value=value.strip())

    return options


def get_mesa_defaults(mesa_dir: Union[str, Path] = "") -> Dict[Any, Any]:
    """Obtain all default options of every namelist used by MESA

    Parameters
    ----------
    mesa_dir : `str / Path`
        Path to MESA source folder. also found in shell as MESA_DIR environment variable

    Returns
    -------
    MESADefaults : `dict`
        Dictionary with all MESA defaults
    """

    # if mesa_dir is empty, try to get MESA_DIR from environment variable
    if mesa_dir == "":
        if os.environ.get("MESA_DIR") is None:
            raise ValueError(
                "`mesa_dir` cannot be empty. also it was not find in the environment variable list"
            )

    # use pathlib
    if isinstance(mesa_dir, str):
        mesa_dir = Path(mesa_dir)

    # load namelists for each MESA module
    mesaNamelists = MESANamelists()

    MESADefaults = dict()
    if "bin2dco" in str(mesa_dir):
        fname = mesa_dir / f"src/bin2dco_controls.defaults"
        MESADefaults["bin2dco_controls"] = namelist_defaults(fname=fname)

    else:
        for namelist in mesaNamelists.star_namelists:
            # check for proper folder name
            folder_name = "star"
            if "eos" in namelist:
                folder_name = "eos"
            if "kap" in namelist:
                folder_name = "kap"

            fname = mesa_dir / f"{folder_name}/defaults/{namelist}.defaults"
            MESADefaults[namelist] = namelist_defaults(fname=fname)

        for namelist in mesaNamelists.binary_namelists:
            folder_name = "binary"
            fname = mesa_dir / f"{folder_name}/defaults/{namelist}.defaults"
            MESADefaults[namelist] = namelist_defaults(fname=fname)

    return MESADefaults


def split_grid(number_of_grids: int = 1, Grid: Dict[Any, Any] = {}) -> Dict[str, Dict[Any, Any]]:
    """Split grid into smaller subgrids

    Parameters
    ----------
    number_of_grids : `int`
        Number of subgrids to split grid

    grid : `dict`
        Dictionary with complete meshgrid points

    Returns
    -------
    subgrids : `dict`
        Dictionary with smaller grids
    """

    if number_of_grids <= 0:
        raise ValueError(f"number_of_grids cannot be lower than 0: {number_of_grids}")

    if len(Grid) == 0:
        raise ValueError(f"Grid cannot be 0: {Grid}")

    # force number_of_grids to be an integer
    number_of_grids = int(number_of_grids)

    # create array with number of elements
    elements_in_grid = np.arange(len(Grid))

    # create array in which each element in another array of indexes
    array_of_indexes = np.array_split(elements_in_grid, number_of_grids)

    for k, arr in enumerate(array_of_indexes):
        for j in arr:
            Grid[f"{j}"]["job_id"] = k

    return Grid


mesa_namelists = MESANamelists()

mesa_main_namelists = MESAMainNamelists()
