#!/usr/bin/env bash
###############################################################################
# utils.sh
#
# Purpose:
#   Shared utility functions for release scripts.
#   Should be sourced by other scripts in this directory.
###############################################################################

# ------------------------------------------------------------------
# get_project_dir
#   Finds the root of the Git repository.
#   Exits if not in a git repository.
# ------------------------------------------------------------------
get_project_dir() {
  local dir
  dir="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "${dir}" ]]; then
    echo "❌ ERROR: Script must be run inside a Git repository." >&2
    exit 1
  fi
  echo "${dir}"
}

# ------------------------------------------------------------------
# get_state_dir
#   Resolves the directory to store deployment state (e.g. current_tag).
#   Prefers /var/lib/portfolio for system-wide state, falls back to $HOME.
# ------------------------------------------------------------------
get_state_dir() {
  local env="$1"
  local state_dir="${STATE_DIR:-}"
  if [[ -z "${state_dir}" ]]; then
    if [[ -d "/var/lib/portfolio" && -w "/var/lib/portfolio" ]]; then
      state_dir="/var/lib/portfolio/${env}"
    elif [[ "$EUID" -eq 0 ]]; then
      mkdir -p "/var/lib/portfolio/${env}" 2>/dev/null || true
      state_dir="/var/lib/portfolio/${env}"
    else
      state_dir="$HOME/.portfolio-state/${env}"
    fi
  fi
  mkdir -p "${state_dir}" 2>/dev/null || true
  echo "${state_dir}"
}

# ------------------------------------------------------------------
# get_compose_image
#   Extracts the image name for a given service from the compose config.
#   Tries yq first, then falls back to an awk script.
#   Usage: get_compose_image <service_name> "${COMPOSE[@]}"
# ------------------------------------------------------------------
get_compose_image() {
  local svc="$1"
  shift
  local compose_cmd=("$@")

  local image_to_check
  image_to_check=$(
    set +o pipefail
    if command -v yq >/dev/null 2>&1; then
      "${compose_cmd[@]}" config 2>/dev/null | yq ".services.${svc}.image" -r 2>/dev/null || echo ""
    else
      "${compose_cmd[@]}" config 2>/dev/null | awk -v svc="${svc}" '
        $1 == svc":" { indent=index($0,svc); found=1; next }
        found && $1 == "image:" { print $2; exit }
        found && index($0, ":") == indent + length($1) && $1 != "image:" { exit }
      ' | tr -d '"'\'' '
    fi
  ) || image_to_check=""

  echo "${image_to_check}"
}

# ------------------------------------------------------------------
# validate_tag
#   Ensures the provided tag exists and is SemVer-like.
# ------------------------------------------------------------------
validate_tag() {
  local tag="$1"
  if [[ -z "$tag" ]]; then
    echo "🛑 ERROR: TAG is empty." >&2
    exit 1
  fi
  if ! [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([\-+].+)?$ ]]; then
    echo "❌ ERROR: Tag '$tag' is not SemVer-like (expected vX.Y.Z or vX.Y.Z-suffix)" >&2
    exit 1
  fi
}
