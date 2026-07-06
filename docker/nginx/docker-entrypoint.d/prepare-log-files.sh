#!/bin/sh
set -eu

nginx_log_dir="${NGINX_LOG_DIR:-/var/log/nginx}"

mkdir -p "${nginx_log_dir}"

for log_file in access.log error.log; do
    log_path="${nginx_log_dir}/${log_file}"
    touch "${log_path}"

    if [ ! -w "${log_path}" ]; then
        echo "Nginx log file is not writable: ${log_path}" >&2
        exit 1
    fi
done
