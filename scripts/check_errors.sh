#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
"${PYTHON:-python3}" -m scripts.make_vfs
sh run.sh --vfs examples/generated/minimal.zip --prompt '' \
    --script examples/stage3.shell
if sh run.sh --vfs examples/generated/deep.zip --prompt 'error> ' \
    --script examples/missing.shell; then
    echo 'Ожидалась ошибка чтения скрипта' >&2
    exit 1
fi
if sh run.sh --vfs examples/missing.zip --prompt 'error> ' \
    --script examples/stage3.shell; then
    echo 'Ожидалась ошибка загрузки VFS' >&2
    exit 1
fi
