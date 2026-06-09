#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

cat > "${tmp_dir}/docker" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail

if [[ "$1" != "ps" ]]; then
  echo "unexpected docker command: $*" >&2
  exit 2
fi

expected=(
  "ps"
  "--filter"
  "label=com.docker.compose.project=portfolio-stage"
  "--filter"
  "label=com.docker.compose.service=be"
  "--filter"
  "label=com.docker.compose.oneoff=False"
  "--format"
  "{{.Names}}"
)

if [[ "$*" != "${expected[*]}" ]]; then
  echo "unexpected docker ps args: $*" >&2
  exit 2
fi

printf '%s\n' "portfolio-stage-be-1"
STUB
chmod +x "${tmp_dir}/docker"

PATH="${tmp_dir}:${PATH}"
source "${REPO_ROOT}/infra/scripts/utils.sh"

actual="$(get_compose_service_containers "portfolio-stage" "be")"
expected="portfolio-stage-be-1"

if [[ "${actual}" != "${expected}" ]]; then
  echo "expected only the long-running backend container"
  echo "expected: ${expected}"
  echo "actual: ${actual}"
  exit 1
fi
