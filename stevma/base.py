"""Main driver for stellar evolution manager"""

import argparse
from pathlib import Path
import sys

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

        # always use pathlib module for files
        if isinstance(self.args.config_fname, str):
            # in case no config file, use defaults
            if len(self.args.config_fname) == 0:
                logger.critical("empty configuration file. using defaults")

            self.args.config_fname = Path(self.args.config_fname)

        # load config
        self.config = self.load_config_file()

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
            "--C",
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

        logger.info("load settings from file")

        if not self.args.config_fname.exists():
            logger.critical(f"no such file found: {self.args.config_fname}")

        return load_yaml(self.args.config_fname)
