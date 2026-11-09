#!/bin/sh
set -eu

template_dir=/etc/nginx/text-resources/templates
resource_dir=/var/cache/nginx/text-resources
map_path=/var/cache/nginx/text_resources_map.conf
temporary_file=
map_temporary_file=

fail() {
    printf 'text resource configuration error: %s\n' "$1" >&2
    exit 1
}

cleanup() {
    if [ -n "$temporary_file" ]; then
        rm -f "$temporary_file"
    fi
    if [ -n "$map_temporary_file" ]; then
        rm -f "$map_temporary_file"
    fi
}

trap cleanup EXIT
trap 'cleanup; exit 1' HUP INT TERM

validate_domain() {
    variable_name=$1
    candidate=$2

    [ -n "$candidate" ] || fail "$variable_name is required"
    [ "${#candidate}" -le 253 ] || fail "$variable_name must be a valid hostname"
    case "$candidate" in
        *[!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-]*)
            fail "$variable_name must be a valid hostname"
            ;;
    esac
    printf '%s\n' "$candidate" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$' ||
        fail "$variable_name must be a valid hostname"
}

validate_email() {
    candidate=$1

    [ -n "$candidate" ] || fail "SECURITY_CONTACT_EMAIL is required"
    case "$candidate" in
        *[!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._+@-]*)
            fail "SECURITY_CONTACT_EMAIL must be a valid email address"
            ;;
    esac
    printf '%s\n' "$candidate" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9._+-]*@[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$' ||
        fail "SECURITY_CONTACT_EMAIL must be a valid email address"
}

render_template() {
    source_path=$1
    target_path=$2
    substitutions=$3

    temporary_file=$(mktemp "${target_path}.XXXXXX")
    envsubst "$substitutions" < "$source_path" > "$temporary_file"
    chmod 644 "$temporary_file"
    mv -f "$temporary_file" "$target_path"
    temporary_file=
}

admin_domain=${ADMIN_DOMAIN:-}
api_domain=${API_DOMAIN:-}
contact_email=${SECURITY_CONTACT_EMAIL:-}

validate_domain ADMIN_DOMAIN "$admin_domain"
validate_domain API_DOMAIN "$api_domain"
[ "$admin_domain" != "$api_domain" ] || fail "ADMIN_DOMAIN and API_DOMAIN must differ"
validate_email "$contact_email"

now_epoch=$(date -u +%s) || fail "could not calculate the security.txt expiration"
expires_epoch=$((now_epoch + 180 * 86400))
expires=$(date -u -d "@$expires_epoch" '+%Y-%m-%dT%H:%M:%SZ') ||
    fail "could not calculate the security.txt expiration"
case "$expires" in
    ????-??-??T??:??:??Z) ;;
    *) fail "could not calculate the security.txt expiration" ;;
esac

mkdir -p "$resource_dir"
export ADMIN_DOMAIN="$admin_domain" API_DOMAIN="$api_domain"

for domain in "$admin_domain" "$api_domain"; do
    domain_dir="$resource_dir/$domain"
    mkdir -p "$domain_dir/.well-known"
    export RESOURCE_DOMAIN="$domain" SECURITY_CONTACT_EMAIL="$contact_email" EXPIRES="$expires"
    render_template "$template_dir/robots.txt.template" "$domain_dir/robots.txt" '$RESOURCE_DOMAIN'
    render_template "$template_dir/security.txt.template" "$domain_dir/.well-known/security.txt" '$RESOURCE_DOMAIN $SECURITY_CONTACT_EMAIL $EXPIRES'
done

map_temporary_file=$(mktemp "${map_path}.XXXXXX")
envsubst '${ADMIN_DOMAIN} ${API_DOMAIN}' < "$template_dir/text_resources_map.conf.template" > "$map_temporary_file"
chmod 644 "$map_temporary_file"
mv -f "$map_temporary_file" "$map_path"
map_temporary_file=
