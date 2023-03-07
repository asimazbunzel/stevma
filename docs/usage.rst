=====
Usage
=====

To use the STEVMA code, an executable called ``run-manager`` is created after installation.

It is accompanied by some command-line options as detailed here:

- **-h, --help**           - show this help message and exit
- **-d, --debug**          - enable debug mode (default: False).
- **-C CONFIG_FNAME, --config-file CONFIG_FNAME** - name of configuration file (default: None).
- **--show-log-name**      - display log filename and exit (default: False).
- **--show-database-name** - display database filename and exit (default: False).
- **--list-grid**          - display grid list and exit (default: False).
- **-v, --visualize**      - enable visualization of grid using matplotlib (default: False). (EXPERIMENTAL: NOT READY TO USE)

Configuration file
------------------

The option ``-C`` (or ``--config-file``) contains all the options that are needed to produce
a grid of MESA simulations.

An example file with all the available options is listed below.

.. code-block:: yaml
   :linenos:

   # ---
   # Config options for stellar evolution manager
   # ---

   # Database options
   database:
     # *name: file & table names (sqlite-type database)
     filename: "example/example-grid.db"
     tablename: "MESAruns"

     # remove_database: flag to delete database file
     remove_database: true

     # drop_table: flag to remove tablename from database
     drop_table: true

   # Specific options for runs of MESA
   runs:
     # id: identifier of the type of MESA simulation. Available values: `mesastar`, `mesabinary`
     id: "mesabinary"

     # meshgrid_filename: name of file with meshgrid options
     meshgrid_filename: "example/grid.yaml"

     # output_directory: directory where MESA namelists and directories will be saved
     output_directory: "example/runs"

     # overwrite: flag to replace directories and files in `output_directory`
     overwrite: false

     # do_kicks: flag to add option for natal-kick exploration. NOT TESTED YET
     do_kicks: false

     # filename_kick_script: file with script to apply a distribution of natal-kicks to a binary
     #                       system
     filename_kick_script:

   # Specific options for template of MESA
   template:
     # is_binary_evolution: flag to set the type of evolution: isolated or binary
     is_binary_evolution: true

     # options_filename: MESA specific options shared by all stars in the grid
     options_filename: "example/mesa_options.yaml"

     # output_directory: directory where template files and MESA source code will be saved
     output_directory: "example/templates"

     # overwrite: flag to replace template files
     overwrite: true

     # extras:
     #   extra_*: files to append to template directory
     extras:
       extra_dir_in_src:
       extra_files_in_src:
       extra_template_files:
       extra_makefile:

   # MESA options
   mesa:
     # mesa*: environment variables needed by the MESA code
     mesa_dir: "/home/asimazbunzel/Developments/mesa-r15140"
     mesasdk_root: "/home/asimazbunzel/Developments/mesasdk-20.12.1"
     mesa_caches_dir: "/home/asimazbunzel/.cache/mesa-r15140"

     # mesabin2dco_dir: if using custom MESAbin2dco, set path to directory
     mesabin2dco_dir: "/home/asimazbunzel/Developments/mesabin2dco"

     # *_columns_filename: files with the name of the columns to be saved as output of each simulation
     #                     in the grid by MESA
     history_columns_filename:
     profile_columns_filename:
     binary_history_columns_filename:

   # Options for the manager which launches the simulations
   manager:
     # identifier of the manager. Options are: "shell", "slurm"
     manager: "shell"

     # job_*: prefix to prepend to job filename(s)
     job_file_prefix: "example/runs/example_"
     job_filename: "run.sh"

     # hpc: these options are only used if manager is either "pbs" or "slurm"
     hpc:
       name: "example_slurm"
       email: "asimazbunzel@iar.unlp.edu.ar"
       out_fname:
       err_fname:
       queue: "bigmem"
       msg: "all"
       nodes: 1
       ppn: 12
       mem: 8
       walltime: "168:00:00"

     # number_of_jobs: number of jobs to divide the mesh
     number_of_jobs: 2

     # number_of_cores: how many cpu cores will be using for each simulation
     number_of_cores: 12

     # number_of_parallel_jobs: how many jobs will be sent to compute in parallel
     number_of_parallel_jobs: 10


