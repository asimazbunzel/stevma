"""Module use to handle a namelists used by MESA
"""

from collections import OrderedDict
import os
from pathlib import Path
from typing import Union

from stevma.mesa.io import parse_fortran_value_to_python


class MESAMainNamelists(object):
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
                "star_plus_star_filename": "#{template}/inlist_star_plus_star",
                "star_plus_pm_filename": "#{template}/inlist_star_plus_pm",
                "cc1_inlist_filename": "#{template}/inlist_cc",
                "cc2_inlist_filename": "#{template}/inlist_cc",
                "ce1_inlist_filename": "#{template}/inlist_ce",
                "ce2_inlist_filename": "#{template}/inlist_ce",
                "stop_after_plus_star": True,
                "do_kicks": False,
                "do_kicks_in_one_run": False,
                "natal_kicks_filename": "grid.data",
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


def namelist_defaults(fname: Union[str, Path]) -> dict:
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

    with open(fname, "r") as f:
        lines = [line.strip() for line in f.readlines() if len(line) > 0]

    options = OrderedDict()
    for k, line in enumerate(lines):
        if not line.startswith("!") and "=" in line:
            line = line.split("!", 1)[0]

            if len(line.split("=")) < 2:
                raise ValueError(f"error in line: {line}")
            elif (
                len(line.split("=")) > 2
            ):  # there is just one string in the defaults with two '='
                name, lval, rval = line.split("=")
                value = f"{lval}={rval}"
            else:
                name, value, *extra_words = line.split("=")

            options[name.strip()] = parse_fortran_value_to_python(value=value.strip())

    return options


def get_mesa_defaults(mesa_dir: Union[str, Path] = "") -> dict:
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

    if mesa_dir == "" and os.environ.get("MESA_DIR") is None:
        raise ValueError(
            "`mesa_dir` cannot be empty. also it was not find in the environment variable list"
        )

    # use pathlib
    if isinstance(mesa_dir, str):
        mesa_dir = Path(mesa_dir)

    namelists = (
        "star_job",
        "controls",
        "pgstar",
        "binary_job",
        "binary_controls",
        "eos",
        "kap",
    )

    star_namelists = ("star_job", "controls", "pgstar")
    binary_namelists = ("binary_job", "binary_controls", "binary_pgstar")

    MESADefaults = dict()
    for namelist in namelists:
        if namelist in star_namelists:
            folder_name = "star"
        elif namelist in binary_namelists:
            folder_name = "binary"
        else:
            folder_name = namelist

        fname = mesa_dir / f"{folder_name}/defaults/{namelist}.defaults"
        MESADefaults[namelist] = namelist_defaults(fname=fname)

    return MESADefaults
