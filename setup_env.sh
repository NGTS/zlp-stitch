#!/usr/bin/env bash
set -e

main() {
    test -d "$(dirname $0)/venv" || error "Cannot find virtual environment, please create"
    PYTHON="$(dirname $0)/venv/bin/python" 
    test -x "${PYTHON}" || error "Cannot find python, please create virtual environment"
    CONDA="$(dirname $0)/venv/bin/conda" 
    test -x "${CONDA}" || error "Cannot find conda, please create virtual environment"
    PIP="$(dirname $0)/venv/bin/pip" 
    test -x "${PIP}" || error "Cannot find pip, please create virtual environment"

    ${CONDA} install astropy numpy
    ${PIP} install fitsio joblib

}

main
