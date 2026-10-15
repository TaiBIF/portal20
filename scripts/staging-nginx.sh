#!/bin/sh
set -eu

certificate=/etc/letsencrypt/live/staging.taibif.tw/fullchain.pem
private_key=/etc/letsencrypt/live/staging.taibif.tw/privkey.pem
active_config=/etc/nginx/conf.d/default.conf

certificate_signature() {
    if [ -s "$certificate" ] && [ -s "$private_key" ]; then
        cksum "$certificate" "$private_key"
    else
        printf '%s\n' missing
    fi
}

render_config() {
    if [ -s "$certificate" ] && [ -s "$private_key" ]; then
        template=/etc/nginx/staging/taibif.conf
    else
        template=/etc/nginx/staging/http.conf
    fi
    cp "$template" "$active_config.tmp"
    mv "$active_config.tmp" "$active_config"
}

# The HTTP template needs no dummy certificate and keeps existing pages available.
initial_signature=$(certificate_signature)
render_config
nginx -t
nginx -g 'daemon off;' &
nginx_pid=$!

watch_certificates() {
    previous_signature=$initial_signature
    while :; do
        sleep 60 &
        wait $!
        current_signature=$(certificate_signature)
        if [ "$current_signature" != "$previous_signature" ]; then
            cp "$active_config" "$active_config.previous"
            render_config
            if nginx -t && nginx -s reload; then
                previous_signature=$current_signature
                printf '%s\n' 'TLS certificate changed; nginx configuration reloaded.'
            else
                mv "$active_config.previous" "$active_config"
                printf '%s\n' 'TLS reload failed; keeping the previous configuration and retrying.' >&2
            fi
        fi
    done
}

watch_certificates &
watcher_pid=$!
stop() {
    kill -TERM "$watcher_pid" 2>/dev/null || true
    kill -QUIT "$nginx_pid" 2>/dev/null || true
    wait "$nginx_pid" 2>/dev/null || true
}
trap stop TERM INT
wait "$nginx_pid" || status=$?
kill -TERM "$watcher_pid" 2>/dev/null || true
exit "${status:-0}"
