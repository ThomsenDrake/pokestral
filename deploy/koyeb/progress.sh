#!/bin/sh
set -eu

: "${KOYEB_ORGANIZATION_ID:?set KOYEB_ORGANIZATION_ID to the target organization id}"
: "${KOYEB_APP_NAME:?set KOYEB_APP_NAME to the target app name}"
: "${KOYEB_SERVICE_NAME:?set KOYEB_SERVICE_NAME to the target service name}"

ORGANIZATION_ID="${KOYEB_ORGANIZATION_ID}"
APP_NAME="${KOYEB_APP_NAME}"
SERVICE_NAME="${KOYEB_SERVICE_NAME}"
MODE="${1:-status}"
SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)

SERVICE_ID=$(koyeb services list \
    --app "${APP_NAME}" \
    --organization "${ORGANIZATION_ID}" \
    --output json \
    | jq -er --arg name "${SERVICE_NAME}" \
        '.services[] | select(.name == $name) | .id')

case "${MODE}" in
    status)
        exec koyeb services exec "${SERVICE_ID}" \
            --organization "${ORGANIZATION_ID}" \
            python -- -m pokemon_vibe.app status \
            --server http://127.0.0.1:8000 \
            --data-dir /data/pokemon
        ;;
    transcript|transcript-raw)
        LINES="${2:-100}"
        case "${LINES}" in
            *[!0-9]*|''|0)
                echo "error: transcript line count must be a positive integer" >&2
                exit 2
                ;;
            *) ;;
        esac
        if [ "${MODE}" = "transcript-raw" ]; then
            exec koyeb services exec "${SERVICE_ID}" \
                --organization "${ORGANIZATION_ID}" \
                python -- -m pokemon_vibe.app transcript \
                --server http://127.0.0.1:8000 \
                --data-dir /data/pokemon \
                --lines "${LINES}"
        fi

        TRANSCRIPT_FILE=$(mktemp "${TMPDIR:-/tmp}/pokemon-vibe-transcript.XXXXXX")
        trap 'rm -f "${TRANSCRIPT_FILE}"' EXIT HUP INT TERM
        if koyeb services exec "${SERVICE_ID}" \
            --organization "${ORGANIZATION_ID}" \
            python -- -m pokemon_vibe.app transcript \
            --server http://127.0.0.1:8000 \
            --data-dir /data/pokemon \
            --lines "${LINES}" >"${TRANSCRIPT_FILE}"
        then
            PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
                python3 -m pokemon_vibe.transcript <"${TRANSCRIPT_FILE}"
        else
            STATUS=$?
            cat "${TRANSCRIPT_FILE}" >&2
            exit "${STATUS}"
        fi
        ;;
    logs)
        exec koyeb services logs "${SERVICE_ID}" \
            --organization "${ORGANIZATION_ID}" \
            --type runtime \
            --tail
        ;;
    *)
        echo "usage: $0 [status|transcript [lines]|transcript-raw [lines]|logs]" >&2
        exit 2
        ;;
esac
