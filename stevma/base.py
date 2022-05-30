"""Main driver for stellar evolution manager"""

import argparse
import os
from pathlib import Path
import sys

import pprint

from stevma.io.io import load_yaml
from stevma.io.logger import logger
from stevma.mesa import MESArun
from stevma.meshgrid import check_for_valid_namelist_options, create_meshgrid_from_dict


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

        # always get MESA_DIR value
        mesa_dir = self.config["mesa"].get("mesa_dir")
        if mesa_dir == "" or mesa_dir is None:
            mesa_dir = os.environ.get("MESA_DIR")
            if mesa_dir == "" or mesa_dir is None:
                logger.critical(
                    "mesa_dir must be defined either in the config file or as environment variable"
                )
                sys.exit(1)

        # always use pathlib
        if isinstance(mesa_dir, str):
            self.mesa_dir = Path(mesa_dir)
        else:
            self.mesa_dir = mesa_dir

        # load mesh of stellar evolution models
        self.meshgrid = None

        self.set_meshgrid()
        self.create_MESAruns()
        self.set_MESAruns_structure()

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

    def set_meshgrid(self, conditions: list = []) -> None:
        """Create grid of evolutionary models"""

        logger.info("creating meshgrid of models")

        # get dict of parameters that will be changing in the grid, each key of the dict
        # corresponds to a certain namelist of the MESA source code
        model_grid = self._load_meshgrid()

        # check of valid options in meshgrid
        if not check_for_valid_namelist_options(d=model_grid, mesa_dir=self.mesa_dir):
            sys.exit(1)

        self.meshgrid = create_meshgrid_from_dict(d=model_grid, conditions=conditions)
        #  [
        #  lambda d: True if d["m1"] < d["m2"] else False,
        #  lambda d: True if d["m2"] / d["m1"] < 0.5 else False,
        #  ],
        #  )

    def create_MESAruns(self) -> None:
        """Create a dictionary with each key being a different MESArun object"""

        logger.info("creating MESArun objects for each element in the meshgrid")

        if self.meshgrid is None:
            logger.critical(
                "meshgrid object is not defined. need to call `set_meshgrid` before"
            )

        # some useful dictionaries for creating MESArun objects
        runsDict = self.config.get("runs")
        templateDict = self.config.get("template")
        mesaDict = self.config.get("mesa")

        # loop over meshgrid to create MESArun objects
        self.MESAruns = dict()
        for key in self.meshgrid.keys():
            self.MESAruns[key] = MESArun(
                identifier=int(key),
                template_directory=templateDict.get("output_directory"),
                run_root_directory=runsDict.get("output_directory"),
                is_binary_evolution=templateDict.get("is_binary_evolution"),
                run_id=runsDict.get("id"),
                mesa_dir=mesaDict.get("mesa_dir"),
                mesasdk_dir=mesaDict.get("mesasdk_root"),
                mesa_caches_dir=mesaDict.get("mesa_caches_dir"),
                **self.meshgrid[key],
            )

            # load options for MESA simulations
            self.MESAruns[key].load_options(templateDict.get("options_filename"))

            # get dictionaries for template & run namelists
            self.MESAruns[key].set_template_namelists()
            self.MESAruns[key].set_run_namelists()

    def set_MESAruns_structure(self):
        """Method that takes care of creating the template & run folders for the meshgrid of
        stellar evolution models
        """

        # some useful dictionaries for creating MESArun objects
        runsDict = self.config.get("runs")
        templateDict = self.config.get("template")
        mesaDict = self.config.get("mesa")

        # create template stucture of MESAruns just once
        keys = list(self.meshgrid.keys())
        key0 = keys[0]
        self.MESAruns[key0].create_template_structure(
            copy_default_workdir=True, replace=templateDict.get("overwrite")
        )
        self.MESAruns[key0].save_namelists_to_file(name_id="template")

        # compile it
        self.MESAruns[key0].compile_template()

        # create and store namelists into each run folder
        for key in self.meshgrid.keys():
            self.MESAruns[key].create_run_structure()
            self.MESAruns[key].save_namelists_to_file(name_id="run")

    def dump_MESAruns_to_database(self) -> None:
        """Save information of MESAruns into a database"""

        return None
