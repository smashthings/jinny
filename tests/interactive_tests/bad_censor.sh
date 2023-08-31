#!/bin/bash

scriptDir=$(realpath $(dirname ${0}))

printf "===== RUNNING ${0} 1 =====\n"
python3 "${scriptDir}/../../src/jinny/jinny.py" -t "${scriptDir}/bad_censor_1.txt" || printf "\n\nGot the expected failure!\n"

printf "===== RUNNING ${0} 2 =====\n"
python3 "${scriptDir}/../../src/jinny/jinny.py" -t "${scriptDir}/bad_censor_2.txt" || printf "\n\nGot the expected failure!\n"

printf "===== RUNNING ${0} 3 =====\n"
python3 "${scriptDir}/../../src/jinny/jinny.py" -t "${scriptDir}/bad_censor_3.txt" && printf "\n\nGot the expected success!\n"

exit 0