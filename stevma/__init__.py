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

    # create meshgrid
    core.set_meshgrid()

    # then, create the dictionary of MESAruns for the meshgrid
    core.create_MESAruns()

    # once the MESAruns are set, create template & runs folder structure
    core.set_MESAruns_structure()

    # next, split the dictionary of MESAruns to be more efficient once they are computed
    core.split_MESAruns()

    # then, store everything into a database
    core.dump_MESAruns_to_database()

    # last, create template job that will be used to launch each different set of smaller meshgrids
    # THIS IS NOT READY TO BE USED
    core.create_template_job()

    core.split_MESAruns()
    core.create_list_of_MESAruns_for_job()


def main():
    """Main driver for stellar evolution manager"""

    logger.info("******************")
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
