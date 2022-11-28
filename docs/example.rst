=======
Example
=======

In this section we show an example of how the manager works.

This example case will create a grid of binary systems to explore with the MESAbinary module of
the MESA code.

All the options needed to replicate it can be found in the `example` folder of the source code in
GitHub, which should contain the following files

.. code-block::

   example
   ├── grid.yaml
   ├── manager_options.yaml
   └── mesa_options.yaml

The file named as `manager_options.yaml` must be sent through the command line when executing
`run-manager`,

.. code-block::

   run-manager -C example/manager_options.yaml -d

The `-d` flag will save more information to a log file as it will be run in debugging mode.

If everything goes well, at the end of the execution of the manager, there will be two new folders
in the example directory: `runs` and `templates`.


Template
~~~~~~~~

The tree structure inside the template should contain

.. code-block::

   templates
   ├── binary
   ├── binary_history_columns.list
   ├── clean
   ├── history_columns.list
   ├── inlist
   ├── inlist_project
   ├── make
   │   ├── binary_run.o
   │   ├── makefile
   │   ├── run_binary_extras.mod
   │   ├── run_binary_extras.o
   │   ├── run_binary_extras.smod
   │   ├── run_binary.mod
   │   ├── run_binary.o
   │   ├── run_star_extras.mod
   │   ├── run_star_extras.o
   │   └── run_star_extras.smod
   ├── mk
   ├── profile_columns.list
   ├── re
   ├── rn
   └── src
       ├── binary_run.f90
       ├── run_binary_extras.f90
       └── run_star_extras.f90


Runs
~~~~

As for the runs folder, will hold the following stuff

.. code-block::

   runs
   ├── hmxb_run.sh
   ├── job_0.folders
   ├── job_1.folders
   ├── m1_100.0_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_10.0_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_13.89495494_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_19.30697729_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_26.82695795_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_37.2759372_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_51.79474679_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   └── m1_71.9685673_m2_15.0_initial_period_in_days_100.0
       ├── inlist1
       ├── inlist2
       └── inlist_binary

The file named `hmxb_run.sh` is the shell script that will send the simulations to be computed
either to a another shell terminal emulator or to a submission queue manager, depending on the
options specified in the YAML with the manager commands.

Files ending in `*.folders` contain a list of the folders where simulations will be computed.

The rest of the folders are the different binaries to be explored in the grid, each of them
containing MESA inlist files with their different options as specified in the `mesa_options.yaml`
file.

Run the scripts
~~~~~~~~~~~~~~~

To start computing the evolution of the binaries in the grid, simply run the `*.sh` scripts:

.. code-block::

   ./hmxb_run.sh job_0.folders &
   ./hmxb_run.sh job_1.folders &

The `&` is used to send the files to the background, but you can also create screen or tmux
sesssion and have complete control of the terminals through them.
