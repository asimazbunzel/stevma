SHELL=bash
CONDA_ROOT=${HOME}/.local/bin/conda

install:
	source ${CONDA_ROOT}/bin/activate && conda activate bin2dco-3.9 && pip3 install .

test:
	source ${CONDA_ROOT}/bin/activate && conda activate bin2dco-3.9 && mesh-manager -d -C test/manager_options.yaml
