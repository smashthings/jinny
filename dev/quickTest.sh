#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

pytest "${scriptDir}/../tests/tests.py"