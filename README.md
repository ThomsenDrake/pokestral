# Mistral Vibe Plays Pokemon

This is a local, loopback-only launcher for Nous Research's
[`pokemon-agent`](https://github.com/NousResearch/pokemon-agent), with the
bundled Hermes autopilot replaced by a persistent Mistral Vibe session.

The emulator/API is installed from upstream commit
`f8a03e4a8bc58f1d9dda6d677a7436cc832a57a9`. This repo adds only the Vibe
driver, local launcher, configuration, tests, and a runtime dashboard rebrand;
it does not clone or vendor the upstream source tree.

## Setup

Prerequisites: `uv`, Mistral Vibe 2.25.6 or newer, `curl`, and a legally
obtained Pokemon Red, Blue, or Yellow Game Boy ROM. No ROM is included or
downloaded.

```bash
uv sync --extra dev
cp .env.example .env
mkdir -p roms
cp /path/to/your/pokemon-blue.gb roms/pokemon-blue.gb
uv run pokemon-vibe doctor
```

The checked-in `.env.example` supplies safe local defaults for
`roms/pokemon-blue.gb`, port `8765`, and `.data/`. Copy it to the ignored `.env`
file as shown above, then edit it if your ROM lives elsewhere. Leave
`POKEMON_VIBE_MODEL` blank to use the active model in `~/.vibe/config.toml`, or
set it to one of your configured Vibe aliases.

If Vibe has not been authenticated on this machine, run `vibe --setup` once.
Credentials remain in Vibe's normal credential store; this project does not
copy or persist them.

## Run

```bash
uv run pokemon-vibe start
```

The dashboard opens automatically at <http://127.0.0.1:8765/dashboard>. Choose
**+ NEW** (or load an existing game), then press **START**. The launcher keeps
the game server and Vibe driver together; `Ctrl-C` stops both. Pass
`--no-open-dashboard` for a headless launch. To operate them separately:

```bash
uv run pokemon-vibe serve
uv run pokemon-vibe play
```

Each pokemon-agent game id is mapped to its own persistent Vibe session in
`.data/vibe-sessions.json`. Loading a saved game therefore resumes the same
Vibe context. The driver saves `vibe-autosave` every 20 completed turns by
default. Change the interval and per-turn safety budgets in `.env`.

## What differs from the Hermes driver

- `vibe -p` is invoked with the project-local `pokemon-player` agent profile,
  `--auto-approve`, and `--experimental-harness`. (Vibe 2.25.8 calls the
  non-interactive approval flag `--auto-approve`; it has no `--auto-accept`
  option.)
- Only Vibe's `bash` tool is exposed, and the prompt restricts it to `curl`
  calls against the loopback game API.
- The driver uses structured RAM state and the collision map and does not attach
  screenshots to Vibe turns.
- Vibe session ids are stored in a sidecar map, so the upstream
  Hermes-specific session field and endpoint are never used.
- The upstream dashboard assets are copied into `.data/` at startup and
  rebranded for Mistral Vibe without modifying the installed package.

Local mode refuses non-loopback hosts and URLs. The default per-turn limits are
8 agent turns and 900 seconds, with no price ceiling. Set
`POKEMON_VIBE_MAX_PRICE` only when a per-invocation cost cap is wanted. The outer
900-second turn budget leaves 180 seconds of process and tool overhead beyond
Vibe's 720-second per-request API timeout.

## Koyeb deployment

`deploy/koyeb/` contains a pinned Linux image and a handoff bundler for moving
a reviewed, paused emulator state to Koyeb. The image uses Vibe 2.25.8. Model
and provider settings live only in the
Git-ignored `deploy/koyeb/vibe-config.toml`; copy
`deploy/koyeb/vibe-config.example.toml` there and configure it locally before
building a handoff bundle. The bundler substitutes that private configuration
only inside its ignored output directory. The service starts the existing game
and agent automatically, listens on port 8000, and persists game saves plus Vibe
transcripts under `/data`. The deployment command below explicitly removes the
default public route that Koyeb may create for an HTTP port. Cloud mode also
keeps an application-level Basic Auth guard as defense in depth; only `/health`
is exempt for Koyeb's health probe.

The Koyeb service needs separately managed credentials:

- A Mistral API key, injected as `MISTRAL_API_KEY`.
- A dashboard username and separate password, injected as
  `POKEMON_DASHBOARD_USERNAME` and `POKEMON_DASHBOARD_PASSWORD`.

Do not reuse the Mistral API key as the dashboard password. Neither secret is
copied into the image or handoff archive.

Pause the local game, create the named handoff save, then derive the reviewed
handoff identity from the local runtime. These commands assume the default
`.data` directory and local port:

```bash
SERVER=http://127.0.0.1:8765
curl -fsS -X POST "${SERVER}/control" \
  -H 'Content-Type: application/json' -d '{"state":"paused"}'
curl -fsS -X POST "${SERVER}/save" \
  -H 'Content-Type: application/json' -d '{"name":"cloud-handoff"}'

GAME_ID=$(curl -fsS "${SERVER}/games/current" | jq -er '.active.id')
SESSION_ID=$(jq -er --arg id "${GAME_ID}" '.games[$id].session_id' \
  .data/vibe-sessions.json)
STATE_SUM=$(shasum -a 256 \
  ".data/games/${GAME_ID}/saves/cloud-handoff.state")
export POKEMON_EXPECTED_GAME_ID="${GAME_ID}"
export POKEMON_EXPECTED_SESSION_ID="${SESSION_ID}"
export POKEMON_EXPECTED_STATE_SHA256=${STATE_SUM%% *}
BUNDLE=$(deploy/koyeb/prepare-bundle.sh)
```

The bundler verifies the pinned Pokemon Blue ROM, exact handoff save, game/Vibe
session mapping, current project workdir, and a quiesced agent. It includes only
the application source, player profile, ROM, and selected game manifest/save;
the originating Vibe transcript is deliberately excluded so the cloud run starts
a fresh conversation. It generates `seed/SHA256SUMS`, which the container
verifies before first use.

Choose private app, service, region, instance, secret, and volume names for your
own Koyeb account. Run exactly one stateful instance with a persistent volume at
`/data`, no public route, and no scale-to-zero. The current Koyeb CLI can deploy
the generated directory directly; `--routes '!/'` prevents the default public
route:

```bash
export KOYEB_ORGANIZATION_ID='<organization-id>'
koyeb deploy "${BUNDLE}" '<app-name>/<service-name>' \
  --organization "${KOYEB_ORGANIZATION_ID}" \
  --archive-builder docker \
  --archive-docker-dockerfile deploy/koyeb/Dockerfile \
  --regions '<region>' \
  --instance-type '<instance-type>' \
  --scale 1 \
  --ports 8000:http \
  --routes '!/' \
  --checks 8000:http:/health \
  --volumes '<volume-name>:/data' \
  --env 'MISTRAL_API_KEY={{secret.<api-key-secret>}}' \
  --env 'POKEMON_DASHBOARD_USERNAME={{secret.<username-secret>}}' \
  --env 'POKEMON_DASHBOARD_PASSWORD={{secret.<password-secret>}}' \
  --wait

koyeb services get '<app-name>/<service-name>' \
  --organization "${KOYEB_ORGANIZATION_ID}" --output json
```

Inspect that final service response and confirm the route list is empty before
treating the deployment as private.

On its first boot against a volume, the image performs the one-shot reset named
by `POKEMON_RESET_ID` (default `seed-v1`). It moves prior cloud `pokemon` and
`vibe` trees under `/data/backups/pre-$POKEMON_RESET_ID`, restores the verified
bundled save, starts a new cloud Vibe session, resets benchmark counters and
milestones to zero, and records a reset marker. A normal redeploy or restart
after that marker preserves subsequent progress. Reset IDs are permanent,
single-use identifiers: the container retains their markers and refuses to
reuse an old ID or pair an existing ID with a different seed. Set a new private
reset ID only when intentionally replacing an existing volume state.

Check progress through Koyeb's authenticated control plane instead of exposing
the dashboard or game API:

```bash
export KOYEB_ORGANIZATION_ID='<organization-id>'
export KOYEB_APP_NAME='<app-name>'
export KOYEB_SERVICE_NAME='<service-name>'
deploy/koyeb/progress.sh                  # current game summary
deploy/koyeb/progress.sh transcript 100   # recent Vibe activity as readable text
deploy/koyeb/progress.sh transcript-raw 100 # unfiltered recovery-journal JSONL
deploy/koyeb/progress.sh logs             # follow runtime logs; Ctrl-C to stop
```

Keep the laptop runner paused but installed until cloud acceptance verifies
private progress queries, the selected model, autonomous turns, save persistence
across a restart, and continuation of the same Vibe session. Only then stop the
local processes.

## Verify

```bash
uv run pytest
uv run ruff check .
```
