#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

pytest -x "${scriptDir}/../tests/tests.py"