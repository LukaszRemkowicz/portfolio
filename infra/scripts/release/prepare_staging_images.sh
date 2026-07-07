#!/usr/bin/env bash
###############################################################################
# prepare_staging_images.sh
#
# Purpose:
#   Prepare staging images by pulling them from GHCR and tagging them locally to
#   the names expected by compose, release.sh, and deploy.sh. This mirrors the
#   production prepare_images.sh flow while using the staging image namespace and
#   the constant staging tag produced by the Publish Staging Images workflow.
#   The celery worker uses the same backend artifact, so this script creates the
#   local stage-worker tag from the pulled stage-be image.
#
# Usage:
#   doppler run -- ./prepare_staging_images.sh
#
# Parameters (Environment Variables):
#   The staging tag is intentionally fixed to v0.0.0-STG.
#   GHCR_REGISTRY  - Registry host. Defaults to ghcr.io.
#   GHCR_NAMESPACE - Full image namespace, injected via Doppler.
#
# Required:
#   GHCR_NAMESPACE
#   GHCR_USERNAME
#   GHCR_TOKEN
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils.sh"

PROJECT_DIR="$(get_project_dir)"
cd "${PROJECT_DIR}"

TAG="v0.0.0-STG"
validate_tag "${TAG}"

ENVIRONMENT="stage"
GHCR_REGISTRY="${GHCR_REGISTRY:-ghcr.io}"
: "${GHCR_NAMESPACE:?GHCR_NAMESPACE is required for prepare_staging_images.sh}"
REMOTE_PREFIX="stage"
LOCAL_PREFIX="${ENVIRONMENT}"
REMOTE_SERVICES=("be" "fe" "nginx")
LOCAL_SERVICES=("be" "worker" "fe" "nginx")
REGISTRY_ALIAS_SERVICES=("be" "worker" "fe" "nginx")
STATE_DIR="$(get_state_dir "${ENVIRONMENT}")"
DIGEST_FILE="${STATE_DIR}/prepared_image_digests.env"
CURRENT_FILE="${STATE_DIR}/current_tag"
PREV_FILE="${STATE_DIR}/prev_tag"
KEEP_IMAGES=5

echo "⚙️  Environment: ${ENVIRONMENT}"
echo "🏷️  Tag: ${TAG}"
echo "📦 Image source: staging registry"

record_digest() {
  local remote_image="$1"
  local local_image="$2"
  local key="$3"
  local digest

  digest="$(docker image inspect --format '{{join .RepoDigests "\n"}}' "${remote_image}" 2>/dev/null | head -n 1 | awk -F'@' 'NF==2 {print $2}')"

  if [[ -z "${digest}" ]]; then
    echo "❌ ERROR: Could not resolve digest for ${remote_image}" >&2
    exit 1
  fi

  mkdir -p "${STATE_DIR}"
  {
    echo "${key}_REMOTE_IMAGE=${remote_image}"
    echo "${key}_LOCAL_IMAGE=${local_image}"
    echo "${key}_DIGEST=${digest}"
  } >> "${DIGEST_FILE}"

  echo "🔒 Digest recorded for ${local_image}: ${digest}"
}

remove_remote_tag() {
  local remote_image="$1"

  echo "🧹 Removing GHCR tag ${remote_image} from local cache"
  docker image rm "${remote_image}" >/dev/null
}

cleanup_registry_aliases() {
  local svc remote_prefix local_prefix remote_ref image_id local_match

  echo "🧼 Sweeping stale GHCR aliases for managed staging images..."

  for svc in "${REGISTRY_ALIAS_SERVICES[@]}"; do
    remote_prefix="${GHCR_NAMESPACE}/${REMOTE_PREFIX}-${svc}:"
    local_prefix="${LOCAL_PREFIX}-${svc}:"

    while IFS= read -r remote_ref; do
      [[ -z "${remote_ref}" ]] && continue

      image_id="$(docker image inspect --format '{{.Id}}' "${remote_ref}" 2>/dev/null || true)"
      [[ -z "${image_id}" ]] && continue

      local_match="$(
        docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}' |
          awk -v prefix="${local_prefix}" -v id="${image_id}" '
            index($1, prefix) == 1 && $2 == id { print $1; exit }
          '
      )"

      if [[ -n "${local_match}" ]]; then
        echo "🧹 Removing stale GHCR alias ${remote_ref} (kept local tag ${local_match})"
        docker image rm "${remote_ref}" >/dev/null || true
      else
        echo "ℹ️  Keeping ${remote_ref} because no matching local runtime tag was found."
      fi
    done < <(docker image ls --format '{{.Repository}}:{{.Tag}}' | awk -v prefix="${remote_prefix}" 'index($0, prefix) == 1')
  done
}

prepare_registry_images() {
  : "${GHCR_USERNAME:?GHCR_USERNAME is required for prepare_staging_images.sh}"
  : "${GHCR_TOKEN:?GHCR_TOKEN is required for prepare_staging_images.sh}"

  echo "🔐 Logging in to ${GHCR_REGISTRY}..."
  printf '%s\n' "${GHCR_TOKEN}" | docker login "${GHCR_REGISTRY}" -u "${GHCR_USERNAME}" --password-stdin

  : > "${DIGEST_FILE}"

  for svc in "${REMOTE_SERVICES[@]}"; do
    local remote_image="${GHCR_NAMESPACE}/${REMOTE_PREFIX}-${svc}:${TAG}"
    local local_image="${LOCAL_PREFIX}-${svc}:${TAG}"
    local digest_key
    digest_key="$(echo "${svc}" | tr '[:lower:]-' '[:upper:]_')"

    echo "⬇️ Pulling ${remote_image}"
    docker pull "${remote_image}"

    echo "🏷️ Tagging ${remote_image} -> ${local_image}"
    docker tag "${remote_image}" "${local_image}"
    record_digest "${remote_image}" "${local_image}" "${digest_key}"

    if [[ "${svc}" == "be" ]]; then
      local worker_image="${LOCAL_PREFIX}-worker:${TAG}"
      echo "🏷️ Tagging ${local_image} -> ${worker_image}"
      docker tag "${local_image}" "${worker_image}"
      record_digest "${remote_image}" "${worker_image}" "WORKER"
    fi

    remove_remote_tag "${remote_image}"
  done
}

verify_local_images() {
  for svc in "${LOCAL_SERVICES[@]}"; do
    local local_image="${LOCAL_PREFIX}-${svc}:${TAG}"
    if ! docker image inspect "${local_image}" >/dev/null 2>&1; then
      echo "❌ ERROR: Missing local image ${local_image}" >&2
      exit 1
    fi
    echo "✅ Local image available: ${local_image}"
  done
}

prepare_registry_images
verify_local_images
cleanup_registry_aliases
prune_local_images "${ENVIRONMENT}" "${KEEP_IMAGES}" "${TAG}" "$(cat "${CURRENT_FILE}" 2>/dev/null || true)" "$(cat "${PREV_FILE}" 2>/dev/null || true)" \
  "${LOCAL_PREFIX}-be" "${LOCAL_PREFIX}-worker" "${LOCAL_PREFIX}-fe" "${LOCAL_PREFIX}-nginx"

echo "🎉 Staging image preparation completed for TAG=${TAG}"
if [[ -f "${DIGEST_FILE}" ]]; then
  echo "📝 Digest file: ${DIGEST_FILE}"
fi
