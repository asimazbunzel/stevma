"""Main module driver to manage MESA simulations
"""

from pathlib import Path
from typing import Union
from shutil import copyfile
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
    identifier : `int`
        Integer for identification purposes for a database

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

    variables : `dict`
        Dictionary with the name and value of the variables to use in the MESA run. This is created
        with the **kwargs if this is the first time creating the object, but is present in the case
        the loading comes from a database

    namelists_for_init : `dict`
        Dictionary containing the information of the namelists needed to start a run (it contains
        input for the `inlist` file which MESA typically looks for)

    namelists_for_template : `dict`
        Dictionary with the options in each MESA namelist that is shared between different runs

    namelists_for_run : `dict`
        Dictionary with the options needed to perform a single MESA run

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
        Options : `dict`
            Dictionary with options to compare against defaults

        namelists : `list`
            List with strings matching MESA namelists

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

    def __pop_empty_namelists__(self, d: dict = {}) -> dict:
        """Remove empty namelists from dict

        Parameters
        ----------
        d : `dict`
            Dictionary to search for empty elements to pop
        """

        namelists = [namelist for namelist in self._defaultStarNamelists]
        namelists.extend(([namelist for namelist in self._defaultBinaryNamelists]))

        keys_to_pop = []
        for namelist in namelists:
            if namelist in d:
                if len(d[namelist]) == 0:
                    keys_to_pop.append(namelist)

        if len(keys_to_pop) > 0:
            for key in keys_to_pop:
                d.pop(key)

        return d

    def set_template_namelists(self) -> None:
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
        projectNamelists = dict()
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

                self.namelists_for_template = self.__pop_empty_namelists__(d=mesabinaryOptions)

            elif self.run_id == "mesabin2dco":
                sys.exit("mesabin2dco template project not ready to be used")

            else:
                sys.exit(
                    f"{self.run_id}: unknown id for creating template of binary namelists"
                )

        else:

            if self.run_id == "mesastar":
                mesastarOptions = self.__get_non_default_values_for_namelists__(
                    Options=self._MESAOptions, namelists=self._defaultStarNamelists
                )

                self.namelists_for_template = self.__pop_empty_namelists__(d=mesastarOptions)

            else:
                sys.exit(
                    f"{self.run_id}: unknown id for creating template star namelists"
                )

    def set_run_namelists(self) -> None:
        """Create namelists with options that change for different MESA runs
        """

        def replace_run_string_in_dict(d: dict = {}) -> dict:
            """Replace a string with `template` in a key

            Parameters
            ----------
            d : `dict`
                Dictionary to search for the string to replace
            """

            for key, value in d.items():
                try:
                    if "#{run}" in d[key]:
                        arr = value.split("/")
                        value = f"{self.run_directory}/{arr[-1]}"
                        d[key] = value
                except TypeError:
                    continue

            return d

        if self.is_binary_evolution:

            if self.run_id == "mesabinary":
                mesabinaryOptions = self.__get_non_default_values_for_namelists__(
                    Options=self.variables, namelists=self._defaultBinaryNamelists
                )

                runOptions = mesabinaryOptions

            elif self.run_id == "mesabin2dco":
                sys.exit("mesabin2dco template project not ready to be used")

            else:
                sys.exit(
                    f"{self.run_id}: unknown id for creating template of binary namelists"
                )

        # load options with MESAstar variable options
        mesastarOptions = self.__get_non_default_values_for_namelists__(
            Options=self.variables, namelists=self._defaultStarNamelists
        )

        runOptions.update(mesastarOptions)

        # once all run options are set, remove empty elements in dictionary and store it as the
        # namelists_for_run
        self.namelists_for_run = self.__pop_empty_namelists__(d=runOptions)

    def create_template_structure(self,
        copy_default_workdir: bool = True,
        extra_src_files: list = [],
        extra_makefile: list = [],
        extra_template_files: list = [],
    ) -> None:
        """Create and copy files and folders to template root

        Parameters
        ----------
        copy_default_workdir : `bool`
            Flag to choose whether to copy the default workdir of MESA

        extra_src_files : `list`
            List of files that should go in the src folder of the template

        extra_makefile : `list`
            List of makefiles that goes in the make folder

        extra_template_files : `list`
            List of files that should be copied in the template folder
        """

        # create folders in template directory
        for name in self._defaultFolderNames:
            folder_name = self.template_directory / name
            folder_name.mkdir(parents=True)

        if copy_default_workdir:
            # set some useful variable names
            if self.is_binary_evolution:
                mesa_folder = "binary"
                src_files = self._defaultSrcFilenamesBinary
            else:
                mesa_folder = "star"
                src_files = self._defaultSrcFilenamesStar

            # loop over common scripts of MESA
            for file in self._defaultScriptFilenames:
                fname = self.mesa_dir / mesa_folder / "work" / file

                if file == "makefile":
                    output_folder = self.template_directory / "make"
                    fname = self.mesa_dir / mesa_folder / "work/make" / file
                else:
                    output_folder = self.template_directory

                # to use copyfile, need to set the name of the output, not just the folder
                if fname.is_file():
                    output_file = output_folder / file
                    copyfile(fname, output_file)
                else:
                    print(f"could not copy file {fname}. file not found")

            # also loop over src files depending on the type of run
            for file in src_files:
                fname = self.mesa_dir / mesa_folder / "work/src" / file
                output_folder = self.template_directory / "src"

                if fname.is_file():
                    output_file = output_folder / file
                    copyfile(fname, output_file)
                else:
                    print(f"could not copy file {fname}. file not found")

        else:
            # try to copy extra files
            if len(extra_src_files) > 0:
                for file in extra_src_files:
                    output_folder = self.template_directory / "src"
                    file = Path(file)
                    if file.is_file():
                        output_file = output_folder / file
                        copyfile(file, output_file)
                    else:
                        print(f"could not copy file {file}. file not found")

                    if ".f" not in file:
                        print(
                            f"file {file} is not a fortran file. copying either way"
                        )
            else:
                print("source files were not provided for custom workdir")

            # extra files in the make folder
            if len(extra_makefile):
                for file in extra_makefile:
                    output_folder = self.template_directory / "make"
                    file = Path(file)
                    if file.is_file():
                        output_file = output_folder / file
                        copyfile(file, output_file)
                    else:
                        print(f"could not copy file {file}. file not found")
            else:
                print("makefile was not provided for custom workdir")

        # copy extra files for the template directory. e.g., the *.list files with what will be
        # saved in MESA output
        if len(extra_template_files) > 0:
            for file in extra_template_files:
                output_folder = self.template_directory
                file = Path(file)
                if file.is_file():
                    output_file = output_folder / file
                    copyfile(file, output_file)
                else:
                    print(f"could not copy file {file}. file not found")

    def create_run_structure(self) -> None:
        """Create and copy files to run root
        """

        if not self.run_directory.is_dir():
            self.run_directory.mkdir(parents=True)

    def save_namelists_to_file(self, loc_id: str = "") -> None:
        """Save namelists to a file

        Parameters
        ----------
        loc_id : `str`
            Identifier to know where to store the inlist. Options are: `template` or `run`
        """

        if loc_id == "template":
            folder_name = self.template_directory
        elif loc_id == "run":
            folder_name = self.run_directory
        else:
            sys.exit(
                f"{loc_id} is not a valid option"
            )
