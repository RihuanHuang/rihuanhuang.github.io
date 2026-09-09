#!/usr/bin/env bash
# 中文字体子集：重切 / 自检
#   ./subset-fonts.sh           重切子集并更新 site.css 里的引用
#   ./subset-fonts.sh --check   只核对不重切，缺字就报错退出（上传前跑这个）
exec py "$(dirname "$0")/subset-fonts.py" "$@"
