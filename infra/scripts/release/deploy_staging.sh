#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils.sh"

ENVIRONMENT="${ENVIRONMENT:-stage}"
TAG="${TAG:-v0.0.0-STG}"
AUTO_APPROVE=false
DRY_RUN=false
BUILD_ARGS=()
FLOW_ARGS=()

for arg in "$@"; do
  case "${arg}" in
    --yes)
      AUTO_APPROVE=true
      ;;
    --dry-run)
      DRY_RUN=true
      FLOW_ARGS+=("${arg}")
      ;;
    --emergency|--no-cache)
      BUILD_ARGS+=("${arg}")
      ;;
    *)
      echo "❌ ERROR: Unknown argument: ${arg}"
      echo "👉 Supported arguments: --yes, --dry-run, --emergency, --no-cache"
      exit 1
      ;;
  esac
done

export ENVIRONMENT TAG AUTO_APPROVE

echo "🚀 Staging deploy plan"
echo "   ENVIRONMENT=${ENVIRONMENT}"
echo "   TAG=${TAG}"
echo "   Steps: build.sh -> release.sh -> deploy.sh"

confirm_continue "Start staging deployment?" || exit 0

echo "🏗️  Running build.sh..."
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "🧾 DRY RUN: would execute: ENVIRONMENT=${ENVIRONMENT} TAG=${TAG} ${SCRIPT_DIR}/build.sh"
else
  "${SCRIPT_DIR}/build.sh" "${BUILD_ARGS[@]}"
fi
echo "✅ build.sh finished."

confirm_continue "Continue to release.sh?" || exit 0

echo "🧪 Running release.sh..."
"${SCRIPT_DIR}/release.sh" "${FLOW_ARGS[@]}"
echo "✅ release.sh finished."

confirm_continue "Continue to deploy.sh?" || exit 0

echo "🚀 Running deploy.sh..."
"${SCRIPT_DIR}/deploy.sh" "${FLOW_ARGS[@]}"
echo "✅ Staging deployment finished."
