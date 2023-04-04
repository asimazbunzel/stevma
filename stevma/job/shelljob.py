"""Module with shell job object"""

from pathlib import Path
import subprocess
from typing import Union
import os


class ShellJob(object):
    """Shell job to handle grid of stellar evolution simulations"""

    def __init__(
        self,
        name: str = "",
        command: str = "",
    ) -> None:

        self.name = name
        self.command = command

    def set_shell_config(self):
        """Configuration for shell job"""

        string = "#!/bin/sh\n"
        string += "\n"
        string += f"# shell script name: {self.name}"

        return string

    def write_job_to_file(self, fname: str = "") -> None:
        """Write job to a file

        Parameters
        ----------
        fname : `string`
           Filename for the shell job.
        """

        msg = self.set_shell_config()
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
