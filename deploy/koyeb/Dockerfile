FROM python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49 AS vibe

ARG VIBE_VERSION=2.25.8
ARG VIBE_SHA256=6fc1ea5d2338bca1bb110d3d36e80dabe92bcb7adcdf877e25fa9697f4c3ad84

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl unzip \
    && curl --fail --show-error --location --retry 3 \
       --output /tmp/vibe.zip \
       "https://github.com/mistralai/mistral-vibe/releases/download/v${VIBE_VERSION}/vibe-linux-x86_64-${VIBE_VERSION}.zip" \
    && echo "${VIBE_SHA256}  /tmp/vibe.zip" | sha256sum --check --strict \
    && mkdir -p /opt/vibe \
    && unzip -q /tmp/vibe.zip -d /opt/vibe \
    && chmod 0755 /opt/vibe/vibe

FROM python:3.12.11-slim-bookworm@sha256:c00fc7b44d844b6da22861ec24af43968a5200eac4ec607b4725d585165d6b49

# Keep a stable cloud workdir so the new Vibe session remains resumable across
# ordinary container restarts.
ARG APP_ROOT=/opt/pokemon-vibe

ENV HOME=/home/pokemon \
    PATH=/opt/vibe:${PATH} \
    PYTHONPATH=${APP_ROOT}/src \
    PYTHONUNBUFFERED=1 \
    VIBE_HOME=/data/vibe \
    POKEMON_PROJECT_ROOT=${APP_ROOT} \
    POKEMON_ROM=/opt/pokemon/roms/pokemon-blue.gb \
    POKEMON_DATA_DIR=/data/pokemon \
    POKEMON_HOST=0.0.0.0 \
    POKEMON_PORT=8000 \
    POKEMON_OPEN_DASHBOARD=false \
    POKEMON_CLOUD=true \
    POKEMON_AUTO_START=true \
    POKEMON_SEED_STATE=cloud-handoff \
    POKEMON_GAME_LABEL="Pokemon Blue" \
    POKEMON_VIBE_BIN=vibe \
    POKEMON_VIBE_MAX_TURNS=8 \
    POKEMON_VIBE_TURN_TIMEOUT=900 \
    POKEMON_TURN_DELAY=1.5 \
    POKEMON_AUTOSAVE_EVERY=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --home-dir /home/pokemon --uid 10001 pokemon

COPY --from=vibe /opt/vibe /opt/vibe

WORKDIR ${APP_ROOT}
COPY deploy/koyeb/requirements.lock /tmp/pokemon-vibe-requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes \
    --requirement /tmp/pokemon-vibe-requirements.lock

COPY src ./src

COPY .vibe ./.vibe
COPY roms/pokemon-blue.gb /opt/pokemon/roms/pokemon-blue.gb
COPY seed /opt/pokemon-seed
COPY deploy/koyeb/vibe-config.example.toml /opt/pokemon-vibe/vibe-config.toml
COPY deploy/koyeb/entrypoint.sh /usr/local/bin/pokemon-vibe-cloud

RUN chmod 0755 /usr/local/bin/pokemon-vibe-cloud \
    && chown -R pokemon:pokemon "${APP_ROOT}" /home/pokemon

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/pokemon-vibe-cloud"]
