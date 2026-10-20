#!/bin/sh
# Opens the class planner in your browser (same as: python3 -m planner). Linux and macOS.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    exec python3 -m planner "$@"
fi
exec python -m planner "$@"
