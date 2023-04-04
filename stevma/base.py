"""Main driver for stellar evolution manager"""

import argparse
import os
import pprint
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

from stevma.io import load_yaml, logger
from stevma.meshgrid import check_for_valid_namelist_options, create_meshgrid_from_dict

# from .io.database import create_database, insert_into_database
# from .job import MESAJob, ShellJob, SlurmJob
# from .mesa import MESArun
# from .meshgrid import check_for_valid_namelist_options, create_meshgrid_from_dict, split_grid


class Manager:
    """Manager class contains the configuration needed to perform the evolution of a set of stellar
    models using the MESA code

    Every option on the Manager is loaded from the command-line interface. Parameters for the grid
    are obtained from different configuration files.
    """

    def __init__(self) -> None:
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
        mesa_dir = self.config["Mesa"].get("mesa_dir")
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

    def init_args(self) -> argparse.ArgumentParser:
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
            "--show-database-name",
            action="store_true",
            default=False,
            dest="database_fname",
            help="display database filename and exit",
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
            help="enable visualization of grid using matplotlib. EXPERIMENTAL: NOT READY TO USE",
        )

        return parser

    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments"""

        parser = self.init_args()

        # print help msg if no arguments were given
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        # get parsed arguments
        args = parser.parse_args()

        # in case DEBUG flag is wanted
        if args.debug:
            from logging import DEBUG

            logger.setLevel(DEBUG)

        # print cli arguments to log file
        msg = "command line arguments are: "
        for k, v in sorted(vars(args).items()):
            msg += f"{k}={v} "
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

        fname = Path(self.config["Models"]["meshgrid_filename"])

        if not fname.exists():
            logger.critical(f"no such file found: {fname}")
            sys.exit(1)

        return load_yaml(fname)

    def set_meshgrid(self, conditions: list = []) -> None:
        """Create grid of evolutionary models

        Parameters
        ----------
        conditions : `list`
            List of conditions to apply to grid. They should be python lambda functions. As an
            example, conditions could be:
            [
            lambda d: True if d['m1'] < d['m2'] else False,
            lambda d: True if d['m2'] / d['m1'] < 0.5 else False,
            ]
        """

        logger.info("creating meshgrid of models")

        # get dict of parameters that will be changing in the grid, each key of the dict
        # corresponds to a certain namelist of the MESA source code
        model_grid = self._load_meshgrid()

        # check of valid options in meshgrid
        if not check_for_valid_namelist_options(d=model_grid, mesa_dir=self.mesa_dir):
            sys.exit(1)

        self.meshgrid = create_meshgrid_from_dict(d=model_grid, conditions=conditions)
