#!/usr/bin/env bash
# 上传前自检：字体覆盖、标签结构、图片宽高比、链接、孤儿文件、中英一致性
#   ./check.sh
# 有问题会列出来并非零退出。
exec py "$(dirname "$0")/check.py" "$@"
