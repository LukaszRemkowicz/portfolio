#!/usr/bin/env bash
###############################################################################
# prepare_images.sh
#
# Purpose:
#   Prepare production release images by pulling them from GHCR and tagging
#   them locally to the names already expected by compose, release.sh, and
#   deploy.sh.
#
# Usage:
#   TAG=v1.2.3 doppler run -- ./prepare_images.sh
#   TEST=true TAG=test-branch-sha doppler run -- ./prepare_images.sh
#
# Parameters (Environment Variables):
#   TAG            - Release tag (vX.Y.Z). If omitted, uses 'git describe'
#   TEST           - If 'true', bypasses SemVer tag validation for test tags
#   GHCR_REGISTRY  - Registry host. Defaults to ghcr.io
#   GHCR_NAMESPACE - Full image namespace, injected via Doppler
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

git fetch --tags >/dev/null 2>&1 || true
TAG="${TAG:-$(git describe --tags --exact-match 2>/dev/null || true)}"
TEST="${TEST:-false}"
if [[ "${TEST}" == "true" ]]; then
  echo "🧪 TEST=true: skipping SemVer validation for TAG=${TAG}"
else
  validate_tag "$TAG"
fi

ENVIRONMENT="production"
GHCR_REGISTRY="${GHCR_REGISTRY:-ghcr.io}"
: "${GHCR_NAMESPACE:?GHCR_NAMESPACE is required for prepare_images.sh}"
REMOTE_PREFIX="production"
LOCAL_PREFIX="${ENVIRONMENT}"
SERVICES=("be" "fe" "nginx")
STATE_DIR="$(get_state_dir "${ENVIRONMENT}")"
DIGEST_FILE="${STATE_DIR}/prepared_image_digests.env"

echo "⚙️  Environment: ${ENVIRONMENT}"
echo "🏷️  Tag: ${TAG}"
echo "📦 Image source: registry"

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

prepare_registry_images() {
  : "${GHCR_USERNAME:?GHCR_USERNAME is required for prepare_images.sh}"
  : "${GHCR_TOKEN:?GHCR_TOKEN is required for prepare_images.sh}"

  echo "🔐 Logging in to ${GHCR_REGISTRY}..."
  printf '%s\n' "${GHCR_TOKEN}" | docker login "${GHCR_REGISTRY}" -u "${GHCR_USERNAME}" --password-stdin

  : > "${DIGEST_FILE}"

  for svc in "${SERVICES[@]}"; do
    local remote_image="${GHCR_NAMESPACE}/${REMOTE_PREFIX}-${svc}:${TAG}"
    local local_image="${LOCAL_PREFIX}-${svc}:${TAG}"
    local digest_key
    digest_key="$(echo "${svc}" | tr '[:lower:]-' '[:upper:]_')"

    echo "⬇️ Pulling ${remote_image}"
    docker pull "${remote_image}"

    echo "🏷️ Tagging ${remote_image} -> ${local_image}"
    docker tag "${remote_image}" "${local_image}"
    record_digest "${remote_image}" "${local_image}" "${digest_key}"
  done
}

verify_local_images() {
  for svc in "${SERVICES[@]}"; do
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

echo "🎉 Image preparation completed for TAG=${TAG}"
if [[ -f "${DIGEST_FILE}" ]]; then
  echo "📝 Digest file: ${DIGEST_FILE}"
fi
