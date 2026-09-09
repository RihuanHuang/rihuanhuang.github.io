#!/usr/bin/env bash
# 从 src/ 拼装 docs/ 的六个页面
#   ./build.sh          生成
#   ./build.sh --diff   只对比不写盘
exec py "$(dirname "$0")/build.py" "$@"
