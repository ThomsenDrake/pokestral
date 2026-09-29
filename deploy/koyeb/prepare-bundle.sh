#!/bin/sh
set -eu

PROJECT_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
EXPECTED_ROM_SHA256="2a951313c2640e8c2cb21f25d1db019ae6245d9c7121f754fa61afd7bee6452d"
: "${POKEMON_EXPECTED_STATE_SHA256:?set POKEMON_EXPECTED_STATE_SHA256 from the reviewed handoff save}"
: "${POKEMON_EXPECTED_GAME_ID:?set POKEMON_EXPECTED_GAME_ID to the paused local game id}"
: "${POKEMON_EXPECTED_SESSION_ID:?set POKEMON_EXPECTED_SESSION_ID to the mapped Vibe session id}"

EXPECTED_STATE_SHA256="${POKEMON_EXPECTED_STATE_SHA256}"
EXPECTED_GAME_ID="${POKEMON_EXPECTED_GAME_ID}"
EXPECTED_SESSION_ID="${POKEMON_EXPECTED_SESSION_ID}"
SERVER="${POKEMON_SERVER:-http://127.0.0.1:8765}"
ROM="${POKEMON_ROM_SOURCE:-${PROJECT_ROOT}/roms/pokemon-blue.gb}"
PRIVATE_VIBE_CONFIG="${PROJECT_ROOT}/deploy/koyeb/vibe-config.toml"

for tool in curl jq pgrep shasum; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "error: ${tool} is required to prepare a deployment bundle" >&2
        exit 1
    fi
done

CONTROL_STATE=$(curl -fsS "${SERVER}/control" | jq -r '.state')
if [ "${CONTROL_STATE}" != "paused" ]; then
    echo "error: pause the local runner before creating a cloud handoff" >&2
    exit 1
fi

GAME_ID=$(curl -fsS "${SERVER}/games/current" | jq -er '.active.id')
SESSION_ID=$(jq -er --arg id "${GAME_ID}" '.games[$id].session_id' \
    "${PROJECT_ROOT}/.data/vibe-sessions.json")
SAVE="${PROJECT_ROOT}/.data/games/${GAME_ID}/saves/cloud-handoff.state"
MANIFEST="${PROJECT_ROOT}/.data/games/${GAME_ID}/manifest.json"
VIBE_ROOT="${VIBE_HOME:-${HOME}/.vibe}"
VIBE_SESSION="${VIBE_ROOT}/logs/session/unified/${SESSION_ID}"

if [ "${GAME_ID}" != "${EXPECTED_GAME_ID}" ]; then
    echo "error: active game is not the predefined fresh-start game" >&2
    exit 1
fi
if [ "${SESSION_ID}" != "${EXPECTED_SESSION_ID}" ]; then
    echo "error: active game is not mapped to the predefined Vibe session" >&2
    exit 1
fi

test -f "${ROM}"
test -f "${SAVE}"
test -f "${MANIFEST}"
test -f "${VIBE_SESSION}/CURRENT"
test -f "${VIBE_SESSION}/meta.json"
if [ ! -f "${PRIVATE_VIBE_CONFIG}" ]; then
    echo "error: copy deploy/koyeb/vibe-config.example.toml to vibe-config.toml and configure it locally" >&2
    exit 1
fi

if ! jq -e --arg id "${SESSION_ID}" --arg root "${PROJECT_ROOT}" \
    '.session_id == $id and .environment.working_directory == $root' \
    "${VIBE_SESSION}/meta.json" >/dev/null; then
    echo "error: Vibe session metadata does not match the current project root" >&2
    exit 1
fi

if pgrep -f -- "--resume ${SESSION_ID}" >/dev/null 2>&1; then
    echo "error: the active Vibe turn has not quiesced yet" >&2
    exit 1
else
    PGREP_STATUS=$?
    if [ "${PGREP_STATUS}" -ne 1 ]; then
        echo "error: could not determine whether the active Vibe turn has quiesced" >&2
        exit 1
    fi
fi

