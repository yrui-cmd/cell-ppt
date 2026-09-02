#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "$0")" && pwd)"
python_bin="${PYTHON:-}"
if [[ -z "$python_bin" ]]; then
  if command -v python3 >/dev/null 2>&1; then python_bin="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then python_bin="$(command -v python)"
  else printf '%s\n' 'Python 3.10-3.14 was not found.' >&2; exit 1
  fi
fi
force_arg=()
skip_dependencies=false
for argument in "$@"; do
  case "$argument" in
    --force) force_arg=(--force) ;;
    --skip-dependencies) skip_dependencies=true ;;
    *) printf '%s\n' "Unknown option: $argument" >&2; exit 2 ;;
  esac
done
"$python_bin" -c 'import sys; assert (3,10) <= sys.version_info[:2] < (3,15)'
if [[ "$skip_dependencies" == false ]]; then
  "$python_bin" -m pip install --disable-pip-version-check --requirement "$project_root/requirements.lock"
fi
"$python_bin" "$project_root/install.py" "${force_arg[@]}"
"$python_bin" "$project_root/doctor.py"
printf '%s\n' 'SETUP_OK|skill=nature-ppt|local_vectorizer=true|remote_optional=true|restart_codex=true'
