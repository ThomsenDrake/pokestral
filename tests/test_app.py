from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pokemon_vibe.app import (
    BasicAuthGuard,
    DriverError,
    SessionStore,
    VibeCLI,
    VibeDriver,
    _bootstrap_cloud_game,
    _internal_server_url,
    _read_game_manifest,
    _validate_bind_host,
    build_parser,
    build_status_report,
    build_turn_prompt,
    check_vibe,
    compact_state,
    extract_session_id,
    parse_vibe_output,
    prepare_vibe_dashboard,
    resolve_project_path,
    serve_game,
    start_instance,
)

SAMPLE_STATE = {
    "metadata": {"game": "Pokemon Red", "frame_count": 123},
    "map": {"map_name": "PALLET TOWN"},
    "player": {
        "name": "RED",
        "money": 3000,
        "badges": ["Boulder"],
        "position": {"x": 7, "y": 5},
        "facing": "down",
    },
    "party": [
        {
            "nickname": "BULBASAUR",
            "species": "Bulbasaur",
            "level": 5,
            "hp": 19,
            "max_hp": 19,
            "status": None,
            "types": ["Grass", "Poison"],
            "moves": [{"name": "Tackle"}, "Growl"],
        }
    ],
    "battle": {"in_battle": False},
    "dialog": {"active": False},
    "collision": {"player_cell": "E5", "ascii": "###\n#@.\n###"},
}


class CompactStateTests(unittest.TestCase):
    def test_compacts_state_without_losing_decision_fields(self) -> None:
        result = compact_state(SAMPLE_STATE)

        self.assertEqual(result["game"], "Pokemon Red")
        self.assertEqual(result["map"], "PALLET TOWN")
        self.assertEqual(result["cell"], "E5")
        self.assertEqual(result["badges"], ["Boulder"])
        self.assertEqual(result["party"][0]["moves"], ["Tackle", "Growl"])
        self.assertIsNone(result["enemy"])

    def test_tolerates_missing_sections(self) -> None:
        result = compact_state({"player": None, "party": None, "battle": None})

        self.assertEqual(result["party"], [])
        self.assertIsNone(result["enemy"])
        self.assertIsNone(result["map"])

    def test_builds_operator_progress_report(self) -> None:
        report = build_status_report(
            current={
                "active": {
                    "id": "game-a",
                    "name": "Arthur",
                    "objectives": [{"tier": "primary", "text": "Leave home"}],
                    "stats": {"turns": 3, "actions": 7, "saves": 3},
                }
            },
            control={"state": "running"},
            state=SAMPLE_STATE,
            manifest={"milestones": [{"description": "Named Arthur"}]},
            session_id="session-a",
            game_label="Pokemon Yellow",
        )

        self.assertEqual(report["control"], "running")
        self.assertEqual(report["game"]["configured_as"], "Pokemon Yellow")
        self.assertEqual(report["game"]["adapter_report"], "Pokemon Red")
        self.assertEqual(report["player"], "RED")
        self.assertEqual(report["stats"]["turns"], 3)
        self.assertEqual(report["latest_milestone"], {"description": "Named Arthur"})
        self.assertEqual(report["vibe_session_id"], "session-a")


class PromptTests(unittest.TestCase):
    def test_prompt_uses_structured_state_and_limits_the_turn(self) -> None:
        prompt = build_turn_prompt(
            server="http://127.0.0.1:8765",
            state=SAMPLE_STATE,
            first_turn=True,
        )

        self.assertNotIn("@/", prompt)
        self.assertIn("Mistral Vibe", prompt)
        self.assertIn("playing Pokemon Blue live", prompt)
        self.assertIn("may label the game as Pokemon Red", prompt)
        self.assertIn("Do not\ninfer building layouts from memory", prompt)
        self.assertIn("POST http://127.0.0.1:8765/action", prompt)
        self.assertIn("1-4 game actions", prompt)
        self.assertIn("set initial objectives", prompt)
        self.assertIn('"objectives":[{"tier":"primary","text":"..."}', prompt)
        self.assertIn('"map": "PALLET TOWN"', prompt)

    def test_prompt_includes_the_blue_house_route_anchor(self) -> None:
        state = dict(SAMPLE_STATE)
        state["map"] = {"map_name": "Red's House 2F"}

        prompt = build_turn_prompt(
            server="http://127.0.0.1:8765",
            state=state,
            first_turn=False,
        )

        self.assertIn("downstairs transition is at the lower edge", prompt)
        self.assertIn("x=7, y=6", prompt)
        self.assertIn("Do not search left", prompt)


