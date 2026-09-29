from __future__ import annotations

import argparse
import base64
import binascii
import ipaddress
import json
import os
import pty
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

UPSTREAM_COMMIT = "f8a03e4a8bc58f1d9dda6d677a7436cc832a57a9"
MIN_VIBE_VERSION = (2, 25, 6)
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class DriverError(RuntimeError):
    """A configuration or runtime error that can be shown to the operator."""


class BasicAuthGuard:
    """Protect public HTTP and WebSocket traffic while allowing loopback control."""

    def __init__(self, app: Any, *, username: str, password: str):
        self.app = app
        self.expected = f"{username}:{password}".encode()

    @staticmethod
    def _is_loopback(scope: dict[str, Any]) -> bool:
        client = scope.get("client")
        if not isinstance(client, (tuple, list)) or not client:
            return False
        try:
            return ipaddress.ip_address(str(client[0]).split("%", 1)[0]).is_loopback
        except ValueError:
            return False

    def _authorized(self, scope: dict[str, Any]) -> bool:
        for raw_name, raw_value in scope.get("headers", []):
            if raw_name.lower() != b"authorization":
                continue
            scheme, separator, token = raw_value.partition(b" ")
            if not separator or scheme.lower() != b"basic":
                return False
            try:
                supplied = base64.b64decode(token, validate=True)
            except (binascii.Error, ValueError):
                return False
            return secrets.compare_digest(supplied, self.expected)
        return False

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        request_type = scope.get("type")
        if (
            request_type not in {"http", "websocket"}
            or scope.get("path") == "/health"
            or self._is_loopback(scope)
            or self._authorized(scope)
        ):
            await self.app(scope, receive, send)
            return

        if request_type == "websocket":
            await send(
                {
                    "type": "websocket.close",
                    "code": 4401,
                    "reason": "Authentication required",
                }
            )
            return

        body = b"Authentication required\n"
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"cache-control", b"no-store"),
                    (b"content-length", str(len(body)).encode()),
                    (b"content-type", b"text/plain; charset=utf-8"),
                    (
                        b"www-authenticate",
                        b'Basic realm="Pokemon dashboard", charset="UTF-8"',
                    ),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def project_root() -> Path:
    configured = os.environ.get("POKEMON_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def resolve_project_path(raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = project_root() / path
    return path.resolve()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def compact_state(state: dict[str, Any]) -> dict[str, Any]:
    """Keep the fields Vibe needs while avoiding a large prompt every turn."""
    metadata = _as_dict(state.get("metadata"))
    player = _as_dict(state.get("player"))
    map_info = _as_dict(state.get("map"))
    collision = _as_dict(state.get("collision"))
    dialog = _as_dict(state.get("dialog"))
    battle = _as_dict(state.get("battle"))
    enemy = _as_dict(battle.get("enemy"))

    party: list[dict[str, Any]] = []
    raw_party = state.get("party")
    if isinstance(raw_party, list):
        for raw_member in raw_party:
            member = _as_dict(raw_member)
            moves = member.get("moves") if isinstance(member.get("moves"), list) else []
            party.append(
                {
                    "nickname": member.get("nickname"),
                    "species": member.get("species"),
                    "level": member.get("level"),
                    "hp": member.get("hp"),
                    "max_hp": member.get("max_hp"),
                    "status": member.get("status"),
                    "types": member.get("types"),
                    "moves": [
                        _as_dict(move).get("name") if isinstance(move, dict) else move
                        for move in moves
                    ],
                }
            )

    return {
        "game": metadata.get("game"),
        "frame": metadata.get("frame_count"),
        "map": map_info.get("map_name"),
        "position": player.get("position"),
        "facing": player.get("facing"),
        "cell": collision.get("player_cell", "E5"),
        "money": player.get("money"),
        "badges": player.get("badges"),
        "party": party,
        "dialog_active": dialog.get("active"),
        "in_battle": battle.get("in_battle"),
        "enemy": (
            {
                "species": enemy.get("species"),
                "level": enemy.get("level"),
                "hp": enemy.get("hp"),
                "max_hp": enemy.get("max_hp"),
                "status": enemy.get("status"),
            }
            if battle.get("in_battle")
            else None
        ),
    }


def build_status_report(
    *,
    current: dict[str, Any],
    control: dict[str, Any],
    state: dict[str, Any],
    manifest: dict[str, Any],
    session_id: str | None,
    game_label: str,
) -> dict[str, Any]:
    active = _as_dict(current.get("active"))
    game_id = active.get("id")
    if not isinstance(game_id, str) or not game_id:
        raise DriverError("No active cloud game")
    compact = compact_state(state)
    player = _as_dict(state.get("player"))
    milestones = manifest.get("milestones")
    latest_milestone = milestones[0] if isinstance(milestones, list) and milestones else None
    return {
        "control": control.get("state"),
        "game": {
            "id": game_id,
            "name": active.get("name"),
            "configured_as": game_label,
            "adapter_report": compact.get("game"),
        },
        "player": player.get("name"),
        "map": compact.get("map"),
        "position": compact.get("position"),
        "facing": compact.get("facing"),
        "party": compact.get("party"),
        "badges": compact.get("badges"),
        "objectives": active.get("objectives"),
        "latest_milestone": latest_milestone,
        "stats": active.get("stats"),
        "vibe_session_id": session_id,
    }


def build_turn_prompt(
    *,
    server: str,
    state: dict[str, Any],
    first_turn: bool,
    game_label: str = "Pokemon Blue",
) -> str:
    collision = _as_dict(state.get("collision"))
    ascii_map = collision.get("ascii")
    if not ascii_map:
        battle = _as_dict(state.get("battle"))
        ascii_map = (
            "(in battle - no overworld map this turn)"
            if battle.get("in_battle")
            else "(no collision map available)"
        )

    first_turn_text = ""
    if first_turn:
        first_turn_text = (
            "This is the first turn for this game session. Before acting, set initial objectives "
            f"with POST {server}/objectives using exactly this JSON shape: "
            '{"objectives":[{"tier":"primary","text":"..."},'
            '{"tier":"secondary","text":"..."},'
            '{"tier":"tertiary","text":"..."}]}.\n\n'
        )

    map_name = _as_dict(state.get("map")).get("map_name")
    blue_route_text = ""
    if game_label.lower() == "pokemon blue" and map_name == "Red's House 2F":
        blue_route_text = (
            "Pokemon Blue route anchor: the downstairs transition is at the lower edge of "
            "this room, around world position x=7, y=6. From the fresh-start position, "
            "move down toward it. Do not search left based on a remembered Red layout.\n\n"
        )
    elif game_label.lower() == "pokemon blue" and map_name == "Pallet Town":
        blue_route_text = (
            "Pokemon Blue route anchor: Oak's Lab is the large building south of both "
            "houses, near the lower center of Pallet Town. Do not identify a building from "
            "Red-layout memory alone.\n\n"
        )

    return f"""You are Mistral Vibe playing {game_label} live.
The upstream Gen I memory adapter may label the game as Pokemon Red; that label is an
implementation detail. Trust the
configured game name, current coordinates, collision map, and dialog state. Do not
infer building layouts from memory. Take ONE short turn, then stop and reply with a
concise summary. The only service you may call is the loopback game server at {server}.

{first_turn_text}{blue_route_text}For this turn:
1. Use the structured state and ASCII map below as the source of truth. The
   player is centered at E5. `.` is walkable, `#` is blocked,
   and `@` is the player. Never route through `#`.
2. Use the bash tool only for curl calls to this server, in this order:
   - POST {server}/event with JSON {{"type":"reasoning","text":"..."}}
   - POST {server}/event with JSON {{"type":"decision","text":"..."}}
   - POST {server}/action with JSON {{"actions":["walk_down","press_a"]}}
   Every POST must set Content-Type: application/json.
3. Take only 1-4 game actions. Valid actions include press_a, press_b, press_start,
   press_select, walk_up, walk_down, walk_left, walk_right, hold_a_30, wait_60,
   and a_until_dialog_end.
4. On a real milestone, POST /event with type key_moment plus description and
   category. Update /objectives only when the goals materially change.

Do not edit files, use git, inspect credentials, install anything, or contact any
host other than {server}.

CURRENT STATE:
{json.dumps(compact_state(state), indent=2, ensure_ascii=False)}

WALKABILITY MAP (player is @ at E5):
{ascii_map}
"""


class SessionStore:
    """Persist one Vibe session id per pokemon-agent game id."""

    def __init__(self, path: Path):
        self.path = path

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "games": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DriverError(f"Cannot read Vibe session map {self.path}: {exc}") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("games"), dict):
            raise DriverError(f"Cannot read Vibe session map {self.path}: invalid schema")
        return payload

    def get(self, game_id: str) -> str | None:
        record = self._read()["games"].get(game_id)
        if isinstance(record, dict) and isinstance(record.get("session_id"), str):
            return record["session_id"]
        return None

    def set(self, game_id: str, session_id: str) -> None:
        payload = self._read()
        payload["version"] = 1
        payload["games"][game_id] = {
            "session_id": session_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(self.path)


def extract_session_id(payload: Any) -> str:
    entries = payload.get("history") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise DriverError("Vibe JSON output did not contain a history list")

    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        session_id = entry.get("sessionId") or entry.get("session_id")
        if (
            entry.get("type") == "message"
            and entry.get("role") == "assistant"
            and isinstance(session_id, str)
            and session_id
        ):
            return session_id
    for entry in reversed(entries):
        if isinstance(entry, dict):
            session_id = entry.get("sessionId") or entry.get("session_id")
            if isinstance(session_id, str) and session_id:
                return session_id
    raise DriverError("Vibe JSON output did not expose a session id")


def parse_vibe_output(output: str) -> Any:
    """Accept Vibe's buffered JSON and newline-delimited streaming output."""
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        entries: list[Any] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                sample = line.strip()[-500:]
                raise DriverError(f"Vibe returned invalid streaming JSON: {sample}") from exc
        if entries:
            return entries
        raise DriverError("Vibe returned no JSON output")


class VibeCLI:
    def __init__(
        self,
        *,
        binary: str,
        workdir: Path,
        model: str | None,
        max_turns: int,
        max_price: float | None,
        timeout: int,
    ):
        self.binary = binary
        self.workdir = workdir.resolve()
        self.model = model
        self.max_turns = max_turns
        self.max_price = max_price
        self.timeout = timeout

    def command(self, prompt: str, session_id: str | None) -> list[str]:
        command = [
            self.binary,
            "--workdir",
            str(self.workdir),
            "--trust",
            "--agent",
            "pokemon-player",
            "--auto-approve",
            "--experimental-harness",
            "--enabled-tools",
            "bash",
            "--max-turns",
            str(self.max_turns),
            "--output",
            "streaming",
        ]
        if self.max_price is not None:
            command.extend(["--max-price", str(self.max_price)])
        if session_id:
            command.extend(["--resume", session_id])
        command.extend(["-p", prompt])
        return command

    def run(self, prompt: str, session_id: str | None = None) -> str:
        environment = os.environ.copy()
        for name in (
            "POKEMON_DASHBOARD_USERNAME",
            "POKEMON_DASHBOARD_PASSWORD",
            "KOYEB_ORGANIZATION_ID",
            "KOYEB_APP_NAME",
            "KOYEB_SERVICE_NAME",
            "POKEMON_EXPECTED_GAME_ID",
            "POKEMON_EXPECTED_SESSION_ID",
            "POKEMON_EXPECTED_STATE_SHA256",
        ):
            environment.pop(name, None)
        if self.model:
            environment["VIBE_ACTIVE_MODEL"] = self.model
        # Unified Harness 2.25.8 does not always close a multi-tool
        # programmatic turn when stdin is not a terminal. Give only Vibe a
        # private PTY while retaining captured stdout/stderr for JSON parsing.
        master_fd, slave_fd = pty.openpty()
        try:
            result = subprocess.run(
                self.command(prompt, session_id),
                cwd=self.workdir,
                env=environment,
                stdin=slave_fd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise DriverError(f"Vibe executable not found: {self.binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise DriverError(f"Vibe turn timed out after {self.timeout}s") from exc
        finally:
            os.close(master_fd)
            os.close(slave_fd)

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error").strip()[-1200:]
            raise DriverError(f"Vibe exited with status {result.returncode}: {detail}")
        payload = parse_vibe_output(result.stdout)
        return extract_session_id(payload)


def _validate_loopback_server(server: str) -> str:
    parsed = urlsplit(server.rstrip("/"))
    if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
        raise DriverError("Pokemon server must be an http:// loopback URL")
    try:
        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        loopback = parsed.hostname.lower() == "localhost"
    if not loopback:
        raise DriverError("Pokemon server must use localhost or a loopback IP")
    return server.rstrip("/")


def _validate_bind_host(host: str, *, cloud: bool) -> None:
    """Keep local launches private while allowing Koyeb's wildcard bind."""
    candidate = host.strip("[]")
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        if candidate.lower() == "localhost":
            return
        raise DriverError("Pokemon server bind host must be loopback") from None
    if address.is_loopback:
        return
    if cloud and address.is_unspecified:
        return
    raise DriverError("Pokemon server bind host must be loopback unless --cloud is enabled")


def _internal_server_url(host: str, port: int) -> str:
    candidate = host.strip("[]")
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        address = None
    if address is not None and address.is_unspecified:
        candidate = "127.0.0.1"
    if ":" in candidate:
        candidate = f"[{candidate}]"
    return f"http://{candidate}:{port}"


class PokemonClient:
    def __init__(self, server: str, timeout: float = 15):
        self.server = _validate_loopback_server(server)
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, object] | None = None) -> bytes:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.server + path,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
            method="POST" if body is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            detail = exc.read(800).decode("utf-8", errors="replace")
            raise DriverError(f"Pokemon API {path} returned HTTP {exc.code}: {detail}") from exc
        except (OSError, URLError) as exc:
            raise DriverError(f"Cannot reach Pokemon API {self.server}{path}: {exc}") from exc
        if len(data) > MAX_RESPONSE_BYTES:
            raise DriverError(f"Pokemon API response for {path} exceeded 10 MiB")
        return data

    def get_json(self, path: str) -> dict[str, Any]:
        try:
            payload = json.loads(self._request(path))
        except json.JSONDecodeError as exc:
            raise DriverError(f"Pokemon API {path} returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise DriverError(f"Pokemon API {path} did not return an object")
        return payload

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, Any]:
        try:
            result = json.loads(self._request(path, payload))
        except json.JSONDecodeError as exc:
            raise DriverError(f"Pokemon API {path} returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise DriverError(f"Pokemon API {path} did not return an object")
        return result

    def download(self, path: str, target: Path) -> None:
        data = self._request(path)
        if not data.startswith(PNG_SIGNATURE):
            raise DriverError(f"Pokemon API {path} did not return a PNG screenshot")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)


class VibeDriver:
    def __init__(
        self,
        *,
        client: Any,
        vibe: Any,
        sessions: SessionStore,
        game_label: str = "Pokemon Blue",
        turn_delay: float = 1.5,
        save_every: int = 20,
    ):
        self.client = client
        self.vibe = vibe
        self.sessions = sessions
        self.game_label = game_label
        self.turn_delay = turn_delay
        self.save_every = save_every
        self.game_id: str | None = None
        self.session_id: str | None = None
        self.turn = 0

    def _event(self, **payload: object) -> None:
        try:
            self.client.post_json("/event", payload)
        except DriverError:
            pass

    def sync_active_game(self) -> bool:
        active = self.client.get_json("/games/current").get("active")
        if not isinstance(active, dict) or not isinstance(active.get("id"), str):
            self.game_id = None
            self.session_id = None
            return False
        game_id = active["id"]
        if game_id != self.game_id:
            self.game_id = game_id
            self.session_id = self.sessions.get(game_id)
            self.turn = 0
            state = self.session_id or "new session"
            print(f"[vibe-driver] active game: {game_id} ({state})", flush=True)
        return True

    def step(self) -> None:
        if not self.game_id:
            raise DriverError("No active game. Create or load one from the dashboard first.")
        state = self.client.get_json("/state")
        previous_session = self.session_id
        prompt = build_turn_prompt(
            server=self.client.server,
            state=state,
            first_turn=previous_session is None,
            game_label=self.game_label,
        )
        self.session_id = self.vibe.run(prompt, session_id=previous_session)
        self.sessions.set(self.game_id, self.session_id)
        if previous_session is None:
            self._event(
                type="key_moment",
                description="Mistral Vibe session started",
                category="milestone",
            )
        self.turn += 1
        if self.save_every > 0 and self.turn % self.save_every == 0:
            self.client.post_json("/save", {"name": "vibe-autosave"})

    def run_once(self) -> None:
        if not self.sync_active_game():
            raise DriverError("No active game. Create or load one from the dashboard first.")
        self.step()

    def run_forever(self) -> None:
        print(f"[vibe-driver] Vibe autopilot connected to {self.client.server}", flush=True)
        print("[vibe-driver] waiting for a game and dashboard START", flush=True)
        self._event(
            type="alert",
            text="Mistral Vibe online - create/load a game, then press START.",
        )
        last_idle: str | None = None
        error_delay = 3.0
        while True:
            try:
                control = self.client.get_json("/control").get("state", "stopped")
                if control != "running":
                    if control != last_idle:
                        print(f"[vibe-driver] {control} - idling", flush=True)
                    last_idle = str(control)
                    time.sleep(1.5)
                    continue
                last_idle = None
                if not self.sync_active_game():
                    print("[vibe-driver] running but no active game", flush=True)
                    time.sleep(2)
                    continue
                self.step()
                error_delay = 3.0
                time.sleep(self.turn_delay)
            except DriverError as exc:
                print(f"[vibe-driver] {exc}", file=sys.stderr, flush=True)
                self._event(type="alert", text=str(exc)[:500])
                time.sleep(error_delay)
                error_delay = min(error_delay * 2, 60.0)


def prepare_vibe_dashboard(source: Path, target: Path) -> None:
    """Copy the pinned upstream assets and replace Hermes-only presentation."""
    if not source.is_dir():
        raise DriverError(f"Upstream dashboard assets are missing: {source}")
    shutil.copytree(source, target, dirs_exist_ok=True)
    for path in target.rglob("*"):
        if not path.is_file() or path.suffix not in {".html", ".js", ".css"}:
            continue
        text = path.read_text(encoding="utf-8")
        text = text.replace(
            "brain '+(active.hermes_session_id?'linked':'pending')",
            "brain Vibe linked'",
        )
        text = text.replace("HERMES", "MISTRAL VIBE")
        text = text.replace("Hermes", "Mistral Vibe")
        path.write_text(text, encoding="utf-8")


def _mount_vibe_dashboard(app: Any, data_dir: Path) -> None:
    @app.on_event("startup")
    async def mount_vibe_dashboard() -> None:
        from fastapi.staticfiles import StaticFiles
        from pokemon_agent import dashboard as upstream_dashboard

        source = Path(upstream_dashboard.__file__).resolve().parent / "static"
        target = data_dir / "runtime" / "dashboard"
        prepare_vibe_dashboard(source, target)
        app.router.routes[:] = [
            route
            for route in app.router.routes
            if not (getattr(route, "path", None) == "/dashboard")
        ]
        app.mount(
            "/dashboard",
            StaticFiles(directory=str(target), html=True),
            name="dashboard",
        )
        print("[server] Mistral Vibe dashboard mounted at /dashboard", flush=True)


def _require_rom(path: Path) -> Path:
    resolved = resolve_project_path(path)
    if not resolved.is_file():
        raise DriverError(
            f"ROM not found: {resolved}. Supply your own legally obtained .gb/.gbc ROM."
        )
    if resolved.suffix.lower() not in {".gb", ".gbc"}:
        raise DriverError("This configured instance supports Game Boy .gb/.gbc Pokemon ROMs")
    return resolved


def serve_game(*, rom: Path, host: str, port: int, data_dir: Path, cloud: bool = False) -> None:
    _validate_bind_host(host, cloud=cloud)
    dashboard_username = os.environ.get("POKEMON_DASHBOARD_USERNAME", "").strip()
    dashboard_password = os.environ.get("POKEMON_DASHBOARD_PASSWORD", "")
    if cloud and (not dashboard_username or not dashboard_password.strip()):
        raise DriverError(
            "POKEMON_DASHBOARD_USERNAME and POKEMON_DASHBOARD_PASSWORD are required in cloud mode"
        )
    rom = _require_rom(rom)
    data_dir = resolve_project_path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    import uvicorn
    from pokemon_agent.server import GameConfig, app, configure

    configure(
        GameConfig(
            rom_path=str(rom),
            game_type="red",
            port=port,
            data_dir=str(data_dir),
        )
    )
    _mount_vibe_dashboard(app, data_dir)
    served_app = (
        BasicAuthGuard(app, username=dashboard_username, password=dashboard_password)
        if cloud
        else app
    )
    print(f"[server] Upstream pokemon-agent commit: {UPSTREAM_COMMIT}", flush=True)
    print(f"[server] Dashboard: http://{host}:{port}/dashboard", flush=True)
    if cloud:
        print("[server] Public game routes require Basic Auth; /health remains public", flush=True)
    uvicorn.run(served_app, host=host, port=port, log_level="info")


def _parse_version(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", text)
    return tuple(int(part) for part in match.groups()) if match else None


def check_vibe(binary: str) -> tuple[str, tuple[int, int, int]]:
    resolved = shutil.which(binary)
    if not resolved:
        raise DriverError(f"Vibe executable not found on PATH: {binary}")
    result = subprocess.run(
        [resolved, "--version"], capture_output=True, text=True, timeout=15, check=False
    )
    output = (result.stdout or result.stderr).strip()
    version = _parse_version(output)
    if result.returncode != 0 or version is None:
        raise DriverError(f"Cannot determine Vibe version from: {output}")
    if version < MIN_VIBE_VERSION:
        minimum = ".".join(str(part) for part in MIN_VIBE_VERSION)
        raise DriverError(f"Vibe {minimum}+ is required; found {'.'.join(map(str, version))}")
    return resolved, version


def _driver_from_args(args: argparse.Namespace) -> VibeDriver:
    root = project_root()
    data_dir = resolve_project_path(args.data_dir)
    binary, _ = check_vibe(args.vibe_bin)
    client = PokemonClient(args.server)
    vibe = VibeCLI(
        binary=binary,
        workdir=root,
        model=args.model or None,
        max_turns=args.max_turns,
        max_price=args.max_price,
        timeout=args.turn_timeout,
    )
    return VibeDriver(
        client=client,
        vibe=vibe,
        sessions=SessionStore(data_dir / "vibe-sessions.json"),
        game_label=args.game_label,
        turn_delay=args.turn_delay,
        save_every=args.save_every,
    )


def _wait_for_server(client: PokemonClient, process: subprocess.Popen[Any]) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise DriverError(f"Pokemon server exited early with status {process.returncode}")
        try:
            health = client.get_json("/health")
            if health.get("status") in {"ok", "healthy"}:
                return
        except DriverError:
            pass
        time.sleep(0.25)
    raise DriverError("Pokemon server did not become healthy within 60 seconds")


def _bootstrap_cloud_game(
    client: PokemonClient,
    *,
    data_dir: Path,
    seed_state: str,
    game_name: str,
    auto_start: bool,
) -> str:
    games = client.get_json("/games").get("games")
    if not isinstance(games, list):
        raise DriverError("Pokemon API /games returned an invalid game list")

    if games:
        game = games[0]
        if not isinstance(game, dict) or not isinstance(game.get("id"), str):
            raise DriverError("Pokemon API /games returned an invalid game record")
        game_id = game["id"]
        client.post_json(f"/games/{quote(game_id, safe='')}/load", {})
        print(f"[cloud] resumed persisted game {game_id}", flush=True)
    else:
        seed_path = data_dir / "saves" / f"{seed_state}.state"
        if not seed_path.is_file():
            raise DriverError(f"Cloud seed state is missing: {seed_path}")
        created = client.post_json("/games/new", {"name": game_name})
        game = created.get("game")
        if not isinstance(game, dict) or not isinstance(game.get("id"), str):
            raise DriverError("Pokemon API did not return the new cloud game id")
        game_id = game["id"]
        client.post_json("/load", {"name": seed_state})
        client.post_json("/save", {"name": seed_state})
        print(f"[cloud] created game {game_id} from {seed_state}", flush=True)

    if auto_start:
        client.post_json("/control", {"state": "running"})
        print("[cloud] autopilot started", flush=True)
    return game_id


def start_instance(args: argparse.Namespace) -> None:
    root = project_root()
    rom = _require_rom(Path(args.rom))
    data_dir = resolve_project_path(args.data_dir)
    check_vibe(args.vibe_bin)
    args.server = _internal_server_url(args.host, args.port)
    command = [
        sys.executable,
        "-m",
        "pokemon_vibe.app",
        "serve",
        "--rom",
        str(rom),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--data-dir",
        str(data_dir),
    ]
    command.append("--cloud" if args.cloud else "--no-cloud")
    server = subprocess.Popen(command, cwd=root, start_new_session=True)
    try:
        client = PokemonClient(args.server)
        _wait_for_server(client, server)
        if args.cloud:
            _bootstrap_cloud_game(
                client,
                data_dir=data_dir,
                seed_state=args.seed_state,
                game_name=args.game_name,
                auto_start=args.auto_start,
            )
        print(f"[pokemon-vibe] open {args.server}/dashboard", flush=True)
        if args.open_dashboard:
            webbrowser.open_new_tab(f"{args.server}/dashboard")
        _driver_from_args(args).run_forever()
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise DriverError(f"{name} must be an integer") from exc


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise DriverError(f"{name} must be a number") from exc


def _env_optional_float(name: str) -> float | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise DriverError(f"{name} must be a number") from exc


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise DriverError(f"{name} must be true or false")


def build_parser() -> argparse.ArgumentParser:
    host = os.environ.get("POKEMON_HOST", "127.0.0.1")
    port = _env_int("POKEMON_PORT", 8765)
    data_dir = os.environ.get("POKEMON_DATA_DIR", str(project_root() / ".data"))
    rom = os.environ.get("POKEMON_ROM", str(project_root() / "roms" / "pokemon-blue.gb"))
    server = os.environ.get("POKEMON_SERVER", _internal_server_url(host, port))
    cloud = _env_bool("POKEMON_CLOUD", False)

    parser = argparse.ArgumentParser(
        prog="pokemon-vibe",
        description="Run pokemon-agent locally with Mistral Vibe as its autonomous player.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="run only the local game server")
    serve_parser.add_argument("--rom", default=rom)
    serve_parser.add_argument("--host", default=host)
    serve_parser.add_argument("--port", type=int, default=port)
    serve_parser.add_argument("--data-dir", default=data_dir)
    serve_parser.add_argument("--cloud", action=argparse.BooleanOptionalAction, default=cloud)

    def add_driver_options(target: argparse.ArgumentParser, *, include_server: bool = True) -> None:
        if include_server:
            target.add_argument("--server", default=server)
        target.add_argument("--data-dir", default=data_dir)
        target.add_argument("--vibe-bin", default=os.environ.get("POKEMON_VIBE_BIN", "vibe"))
        target.add_argument("--model", default=os.environ.get("POKEMON_VIBE_MODEL", ""))
        target.add_argument(
            "--game-label", default=os.environ.get("POKEMON_GAME_LABEL", "Pokemon Blue")
        )
        target.add_argument("--max-turns", type=int, default=_env_int("POKEMON_VIBE_MAX_TURNS", 8))
        target.add_argument(
            "--max-price",
            type=float,
            default=_env_optional_float("POKEMON_VIBE_MAX_PRICE"),
        )
        target.add_argument(
            "--turn-timeout", type=int, default=_env_int("POKEMON_VIBE_TURN_TIMEOUT", 900)
        )
        target.add_argument(
            "--turn-delay", type=float, default=_env_float("POKEMON_TURN_DELAY", 1.5)
        )
        target.add_argument(
            "--save-every", type=int, default=_env_int("POKEMON_AUTOSAVE_EVERY", 20)
        )

    play_parser = subparsers.add_parser("play", help="run only the Vibe autopilot")
    add_driver_options(play_parser)
    play_parser.add_argument("--once", action="store_true", help="take one turn and exit")

    start_parser = subparsers.add_parser("start", help="run server and Vibe autopilot together")
    start_parser.add_argument("--rom", default=rom)
    start_parser.add_argument("--host", default=host)
    start_parser.add_argument("--port", type=int, default=port)
    start_parser.add_argument("--cloud", action=argparse.BooleanOptionalAction, default=cloud)
    start_parser.add_argument(
        "--seed-state", default=os.environ.get("POKEMON_SEED_STATE", "cloud-handoff")
    )
    start_parser.add_argument(
        "--game-name",
        default=os.environ.get("POKEMON_GAME_NAME", "Pokemon Blue"),
    )
    start_parser.add_argument(
        "--auto-start",
        action=argparse.BooleanOptionalAction,
        default=_env_bool("POKEMON_AUTO_START", False),
    )
    start_parser.add_argument(
        "--open-dashboard",
        action=argparse.BooleanOptionalAction,
        default=_env_bool("POKEMON_OPEN_DASHBOARD", True),
    )
    add_driver_options(start_parser, include_server=False)

    doctor_parser = subparsers.add_parser("doctor", help="check local prerequisites")
    doctor_parser.add_argument("--rom", default=rom)
    doctor_parser.add_argument("--vibe-bin", default=os.environ.get("POKEMON_VIBE_BIN", "vibe"))

    internal_server = _internal_server_url(host, port)
    status_parser = subparsers.add_parser("status", help="print current game progress as JSON")
    status_parser.add_argument(
        "--server", default=os.environ.get("POKEMON_SERVER", internal_server)
    )
    status_parser.add_argument("--data-dir", default=data_dir)
    status_parser.add_argument(
        "--game-label", default=os.environ.get("POKEMON_GAME_LABEL", "Pokemon Blue")
    )

    transcript_parser = subparsers.add_parser(
        "transcript", help="print recent raw Vibe journal lines"
    )
    transcript_parser.add_argument(
        "--server", default=os.environ.get("POKEMON_SERVER", internal_server)
    )
    transcript_parser.add_argument("--data-dir", default=data_dir)
    transcript_parser.add_argument("--lines", type=int, default=100)

    return parser


def run_doctor(args: argparse.Namespace) -> None:
    binary, version = check_vibe(args.vibe_bin)
    print(f"[ok] Vibe {'.'.join(map(str, version))}: {binary}")
    agent_file = project_root() / ".vibe" / "agents" / "pokemon-player.toml"
    if not agent_file.is_file():
        raise DriverError(f"Vibe agent profile missing: {agent_file}")
    print(f"[ok] Vibe agent profile: {agent_file}")
    curl = shutil.which("curl")
    if not curl:
        raise DriverError("curl is required by the Vibe player agent")
    print(f"[ok] curl: {curl}")
    try:
        import pokemon_agent
    except ImportError as exc:
        raise DriverError("pokemon-agent is not installed; run `uv sync --extra dev`") from exc
    print(f"[ok] pokemon-agent import: {Path(pokemon_agent.__file__).resolve()}")
    rom = _require_rom(Path(args.rom))
    print(f"[ok] ROM: {rom}")
    print("[note] Vibe credentials/model are exercised only when a play turn starts.")


def _active_game(client: PokemonClient) -> tuple[dict[str, Any], str]:
    current = client.get_json("/games/current")
    active = _as_dict(current.get("active"))
    game_id = active.get("id")
    if not isinstance(game_id, str) or not game_id:
        raise DriverError("No active game")
    return current, game_id


def _read_game_manifest(data_dir: Path, game_id: str) -> dict[str, Any]:
    games_dir = (resolve_project_path(data_dir) / "games").resolve()
    manifest_path = (games_dir / game_id / "manifest.json").resolve()
    if games_dir not in manifest_path.parents:
        raise DriverError("Active game id resolves outside the game data directory")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriverError(f"Cannot read active game manifest {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise DriverError(f"Cannot read active game manifest {manifest_path}: invalid schema")
    return manifest


def run_status(args: argparse.Namespace) -> None:
    client = PokemonClient(args.server)
    current, game_id = _active_game(client)
    data_dir = resolve_project_path(args.data_dir)
    session_id = SessionStore(data_dir / "vibe-sessions.json").get(game_id)
    report = build_status_report(
        current=current,
        control=client.get_json("/control"),
        state=client.get_json("/state"),
        manifest=_read_game_manifest(data_dir, game_id),
        session_id=session_id,
        game_label=args.game_label,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


def run_transcript(args: argparse.Namespace) -> None:
    if args.lines < 1:
        raise DriverError("--lines must be at least 1")
    client = PokemonClient(args.server)
    _, game_id = _active_game(client)
    session_id = SessionStore(resolve_project_path(args.data_dir) / "vibe-sessions.json").get(
        game_id
    )
    if session_id is None:
        raise DriverError(f"No Vibe session is mapped to game {game_id}")
    vibe_home = Path(os.environ.get("VIBE_HOME", "~/.vibe")).expanduser().resolve()
    journal_dir = vibe_home / "logs" / "session" / "unified" / session_id / "journal"
    journals = sorted(path for path in journal_dir.glob("*.jsonl") if path.stat().st_size)
    if not journals:
        raise DriverError(f"No non-empty Vibe journal found for session {session_id}")
    with journals[-1].open(encoding="utf-8", errors="replace") as stream:
        sys.stdout.writelines(deque(stream, maxlen=args.lines))


def _handle_termination(_signum: int, _frame: Any) -> None:
    raise KeyboardInterrupt


def main(argv: Sequence[str] | None = None) -> int:
    from dotenv import load_dotenv

    load_dotenv(project_root() / ".env", override=False)
    signal.signal(signal.SIGTERM, _handle_termination)
    try:
        args = build_parser().parse_args(argv)
        if args.command == "serve":
            serve_game(
                rom=Path(args.rom),
                host=args.host,
                port=args.port,
                data_dir=Path(args.data_dir),
                cloud=args.cloud,
            )
        elif args.command == "play":
            driver = _driver_from_args(args)
            driver.run_once() if args.once else driver.run_forever()
        elif args.command == "start":
            start_instance(args)
        elif args.command == "doctor":
            run_doctor(args)
        elif args.command == "status":
            run_status(args)
        elif args.command == "transcript":
            run_transcript(args)
        return 0
    except KeyboardInterrupt:
        print("\n[pokemon-vibe] stopped", file=sys.stderr)
        return 130
    except DriverError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
