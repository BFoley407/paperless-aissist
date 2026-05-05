#!/bin/sh
set -eu

APP_USER="app"
APP_GROUP="app"
APP_HOME="/home/${APP_USER}"

PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

case "${PUID}${PGID}" in
  *[!0-9]*)
    echo "PUID and PGID must be numeric" >&2
    exit 1
    ;;
esac

if [ "${PUID}" = "0" ] || [ "${PGID}" = "0" ]; then
  echo "PUID/PGID cannot be 0; refusing to run app processes as root" >&2
  exit 1
fi

if getent group "${APP_GROUP}" >/dev/null 2>&1; then
  groupmod -o -g "${PGID}" "${APP_GROUP}"
else
  groupadd -o -g "${PGID}" "${APP_GROUP}"
fi

if id -u "${APP_USER}" >/dev/null 2>&1; then
  usermod -o -u "${PUID}" -g "${PGID}" "${APP_USER}"
else
  useradd -o -u "${PUID}" -g "${PGID}" -m -d "${APP_HOME}" -s /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p /app/data /var/log/supervisor /var/log/nginx /var/lib/nginx/body /var/lib/nginx/cache /tmp
chown -R "${PUID}:${PGID}" /app /var/log/supervisor /var/log/nginx /var/lib/nginx /tmp

exec gosu "${PUID}:${PGID}" "$@"
