"""Base module for manager"""

import os
import platform
from pathlib import Path
import signal
import sys

from stevma.io.logger import logger

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

    pass


def main():
    """Main driver for stellar evolution manager"""

    logger.info("start manager")

    # catch CTRL-C signal
    signal.signal(signal.SIGINT, __signal_handler)

    # current working directory
    curr_dir = os.getcwd()

    logger.debug(f"current working directory is {curr_dir}")
    logger.info(
        f"{platform.python_implementation()} {platform.python_version()} detected"
    )

    # start manager
    start()

    # shutdown
    end()