class SessionStoreTests(unittest.TestCase):
    def test_persists_vibe_sessions_per_game_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vibe-sessions.json"
            store = SessionStore(path)

            self.assertIsNone(store.get("game-a"))
            store.set("game-a", "session-a")
            store.set("game-b", "session-b")

            reloaded = SessionStore(path)
            self.assertEqual(reloaded.get("game-a"), "session-a")
            self.assertEqual(reloaded.get("game-b"), "session-b")
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_refuses_to_overwrite_a_corrupt_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vibe-sessions.json"
            path.write_text("not json", encoding="utf-8")

            with self.assertRaisesRegex(DriverError, "Cannot read Vibe session map"):
                SessionStore(path).set("game-a", "session-a")


class VibeCLITests(unittest.TestCase):
    def test_extracts_latest_assistant_session(self) -> None:
        payload = [
            {"type": "message", "role": "assistant", "sessionId": "old"},
            {"type": "effect", "sessionId": "new"},
            {"type": "message", "role": "assistant", "sessionId": "new"},
        ]

        self.assertEqual(extract_session_id(payload), "new")

    def test_parses_streaming_json_lines(self) -> None:
        output = "\n".join(
            [
                json.dumps({"type": "message", "role": "user", "sessionId": "session-a"}),
                json.dumps({"type": "effect", "sessionId": "session-a"}),
            ]
        )

        self.assertEqual(extract_session_id(parse_vibe_output(output)), "session-a")

    def test_builds_a_bounded_resumable_vibe_invocation(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                [{"type": "message", "role": "assistant", "sessionId": "session-new"}]
            ),
            stderr="",
        )
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("pokemon_vibe.app.subprocess.run", return_value=completed) as run,
            patch.dict(
                os.environ,
                {
                    "MISTRAL_API_KEY": "provider-secret",
                    "POKEMON_DASHBOARD_USERNAME": "private-user",
                    "POKEMON_DASHBOARD_PASSWORD": "private-password",
                    "KOYEB_ORGANIZATION_ID": "private-organization",
                },
                clear=False,
            ),
        ):
            cli = VibeCLI(
                binary="/opt/bin/vibe",
                workdir=Path(tmp),
                model="configured-model",
                max_turns=7,
                max_price=0.2,
                timeout=30,
            )
            session_id = cli.run("take a turn", session_id="session-old")

        self.assertEqual(session_id, "session-new")
        command = run.call_args.args[0]
        self.assertEqual(command[0], "/opt/bin/vibe")
        self.assertIn("pokemon-player", command)
        self.assertIn("--auto-approve", command)
        self.assertIn("--experimental-harness", command)
        self.assertEqual(command[command.index("--enabled-tools") + 1], "bash")
        self.assertEqual(command[command.index("--resume") + 1], "session-old")
        self.assertEqual(command[command.index("--max-turns") + 1], "7")
        self.assertEqual(command[command.index("--max-price") + 1], "0.2")
        self.assertEqual(command[command.index("--output") + 1], "streaming")
        environment = run.call_args.kwargs["env"]
        self.assertEqual(environment["VIBE_ACTIVE_MODEL"], "configured-model")
        self.assertEqual(environment["MISTRAL_API_KEY"], "provider-secret")
        self.assertNotIn("POKEMON_DASHBOARD_USERNAME", environment)
        self.assertNotIn("POKEMON_DASHBOARD_PASSWORD", environment)
        self.assertNotIn("KOYEB_ORGANIZATION_ID", environment)

    def test_omits_price_limit_when_unbounded(self) -> None:
        cli = VibeCLI(
            binary="/opt/bin/vibe",
            workdir=Path("/tmp"),
            model=None,
            max_turns=8,
            max_price=None,
            timeout=900,
        )

        self.assertNotIn("--max-price", cli.command("take a turn", session_id=None))


