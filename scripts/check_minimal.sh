#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"${PYTHON:-python3}" -m scripts.make_vfs
sh run.sh --vfs examples/generated/minimal.zip --prompt 'minimal> ' \
    --script examples/stage3.shell
