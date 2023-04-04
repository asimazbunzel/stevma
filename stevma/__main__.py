# type: ignore[attr-defined]
import os
import platform
import pprint
import signal
import sys
import time

from stevma.base import Manager
from stevma.io import LOG_FILENAME, logger
from stevma.mesa import MESAGrid


def __signal_handler(signal, frame) -> None:
    """Callback for CTRL-C"""
    end()


def end() -> None:
    """Stop manager"""

    print("shutting down")

    # time it
    _endTime = time.time()

    logger.info(f"[-- manager uptime: {_endTime - _startTime:.2f} sec --]")
    logger.info("manager stopped")

    sys.exit(0)


def start() -> None:
    """Start manager"""

    logger.info("manager started")

    # manager
    core = Manager()

    # if only wanting to print name of log name
    if core.args.log_fname:
        print(f"LOG FILENAME is: `{LOG_FILENAME}`")
        end()

    print("initializing manager and creating grid of MESA models", end="... ", flush=True)

    # create meshgrid
    core.set_meshgrid()

    # grid of MESA models
    global grid
    grid = MESAGrid(meshgrid=core.meshgrid, config=core.config)
    # then, create the dictionary of MESAruns for the meshgrid
    grid.create_MESAmodels()

    print("done")


def run() -> None:
    """Run manager"""

    print("creating structure of MESAmodels with database backup", end="... ", flush=True)
    # once the MESAruns are set, create template & runs folder structure
    grid.set_MESAmodels_structure()
    grid.split_MESAmodels()

    # then, store everything into a database
    grid.dump_MESAmodels_to_database()

    # last, create template job that will be used to launch each different set of smaller meshgrids
    # also created in this step
    grid.create_template_job()
    grid.create_list_of_MESAruns_for_job()
    print("done")

    print("compiling MESA source code", end="... ", flush=True)
    grid.compile_template()
    print("done")

    # **************************************************
    # reserved for submission of models to queue manager
    # **************************************************


def main() -> None:
    """Main driver for stellar evolution manager"""

    logger.info("********************************************************")
    logger.info("               Stellar Evolution Manager                ")
    logger.info("********************************************************")
    logger.info("initialize manager for grid of stellar evolution models")

    curr_dir: str = os.getcwd()
    logger.info(f"current working directory is `{curr_dir}`")
    logger.info(f"{platform.python_implementation()} {platform.python_version()} detected")

    # catch CTRL-C signal
    signal.signal(signal.SIGINT, __signal_handler)

    # time it
    global _startTime
    _startTime = time.time()

    # start manager
    start()

    # run manager
    run()

    # shutdown
    end()
