#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sh run.sh --vfs 'path with spaces/sample.zip' --prompt '' \
    --script examples/stage2.shell
if sh run.sh --vfs examples/sample.zip --prompt 'error> ' \
    --script examples/missing.shell; then
    echo 'Ожидалась ошибка чтения скрипта' >&2
    exit 1
fi
