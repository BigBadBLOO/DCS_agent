#!/bin/sh
prefix="/usr/share/ckd-agent"
script="$prefix/Agent.py"
path_to_config="$prefix/config/default.config"

python3 $script $path_to_config &
