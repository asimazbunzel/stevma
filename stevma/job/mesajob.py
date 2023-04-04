"""Module with MESA job object"""

from typing import Union

import os
from pathlib import Path


class MESAJob:
    """Controls for MESA stellar evolution simulations needed to make runs

    Parameters
    ----------
    mesa_dir : `str / Path`
       environmental variable for the MESA_DIR

    mesasdk_dir : `str / Path`
       folder with the MESASDK

    mesa_caches_dir : `str / Path`
       folder with cache used by MESA
    """

    def __init__(
        self,
        mesa_dir: Union[str, Path] = "",
        mesasdk_dir: Union[str, Path] = "",
        mesa_caches_dir: Union[str, Path] = "",
        is_binary_evolution: bool = False,
    ) -> None:

        # check if variables are OK
        if mesa_dir == "" or mesa_dir is None:
            if os.environ.get("MESA_DIR") is None:
                raise ValueError("`MESA_DIR` is not present")

        if mesasdk_dir == "" or mesasdk_dir is None:
            if os.environ.get("MESASDK_ROOT") is None:
                raise ValueError("`MESASDK_ROOT` is not present")

        if mesa_caches_dir == "" or mesa_caches_dir is None:
            if os.environ.get("MESA_CACHES_DIR") is None:
                raise ValueError("`MESA_CACHES_DIR` is not present")

        # mesa specific folders
        if isinstance(mesa_dir, str):
            self.mesa_dir = Path(mesa_dir)
        else:
            self.mesa_dir = mesa_dir

        if isinstance(mesasdk_dir, str):
            self.mesasdk_dir = Path(mesasdk_dir)
        else:
            self.mesasdk_dir = mesasdk_dir

        if isinstance(mesa_caches_dir, str):
            self.mesa_caches_dir = Path(mesa_caches_dir)
        else:
            self.mesa_caches_dir = mesa_caches_dir

        self.is_binary_evolution = is_binary_evolution

    def set_mesainit_string(self) -> str:
        """Create string to initialize MESA inside a shell script"""

        string = "\nmesainit () {\n"
        string += f'   export MESASDK_ROOT="{self.mesasdk_dir}"\n'
        string += f'   export MESA_DIR="{self.mesa_dir}"\n'
        string += f'   export MESA_CACHES_DIR="{self.mesa_caches_dir}"\n'
        string += "   source $MESASDK_ROOT/bin/mesasdk_init.sh\n"
        string += "}\n"

        return string

    def set_mesa_env_variables_string(
        self,
        template_directory: Union[str, Path],
        runs_directory: Union[str, Path],
        set_mesa_inlist: bool = True,
    ) -> str:
        """Create string with MESA environment variables

        Parameters
        ----------
        template_directory : `str / Path`
            Location of template folder

        runs_directory : `str / Path`
            Location of runs folder

        set_mesa_inlist : `bool`
            Flag to add MESA_INLIST env variable pointing to `template_directory/inlist` file
        """

        # be sure we have a string
        template_directory = str(template_directory)
        runs_directory = str(runs_directory)

        string = f"\nexport MESA_TEMPLATE_DIR={template_directory}\n"
        string += f"export MESA_RUNS_DIR={runs_directory}\n"
        if set_mesa_inlist:
            string += f"export MESA_INLIST={template_directory}/inlist\n"

        return string

    def set_main_loop_string(self):
        """Create string with main loop of stellar evolution runs"""

        # get the name of the binary of MESA depending on the type of run
        if self.is_binary_evolution:
            binary_name = "binary"
        else:
            binary_name = "star"

        string = "\n"
        string += "mesainit\n\n"
        string += "filename=$1\n"
        string += "cd $MESA_RUNS_DIR\n"
        string += "while read line; do\n"
        string += "   dir=$line\n"
        string += "   echo going to evolve the run inside: $dir\n"
        string += "   cd $dir\n"
        string += f"   $MESA_TEMPLATE_DIR/{binary_name} | tee log\n"
        string += "   cd $MESA_RUNS_DIR\n"
        string += "done < $filename"

        return string
