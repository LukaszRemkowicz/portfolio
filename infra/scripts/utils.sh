#!/usr/bin/env bash
###############################################################################
# utils.sh
#
# Purpose:
#   Shared utility functions for infrastructure scripts.
#   May be sourced by release, backup, monitoring, and related script groups.
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
    # Fallback to current directory for prod/environments without .git
    dir="$(pwd)"
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
# get_project_name
#   Resolves the Docker project name consistently.
#   Prioritizes $COMPOSE_PROJECT_NAME, defaults to folder/git-derived naming.
# ------------------------------------------------------------------
get_project_name() {
  local base_name="${COMPOSE_PROJECT_NAME:-}"

  # 1. Try extracting name from COMPOSE_FILE if it exists
  if [[ -z "${base_name}" && -n "${COMPOSE_FILE:-}" && -f "${COMPOSE_FILE}" ]]; then
    base_name=$(grep -E "^name:[[:space:]]+" "${COMPOSE_FILE}" | awk '{print $2}' | tr -d '"'\'' ' | head -n 1)
  fi

  # 2. Fallback to folder name
  if [[ -z "${base_name}" ]]; then
    base_name=$(basename "$(get_project_dir)")
  fi

  # 3. Handle suffixing if ENVIRONMENT is set
  if [[ -n "${ENVIRONMENT:-}" ]]; then
    local suffix
    suffix=$(get_env_suffix "${ENVIRONMENT}")
    if [[ "${base_name}" == *"${suffix}"* ]]; then
      echo "${base_name}"
    else
      echo "${base_name}-${suffix}"
    fi
  else
    echo "${base_name}"
  fi
}

# ------------------------------------------------------------------
# get_db_name
#   Resolves the standardized database name based on ENVIRONMENT.
# ------------------------------------------------------------------
get_db_name() {
  case "${ENVIRONMENT:-}" in
    production|prod) echo "portfolio_prod" ;;
    staging|stage|stg) echo "portfolio_stage" ;;
    *) echo "portfolio_dev" ;;
  esac
}

# ------------------------------------------------------------------
# get_env_suffix
#   Maps environment names to Docker Compose filename suffixes.
# ------------------------------------------------------------------
get_env_suffix() {
  local env="$1"
  case "${env}" in
    production) echo "prod" ;;
    prod)       echo "prod" ;;
    staging)    echo "stage" ;;
    stage)      echo "stage" ;;
    stg)        echo "stage" ;;
    *)          echo "${env}" ;;
  esac
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

# ------------------------------------------------------------------
# confirm_continue
#   Prompts the operator before continuing to the next deployment phase.
#   Skips the prompt when AUTO_APPROVE=true.
# ------------------------------------------------------------------
confirm_continue() {
  local prompt="${1:-Continue?}"
  local response

  if [[ "${AUTO_APPROVE:-false}" == "true" ]]; then
    echo "⏭️  AUTO_APPROVE=true, continuing without prompt."
    return 0
  fi

  printf "%s [y/N]: " "${prompt}"
  read -r response

  case "${response}" in
    y|Y|yes|YES)
      return 0
      ;;
    *)
      echo "🛑 Stopped by user."
      return 1
      ;;
  esac
}

# ------------------------------------------------------------------
# prune_local_images
#   Removes older local image tags while protecting the prepared/current/prev
#   tags and keeping the most recent N tags per repository.
#   Usage: prune_local_images <environment_prefix> <keep_images> <prepared_tag> <current_tag> <prev_tag> <repo...>
# ------------------------------------------------------------------
prune_local_images() {
  local env_prefix="$1"
  local keep_images="$2"
  local prepared_tag="$3"
  local current_tag="$4"
  local prev_tag="$5"
  shift 5

  local repo t

  echo "🧹 Cleaning up local ${env_prefix} images..."
  echo "📌 Keeping tags: prepared=${prepared_tag:-none} current=${current_tag:-none} prev=${prev_tag:-none}"

  for repo in "$@"; do
    local tags=()

    echo "➡️ Repo: ${repo}"

    while IFS=$'\t' read -r _ tag; do
      if [[ -n "${tag}" && "${tag}" != "<none>" && "${tag}" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+ ]]; then
        tags+=("${tag}")
      fi
    done < <(
      docker images "${repo}" --format '{{.CreatedAt}}\t{{.Tag}}' | sort -r
    )

    if (( ${#tags[@]} > keep_images )); then
      for ((i=keep_images; i<${#tags[@]}; i++)); do
        t="${tags[$i]}"

        if [[ "${t}" == "${prepared_tag}" ]] || [[ -n "${current_tag}" && "${t}" == "${current_tag}" ]] || [[ -n "${prev_tag}" && "${t}" == "${prev_tag}" ]]; then
          echo "📌 Skipping protective tag: ${repo}:${t}"
          continue
        fi

        echo "🗑️ Removing old image: ${repo}:${t}"
        docker image rm -f "${repo}:${t}" >/dev/null 2>&1 || true
      done
    else
      echo "✔️ Nothing to clean for ${repo}"
    fi
  done
}
