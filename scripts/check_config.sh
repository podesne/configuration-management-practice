#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh run.sh --vfs examples/sample.zip --prompt 'config> ' \
    --script examples/stage2.shell
