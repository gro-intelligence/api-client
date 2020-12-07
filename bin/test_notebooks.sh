#!/bin/bash

set -e -u -o pipefail

# This script tests/validates our sample Jupyter notebooks. The goals are:
# - ensure our sample notebooks work correctly.
# - integration testing for our groclient library.
#
# Currently, this script only tests a subset of notebooks due to some issues
# (e.g. problems with the notebooks, library issues, etc). Also, only some of
# the tested notebooks have their stored outputs validated: "lax" validation
# just checks that the notebook executes without errors, whereas "strict"
# validation checks that each code cell's output matches the stored output.
# Some notebooks always query the latest data, making strict checking
# infeasible.

# untested notebooks:
# - analogous_years/get_started_with_analogous_years.ipynb: numpy shape issue
# - crop_models/Sao_Paulo_brazil_sugar_content_modeling.ipynb: hm, out of order execution?
# - crop_models/brazil_soybeans.ipynb: requires gdal stuff
# - crop_models/ethiopia_cereals.ipynb: slow
# - crop_models/kenya_cereals.ipynb: slow
# - prevented_plant/prevented_plant_models.ipynb: Shapely requires geos_c library
# - similar_regions/example.ipynb: geopandas requires gdal stuff

# base directory containing notebooks
NOTEBOOKS_BASEDIR=api/client/samples
TMP_VENV='' # most recently created venv directory

# creates and activates new virtualenv, installs requirements, installs pytest
# and nbval. the new virtualenv path is stored in $TMP_VENV.
function setup_venv {
  local reqs_file="$1"
  TMP_VENV=$(mktemp -d venv_test_notebooks.XXX)

  python3 -m venv "$TMP_VENV"
  source "$TMP_VENV/bin/activate"
  echo "--> installing dependencies into tmp venv $TMP_VENV..."
  pip install -q -U pip wheel
  if [ -f "$reqs_file" ]; then
    pip install -q -r "$reqs_file"
  else
    echo "note: requirements file not found ($reqs_file), skipping"
  fi
  pip install -q groclient pytest nbval
}

# deactivates and deletes given virtualenv.
function cleanup_venv {
  deactivate
  rm -rf "$TMP_VENV"
}

# cleanup function for unanticipated early exits.
function cleanup_trap {
  if [ -d "$TMP_VENV" ]; then
    echo "cleaning up last venv: $TMP_VENV"
    rm -rf "$TMP_VENV"
  fi
}

trap cleanup_trap EXIT

function nbval {
  echo -e "\n\n\n-> validating notebook $2 w/ strictness '$1'..."
  local strictness="$1"
  local nb_file="${NOTEBOOKS_BASEDIR}/${2}"

  # uses requirements.txt that's next to the notebook file
  local nb_basedir=$(dirname "$nb_file")
  local reqs_file="${nb_basedir}/requirements.txt"
  local nbval_flag
  case "$strictness" in
    "strict") nbval_flag="--nbval";;
    "lax")    nbval_flag="--nbval-lax";;
    *) echo "nbval argument must be 'strict' or 'lax', not '$strictness'"; exit 1;;
  esac

  echo "--> creating venv..."
  setup_venv "$reqs_file"  # new venv path is stored in $TMP_VENV
  echo "--> running nbval..."
  pytest "$nbval_flag" "$nb_file"
  echo "--> cleaning up venv..."
  cleanup_venv
  echo "-> notebook $2 done"
}


# Fail if GROAPI_TOKEN isn't set properly. The 1st conditional uses parameter
# expansion because otherwise the script fails due to set -u.
if [ -z "${GROAPI_TOKEN+dummyval}" ] || [ "$GROAPI_TOKEN" == "dummytoken" ]; then
  echo "Error: the environment variable \$GROAPI_TOKEN must be set to a working token to test notebooks."
  exit 1
fi

nbval strict at-time-query-examples.ipynb
nbval strict analysis_kits/stocks_to_use_price_model/stocks_to_use_price_model.ipynb
nbval lax anomaly_detection/sample_anomaly_detection.ipynb
nbval lax "drought/El Niño, La Niña and Droughts in East Africa.ipynb"
