=====
Usage
=====

To use the STEVMA code, an executable called `run-manager` is created after installation.

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

The option `-C` (or `--config-file`) contains all the options that are needed to produce
a grid of MESA simulations.

An example file with all the available options is listed below.

.. code-block:: yaml

   # Config options for stellar evolution manager

   # database options
   database:
     # name of the database file
     filename: "hmxb.db"

   # configuration for MESA runs
   runs:
     # an id for the type of run. Available options are: `mesastar`, `mesabinary` and `mesabin2dco`
     # `mesastar` is used to evolve isolated stars
     # `mesabinary` models binaries using the standard MESAbinary module
     # `mesabin2dco` uses the modified mesabinary which includes common-envelope and core-collapse
     id: "mesabinary"

     # name of the file with the grid to be explored. This file must be in YAML format and valid
     # names of MESA options
     meshgrid_filename: "example/grid.yaml"

     # directory where runs will be stored
     output_directory: "example/runs"

     # whether to add the condition to avoid re-doing a simulation that has already been created in
     # the `output_directory`
     overwrite: false

     # include a call to a natal-kick exploration
     do_kicks: false

     # if `do_kicks` is true, this is the file with the kick information.
     # TODO: better explain how it works
     filename_kick_script:

   # Options for the MESA template part of the code. This template contains all the options that
   # are common to every simulation as well as the MESA executable and extra source codes
   template:
     # flag to control the type of MESA simulation between the isolated or binary cases
     is_binary_evolution: true

     # YAML file with the options that are common to each simulation. It must contain valid MESA
     # options
     options_filename: "example/mesa_options.yaml"

     # folder where MESA source code will be located
     output_directory: "example/templates"

     # whether to overwrite the creation of a template in a location which already has a template
     overwrite: true

     # extras folders and files to include in the template
     extras:
       extra_dir_in_src:
       extra_files_in_src:
       extra_template_files:
       extra_makefile:

   # MESA options
   mesa:
     # location of the MESA installation
     mesa_dir: "/home/asimazbunzel/Developments/mesa-r15140"

     # location of the software development kit of MESA
     mesasdk_root: "/home/asimazbunzel/Developments/mesasdk-20.12.1"

     # location of the caches folder of MESA
     mesa_caches_dir: "/home/asimazbunzel/.cache/mesa-r15140"

     # location of your local copy of the mesabin2dco custom MESA build
     # (only needed if `id: "mesabin2dco"`)
     mesabin2dco_dir: "/home/asimazbunzel/Developments/mesabin2dco"

     # files with the name of the columns to be saved by MESA
     history_columns_filename:
     profile_columns_filename:
     binary_history_columns_filename:

   # options for the manager of simulations
   manager:
     # identifier of the manager. options are: "shell", "slurm"
     manager: "slurm"

     # prefix to prepend to job filename(s)
     job_file_prefix: "example/runs/hmxb_"
     job_filename: "run.sh"

     # hpc options are only used if manager is "slurm"
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

     # options to use for the entire mesh of models:
     # number of jobs to divide the mesh
     number_of_jobs: 50
     # how many cpu cores will be using for each simulation
     number_of_cores: 12
     # how many jobs will be sent to compute in parallel (only used if `manager: "slurm`)
     number_of_parallel_jobs: 10

About the MESA options
----------------------

- meshgrid file
~~~~~~~~~~~~~~~

The option `meshgrid_filename` should point to a YAML formated file with the different parameters
that will change between simulations of the grid. The available options are the different controls
of the MESA code: `star_job`, `controls`, `binary_job` and `binary_controls`. Inside each of them,
parameters can be set as coming from the `defaults` folder of the MESA code.

For example, a valid file with a grid simulation would be:

.. code-block:: yaml

   binary_controls:

     m1: [ 10.        ,  13.89495494,  19.30697729,  26.82695795,
           37.2759372 ,  51.79474679,  71.9685673 , 100.        ]

     m2: 15

     initial_period_in_days: 100

This file will produce 8 different simulations in the 3D grid (m1, m2, initial_period_in_days)
space. One for each possible combination of all these parameters.


- options file
~~~~~~~~~~~~~~~

In the case of the `options_filename` the situation is similar. Only valid controls from MESA are
allowed. In this file the only thing to be careful about comes from the options connected to a
custom `mesabin2dco` type of simulation. In the case the following lines **must** be included:

.. code-block::

   bin2dco_controls:

     star_plus_pm_filename: " #{template}/inlist_project"

     cc2_inlist_filename: "#{template}/inlist_cc"
     ce2_inlist_filename: "#{template}/inlist_ce"

The rest of the file should contain parameters that do not change between simulations.

For example, assuming a fixed wind prescription would imply adding:

.. code-block::

   controls:
     cool_wind_full_on_T: 0.8d4
     hot_wind_full_on_T: 1.2d4
     cool_wind_RGB_scheme: "Dutch"
     cool_wind_AGB_scheme: "Dutch"
     hot_wind_scheme: "Dutch"
     Dutch_wind_lowT_scheme: "de Jager"
     Dutch_scaling_factor: 0.4d0