class ConfigurationTests(unittest.TestCase):
    def test_start_parser_has_one_coherent_local_server(self) -> None:
        args = build_parser().parse_args(["start", "--host", "127.0.0.2", "--port", "9000"])

        self.assertEqual(args.host, "127.0.0.2")
        self.assertEqual(args.port, 9000)
        self.assertFalse(hasattr(args, "server"))
        self.assertTrue(args.open_dashboard)

        no_open = build_parser().parse_args(["start", "--no-open-dashboard"])
        self.assertFalse(no_open.open_dashboard)

    def test_cloud_mode_uses_loopback_for_the_internal_driver(self) -> None:
        self.assertEqual(_internal_server_url("0.0.0.0", 8000), "http://127.0.0.1:8000")
        _validate_bind_host("0.0.0.0", cloud=True)
        with self.assertRaisesRegex(DriverError, "unless --cloud"):
            _validate_bind_host("0.0.0.0", cloud=False)

        args = build_parser().parse_args(["start", "--cloud", "--host", "0.0.0.0", "--auto-start"])
        self.assertTrue(args.cloud)
        self.assertTrue(args.auto_start)
        self.assertEqual(args.game_label, "Pokemon Blue")
        self.assertEqual(args.max_turns, 8)
        self.assertIsNone(args.max_price)
        self.assertEqual(args.turn_timeout, 900)

    def test_play_defaults_to_loopback_when_bind_host_is_wildcard(self) -> None:
        with patch.dict(
            os.environ,
            {"POKEMON_HOST": "0.0.0.0", "POKEMON_PORT": "8000"},
            clear=True,
        ):
            args = build_parser().parse_args(["play", "--once"])

        self.assertEqual(args.server, "http://127.0.0.1:8000")

    def test_start_forwards_an_explicit_no_cloud_to_the_server(self) -> None:
        process = Mock()
        process.poll.return_value = None
        process.wait.return_value = 0
        driver = Mock()
        with (
            patch.dict(os.environ, {"POKEMON_CLOUD": "true"}, clear=True),
            patch("pokemon_vibe.app._require_rom", return_value=Path("/tmp/game.gb")),
            patch("pokemon_vibe.app.check_vibe"),
            patch("pokemon_vibe.app.subprocess.Popen", return_value=process) as popen,
            patch("pokemon_vibe.app._wait_for_server"),
            patch("pokemon_vibe.app._driver_from_args", return_value=driver),
        ):
            args = build_parser().parse_args(["start", "--no-cloud", "--no-open-dashboard"])
            start_instance(args)

        command = popen.call_args.args[0]
        self.assertIn("--no-cloud", command)
        self.assertNotIn("--cloud", command)

    def test_cloud_credentials_reject_whitespace_only_values(self) -> None:
        for username, password in (("   ", "password"), ("trainer", "\t")):
            with (
                self.subTest(username=username, password=password),
                patch.dict(
                    os.environ,
                    {
                        "POKEMON_DASHBOARD_USERNAME": username,
                        "POKEMON_DASHBOARD_PASSWORD": password,
                    },
                    clear=True,
                ),
            ):
                with self.assertRaisesRegex(DriverError, "required in cloud mode"):
                    serve_game(
                        rom=Path("missing.gb"),
                        host="0.0.0.0",
                        port=8000,
                        data_dir=Path(".data"),
                        cloud=True,
                    )

    def test_vibe_version_gate(self) -> None:
        too_old = subprocess.CompletedProcess([], 0, stdout="vibe 2.25.5", stderr="")
        current = subprocess.CompletedProcess([], 0, stdout="vibe 2.25.6", stderr="")
        with (
            patch("pokemon_vibe.app.shutil.which", return_value="/opt/bin/vibe"),
            patch("pokemon_vibe.app.subprocess.run", return_value=too_old),
        ):
            with self.assertRaisesRegex(DriverError, r"2\.25\.6\+"):
                check_vibe("vibe")
        with (
            patch("pokemon_vibe.app.shutil.which", return_value="/opt/bin/vibe"),
            patch("pokemon_vibe.app.subprocess.run", return_value=current),
        ):
            self.assertEqual(check_vibe("vibe"), ("/opt/bin/vibe", (2, 25, 6)))

    def test_reads_latest_milestone_from_the_persisted_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            game_dir = data_dir / "games" / "game-a"
            game_dir.mkdir(parents=True)
            (game_dir / "manifest.json").write_text(
                json.dumps({"milestones": [{"description": "Reached Pallet Town"}]}),
                encoding="utf-8",
            )

            manifest = _read_game_manifest(data_dir, "game-a")

        self.assertEqual(manifest["milestones"][0]["description"], "Reached Pallet Town")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(DriverError, "outside the game data directory"):
                _read_game_manifest(Path(tmp), "../outside")

    def test_relative_runtime_paths_are_rooted_at_the_project(self) -> None:
        self.assertEqual(
            resolve_project_path(".data"),
            (Path(__file__).resolve().parents[1] / ".data").resolve(),
        )


class BasicAuthGuardTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(
        self,
        *,
        request_type: str = "http",
        path: str = "/dashboard/",
        client: tuple[str, int] = ("203.0.113.10", 443),
        authorization: bytes | None = None,
    ) -> tuple[bool, list[dict[str, object]]]:
        called = False
        sent: list[dict[str, object]] = []

        async def inner(scope: object, receive: object, send: object) -> None:
            nonlocal called
            called = True

        async def receive() -> dict[str, object]:
            return {"type": "http.request"}

        async def send(message: dict[str, object]) -> None:
            sent.append(message)

        headers = [] if authorization is None else [(b"authorization", authorization)]
        guard = BasicAuthGuard(inner, username="trainer", password="secret")
        await guard(
            {"type": request_type, "path": path, "client": client, "headers": headers},
            receive,
            send,
        )
        return called, sent

    async def test_rejects_unauthenticated_public_http(self) -> None:
        called, sent = await self.invoke()

        self.assertFalse(called)
        self.assertEqual(sent[0]["status"], 401)
        self.assertIn(
            (b"www-authenticate", b'Basic realm="Pokemon dashboard", charset="UTF-8"'),
            sent[0]["headers"],
        )

    async def test_accepts_valid_basic_auth(self) -> None:
        token = base64.b64encode(b"trainer:secret")
        called, sent = await self.invoke(authorization=b"Basic " + token)

        self.assertTrue(called)
        self.assertEqual(sent, [])

    async def test_allows_loopback_control_and_public_health(self) -> None:
        loopback_called, _ = await self.invoke(client=("127.0.0.1", 50000))
        health_called, _ = await self.invoke(path="/health")

        self.assertTrue(loopback_called)
        self.assertTrue(health_called)

    async def test_rejects_unauthenticated_public_websocket(self) -> None:
        called, sent = await self.invoke(request_type="websocket", path="/ws")

        self.assertFalse(called)
        self.assertEqual(
            sent, [{"type": "websocket.close", "code": 4401, "reason": "Authentication required"}]
        )


class FakePokemonClient:
    def __init__(self, screenshot_bytes: bytes = b"\x89PNG\r\n\x1a\n") -> None:
        self.server = "http://127.0.0.1:8765"
        self.screenshot_bytes = screenshot_bytes
        self.posts: list[tuple[str, dict[str, object]]] = []

    def get_json(self, path: str) -> dict[str, object]:
        if path == "/games/current":
            return {"active": {"id": "game-a", "name": "Test run"}}
        if path == "/state":
            return SAMPLE_STATE
        raise AssertionError(f"unexpected path: {path}")

    def download(self, path: str, target: Path) -> None:
        self.last_download = path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.screenshot_bytes)

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.posts.append((path, payload))
        return {"success": True}


class FakeCloudClient:
    def __init__(self, games: list[dict[str, object]]) -> None:
        self.games = games
        self.posts: list[tuple[str, dict[str, object]]] = []

    def get_json(self, path: str) -> dict[str, object]:
        if path == "/games":
            return {"games": self.games}
        raise AssertionError(f"unexpected path: {path}")

    def post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        self.posts.append((path, payload))
        if path == "/games/new":
            return {"game": {"id": "game-new"}}
        return {"success": True}


