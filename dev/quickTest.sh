#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

pytest -x -v "${scriptDir}/../tests/tests.py"

python3 "${scriptDir}/../src/jinny/jinny.py" -t "${scriptDir}/../tests/test_assets/filters_template.yml" -i "${scriptDir}/../tests/test_assets/sample_values.yml" > /dev/null

if [[ $? != "1" ]]; then
  python3 "${scriptDir}/../src/jinny/jinny.py" -t "${scriptDir}/../tests/test_assets/filters_template.yml" -i "${scriptDir}/../tests/test_assets/sample_values.yml"
  printf "Failed safe check for using unsafe functions without the CLI --unsafe argument!\n\nPlease check the preceding output for why this command SUCCEEDED as it should have failed as it did not provide the --unsafe CLI argument"
  exit 1
fi

python3 "${scriptDir}/../src/jinny/jinny.py" -t "${scriptDir}/../tests/test_assets/filters_template.yml" -i "${scriptDir}/../tests/test_assets/sample_values.yml" --unsafe 1> /dev/null

if [[ $? != "0" ]]; then
  printf "The previous command should have succeeded, please check the error output"
  exit 1
fi