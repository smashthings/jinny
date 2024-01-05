#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

python3 "${scriptDir}/../src/jinny/jinny.py" $@