About the database options
--------------------------

When creating a grid of simulations, it is better to keep track of them. For that, the code creates
a file containing all this information using `SQLite <https://www.sqlite.org/index.html>`_ (an SQL
database engine). This database stores a table with all the names of the runs in the grid as well
as the directory of the MESA template and runs. In addition, it also contains some identifiers for
each of the runs and for the jobs into which the grid is split, and a *status* which is set, for
now, to be the same for each run: *not computed*.

The database is intended to be used in combination with the
`stevdb <https://github.com/asimazbunzel/stevdb>`_ code, an stellar-evolution database manager,
which appends more tables to the database to have a complete summary of each simulation in the grid
going through different stages during the evolution of the star and/or binary.

For more information on the structure of the table in the database see
:ref: `example:Database table`


About the MESA options
----------------------

meshgrid file
~~~~~~~~~~~~~

The option ``meshgrid_filename`` should point to a YAML formatted file with the different
parameters that will change between simulations of the grid. The available options for these
parameters are defined by the different controls in the MESA code: ``star_job``, ``controls``,
``binary_job`` and ``binary_controls``. Inside each of them, parameters can be set as coming from
the ``defaults`` folder of the MESA code.

For example, a file containing the following options:

.. code-block:: yaml

   binary_controls:

     m1: [ 10.  ,  13.89,  19.30,  26.82,
           37.27,  51.79,  71.96, 100.  ]

     m2: 15

     initial_period_in_days: 100

would produce 8 different simulations in the 3D (m1, m2, initial_period_in_days)-space. One for
each possible combination of all these parameters.


options file
~~~~~~~~~~~~

In the case of the ``options_filename`` the situation is similar. Only valid controls from MESA are
allowed. Controls found inside this file will ont change between different simulations. If a MESA
control is not found in here, the default value is assumed (as found in the ``defaults`` directory
inside the MESA code).

.. warning::
   There will exist an option for the ``id`` control in the ``runs`` section which will be used to
   produce a grid of simulations using the ``mesabin2dco`` custom-made code (see
   `MESAbin2dco <https://github.com/asimazbunzel/mesabin2dco>`_). In this case the following lines
   **must** be included:

   .. code-block::

      bin2dco_controls:

        star_plus_pm_filename: " #{template}/inlist_project"

        cc2_inlist_filename: "#{template}/inlist_cc"
        ce2_inlist_filename: "#{template}/inlist_ce"

   The tag seen in the example above, `#{template}` is used by the manager to replace that string
   with the actual path to the template directory.

.. note::
   This same syntax of tagging the template directory with `#{template}` should also be
   used in case the `history_columns_filename`, `profile_columns_filename` and/or
   `binary_history_columns_filename` are set in the config-file. In this case, the
   `options_filename` should include lines with
   `binary_history_columns_file: "#{template}/binary_history_columns.list"`,
   `history_columns_file: "#{template}/history_columns.list"` and/or
   `profile_columns_file: "#{template}/profile_columns.list"` in the corresponding `binary_job`
   and/or `star_job` sections.

Example: a fixed wind prescription according to the `Dutch` scheme defined in MESA, with the custom
column names defined in a file called `history_columns.list` would imply adding the following
options:

.. code-block::

   star_job:
     history_columns_file: "#{template}/history_columns.list"

   controls:
     cool_wind_full_on_T: 0.8d4
     hot_wind_full_on_T: 1.2d4
     cool_wind_RGB_scheme: "Dutch"
     cool_wind_AGB_scheme: "Dutch"
     hot_wind_scheme: "Dutch"
     Dutch_wind_lowT_scheme: "de Jager"
     Dutch_scaling_factor: 0.4d0
