=======
Example
=======

In this section we show an example of how the manager works.

This example case will create a grid of binary systems to explore with the MESAbinary module of
the MESA code.

All the options needed to replicate it can be found in the ``example`` directory of the source code
in GitHub (see `example-grid <https://github.com/asimazbunzel/stevma/tree/main/example>`_).

This directory contains the following files:

.. code-block::

   example
   ├── grid.yaml
   ├── manager_options.yaml
   └── mesa_options.yaml

The file named as ``manager_options.yaml`` must be passed through the command line when executing
``run-manager``:

.. code-block::

   run-manager -C example/manager_options.yaml -d

The ``-d`` flag will save more information to a log file as it will be executed in debugging mode
(for more command-line options, see :ref: `usage:Usage from the command line`). To access to the
log filename, first run the manager with the ``--show-log-name`` option.

If everything goes well, at the end of the execution of the manager, there will be two new
directories in the example directory: ``runs`` and ``templates``.

In case something goes wrong, the log file will have more information to help debug the error.

Template
~~~~~~~~

On the one hand, the tree structure inside the template should contain

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

On the other hand, the runs directory will have the following stuff

.. code-block::

   runs
   ├── example_run.sh
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
   ├── m1_13.89_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_19.3_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_26.82_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_37.27_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   ├── m1_51.79_m2_15.0_initial_period_in_days_100.0
   │   ├── inlist1
   │   ├── inlist2
   │   └── inlist_binary
   └── m1_71.96_m2_15.0_initial_period_in_days_100.0
       ├── inlist1
       ├── inlist2
       └── inlist_binary

The file named ``example_run.sh`` is the shell script that will handle the launch of all the
simulations in the grid. The script can be managed by the shell itself or by a queue manager. This
is controlled by the option ``manager`` in the ``manager`` section (see file
``example/manager_options.yaml``). The available options are: ``shell`` or ``slurm``.

Files with the ``*.folders`` suffix contain a list of the directories where simulations will be
computed.

The rest of the directories found inside ``runs`` corresponds to the different binaries to be
explored in the grid, each of them containing MESA inlist files with their different options as
specified in the ``mesa_options.yaml`` file.

Database
~~~~~~~~

On top of all this, a file with the database will be created. It will contain the following
table:

.. list-table: MESAruns
   :widths: 5 45 20 20 5 5
   :header-rows: 1

   * - id
     - run_name
     - template_directory
     - runs_directory
     - job_id
     - status
   * - 0
     - m1_10.0_m2_15.0_initial_period_in_days_100.0
     - example/templates
     - example/runs
     - 0
     - not computed
   * - 1
     - m1_13.89_m2_15.0_initial_period_in_days_100.0
     - example/templates
     - example/runs
     - 0
     - not computed

The complete table should have 8 elements and can be loaded using the ``sqlite3`` command-line
program,

.. code-block::

   $ cd example
   $ sqlite3
   sqlite> ATTACH DATABASE "example-grid.db" as example;
   sqlite> .header on
   sqlite> .mode column --wrap 50
   sqlite> SELECT * FROM MESAruns;


Run the scripts
~~~~~~~~~~~~~~~

To start computing the evolution of the binaries in the grid, simply run the ``*.sh`` scripts:

.. code-block::

   ./hmxb_run.sh job_0.folders &
   ./hmxb_run.sh job_1.folders &

The ``&`` is used to send the files to the background, but you can also create screen or tmux
sesssion and have complete control of the terminals through them.
