#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"${PYTHON:-python3}" -m scripts.make_vfs
sh run.sh --vfs examples/generated/several.zip --prompt 'several> ' \
    --script examples/stage3.shell
