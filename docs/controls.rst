========
Controls
========

All the available options passed through the ``--config-file`` command line are listed here.

This options must be saved in a YAML-styled file as shown in the :ref: `example:Example`

database
--------

Options related to database.

filename
~~~~~~~~

Name of the database file (SQLite-type)

.. code-block:: yaml

   filename: "example/example-grid.db"

tablename
~~~~~~~~~

Name of the table holding the information of the grid inside the database

.. code-block:: yaml

   tablename: "MESAruns"

remove_database
~~~~~~~~~~~~~~~

Flag to delete database file

.. code-block:: yaml

   remove_database: true

drop_table
~~~~~~~~~~

Flag to remove tablename from database

.. code-block:: yaml

  drop_table: true

runs
----

Specific options for runs of MESA

id
~~

Identifier of the type of MESA simulation. Available values: ``mesastar``, ``mesabinary``

.. code-block:: yaml

  id: "mesabinary"

meshgrid_filename
~~~~~~~~~~~~~~~~~

Name of file with meshgrid options

.. code-block:: yaml

   meshgrid_filename: "example/grid.yaml"

output_directory
~~~~~~~~~~~~~~~~

Directory where MESA namelists and directories will be saved

.. code-block:: yaml

   output_directory: "example/runs"

overwrite
~~~~~~~~~

Flag to replace directories and files in ``output_directory``

.. code-block:: yaml

   overwrite: false

do_kicks
~~~~~~~~

Flag to add option for natal-kick exploration. NOT TESTED YET

.. code-block:: yaml

   do_kicks: false

filename_kick_script
~~~~~~~~~~~~~~~~~~~~

File with script to apply a distribution of natal-kicks to a binary system. NOT TESTED YET

.. code-block:: yaml

   filename_kick_script:

template
--------

Specific options for template of MESA

is_binary_evolution
~~~~~~~~~~~~~~~~~~~

Flag to set the type of evolution: isolated or binary

.. code-block:: yaml

  is_binary_evolution: true

options_filename
~~~~~~~~~~~~~~~~

MESA specific options shared by all stars in the grid

.. code-block:: yaml

  options_filename: "example/mesa_options.yaml"

output_directory
~~~~~~~~~~~~~~~~

Directory where template files and MESA source code will be saved


.. code-block:: yaml

  output_directory: "example/templates"

overwrite
~~~~~~~~~

Flag to replace template files

.. code-block:: yaml

  overwrite: true

extras
~~~~~~

Directories and files to append to template directory (``template > output_directory``), inside:
``src`` and/or ``make``. It even allows to replace the ``makefile`` inside the ``make`` directory
for a custom one.

.. code-block:: yaml

   extras:
     extra_dir_in_src:
     extra_files_in_src:
     extra_template_files:
     extra_makefile:

mesa
----

MESA options

mesa_dir, mesasdk_root, mesa_caches_dir
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Environment variables needed by the MESA code

.. code-block:: yaml

  mesa_dir: "/home/asimazbunzel/Developments/mesa-r15140"
  mesasdk_root: "/home/asimazbunzel/Developments/mesasdk-20.12.1"
  mesa_caches_dir: "/home/asimazbunzel/.cache/mesa-r15140"

mesabin2dco_dir
~~~~~~~~~~~~~~~

If using custom MESAbin2dco, set path to directory (NOT READY TO USE)

.. code-block:: yaml

  mesabin2dco_dir: "/home/asimazbunzel/Developments/mesabin2dco"

history_columns_filename, profile_columns_filename, binary_history_columns_filename
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Files with the name of the columns to be saved as output of each simulation in the grid by MESA

.. code-block:: yaml

  history_columns_filename:
  profile_columns_filename:
  binary_history_columns_filename:

manager
-------

Options for the manager which launches the simulations

manager
~~~~~~~

Identifier of the manager. Options are: "shell", "slurm"

.. code-block:: yaml

  manager: "shell"

job_file_prefix, job_filename
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prefix to prepend to job filename(s)

.. code-block:: yaml

  job_file_prefix: "example/runs/example_"
  job_filename: "run.sh"

hpc
~~~

These options are only used if manager is either "pbs" or "slurm". All are valid settings from the
Slurm queue manager

.. code-block:: yaml

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

number_of_jobs
~~~~~~~~~~~~~~

Number of jobs to divide the mesh

.. code-block:: yaml

  number_of_jobs: 2

number_of_cores
~~~~~~~~~~~~~~~

How many cpu cores will be using for each simulation

.. code-block:: yaml

  number_of_cores: 12

number_of_parallel_jobs
~~~~~~~~~~~~~~~~~~~~~~~

How many jobs will be sent to compute in parallel

.. code-block:: yaml

  number_of_parallel_jobs: 10
