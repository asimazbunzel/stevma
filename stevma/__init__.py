"""Base module for manager"""

import os
import platform
from pathlib import Path
import signal
import sys

from stevma.io.logger import logger, LOG_FILENAME
from stevma.base import Manager

__version__ = "0.0.1"


def __signal_handler(signal, frame):
    """Callback for CTRL-C"""
    end()


def end():
    """Stop manager"""

    logger.info("manager stopped")

    sys.exit(0)


def start():
    """Start manager"""

    logger.info("manager started")

    # if only wanting to print name of log name
    if core.args.log_fname:
        print(f"LOG FILENAME is: `{LOG_FILENAME}`")
        sys.exit(0)


def main():
    """Main driver for stellar evolution manager"""

    logger.info("initialize manager")

    # catch CTRL-C signal
    signal.signal(signal.SIGINT, __signal_handler)

    # current working directory
    curr_dir = os.getcwd()

    logger.debug(f"current working directory is {curr_dir}")
    logger.info(
        f"{platform.python_implementation()} {platform.python_version()} detected"
    )

    # main driver
    global core
    core = Manager()

    # start manager
    start()

    # shutdown
    end()
