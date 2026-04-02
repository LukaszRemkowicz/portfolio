#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils.sh"

ENVIRONMENT="production"
AUTO_APPROVE=false
DRY_RUN=false
PASSTHROUGH_ARGS=()

for arg in "$@"; do
  case "${arg}" in
    --yes)
      AUTO_APPROVE=true
      ;;
    --dry-run)
      DRY_RUN=true
      PASSTHROUGH_ARGS+=("${arg}")
      ;;
    *)
      PASSTHROUGH_ARGS+=("${arg}")
      ;;
  esac
done

: "${TAG:?TAG is required for deploy_production.sh}"

export ENVIRONMENT TAG AUTO_APPROVE

echo "🚀 Production deploy plan"
echo "   ENVIRONMENT=${ENVIRONMENT}"
echo "   TAG=${TAG}"
echo "   Steps: prepare_images.sh -> release.sh -> deploy.sh"

confirm_continue "Start production deployment?" || exit 0

echo "📦 Running prepare_images.sh..."
if [[ "${DRY_RUN}" == "true" ]]; then
  echo "🧾 DRY RUN: would execute: TAG=${TAG} ${SCRIPT_DIR}/prepare_images.sh"
else
  "${SCRIPT_DIR}/prepare_images.sh"
fi
echo "✅ prepare_images.sh finished."

confirm_continue "Continue to release.sh?" || exit 0

echo "🧪 Running release.sh..."
"${SCRIPT_DIR}/release.sh" "${PASSTHROUGH_ARGS[@]}"
echo "✅ release.sh finished."

confirm_continue "Continue to deploy.sh?" || exit 0

echo "🚀 Running deploy.sh..."
"${SCRIPT_DIR}/deploy.sh" "${PASSTHROUGH_ARGS[@]}"
echo "✅ Production deployment finished."
