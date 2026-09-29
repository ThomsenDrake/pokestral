from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlsplit


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    chunks = []
    for item in content:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            chunks.append(item["text"].strip())
    return "\n".join(chunk for chunk in chunks if chunk)


def _label(label: str, text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    lines = text.splitlines()
    if len(lines) == 1:
        return [f"{label}: {lines[0]}"]
    return [f"{label}:", *(f"  {line}" if line else "" for line in lines)]


def _prompt_state(prompt: str) -> dict[str, Any]:
    marker = "CURRENT STATE:\n"
    if marker not in prompt:
        return {}
    raw_state = prompt.split(marker, 1)[1].split("\n\nWALKABILITY MAP", 1)[0]
    try:
        state = json.loads(raw_state)
    except json.JSONDecodeError:
        return {}
    return _as_dict(state)


def _state_summary(state: dict[str, Any]) -> str:
    map_name = state.get("map")
    if isinstance(map_name, dict):
        map_name = map_name.get("map_name")
    player = _as_dict(state.get("player"))
    position = _as_dict(state.get("position")) or _as_dict(player.get("position"))
    facing = state.get("facing") or player.get("facing")

    parts = []
    if map_name:
        parts.append(str(map_name))
    if position:
        parts.append(f"x={position.get('x')}, y={position.get('y')}")
    if facing:
        parts.append(f"facing={facing}")

    party = state.get("party")
    if isinstance(party, list):
        parts.append(f"party={len(party)}")
    badges = state.get("badges")
    if isinstance(badges, list):
        parts.append(f"badges={len(badges)}")
    return " | ".join(parts)


def _turn_lines(record: dict[str, Any]) -> list[str]:
    payload = _as_dict(record.get("payload"))
    if payload.get("method") != "turn/start":
        return []
    params = _as_dict(payload.get("params"))
    prompt = _content_text(params.get("message"))
    turn_id = str(payload.get("client_command_id", "unknown")).removeprefix("turn-")[:8]
    lines = [f"--- Turn {turn_id} ---"]
    summary = _state_summary(_prompt_state(prompt))
    if summary:
        lines.append(f"STATE: {summary}")
    return lines


def _assistant_lines(record: dict[str, Any]) -> list[tuple[str, list[str]]]:
    if record.get("type") != "projection_delta":
        return []
    results = []
    payload = _as_dict(record.get("payload"))
    deltas = payload.get("delta")
    if not isinstance(deltas, list):
        return []
    for delta in deltas:
        if not isinstance(delta, dict) or delta.get("op") != "append_entry":
            continue
        entry = _as_dict(delta.get("entry"))
        if entry.get("type") != "message" or entry.get("role") != "assistant":
            continue
        entry_id = str(entry.get("id", ""))
        lines = _label("AGENT", _content_text(entry.get("content")))
        if lines:
            results.append((entry_id, lines))
    return results


def _curl_request(command: str) -> tuple[str, dict[str, Any]] | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None

    path = ""
    body: dict[str, Any] = {}
    for index, token in enumerate(tokens):
        if token.startswith(("http://", "https://")):
            path = urlsplit(token).path
        if token in {"-d", "--data", "--data-raw"} and index + 1 < len(tokens):
            try:
                body = _as_dict(json.loads(tokens[index + 1]))
            except json.JSONDecodeError:
                body = {}
    return (path, body) if path else None


def _tool_result(record: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if record.get("type") != "action_result":
        return None
    result = _as_dict(_as_dict(record.get("payload")).get("result"))
    candidates = (result, _as_dict(result.get("result")))
    for completed in candidates:
        if completed.get("type") not in {"tool_succeeded", "tool_failed"}:
            continue
        call_id = completed.get("call_id")
        tool_output = _as_dict(completed.get("result"))
        structured = _as_dict(tool_output.get("structured_content"))
        if not structured:
            structured = _as_dict(tool_output.get("structuredContent"))
        if isinstance(call_id, str) and structured:
            return call_id, structured
    return None


def _decode_stdout(structured: dict[str, Any]) -> dict[str, Any]:
    stdout = structured.get("stdout")
    if not isinstance(stdout, str) or not stdout.strip():
        return {}
    try:
        return _as_dict(json.loads(stdout))
    except json.JSONDecodeError:
        return {}


def _tool_lines(structured: dict[str, Any]) -> list[str]:
    command = structured.get("command")
    if not isinstance(command, str):
        return []
    parsed = _curl_request(command)
    if parsed is None:
        return []
    path, body = parsed

    returncode = structured.get("returncode")
    if isinstance(returncode, int) and returncode != 0:
        detail = structured.get("stderr") or structured.get("stdout") or "unknown error"
        return _label("ERROR", str(detail))

    if path == "/event":
        event_type = str(body.get("type", "event")).replace("_", " ").upper()
        text = body.get("text") or body.get("description")
        return _label(event_type, str(text or ""))

    if path == "/objectives":
        objectives = body.get("objectives")
        if not isinstance(objectives, list):
            return []
        lines = ["OBJECTIVES:"]
        for objective in objectives:
            item = _as_dict(objective)
            tier = item.get("tier", "goal")
            text = item.get("text", "")
            lines.append(f"  {tier}: {text}")
        return lines

    if path == "/action":
        actions = body.get("actions")
        if not isinstance(actions, list):
            actions = []
        lines = ["ACTION: " + " -> ".join(str(action) for action in actions)]
        response = _decode_stdout(structured)
        state = _as_dict(response.get("state_after"))
        summary = _state_summary(state)
        executed = response.get("actions_executed")
        if summary:
            prefix = f"RESULT ({executed} executed)" if isinstance(executed, int) else "RESULT"
            lines.append(f"{prefix}: {summary}")
        return lines

    if path == "/save":
        return _label("SAVE", str(body.get("name", "unnamed")))
    if path == "/load":
        return _label("LOAD", str(body.get("name", "unnamed")))
    return []


def _session_id(records: Iterable[dict[str, Any]]) -> str | None:
    for record in records:
        payload = _as_dict(record.get("payload"))
        params = _as_dict(payload.get("params"))
        session_id = params.get("sessionId") or params.get("session_id")
        if isinstance(session_id, str) and session_id:
            return session_id
        deltas = payload.get("delta")
        if not isinstance(deltas, list):
            continue
        for delta in deltas:
            entry = _as_dict(_as_dict(delta).get("entry"))
            session_id = entry.get("sessionId") or entry.get("session_id")
            if isinstance(session_id, str) and session_id:
                return session_id
    return None


def render_transcript(raw_lines: Iterable[str]) -> str:
    records = []
    skipped = 0
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if isinstance(record, dict):
            records.append(record)

    if not records:
        raise ValueError("input did not contain any Vibe journal records")

    session_id = _session_id(records)
    heading = f"Vibe session {session_id}" if session_id else "Vibe transcript"
    output = [heading, f"Readable events from {len(records)} journal records.", ""]
    seen_entries: set[str] = set()
    seen_calls: set[str] = set()
    event_count = 0

    for record in records:
        lines = _turn_lines(record)
        if lines:
            if output[-1] != "":
                output.append("")
            output.extend(lines)
            output.append("")
            event_count += 1

        for entry_id, lines in _assistant_lines(record):
            if entry_id and entry_id in seen_entries:
                continue
            if entry_id:
                seen_entries.add(entry_id)
            output.extend(lines)
            output.append("")
            event_count += 1

        tool = _tool_result(record)
        if tool is None:
            continue
        call_id, structured = tool
        if call_id in seen_calls:
            continue
        seen_calls.add(call_id)
        lines = _tool_lines(structured)
        if lines:
            output.extend(lines)
            output.append("")
            event_count += 1

    if event_count == 0:
        output.append(
            "No readable events were found in this window. Try a larger line count or "
            "use transcript-raw."
        )
    if skipped:
        output.append(f"[Skipped {skipped} non-JSON wrapper line(s).]")
    return "\n".join(output).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a Vibe recovery journal as readable text")
    parser.parse_args(argv)
    try:
        sys.stdout.write(render_transcript(sys.stdin))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
