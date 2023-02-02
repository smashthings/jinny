#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

for f in "${scriptDir}/../tests/interactive_tests/"*.sh; do
  printf "Running ${f}...\n"
  bash $f
  if [[ $? != "0" ]]; then
    printf "Failed to run test, exiting!\n"
    exit 1
  fi
done

