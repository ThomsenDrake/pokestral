#!/bin/sh
set -eu

ROM_SHA256="2a951313c2640e8c2cb21f25d1db019ae6245d9c7121f754fa61afd7bee6452d"
GAME_ROOT="/opt/pokemon-seed/pokemon/games"
RESET_ID="${POKEMON_RESET_ID:-seed-v1}"
RESET_MARKER="/data/.pokemon-vibe-reset-${RESET_ID}"
CURRENT_MARKER="/data/.pokemon-vibe-reset-current"
RESET_PENDING="/data/.pokemon-vibe-reset-pending"
BACKUP_DIR="/data/backups/pre-${RESET_ID}"
STAGE_DIR="/data/.pokemon-vibe-reset-${RESET_ID}.staging"

case "${RESET_ID}" in
    ''|*[!A-Za-z0-9._-]*)
        echo "error: POKEMON_RESET_ID may contain only letters, digits, dots, underscores, and hyphens" >&2
        exit 1
        ;;
    current|pending|*.tmp|*.staging)
        echo "error: POKEMON_RESET_ID uses a reserved marker name: ${RESET_ID}" >&2
        exit 1
        ;;
    *) ;;
esac

require_nonblank() {
    case "$2" in
        *[![:space:]]*) ;;
        *)
            echo "error: $1 is required and may not be blank" >&2
            exit 1
            ;;
    esac
}

marker_matches_seed() {
    grep -Fqx "reset_id=${RESET_ID}" "$1" \
        && grep -Fqx "game_id=${GAME_ID}" "$1" \
        && grep -Fqx "state_sha256=${STATE_SHA256}" "$1"
}

write_marker() {
    printf '%s\n' \
        "reset_id=${RESET_ID}" \
        "game_id=${GAME_ID}" \
        "vibe_session=new" \
        "state_sha256=${STATE_SHA256}" \
        > "$1"
}

require_nonblank MISTRAL_API_KEY "${MISTRAL_API_KEY:-}"
require_nonblank POKEMON_DASHBOARD_USERNAME "${POKEMON_DASHBOARD_USERNAME:-}"
require_nonblank POKEMON_DASHBOARD_PASSWORD "${POKEMON_DASHBOARD_PASSWORD:-}"
POKEMON_ROM=${POKEMON_ROM:-}
require_nonblank POKEMON_ROM "${POKEMON_ROM}"

echo "${ROM_SHA256}  ${POKEMON_ROM}" | sha256sum --check --strict
(cd /opt/pokemon-seed && sha256sum --check --strict SHA256SUMS)

set -- "${GAME_ROOT}"/*
if [ "$#" -ne 1 ] || [ ! -d "$1" ]; then
    echo "error: the verified seed must contain exactly one game directory" >&2
    exit 1
fi
GAME_DIR=$1
GAME_ID=${GAME_DIR##*/}
STATE_PATH="${GAME_DIR}/saves/cloud-handoff.state"
STATE_SUM=$(sha256sum "${STATE_PATH}")
STATE_SHA256=${STATE_SUM%% *}

mkdir -p /data
RESET_REQUIRED=true
PENDING_RESET=false
if [ -e "${RESET_PENDING}" ]; then
    if [ ! -f "${RESET_PENDING}" ] || ! marker_matches_seed "${RESET_PENDING}"; then
        echo "error: another reset is pending; restore it before changing POKEMON_RESET_ID" >&2
        exit 1
    fi
    PENDING_RESET=true
fi

if [ -f "${CURRENT_MARKER}" ] && marker_matches_seed "${CURRENT_MARKER}"; then
    if [ -e "${RESET_MARKER}" ] \
        && { [ ! -f "${RESET_MARKER}" ] || ! marker_matches_seed "${RESET_MARKER}"; }
    then
        echo "error: reset history is invalid for ${RESET_ID}" >&2
        exit 1
    fi
    if [ ! -f "${RESET_MARKER}" ]; then
        write_marker "${RESET_MARKER}.tmp"
        mv "${RESET_MARKER}.tmp" "${RESET_MARKER}"
    fi
    rm -f "${RESET_PENDING}"
    RESET_REQUIRED=false
