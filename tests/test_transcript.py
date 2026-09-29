from __future__ import annotations

import json
import unittest

from pokemon_vibe.transcript import render_transcript


def journal_line(record_type: str, payload: dict[str, object]) -> str:
    return json.dumps({"type": record_type, "payload": payload})


def tool_result(call_id: str, command: str, stdout: dict[str, object]) -> str:
    return journal_line(
        "action_result",
        {
            "state": "succeeded",
            "result": {
                "type": "tool_succeeded",
                "call_id": call_id,
                "result": {
                    "structured_content": {
                        "command": command,
                        "returncode": 0,
                        "stderr": "",
                        "stdout": json.dumps(stdout),
                    },
                    "type": "success",
                },
            },
        },
    )


class TranscriptTests(unittest.TestCase):
    def test_renders_turn_messages_and_game_actions_without_protocol_noise(self) -> None:
        prompt = """You are playing Pokemon Blue.

CURRENT STATE:
{
  "map": "Red's House 2F",
  "position": {"x": 4, "y": 5},
  "facing": "left",
  "party": [],
  "badges": []
}

WALKABILITY MAP (player is @ at E5):
...
"""
        lines = [
            journal_line(
                "command_reserved",
                {
                    "client_command_id": "turn-1234567890",
                    "method": "turn/start",
                    "params": {
                        "sessionId": "session-a",
                        "message": [{"type": "text", "text": prompt}],
                    },
                },
            ),
            journal_line(
                "projection_delta",
                {
                    "delta": [
                        {
                            "op": "append_entry",
                            "entry": {
                                "id": "message-a",
                                "type": "message",
                                "role": "assistant",
                                "sessionId": "session-a",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "I will move toward the stairs.",
                                    }
                                ],
                            },
                        }
                    ]
                },
            ),
            tool_result(
                "reasoning-a",
                "curl -s -X POST http://127.0.0.1:8000/event "
                "-H 'Content-Type: application/json' "
                '-d \'{"type":"reasoning","text":"Arthur is near the stairs."}\'',
                {"success": True},
            ),
            tool_result(
                "decision-a",
                "curl -s -X POST http://127.0.0.1:8000/event "
                "-H 'Content-Type: application/json' "
                '-d \'{"type":"decision","text":"Walk down, then right."}\'',
                {"success": True},
            ),
            tool_result(
                "action-a",
                "curl -s -X POST http://127.0.0.1:8000/action "
                "-H 'Content-Type: application/json' "
                '-d \'{"actions":["walk_down","walk_right"]}\'',
                {
                    "success": True,
                    "actions_executed": 2,
                    "state_after": {
                        "map": {"map_name": "Red's House 2F"},
                        "player": {
                            "position": {"x": 5, "y": 6},
                            "facing": "right",
                        },
                        "party": [],
                    },
                },
            ),
            journal_line(
                "action_intent",
                {"request": {"model_input": {"messages": "large protocol snapshot"}}},
            ),
        ]

        output = render_transcript(lines)

        self.assertIn("Vibe session session-a", output)
        self.assertIn("--- Turn 12345678 ---", output)
        self.assertIn("STATE: Red's House 2F | x=4, y=5 | facing=left", output)
        self.assertIn("AGENT: I will move toward the stairs.", output)
        self.assertIn("REASONING: Arthur is near the stairs.", output)
        self.assertIn("DECISION: Walk down, then right.", output)
        self.assertIn("ACTION: walk_down -> walk_right", output)
        self.assertIn(
            "RESULT (2 executed): Red's House 2F | x=5, y=6 | facing=right | party=0",
            output,
        )
        self.assertNotIn("large protocol snapshot", output)
        self.assertNotIn('"payload"', output)

    def test_handles_shell_escaped_apostrophes_and_skips_hook_duplicates(self) -> None:
        command = (
            "curl -s -X POST http://127.0.0.1:8000/event "
            "-H 'Content-Type: application/json' "
            '-d \'{"type":"reasoning","text":"Leave Red\'\\\'\'s house."}\''
        )
        duplicate_hook = journal_line(
            "action_result",
            {
                "result": {
                    "result": {
                        "type": "hook_completed",
                        "output": {"tool_result": {"structured_content": {"command": command}}},
                    }
                }
            },
        )

        output = render_transcript(
            [tool_result("reasoning-b", command, {"success": True}), duplicate_hook]
        )

        self.assertEqual(output.count("REASONING: Leave Red's house."), 1)

    def test_reports_when_window_has_only_protocol_records(self) -> None:
        output = render_transcript([journal_line("action_intent", {"request": {}})])

        self.assertIn("No readable events were found", output)

    def test_ignores_projection_with_null_delta(self) -> None:
        output = render_transcript([journal_line("projection_delta", {"delta": None})])

        self.assertIn("No readable events were found", output)


if __name__ == "__main__":
    unittest.main()
