"""Main module driver to manage MESA simulations
"""

from typing import Any, Dict

import pprint
import subprocess
import sys

from stevma.io import Database, logger, progress_bar
from stevma.job import MESAJob, ShellJob, SlurmJob

from .mesa import MESAmodel
from .utils import get_mesa_defaults, mesa_namelists, split_grid

__all__ = ["get_mesa_defaults", "mesa_namelists"]


class MESAGrid:
    """Class representing a grid of MESA models

    Parameters
    ----------
    meshgrid : `dict`
        Dictionary with input values of the grid of MESA models
    """

    def __init__(self, meshgrid: Dict[Any, Any] = dict(), config: Dict[Any, Any] = dict()) -> None:
        self.meshgrid = meshgrid
        self.config = config

        # load MESA models into a dictionary
        self.MESAmodels: Dict[Any, Any] = dict()

        # load database as an object
        self.database = Database(
            database_name=self.config["Database"].get("filename"),
            remove_database=self.config["Database"].get("remove_database"),
        )

    def create_MESAmodels(self) -> None:
        """Create a dictionary with each key being a different MESAmodel object"""

        logger.info("creating MESAmodel objects for each element in the meshgrid")

        if len(self.meshgrid) == 0:
            logger.critical("meshgrid object is not defined. need to call `set_meshgrid` before")
            sys.exit(1)

        # some useful dictionaries for creating MESAmodel objects
        runsDict = self.config.get("Models")
        templateDict = self.config.get("Template")
        mesaDict = self.config.get("Mesa")

        # loop over meshgrid to create MESAmodel objects
        for key in self.meshgrid.keys():
            logger.info(f"updating MESAmodels with id: {key}")

            self.MESAmodels[key] = dict()
            self.MESAmodels[key].update(
                {
                    "MESAmodel": MESAmodel(
                        identifier=int(key),
                        template_directory=templateDict.get("output_directory"),  # type: ignore
                        run_root_directory=runsDict.get("output_directory"),  # type: ignore
                        is_binary_evolution=templateDict.get("is_binary_evolution"),  # type: ignore
                        model_id=runsDict.get("id"),  # type: ignore
                        mesa_dir=mesaDict.get("mesa_dir"),  # type: ignore
                        mesasdk_dir=mesaDict.get("mesasdk_root"),  # type: ignore
                        mesa_caches_dir=mesaDict.get("mesa_caches_dir"),  # type: ignore
                        mesabin2dco_dir=mesaDict.get("mesabin2dco_dir"),  # type: ignore
                        **self.meshgrid[key],
                    )
                }
            )

            # load options for MESA simulations
            self.MESAmodels[key]["MESAmodel"].load_options(templateDict.get("options_filename"))  # type: ignore

            # get dictionaries for template & run namelists
            self.MESAmodels[key]["MESAmodel"].set_template_namelists()
            self.MESAmodels[key]["MESAmodel"].set_run_namelists()

    def set_MESAmodels_structure(self) -> None:
        """Method that takes care of creating the template & run directories for the meshgrid of
        stellar evolution models
        """

        logger.info("setting template and run structure for MESA runs")

        # some useful dictionaries for creating MESArun objects
        runsDict = self.config.get("Models")
        templateDict = self.config.get("Template")
        mesaDict = self.config.get("Mesa")

        # extras
        extra_template_files = []
        extra_src_folders = []
        extra_src_files = []
        extra_makefile = []

        # check for extra files and folders
        extras = templateDict.get("extras")  # type: ignore

        if not extras["extra_dir_in_src"] is None:
            if len(extras["extra_dir_in_src"]) > 0:
                extra_src_folders = extras["extra_dir_in_src"]

        if not extras["extra_files_in_src"] is None:
            if len(extras["extra_files_in_src"]) > 0:
                extra_src_files = extras["extra_files_in_src"]

        if not extras["extra_template_files"] is None:
            if len(extras["extra_template_files"]) > 0:
                extra_template_files = extras["extra_template_files"]

        if not extras["extra_makefile"] is None:
            if len(extras["extra_makefile"]) > 0:
                extra_makefile = extras["extra_makefile"]

        # if the id of the runs is `mesabin2dco`, add inlists from src code
        if runsDict.get("id") == "mesabin2dco":  # type: ignore
            extra_template_files.append(f"{mesaDict.get('mesabin2dco_dir')}/inlist_ce")  # type: ignore
            extra_template_files.append(f"{mesaDict.get('mesabin2dco_dir')}/inlist_cc")  # type: ignore

        # create template stucture of MESAruns just once
        keys = list(self.meshgrid.keys())
        key0 = keys[0]
        self.MESAmodels[key0]["MESAmodel"].create_template_structure(
            copy_default_workdir=True,
            replace=templateDict.get("overwrite"),  # type: ignore
            extra_src_folders=extra_src_folders,
            extra_src_files=extra_src_files,
            extra_makefile=extra_makefile,
            extra_template_files=extra_template_files,
        )
        self.MESAmodels[key0]["MESAmodel"].save_namelists_to_file(name_id="template")

        # also, save *.list files with the information on the columns that will be saved by MESA
        list_filenames = []
        for name in [
            mesaDict.get("history_columns_filename"),  # type: ignore
            mesaDict.get("profile_columns_filename"),  # type: ignore
            mesaDict.get("binary_history_columns_filename"),  # type: ignore
        ]:
            if name is not None and name != "":
                list_filenames.append(name)
        self.MESAmodels[key0]["MESAmodel"].copy_column_list_files(filenames=list_filenames)

        # create and store namelists into each run folder
        for key in self.meshgrid.keys():
            self.MESAmodels[key]["MESAmodel"].create_run_structure()
            self.MESAmodels[key]["MESAmodel"].save_namelists_to_file(name_id="run")

    def compile_template(self) -> None:
        """Compile template with MESA source code"""
        # compile it
        self.MESAmodels["0"]["MESAmodel"].compile_template()

    def split_MESAmodels(self) -> None:
        """Split the meshgrid of MESAmodels into smaller ones by adding a new key to the dictionary
        with the name `job_id`
        """

        logger.info("splitting MESAmodels dictionary into smaller meshgrids")

        # dictionary with manager settings
        managerDict = self.config.get("Manager")

        # split grid
        self.MESAmodels = split_grid(
            number_of_grids=managerDict.get("number_of_jobs"), Grid=self.MESAmodels  # type: ignore
        )

    def dump_MESAmodels_to_database(self) -> None:
        """Save information of MESAmodels into a database"""

        logger.info("dumping MESAmodels into database")

        # utils
        table_name = self.config["Database"].get("tablename")
        drop_table = self.config["Database"].get("drop_table")

        # drop table if exists
        if drop_table:
            self.database.drop_table(table_name=table_name)

        # first time in the loop will create database. the rest will only insert things
        create_db = True
        for key in self.MESAmodels.keys():
            # dict to insert into db, pay attention to the "status" hardcoded to be "not computed"
            table_dict = {
                "id": int(key),
                "model_name": str(self.MESAmodels[key]["MESAmodel"].run_name),
                "template_directory": str(self.MESAmodels[key]["MESAmodel"].template_directory),
                "runs_directory": str(self.MESAmodels[key]["MESAmodel"].run_root_directory),
                "job_id": int(self.MESAmodels[key]["job_id"]),
                "status": "not computed",
            }

            # create database if needed
            if create_db:
                logger.debug(f"creating table: {table_name} in database")
                self.database.create_table(table_name=table_name, table_data_dict=table_dict)
                # creation completed !
                create_db = False

            # insert row into db
            logger.debug(f"inserting database element ({key}): {table_dict}")
            self.database.insert_record(table_name=table_name, table_data_dict=table_dict)

    def create_template_job(self) -> None:
        """Create the shell script to be used to run the stellar evolution simulations"""

        logger.info(
            "creating template job that will be used to launch different runs of the meshgrid"
        )

        # some useful dictionaries for creating template job script
        mesaDict = self.config.get("Mesa")
        templateDict = self.config.get("Template")
        runsDict = self.config.get("Models")
        managerDict = self.config.get("Manager")

        # mesaJob object contains all the stuff needed to make a MESA run
        mesaJob = MESAJob(
            mesa_dir=mesaDict.get("mesa_dir"),  # type: ignore
            mesasdk_dir=mesaDict.get("mesasdk_root"),  # type: ignore
            mesa_caches_dir=mesaDict.get("mesa_caches_dir"),  # type: ignore
            is_binary_evolution=templateDict.get("is_binary_evolution"),  # type: ignore
        )

        # create command which will go into a shell script
        command = mesaJob.set_mesainit_string()
        command += mesaJob.set_mesa_env_variables_string(
            template_directory=templateDict.get("output_directory"),  # type: ignore
            runs_directory=runsDict.get("output_directory"),  # type: ignore
        )
        command += mesaJob.set_main_loop_string()

        # create manager job and write it to a file
        fname = ""
        if managerDict.get("job_file_prefix") != "":  # type: ignore
            fname += f"{managerDict.get('job_file_prefix')}"  # type: ignore
        if managerDict.get("job_filename") != "":  # type: ignore
            fname += f"{managerDict.get('job_filename')}"  # type: ignore

        # if fname is empty, exit with an error
        if fname == "":
            logger.critical(
                "both `job_file_prefix` and `job_filename` cannot be empty strings. "
                "cannot create job filename"
            )
            sys.exit(1)

        # create the script depending on the type of manager to use for the simulations
        if managerDict.get("manager") == "shell":  # type: ignore

            job = ShellJob(name=fname, command=command)
            job.write_job_to_file(fname=fname)

        elif managerDict.get("manager") == "slurm":  # type: ignore

            job = SlurmJob(  # type: ignore
                name=managerDict.get("hpc")["name"],  # type: ignore
                command=command,
                out_fname=managerDict.get("hpc")["out_fname"],  # type: ignore
                err_fname=managerDict.get("hpc")["err_fname"],  # type: ignore
                queue=managerDict.get("hpc")["queue"],  # type: ignore
                msg=managerDict.get("hpc")["msg"],  # type: ignore
                email=managerDict.get("hpc")["email"],  # type: ignore
                nodes=managerDict.get("hpc")["nodes"],  # type: ignore
                ppn=managerDict.get("hpc")["ppn"],  # type: ignore
                mem=managerDict.get("hpc")["mem"],  # type: ignore
                walltime=managerDict.get("hpc")["walltime"],  # type: ignore
            )
            job.write_job_to_file(fname=fname)

        else:
            logger.critical(
                "using a different manager than `shell` or `slurm` is not ready to be used "
                "to create a template job"
            )
            sys.exit(1)

    def create_list_of_MESAruns_for_job(self) -> None:
        """Create a txt file in which every row is a different run of the meshgrid depending on the
        `job_id`
        """

        logger.info(
            "creating txt files with the list of folders to be computed by the "
            "stellar evolutionary code depending on the job_id value"
        )

        # useful dicts
        managerDict = self.config.get("Manager")
        runsDict = self.config.get("Models")

        number_of_jobs = managerDict.get("number_of_jobs")  # type: ignore
        for k in range(number_of_jobs):
            fname = f"{runsDict.get('output_directory')}/job_{k}.folders"  # type: ignore
            logger.debug(f"going to write folders for job_id {k} in file {fname}")

            directory_list = []
            for id_number in self.MESAmodels:
                # each element in the dict has a MESAmodel object and a job_id
                mesaModel = self.MESAmodels[id_number]["MESAmodel"]
                jobId = self.MESAmodels[id_number]["job_id"]

                # just append with the proper job_id value
                if jobId == k:
                    directory_list.append(mesaModel.run_name)

            logger.debug(f"folder list for job_id {k}: {directory_list}")
            logger.debug(f"number of folders: {len(directory_list)}")

            with open(fname, "w") as f:
                for directory in directory_list:
                    f.write(f"{directory}\n")

    def submit_specific_job(self, job_id: int = 0) -> None:
        """Submit a job to a queue"""

        # check for a valid job_id number
        if job_id < 0:
            logger.critical("job_id (int) number cannot be lower than 0")
            sys.exit(1)

        # useful dicts
        managerDict = self.config.get("Manager")
        runsDict = self.config.get("Models")

        # get number of jobs
        number_of_jobs = managerDict.get("number_of_jobs")  # type: ignore

        # check that the job_id is lower than the number of jobs
        if job_id > number_of_jobs:
            logger.critical("job_id cannot be higher than the number of jobs (number_of_jobs)")
            sys.exit(1)

        # name of the file with the runs of the specific job_id
        fname = f"{runsDict.get('output_directory')}/job_{job_id}.folders"  # type: ignore

        # submit depending on the manager
        if managerDict.get("manager") == "shell":  # type: ignore
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