elif [ -e "${CURRENT_MARKER}" ] && [ ! -f "${CURRENT_MARKER}" ]; then
    echo "error: current reset marker is not a regular file: ${CURRENT_MARKER}" >&2
    exit 1
elif [ -f "${RESET_MARKER}" ]; then
    if ! marker_matches_seed "${RESET_MARKER}"; then
        echo "error: reset id ${RESET_ID} belongs to a different seed; choose a new POKEMON_RESET_ID" >&2
        exit 1
    elif [ "${PENDING_RESET}" = true ]; then
        write_marker "${CURRENT_MARKER}.tmp"
        mv "${CURRENT_MARKER}.tmp" "${CURRENT_MARKER}"
        rm -f "${RESET_PENDING}"
        RESET_REQUIRED=false
    elif [ ! -e "${CURRENT_MARKER}" ]; then
        # Upgrade a volume written by the original one-marker implementation.
        write_marker "${CURRENT_MARKER}.tmp"
        mv "${CURRENT_MARKER}.tmp" "${CURRENT_MARKER}"
        RESET_REQUIRED=false
    else
        echo "error: reset id ${RESET_ID} was already used; choose a new POKEMON_RESET_ID" >&2
        exit 1
    fi
elif [ -e "${RESET_MARKER}" ]; then
    echo "error: reset marker is not a regular file: ${RESET_MARKER}" >&2
    exit 1
fi

if [ "${RESET_REQUIRED}" = true ]; then
    if [ "${PENDING_RESET}" = false ]; then
        if [ -e "${BACKUP_DIR}" ]; then
            echo "error: reset id ${RESET_ID} was already used or has ambiguous recovery state" >&2
            exit 1
        fi
        rm -f "${RESET_PENDING}.tmp"
        write_marker "${RESET_PENDING}.tmp"
        mv "${RESET_PENDING}.tmp" "${RESET_PENDING}"
    fi

    mkdir -p "${BACKUP_DIR}"

    # Preserve the discarded cloud attempt once. If a reset was interrupted
    # after the pending marker and backup move, the backup remains authoritative
    # and any partial replacement is preserved separately before restaging.
    for name in pokemon vibe; do
        current="/data/${name}"
        backup="${BACKUP_DIR}/${name}"
        if [ -e "${current}" ]; then
            if [ ! -e "${backup}" ]; then
                mv "${current}" "${backup}"
            else
                partial_number=1
                partial="${backup}.partial-${partial_number}"
                while [ -e "${partial}" ]; do
                    partial_number=$((partial_number + 1))
                    partial="${backup}.partial-${partial_number}"
                done
                mv "${current}" "${partial}"
            fi
        fi
    done

    rm -rf "${STAGE_DIR}"
    mkdir -p "${STAGE_DIR}/pokemon" "${STAGE_DIR}/vibe"
    cp -a /opt/pokemon-seed/pokemon/. "${STAGE_DIR}/pokemon/"
    cp -a /opt/pokemon-seed/vibe/. "${STAGE_DIR}/vibe/"
    (cd "${STAGE_DIR}" && sha256sum --check --strict /opt/pokemon-seed/SHA256SUMS)

    mv "${STAGE_DIR}/pokemon" /data/pokemon
    mv "${STAGE_DIR}/vibe" /data/vibe
    rmdir "${STAGE_DIR}"
    write_marker "${RESET_MARKER}.tmp"
    mv "${RESET_MARKER}.tmp" "${RESET_MARKER}"
    write_marker "${CURRENT_MARKER}.tmp"
    mv "${CURRENT_MARKER}.tmp" "${CURRENT_MARKER}"
    rm -f "${RESET_PENDING}"
    echo "[cloud] hard cutover installed the pinned fresh-start state"
fi

install -d -m 0700 /data/vibe
install -m 0600 /opt/pokemon-vibe/vibe-config.toml /data/vibe/config.toml

test -f /data/pokemon/vibe-sessions.json
test -f "/data/pokemon/games/${GAME_ID}/saves/cloud-handoff.state"

chown -R pokemon:pokemon /data
exec gosu pokemon:pokemon python -m pokemon_vibe.app start --cloud --no-open-dashboard