class CloudBootstrapTests(unittest.TestCase):
    def test_resumes_latest_persisted_game_and_starts(self) -> None:
        client = FakeCloudClient([{"id": "game-existing"}])

        game_id = _bootstrap_cloud_game(
            client,
            data_dir=Path("/unused"),
            seed_state="cloud-handoff",
            game_name="Cloud run",
            auto_start=True,
        )

        self.assertEqual(game_id, "game-existing")
        self.assertEqual(
            client.posts,
            [
                ("/games/game-existing/load", {}),
                ("/control", {"state": "running"}),
            ],
        )

    def test_creates_game_from_seed_when_volume_has_no_games(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            saves = data_dir / "saves"
            saves.mkdir()
            (saves / "cloud-handoff.state").write_bytes(b"state")
            client = FakeCloudClient([])

            game_id = _bootstrap_cloud_game(
                client,
                data_dir=data_dir,
                seed_state="cloud-handoff",
                game_name="Cloud run",
                auto_start=False,
            )

        self.assertEqual(game_id, "game-new")
        self.assertEqual(
            client.posts,
            [
                ("/games/new", {"name": "Cloud run"}),
                ("/load", {"name": "cloud-handoff"}),
                ("/save", {"name": "cloud-handoff"}),
            ],
        )


class FakeVibe:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def run(self, prompt: str, session_id: str | None = None) -> str:
        self.calls.append((prompt, session_id))
        return "session-a"


class DriverTests(unittest.TestCase):
    def test_one_turn_binds_a_vibe_session_and_autosaves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = FakePokemonClient()
            vibe = FakeVibe()
            store = SessionStore(root / "vibe-sessions.json")
            driver = VibeDriver(
                client=client,
                vibe=vibe,
                sessions=store,
                save_every=1,
            )

            driver.run_once()

            self.assertEqual(store.get("game-a"), "session-a")
            self.assertIsNone(vibe.calls[0][1])
            self.assertIn("set initial objectives", vibe.calls[0][0])
            self.assertIn(("/save", {"name": "vibe-autosave"}), client.posts)
            self.assertIn(
                (
                    "/event",
                    {
                        "type": "key_moment",
                        "description": "Mistral Vibe session started",
                        "category": "milestone",
                    },
                ),
                client.posts,
            )

    def test_loaded_game_resumes_its_existing_vibe_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = SessionStore(root / "vibe-sessions.json")
            store.set("game-a", "session-existing")
            vibe = FakeVibe()
            driver = VibeDriver(
                client=FakePokemonClient(),
                vibe=vibe,
                sessions=store,
                save_every=20,
            )

            driver.run_once()

            self.assertEqual(vibe.calls[0][1], "session-existing")
            self.assertNotIn("set initial objectives", vibe.calls[0][0])

    def test_transient_error_retries_without_pausing_control(self) -> None:
        class RetryClient(FakePokemonClient):
            def __init__(self) -> None:
                super().__init__()
                self.control_reads = 0

            def get_json(self, path: str) -> dict[str, object]:
                if path == "/control":
                    self.control_reads += 1
                    if self.control_reads == 1:
                        return {"state": "running"}
                    raise KeyboardInterrupt
                return super().get_json(path)

        class FailingVibe:
            def run(self, prompt: str, session_id: str | None = None) -> str:
                raise DriverError("temporary provider failure")

        with tempfile.TemporaryDirectory() as tmp:
            client = RetryClient()
            driver = VibeDriver(
                client=client,
                vibe=FailingVibe(),
                sessions=SessionStore(Path(tmp) / "vibe-sessions.json"),
            )
            with patch("pokemon_vibe.app.time.sleep") as sleep:
                with self.assertRaises(KeyboardInterrupt):
                    driver.run_forever()

        self.assertNotIn(("/control", {"state": "paused"}), client.posts)
        sleep.assert_called_once_with(3.0)


class DashboardTests(unittest.TestCase):
    def test_rebrands_the_upstream_dashboard_for_vibe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            (source / "index.html").write_text(
                "<title>Hermes Plays Pok\u00e9mon</title>HERMES PLAYS POK\u00c9MON",
                encoding="utf-8",
            )
            (source / "app.js").write_text(
                "const s='brain '+(active.hermes_session_id?'linked':'pending');",
                encoding="utf-8",
            )
            (source / "style.css").write_text("/* HERMES PLAYS POK\u00c9MON */", encoding="utf-8")

            prepare_vibe_dashboard(source, target)

            combined = "\n".join(p.read_text(encoding="utf-8") for p in target.iterdir())
            self.assertNotIn("Hermes", combined)
            self.assertNotIn("HERMES", combined)
            self.assertIn("Mistral Vibe Plays Pok\u00e9mon", combined)
            self.assertIn("brain Vibe linked", combined)


if __name__ == "__main__":
    unittest.main()
