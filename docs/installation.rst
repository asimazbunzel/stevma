============
Installation
============

Cloning STEVMA
--------------

First, clone the repository in your computer:

.. code-block::

   git clone https://github.com/asimazbunzel/stevma.git

or

.. code-block::

   git clone git@github.com:asimazbunzel/stevma.git

depending if you have git set up or you are using an SSH key.

Installing STEVMA
-----------------

Once the repository is cloned in a local directory, `cd` into this new directory and
run the following code

.. code-block::

   pip install .

This will create the executable `run-manager` that will handle the creation of the
grid.

.. note::

   USE A CONDA ENVIRONMENT

   The usage of a conda environment is strongly recommended as it will automatically
   handle the different versions of the libraries needed by the code to work
