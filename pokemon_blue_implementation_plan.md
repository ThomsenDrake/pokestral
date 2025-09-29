# Implementation Plan – Mistral-Powered Pokémon Blue Agent

This plan outlines how to build a fully autonomous agent that completes **Pokémon Blue** using the **Mistral** language model, the **PyBoy** emulator, and supplementary tools. It is organized into phases that parallel the high-level requirements in the revised PRD.

---

## 1. Project Setup & Tooling

### Legal ROM Acquisition
- Require users to provide their own Pokémon Blue cartridge and dump a `.gb` ROM.
- Implement a CLI tool to verify the ROM’s checksum (CRC32/SHA1) against known valid hashes.

### Repository Structure

```
emulator/         # PyBoy init, game loop, frame skipping, video capture
memory_map/       # RAM constants and helpers
state_detector/   # FSM for game state detection
prompt_manager/   # Prompt building, action history, context management
agent_core/       # Mistral API orchestration and tool handling
tools/            # Pathfinding, puzzles, battle helpers
database/         # SQLite schema and data layer
dashboard/        # Streamlit or FastAPI UI
tests/            # Unit & integration tests
```

### Dependency Management
- Use `uv` or `pip` for virtual environment and dependency installation.
- Install required packages: `PyBoy`, `Pydantic`, `FastAPI`, `Streamlit`, `SQLAlchemy`, etc.
- Pin versions in `pyproject.toml` or `requirements.txt`.

### Docker & CI
- Provide a `Dockerfile` and `docker-compose.yml`.
- Install SDL2, FFmpeg, and system libraries.
- Set up CI (e.g., GitHub Actions) to run unit tests on each commit.

---

## 2. Memory Mapping

Accurate RAM addresses are essential for extracting game state. Use the Data Crystal RAM map to populate `pokemon_memory_map.py` with constants such as:

| Symbol | Address | Description |
|--------|---------|-------------|
| `NUM_POKEMON_PARTY` | `0xD163` | Number of Pokémon in party |
| `PARTY_POKEMON_START` | `0xD164` | Start of species list |
| `POKEMON1_HP` | `0xD16C–0xD16D` | Current HP |
| `POKEMON1_LEVEL` | `0xD18C` | Level |
| `POKEMON1_MAX_HP` | `0xD18D–0xD18E` | Max HP |
| `PLAYER_MONEY` | `0xD347–0xD349` | Money (BCD) |
| `BADGES_FLAGS` | `0xD356` | Gym badge flags |
| `CURRENT_MAP` | `0xD35E` | Current map |
| `PLAYER_Y` | `0xD361` | Y coordinate |
| `PLAYER_X` | `0xD362` | X coordinate |
| `IN_BATTLE_FLAG` | `0xD057` | Battle detection |
| `BATTLE_TYPE` | `0xD05A` | Battle type |
| `MAP_HEADER` | `0xD367–0xD39C` | Map dimensions and pointers |

**Example helper:**

```python
def get_money(memory: PyBoyMemoryView) -> int:
    bcd = memory[0xD347:0xD34A]
    return bcd[0] * 10000 + bcd[1] * 100 + bcd[2]

def get_party_species(memory: PyBoyMemoryView) -> list[int]:
    count = memory[0xD163]
    return list(memory[0xD164:0xD164 + count])
```

---

## 3. Game State Detection

Create a `state_detector.py` module with an enum for states:

- `TITLE_SCREEN`
- `OVERWORLD`
- `BATTLE`
- `MENU`
- `DIALOG`
- `POKE_CENTER`
- `POKE_MART`
- `VICTORY`
- `GAME_OVER`

Use heuristics:

- Battle: `IN_BATTLE_FLAG` or `BATTLE_TYPE` != 0  
- Dialog/Menu: Check for known dialog flags or inactivity  
- PokéCenter/Mart: Check `CURRENT_MAP`  
- Victory: Detect Hall of Fame and credits  

Include unit tests for state detection.

---

## 4. Pathfinding & Tools

### Pathfinder Module

