#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"${PYTHON:-python3}" -m scripts.make_vfs
sh run.sh --vfs examples/generated/deep.zip --prompt 'deep> ' \
    --script examples/stage4.shell
