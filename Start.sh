#!/bin/bash

# -
# | BareBooru
# | Minimalistic and flexible media tagging tool
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

ScriptPath=$(realpath $0)
ScriptDir=$(dirname $ScriptPath)
cd $ScriptDir

mkdir -p Data/Files/ Data/Cache/ 2>/dev/null

python3 ./Run/BareBooru.py