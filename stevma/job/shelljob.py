"""Module with shell job object"""

import subprocess


class ShellJob:
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
        string += "# This script was created by the STEVMA module\n"
        string += "# to manually run the grid of stellar evolution\n"
        string += "# models, give executable permissions to the script\n"
        string += "# and then submit the desired models found in the\n"
        string += "# different *.folders files using the shell script\n"
        string += f"# with name: {self.name}\n"
        string += f"# e.g.: `$ {self.name} job_0.folders`\n"

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

    def submit(self, fname: str = "", root_dir: str = "") -> None:
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
                print(f"WARNING: could not run shell job: {str(stderr)}")
        except Exception as e:
            print(e)
