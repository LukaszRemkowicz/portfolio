#!/bin/sh
set -eu

APP_USER="${APP_USER:-node}"
RUNTIME_ROOT="${FRONTEND_ASSET_ROOT:-/app/runtime-assets}"

APP_UID="$(id -u "${APP_USER}")"
APP_GID="$(id -g "${APP_USER}")"

mkdir -p "${RUNTIME_ROOT}/current" "${RUNTIME_ROOT}/previous"
chown -R "${APP_UID}:${APP_GID}" "${RUNTIME_ROOT}"

exec su-exec "${APP_UID}:${APP_GID}" "$@"
