#!/usr/bin/env bash

set -e

BASE_DIR=`pwd`
NAME=$(basename $BASE_DIR)
if [[ "$NAME" != "pyte-prism" ]];then
    echo "must run this in project root"
    exit 1
fi

## Requirements
## poetry config http-basic.pypi username password
## poetry config http-basic.testpypi username password
ENVIRONMENT=${1:-testpypi}
poetry publish -v -r ${ENVIRONMENT} --build
