"""Main driver for stellar evolution manager"""

import argparse
import os
from pathlib import Path
import sys

import pprint

from stevma.io.io import load_yaml
from stevma.io.logger import logger


class Manager(object):
    """Manager class contains the configuration needed to perform the evolution of a set of stellar
    models using the MESA code

    Parameters
    ----------
    """

    def __init__(self):
        # command line arguments
        self.args = self.parse_args()

        if self.args.config_fname is None:
            logger.critical("config-file cannot be empty")
            sys.exit(1)

        # always use pathlib module for files
        if isinstance(self.args.config_fname, str):
            # in case no config file, use defaults
            if len(self.args.config_fname) == 0:
                logger.critical("empty configuration file. using defaults")
                sys.exit(1)

            self.args.config_fname = Path(self.args.config_fname)

        # load config
        self.config = self.load_config_file()

        # load mesh of stellar evolution models
        self.meshgrid = None
        self.set_meshgrid()

    def init_args(self):
        """Initialize parser of arguments from the command line"""

        parser = argparse.ArgumentParser(
            prog="run-manager",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="make a grid of MESAbinary (MESAbin2dco) runs",
        )

        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            default=False,
            dest="debug",
            help="enable debug mode",
        )

        parser.add_argument(
            "-C",
            "--config-file",
            dest="config_fname",
            help="name of configuration file",
        )

        parser.add_argument(
            "--show-log-name",
            action="store_true",
            default=False,
            dest="log_fname",
            help="display log filename and exit",
        )

        parser.add_argument(
            "--list-grid",
            action="store_true",
            default=False,
            dest="list_grid",
            help="display grid list and exit",
        )

        parser.add_argument(
            "-v",
            "--visualize",
            action="store_true",
            default=False,
            dest="visualize",
            help="enable visualization of grid using matplotlib",
        )

        return parser

    def parse_args(self):
        """Parse command line arguments"""

        args = self.init_args().parse_args()

        # in case DEBUG flag is wanted
        if args.debug:
            from logging import DEBUG

            logger.setLevel(DEBUG)

        # print cli arguments to log file
        msg = "command line arguments are: "
        for k, v in sorted(vars(args).items()):
            msg += f"{k}: {v} "
        logger.debug(msg[:-1])

        return args

    def load_config_file(self) -> dict:
        """Load configuration file with options used by the manager"""

        logger.info("loading settings from file")

        if not self.args.config_fname.exists():
            logger.critical(f"no such file found: {self.args.config_fname}")
            sys.exit(1)

        return load_yaml(self.args.config_fname)

    def _load_meshgrid(self) -> dict:
        """Load mesh of stellar evolution models from a file"""

        logger.info("loading file with mesh of stellar evolution models")

        fname = Path(self.config["runs"]["meshgrid_filename"])

        if not fname.exists():
            logger.critical(f"no such file found: {fname}")
            sys.exit(1)

        return load_yaml(fname)

    def set_meshgrid(self) -> None:
        """Create grid of evolutionary models"""

        def check_for_valid_namelist_options(d: dict = {}) -> bool:
            """Function that checks whether a dictionary contains valid namelists of MESA as well
            as valid name of options

            Parameters
            ----------
            d : `dict`
                Dictionary with MESA options for the meshgrid
            """

            # import some info from mesa module
            from stevma.mesa import _defaultStarNamelists, _defaultBinaryNamelists
            from stevma.mesa.mesa import get_mesa_defaults

            # need MESA defaults parameters to check whether the arguments of the meshgrid are valid
            _MESADefaults = get_mesa_defaults(mesa_dir=os.environ["MESA_DIR"])

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

        # get dict of parameters that will be changing in the grid, each key of the dict
        # corresponds to a certain namelist of the MESA source code
        model_grid = self._load_meshgrid()

        # check of valid options in meshgrid
        if not check_for_valid_namelist_options(d=model_grid):
            sys.exit(1)

        number_of_gridpoints = get_number_of_gridpoints(d=model_grid)
        print(number_of_gridpoints)