- Extract tile map using `tilemap_background`.
- Build passable/impassable grid.
- Implement BFS or Dijkstra for pathfinding.

**BFS Example:**

```python
from collections import deque

def bfs(start, goal, graph):
    frontier = deque([start])
    came_from = {start: None}
    while frontier:
        current = frontier.popleft()
        if current == goal:
            break
        for next_node in graph.neighbors(current):
            if next_node not in came_from:
                frontier.append(next_node)
                came_from[next_node] = current
    # Reconstruct path
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from.get(cur)
    return list(reversed(path))
```

### Puzzle Solver & Tools
- **Boulder Solver:** BFS or A* for Strength puzzles.
- **Battle Helper:** Suggest best move based on type matchups.
- **Item Manager:** Manage healing/capture item usage.

---

## 5. Prompt & Context Management

- **System Prompt:** Game objective, memory map, tools, JSON output.  
- **Context:** Include location, party, items, badges, state, history, goals.  
- **Summaries:** Every 100 actions, compress every 1000.  
- **Guidance Critique:** Periodically review recent actions and correct hallucinations.  
- **Token Limit:** ≤ 10k tokens. Drop stale history as needed.

---

## 6. Mistral API Integration

- Create `mistral_client.py` to send requests with JSON schema enforcement.
- Use Pydantic to validate responses.
- Implement retries with exponential backoff.
- Handle tool calls prefixed with `TOOL:`.

---

## 7. Agent Core

`agent_core.py` orchestrates the loop:

1. Initialize emulator, state detector, prompt manager, and Mistral client.  
2. Advance emulator frames with `pyboy.tick()`.  
3. Capture state and detect current game state.  
4. Build prompt and query Mistral API.  
5. Execute actions or invoke tools.  
6. Log actions and results to SQLite.  
7. Save checkpoints periodically.

Use `asyncio` to handle rate limiting and API calls.

---

## 8. Logging, Database & Monitoring

- Use SQLite tables: `runs`, `events`, `summaries`, `errors`.  
- Structured logging with timestamps and run IDs.  
- Build a Streamlit dashboard to show:
  - Current state, location, party
  - Action timeline and reasons
  - Goals and progress
  - Performance metrics
- Expose Prometheus metrics (optional).

---

## 9. Testing & QA

- **Unit Tests:** For memory parsing, state detection, pathfinding, and prompt logic.  
- **Integration Tests:** Simulate gameplay segments with scripted responses.  
- **Stress Tests:** Run for 24–48 hours to check for leaks.  
- **Regression Tests:** Re-run saved states after changes.

---

## 10. Performance & Optimization

- **Frame Skipping:** Target ≥10× real-time.  
- **Selective Screenshots:** Every 100 actions or on demand.  
- **Dynamic Context Trimming:** Drop old context before 10k tokens.  
- **Efficient Memory Access:** Read only required addresses.  
- **Response Caching:** Cache repeated responses for ~1 minute.

---

## 11. Deployment & Operations

- Build a Docker image with all dependencies.  
- Use `systemd` or Supervisor for automatic restarts.  
- Provide configuration via `.env` or YAML.  
- Include documentation for setup, usage, and logs.  
- Optional FFmpeg streaming support.

---

## 12. Timeline & Milestones (Sample)

| Week | Tasks |
|------|-------|
| 1 | Repo setup, ROM verification, memory map implementation |
| 2 | FSM state detector, basic prompt manager, stub client |
| 3 | Pathfinder module, collision map, tests |
| 4 | MistralClient JSON mode, basic agent loop, SQLite logging |
| 5 | Prompt history, guidance critique, battle helper, live tests |
| 6 | Logging, checkpointing, dashboard, performance tuning |
| 7 | Long-run testing, heuristic tuning, docs, streaming, final report |

---

## Conclusion

This plan provides a detailed roadmap to create a **robust, autonomous Pokémon Blue agent**. It emphasizes accurate memory mapping, game state detection, pathfinding, prompt management, and structured interactions with the Mistral API. Following these phases enables the team to **systematically build, test, and deploy** an agent capable of completing Pokémon Blue end-to-end — and sets the stage for future games and research.