#!/bin/bash

set -e

scriptDir=$(realpath $(dirname ${0}))

git tag "v$(cat "${scriptDir}/../src/jinny/version")"

git push --tags