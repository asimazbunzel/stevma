"""Module with Slurm job object"""

from typing import Union

import os
import subprocess
from pathlib import Path


class SlurmJob:
    """Slurm job to handle grid of stellar evolution simulations"""

    def __init__(
        self,
        name: str = "",
        command: str = "",
        out_fname: str = "/dev/null",
        err_fname: str = "/dev/null",
        queue: str = "furious",
        msg: str = "ALL",
        email="",
        nodes: int = 1,
        ppn: int = 8,
        mem: int = 8,
        walltime: str = "168:00:00",
    ) -> None:

        self.name = name

        # this holds the actual script to compute the grid
        self.command = command

        # output filename
        self.out_fname = out_fname
        if self.out_fname == "" or self.out_fname is None:
            self.out_fname = "/dev/null"

        # error filename
        self.err_fname = err_fname
        if self.err_fname == "" or self.err_fname is None:
            self.err_fname = self.out_fname

        # queue string
        self.queue = queue
        if self.queue is None:
            raise ValueError("Slurm job requires type of queue")

        self.msg = msg
        if self.msg == "" or self.msg is None:
            self.msg = "bea"

        # user mail
        self.email = email
        if self.email == "" or self.email is None:
            raise ValueError("Slurm job requires email")

        # number of nodes to use
        self.nodes = int(nodes)
        if self.nodes < 1 or self.nodes is None:
            raise ValueError("Slurm job requires nodes to be an integer >= 1")

        # processors per node
        self.ppn = int(ppn)
        if self.ppn < 1 or self.ppn is None:
            raise ValueError("Slurm job requires ppn to be an integer >= 1")

        # memory requested
        self.mem = int(mem)
        if self.mem < 1 or self.mem is None:
            raise ValueError("Slurm job requires mem to be an integer > 1 (in Gb)")

        # walltime for job (max is 168:00:00)
        self.walltime = walltime
        if self.walltime == "" or self.walltime is None:
            self.walltime = "168:00:00"

    def set_shell_config(self) -> str:
        """Configuraton stuff for the shell"""

        string = "#!/bin/sh\n"
        string += "\n"
        string += f"# shell script name: {self.name}"

        return string

    def set_slurm_config(self) -> str:
        """Configuration options of the Slurm job"""
        string = "#SBATCH -S /bin/bash\n"
        string += f"#SBATCH --job-name={self.name}\n"
        string += f"#SBATCH --out={self.out_fname}\n"
        string += f"#SBATCH --partition {self.queue}\n"
        string += f"#SBATCH --mail-type={self.msg}\n"
        string += f"#SBATCH --mail-user={self.email}\n"
        string += f"#SBATCH --time={self.walltime}\n"
        string += f"#SBATCH --nodes={self.nodes} --cpus-per-task={self.ppn}\n"
        string += f"#SBATCH --mem={self.mem}gb\n"
        string += '\nexport SCRATCH="/scratch/$USER.$PBS_JOBID"\n'
        return string

    def write_job_to_file(self, fname: str = "") -> None:
        """Write job to a file

        Parameters
        ----------
        fname : `string`
            Filename for the Slurm job
        """

        msg = self.set_shell_config()
        msg += "\n\n"
        msg += self.set_slurm_config()
        msg += "\n"
        msg += self.command

        with open(fname, "w") as f:
            f.write(msg)

    def submit(self, fname: str = "", root_dir: str = ""):
        """Submit Slurm job to queue

        Parameters
        ----------
        fname : `string`
           Filename of the PBS job.
        """
        try:
            p = subprocess.Popen(
                f"chmod +x {fname}; ./{fname}",
                shell=True,
                executable="/bin/sh",
                cwd=root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, stderr = p.communicate()
            if stderr is not None:
                print(f"WARNING: could not run shell job: {stderr}")
        except Exception as e:
            print(e)
