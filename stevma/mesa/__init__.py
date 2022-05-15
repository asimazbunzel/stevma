"""Main module driver to manage MESA simulations
"""

from pathlib import Path
import pprint
from typing import Union
import sys

import yaml

from stevma.mesa.mesa import MESAMainNamelists, get_mesa_defaults
from stevma.mesa.io import load_yaml


class MESArun(object):
    """Object corresponding to a single MESA simulation

    This simulation can be either a single or a binary evolution.

    This class holds the information needed to compute the evolution as well as other useful stuff

    Parameters
    ----------
    template_directory : `str / Path`
        Folder location of the template used in the run

    run_root_directory : `str / Path`
        The location where the output of MESA will be located

    is_binary_evolution : `bool`
        Flag to control the type of module to use by MESA to run either a single or a binary
        evolution

    run_id: `str`
        Identifier for the run. It is used in combination with is_binary_evolution. Possible
        options are `mesastar`, `mesabinary` or `mesabin2dco`

    custom_run_name : `str`
        Name of the folder where the output of MESA will be stored

    mesa_dir : `str / Path`
        Location of the MESA source code

    **kwargs : `dict`
        All options that are changing between simulations should be here. Their names should match
        the ones defined by the MESA namelists. E.g., to simulate a star of 10 solar masses, one
        should pass the argument: `star_mass = 10`
    """

    # some defaults for MESA
    _defaultScriptFilenames = ("clean", "mk", "re", "rn", "makefile")
    _defaultFolderNames = ("make", "src")
    _defaultSrcFilenamesStar = ("run.f90", "run_star_extras.f90")
    _defaultSrcFilenamesBinary = (
        "binary_run.f90",
        "run_binary_extras.f90",
        "run_star_extras.f90",
    )
    _defaultStarNamelists = ("star_job", "eos", "kap", "controls", "pgstar")
    _defaultBinaryNamelists = ("binary_job", "binary_controls", "binary_pgstar")

    def __init__(
        self,
        identifier: int = 0,
        template_directory: Union[str, Path] = "",
        run_root_directory: Union[str, Path] = "",
        is_binary_evolution: bool = False,
        run_id: str = "",
        custom_run_name: str = "",
        mesa_dir: str = "",
        variables: dict = {},
        namelists_for_init: dict = {},
        namelists_for_template: dict = {},
        namelists_for_run: dict = {},
        **kwargs,
    ) -> None:

        # id to use in the database
        self.identifier = identifier

        # let folders be handled by pathlib module
        if isinstance(template_directory, str):
            self.template_directory = Path(template_directory)
        else:
            self.template_directory = template_directory

        if isinstance(run_root_directory, str):
            self.run_root_directory = Path(run_root_directory)
        else:
            self.run_root_directory = run_root_directory

        # flag to control the type of run between star or binary
        self.is_binary_evolution = is_binary_evolution

        # mesa_run_id sets the id for the type of run
        self.run_id = run_id

        if isinstance(mesa_dir, str):
            self.mesa_dir = Path(mesa_dir)
        else:
            self.mesa_dir = mesa_dir

        # load MESA defaults
        self._MESADefaults = get_mesa_defaults(mesa_dir=self.mesa_dir)

        # hidden name of run
        self.__run_name_from_kwargs__ = ""

        # get name and value of parameter that will be changing in the grid
        # in case this is in a database, it can be set at runtime
        if len(variables) == 0:
            variables = dict()
            for key, value in kwargs.items():
                found_variable_name = False
                for namelist in self._MESADefaults.keys():
                    if key in self._MESADefaults.get(namelist):
                        found_variable_name = True
                        break

                if found_variable_name:
                    # check whether the namelist is already present in the
                    # variable dictionary, else add it
                    if namelist not in variables:
                        variables[namelist] = dict()
                    # then, add key and value to variable dictionary
                    variables[namelist][key] = value
                    self.__run_name_from_kwargs__ += f"{key}_{value}_"
                else:
                    sys.exit(f"could not find {key} in MESA parameter list")
        self.variables = variables

        if custom_run_name != "":
            self.run_name = custom_run_name
        else:
            self.run_name = self.__run_name_from_kwargs__[:-1]

        # run folder is a combination of the root of run plus a custom name
        self.run_directory = self.run_root_directory / self.run_name

        # again, if not the first time using this, a database can have this information
        if len(namelists_for_init) == 0:
            self.namelists_for_init = None
        if len(namelists_for_template) == 0:
            self.namelists_for_template = None
        if len(namelists_for_run) == 0:
            self.namelists_for_run = None

    def load_options(self, fname: Union[str, Path] = "") -> None:
        """Load options needed for a MESA run

        Parameters
        ----------
        fname : `str / Path`
            Filename with MESA options
        """

        # always use pathlib
        if isinstance(fname, str):
            fname = Path(fname)

        # check whether file exists or not
        if not fname.is_file():
            raise FileNotFoundError(f"`{fname}` file not found")

        # load MESA options from YAML file as a dict
        self._MESAOptions = load_yaml(fname=fname)

    def __get_non_default_values_for_namelists__(
        self, Options: dict = {}, namelists: list = []
    ) -> dict:
        """Look for non default options in namelists when compared to MESA defaults

        Parameters
        ----------

        Returns
        -------
        """

        if len(Options) == 0:
            raise ValueError(f"`Options` (dict argument) cannot be an empty dictionary")

        nonDefaultOptions = dict()
        for namelist in namelists:
            nonDefaultOptions[namelist] = dict()

            optionsForNamelist = Options.get(namelist, None)
            if optionsForNamelist is not None:
                for key, value in optionsForNamelist.items():
                    # some patches for some controls that are problematic
                    if (
                        key == "read_extra_binary_controls_inlist1"
                        or key == "read_extra_binary_controls_inlist2"
                        or key == "read_extra_binary_controls_inlist3"
                        or key == "read_extra_binary_controls_inlist4"
                        or key == "read_extra_binary_controls_inlist5"
                    ):
                        nonDefaultOptions[namelist][key] = value
                        continue
                    elif (
                        key == "extra_binary_controls_inlist1_name"
                        or key == "extra_binary_controls_inlist2_name"
                        or key == "extra_binary_controls_inlist3_name"
                        or key == "extra_binary_controls_inlist4_name"
                        or key == "extra_binary_controls_inlist5_name"
                    ):
                        if "#{run}" in value:
                            arr = value.split("/")
                            value = f"{self.run_directory}/{arr[-1]}"
                        elif "#{template}" in value:
                            arr = value.split("/")
                            value = f"{self.template_directory}/{arr[-1]}"
                        else:
                            sys.exit(
                                "could not find string matching #{run} or #{template} to replace in extra_binary_controls_inlist1_name"
                            )
                        nonDefaultOptions[namelist][key] = value
                        continue

                    # only add those options that do not match defaults
                    if value != self._MESADefaults.get(namelist)[key]:
                        # this is to replace some template & run strings
                        if isinstance(value, str):
                            if "#{run}" in value:
                                arr = value.split("/")
                                value = f"{self.run_directory}/{arr[-1]}"
                            elif "#{template}" in value:
                                arr = value.split("/")
                                value = f"{self.template_directory}/{arr[-1]}"

                        nonDefaultOptions[namelist][key] = value

        return nonDefaultOptions

    def set_template_namelists(self):
        """Create namelists with options that do not change for different MESA runs

        These options are then considered to be a template for the run
        """

        def replace_template_string_in_dict(d: dict = {}) -> dict:
            """Replace a string with `template` in a key"""
            for key, value in d.items():
                try:
                    if "#{template}" in d[key]:
                        arr = value.split("/")
                        value = f"{self.template_directory}/{arr[-1]}"
                        d[key] = value
                except TypeError:
                    continue

            return d

        # load main namelists of MESA
        MESANamelists = MESAMainNamelists()

        # first, structure the template for the most important namelist which lives
        # in the `inlist` file
        inlistNamelists = dict()
        if self.is_binary_evolution:

            if self.run_id == "mesabinary":
                # need to replace some strings here
                for namelist in self._defaultBinaryNamelists:
                    dictNamelist = MESANamelists.namelists_for_mesabinary[namelist]
                    inlistNamelists[namelist] = replace_template_string_in_dict(
                        dictNamelist
                    )

            elif self.run_id == "mesabin2dco":
                dictNamelist = MESANamelists.namelists_for_mesabin2dco[
                    "bin2dco_controls"
                ]
                inlistNamelists["bin2dco_controls"] = replace_template_string_in_dict(
                    dictNamelist
                )

            else:
                sys.exit(
                    f"{self.run_id}: unknown id for creating template of binary namelists"
                )

        else:

            if self.run_id == "mesastar":
                # again, some replacements are needed
                for namelist in self._defaultStarNamelists:
                    dictNamelist = MESANamelists.namelists_for_mesastar[namelist]
                    inlistNamelists[namelist] = replace_template_string_in_dict(
                        dictNamelist
                    )

            else:
                sys.exit(
                    f"{self.run_id}: unknown id for creating template star namelists"
                )

        self.namelists_for_init = inlistNamelists

        # next, the structure for the `inlist_project` is created. this file is called from inside
        # the previously created `inlist`
        if self.is_binary_evolution:

            if self.run_id == "mesabinary":
                mesabinaryOptions = self.__get_non_default_values_for_namelists__(
                    Options=self._MESAOptions, namelists=self._defaultBinaryNamelists
                )

                # for these, we need to set up inlist(1) & inlist(2) if not present already
                if "inlist_names(1)" not in mesabinaryOptions["binary_job"]:
                    mesabinaryOptions["binary_job"][
                        "inlist_names(1)"
                    ] = f"{self.run_directory}/inlist1"
                if "inlist_names(2)" not in mesabinaryOptions["binary_job"]:
                    mesabinaryOptions["binary_job"][
                        "inlist_names(2)"
                    ] = f"{self.run_directory}/inlist2"

                self.namelists_for_template = mesabinaryOptions
