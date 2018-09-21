#!/bin/bash

export MOOSE_SETTINGS_MODULE=tests.settings
echo $@
py.test -vv $@