ROM_SUM=$(shasum -a 256 "${ROM}")
ROM_SHA256=${ROM_SUM%% *}
STATE_SUM=$(shasum -a 256 "${SAVE}")
STATE_SHA256=${STATE_SUM%% *}
if [ "${ROM_SHA256}" != "${EXPECTED_ROM_SHA256}" ]; then
    echo "error: ROM checksum does not match the configured Pokemon Blue ROM" >&2
    exit 1
fi
if [ "${STATE_SHA256}" != "${EXPECTED_STATE_SHA256}" ]; then
    echo "error: cloud handoff checksum changed; create and review a new handoff" >&2
    exit 1
fi

if [ "$#" -gt 0 ]; then
    BUNDLE=$1
    mkdir -p "${BUNDLE}"
    if find "${BUNDLE}" -mindepth 1 -print -quit | grep -q .; then
        echo "error: bundle destination must be empty: ${BUNDLE}" >&2
        exit 1
    fi
else
    BUNDLE=$(mktemp -d "${TMPDIR:-/tmp}/pokemon-vibe-koyeb.XXXXXX")
fi

mkdir -p \
    "${BUNDLE}/src/pokemon_vibe" \
    "${BUNDLE}/.vibe/agents" \
    "${BUNDLE}/deploy/koyeb" \
    "${BUNDLE}/roms" \
    "${BUNDLE}/seed/pokemon/games/${GAME_ID}/saves" \
    "${BUNDLE}/seed/pokemon/saves" \
    "${BUNDLE}/seed/vibe"

cp -p "${PROJECT_ROOT}"/src/pokemon_vibe/*.py "${BUNDLE}/src/pokemon_vibe/"
cp -p "${PROJECT_ROOT}/.vibe/agents/pokemon-player.toml" "${BUNDLE}/.vibe/agents/"
cp -p \
    "${PROJECT_ROOT}/deploy/koyeb/Dockerfile" \
    "${PROJECT_ROOT}/deploy/koyeb/entrypoint.sh" \
    "${PROJECT_ROOT}/deploy/koyeb/requirements.lock" \
    "${BUNDLE}/deploy/koyeb/"
cp -p "${PRIVATE_VIBE_CONFIG}" "${BUNDLE}/deploy/koyeb/vibe-config.example.toml"
cp -p "${PROJECT_ROOT}/pyproject.toml" "${PROJECT_ROOT}/README.md" "${BUNDLE}/"
cp -p "${ROM}" "${BUNDLE}/roms/pokemon-blue.gb"
# Benchmark counters describe the new cloud run, not the discarded laptop
# attempt that produced the save. Keep its objectives, identity, and timestamps
# while starting turns/actions/saves and milestone history at zero.
jq '.stats = {"turns": 0, "actions": 0, "blackouts": 0, "saves": 0}
    | .milestones = []' \
    "${MANIFEST}" \
    > "${BUNDLE}/seed/pokemon/games/${GAME_ID}/manifest.json"
cp -p "${SAVE}" \
    "${BUNDLE}/seed/pokemon/games/${GAME_ID}/saves/cloud-handoff.state"
cp -p "${SAVE}" "${BUNDLE}/seed/pokemon/saves/cloud-handoff.state"
# A hard cutover starts a new cloud-side Vibe conversation. Importing the
# laptop session makes the first cloud turn replay a large historical context
# and defeats fresh-run semantics; the driver records the new session id here
# after its first successful turn.
printf '%s\n' '{"version": 1, "games": {}}' \
    > "${BUNDLE}/seed/pokemon/vibe-sessions.json"

chmod 0600 "${BUNDLE}/seed/pokemon/vibe-sessions.json"

SEED_SUMS="${BUNDLE}/.seed-sha256sums"
(
    cd "${BUNDLE}/seed"
    find . -type f -print \
        | LC_ALL=C sort \
        | while IFS= read -r file; do
            shasum -a 256 "${file}"
        done
) > "${SEED_SUMS}"
mv "${SEED_SUMS}" "${BUNDLE}/seed/SHA256SUMS"
chmod 0444 "${BUNDLE}/seed/SHA256SUMS"
printf '%s\n' "${BUNDLE}"
