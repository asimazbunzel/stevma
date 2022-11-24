"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mstevma` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``stevma.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``stevma.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import os
from pathlib import Path
import platform
import signal
import sys

from .base import Manager
from .io.logger import LOG_FILENAME, logger


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
    core.create_template_job()

    core.split_MESAruns()
    core.create_list_of_MESAruns_for_job()


def main():
    """Main driver for stellar evolution manager"""

    logger.info("******************************************************")
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
