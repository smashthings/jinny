#!/bin/bash

set -e

scriptDir=$(realpath $(dirname ${0}))
currDir=$(pwd)

trap "cd ${currDir}" EXIT

git tag "v$(cat "${scriptDir}/../src/jinny/version")"

git push --tags

cd "${scriptDir}/../docs"
docker compose run prod

aws s3 cp dist/index.html s3://jinny.southall.solutions --region eu-west-1