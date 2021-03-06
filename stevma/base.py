"""Main driver for stellar evolution manager"""

import argparse
import os
from pathlib import Path
import subprocess
import sys

import pprint

from stevma.io.io import load_yaml
from stevma.io.logger import logger
from stevma.job import MESAJob, ShellJob
from stevma.mesa import MESArun
from stevma.meshgrid import (
    check_for_valid_namelist_options,
    create_meshgrid_from_dict,
    split_grid,
)


class Manager(object):
    """Manager class contains the configuration needed to perform the evolution of a set of stellar
    models using the MESA code

    Parameters
    ----------
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

    def parse_args(self) -> argparse.Namespace:
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
            sys.exit(1)

        # some useful dictionaries for creating MESArun objects
        runsDict = self.config.get("runs")
        templateDict = self.config.get("template")
        mesaDict = self.config.get("mesa")

        # loop over meshgrid to create MESArun objects
        self.MESAruns = dict()
        for key in self.meshgrid.keys():
            self.MESAruns[key] = dict()
            self.MESAruns[key].update(
                {
                    "MESArun": MESArun(
                        identifier=int(key),
                        template_directory=templateDict.get("output_directory"),
                        run_root_directory=runsDict.get("output_directory"),
                        is_binary_evolution=templateDict.get("is_binary_evolution"),
                        run_id=runsDict.get("id"),
                        mesa_dir=mesaDict.get("mesa_dir"),
                        mesasdk_dir=mesaDict.get("mesasdk_root"),
                        mesa_caches_dir=mesaDict.get("mesa_caches_dir"),
                        mesabin2dco_dir=mesaDict.get("mesabin2dco_dir"),
                        **self.meshgrid[key],
                    )
                }
            )

            # load options for MESA simulations
            self.MESAruns[key]["MESArun"].load_options(
                templateDict.get("options_filename")
            )

            # get dictionaries for template & run namelists
            self.MESAruns[key]["MESArun"].set_template_namelists()
            self.MESAruns[key]["MESArun"].set_run_namelists()

    def set_MESAruns_structure(self) -> None:
        """Method that takes care of creating the template & run folders for the meshgrid of
        stellar evolution models
        """

        logger.info("setting template and run structure for MESA runs")

        # some useful dictionaries for creating MESArun objects
        runsDict = self.config.get("runs")
        templateDict = self.config.get("template")
        mesaDict = self.config.get("mesa")

        # if the id of the runs is `mesabin2dco`, add inlists from src code
        extra_template_files = []
        if runsDict.get("id") == "mesabin2dco":
            extra_template_files.append(f"{mesaDict.get('mesabin2dco_dir')}/inlist_ce")
            extra_template_files.append(f"{mesaDict.get('mesabin2dco_dir')}/inlist_cc")

        # create template stucture of MESAruns just once
        keys = list(self.meshgrid.keys())
        key0 = keys[0]
        self.MESAruns[key0]["MESArun"].create_template_structure(
            copy_default_workdir=True,
            replace=templateDict.get("overwrite"),
            extra_template_files=extra_template_files,
        )
        self.MESAruns[key0]["MESArun"].save_namelists_to_file(name_id="template")

        # also, save *.list files with the information on the columns that will be saved by MESA
        list_filenames = []
        for name in [
            mesaDict.get("history_columns_filename"),
            mesaDict.get("profile_columns_filename"),
            mesaDict.get("binary_history_columns_filename"),
        ]:
            if name is not None and name != "":
                list_filenames.append(name)
        self.MESAruns[key0]["MESArun"].copy_column_list_files(filenames=list_filenames)

        # compile it
        self.MESAruns[key0]["MESArun"].compile_template()

        # create and store namelists into each run folder
        for key in self.meshgrid.keys():
            self.MESAruns[key]["MESArun"].create_run_structure()
            self.MESAruns[key]["MESArun"].save_namelists_to_file(name_id="run")

    def dump_MESAruns_to_database(self) -> None:
        """Save information of MESAruns into a database"""

        logger.info("dumping MESAruns into database")

        return None

    def split_MESAruns(self) -> None:
        """Split the meshgrid of MESAruns into smaller ones by adding a new key to the dictionary
        with the name `job_id`
        """

        logger.info("splitting MESAruns dictionary into smaller meshgrids")

        # dictionary with manager settings
        managerDict = self.config.get("manager")

        # split grid
        self.MESAruns = split_grid(
            number_of_grids=managerDict.get("number_of_jobs"), Grid=self.MESAruns
        )

    def create_template_job(self) -> None:
        """Create the shell script to be used to run the stellar evolution simulations"""

        logger.info(
            "creating template job that will be used to launch different runs of the meshgrid"
        )

        # some useful dictionaries for creating template job script
        mesaDict = self.config.get("mesa")
        templateDict = self.config.get("template")
        runsDict = self.config.get("runs")
        managerDict = self.config.get("manager")

        # mesaJob object contains all the stuff needed to make a MESA run
        mesaJob = MESAJob(
            mesa_dir=mesaDict.get("mesa_dir"),
            mesasdk_dir=mesaDict.get("mesasdk_root"),
            mesa_caches_dir=mesaDict.get("mesa_caches_dir"),
            is_binary_evolution=templateDict.get("is_binary_evolution"),
        )

        # create command which will go into a shell script
        command = mesaJob.set_mesainit_string()
        command += mesaJob.set_mesa_env_variables_string(
            template_directory=templateDict.get("output_directory"),
            runs_directory=runsDict.get("output_directory"),
        )
        command += mesaJob.set_main_loop_string()

        # create manager job and write it to a file
        if managerDict.get("manager") == "shell":
            # get name of job file
            fname = ""
            if managerDict.get("job_file_prefix") != "":
                fname += f"{managerDict.get('job_file_prefix')}"

            if managerDict.get("job_filename") != "":
                fname += f"{managerDict.get('job_filename')}"

            # if fname is empty, exit with an error
            if fname == "":
                logger.critical(
                    "both `job_file_prefix` and `job_filename` cannot be empty strings. cannot create job filename"
                )
                sys.exit(1)

            job = ShellJob(name="ShellJob", command=command)
            job.write_job_to_file(fname=fname)

        else:
            logger.critical(
                "using a different manager than `shell` is not ready to be used to create a template job"
            )
            sys.exit(1)

    def create_list_of_MESAruns_for_job(self) -> None:
        """Create a txt file in which every row is a different run of the meshgrid depending on the
        `job_id`
        """

        logger.info(
            "creating txt files with the list of folders to be computed by the stellar evolutionary code depending on the job_id value"
        )

        # useful dicts
        managerDict = self.config.get("manager")
        runsDict = self.config.get("runs")

        number_of_jobs = managerDict.get("number_of_jobs")
        for k in range(number_of_jobs):
            fname = f"{runsDict.get('output_directory')}/job_{k}.folders"
            logger.debug(f"going to write folders for job_id {k} in file {fname}")

            folder_list = []
            for id_number in self.MESAruns:
                # each element in the dict has a MESArun object and a job_id
                mesaRun = self.MESAruns[id_number]["MESArun"]
                jobId = self.MESAruns[id_number]["job_id"]

                # just append with the proper job_id value
                if jobId == k:
                    folder_list.append(mesaRun.run_name)

            logger.debug(f"folder list for job_id {k}: {folder_list}")
            logger.debug(f"number of folders: {len(folder_list)}")

            with open(fname, "w") as f:
                for folder in folder_list:
                    f.write(f"{folder}\n")

    def submit_specific_job(self, job_id: int = 0) -> None:
        """Submit a job to a queue"""

        # check for a valid job_id number
        if job_id < 0:
            logger.critical("job_id (int) number cannot be lower than 0")
            sys.exit(1)

        # useful dicts
        managerDict = self.config.get("manager")
        runsDict = self.config.get("runs")

        # get number of jobs
        number_of_jobs = managerDict.get("number_of_jobs")

        # check that the job_id is lower than the number of jobs
        if job_id > number_of_jobs:
            logger.critical(
                "job_id cannot be higher than the number of jobs (number_of_jobs)"
            )
            sys.exit(1)

        # name of the file with the runs of the specific job_id
        fname = f"{runsDict.get('output_directory')}/job_{job_id}.folders"

        # submit depending on the manager
        if managerDict.get("manager") == "shell":
            try:
                p = subprocess.Popen(
                    f"sh {fname}",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                stdout, stderr = p.communicate()
                print(stdout[:-1])

            except Exception as e:
                print(e)

        else:
            logger.critical(
                "using a different manager than `shell` is not ready to be used to submit a job"
            )
            sys.exit(1)
