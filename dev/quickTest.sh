#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

pytest -x -v "${scriptDir}/../tests/tests.py"