### Mission Overview

You are tasked with building a robust, autonomous AI agent that can complete *Pokémon Blue* from start to finish. The agent will run a Game Boy emulator (PyBoy) headless, extract RAM state, interact with the Mistral API for decision‑making, and employ tools (pathfinder, puzzle solver, battle helper) to act intelligently. The objective is to defeat the Elite Four in ≤300 hours with >99.5 % valid actions, maintain context length ≤10 k tokens, achieve >95 % state detection accuracy, and run continuously for ≥48 hours without crashes.

You have two key resources located in the project root: `pokemon_blue_agent_prd.md` (the PRD) and `pokemon_blue_implementation_plan.md` (the detailed implementation plan). You may consult these documents at any time during development. Additionally, there is already a **Pokémon Blue ROM file** available at `roms/pokemon-blue-version.gb` for your use.

### Where to Start

1. **Environment Setup**:

   * Install [uv](https://github.com/astral-sh/uv) and use it to create a virtual environment and manage dependencies. Avoid using vanilla pip. With uv, you can run commands like `uv pip install -r requirements.txt` or `uv pip install pyboy pydantic fastapi`.
   * Set up the repository structure as outlined in the implementation plan (`emulator/`, `memory_map/`, `state_detector/`, `prompt_manager/`, `agent_core/`, `tools/`, `database/`, `dashboard/`, `tests/`).

2. **Implement Memory Mapping**:

   * Create `pokemon_memory_map.py` with constants for key RAM addresses, such as:

     * Number of Pokémon in party at `0xD163`.
     * Party Pokémon species starting at `0xD164`.
     * Player money stored in three bytes at `0xD347–0xD349`.
     * Current map number (`0xD35E`), player coordinates (`0xD361`/`0xD362`), and block coordinates (`0xD363`/`0xD364`).
   * Write helper functions to convert these byte sequences into meaningful values and unit‑test them.

3. **Build the Finite State Machine (FSM)**:

   * Define a `GameState` enum and a detection routine that uses RAM flags such as `IN_BATTLE_FLAG` (0xD057), `BATTLE_TYPE` (0xD05A) and player coordinates to classify states (OVERWORLD, BATTLE, DIALOG, etc.).
   * Create unit tests with mock RAM snapshots to validate each state transition.

4. **Develop Tool Modules**:

   * **Pathfinder**: Implement a BFS or Dijkstra algorithm to navigate tile maps. Use the canonical pattern of maintaining a `frontier` queue, `came_from` dictionary and an early exit when the goal is dequeued. Provide a function that returns a list of directional actions (e.g., UP, DOWN).
   * **Puzzle Solver**: Stub out a module to handle boulder/strength puzzles using graph search.
   * **Battle Helper (optional)**: Plan a helper for computing damage and suggesting moves.

5. **Design the Prompt Manager**:

   * Construct prompts that include current location, party summary, items, money, badges, recent actions, goals, and summarised history. Summarise every 100 actions and compress every 1 000 actions to keep prompts under 10 k tokens.
   * Include instructions for Mistral to output JSON with fields `action` and `reason` and to call tools when needed.

6. **Integrate the Mistral API**:

   * Use JSON mode (`response_format={"type":"json_object"}`) and validate responses with Pydantic. Implement retries and fallbacks for API errors.
   * Support tool invocation by detecting when the model requests `TOOL:pathfinder` or other tools and providing the results back to the model.

7. **Develop the Agent Core**:

   * Orchestrate the game loop: tick the emulator, read memory, detect state, build prompts, query Mistral, parse the response, execute actions via PyBoy, and log everything.
   * Implement dynamic frame skipping and selective screenshot capture to improve performance.
   * Add checkpointing and recovery to survive long unattended runs.

8. **Logging, Database & Dashboard**:

   * Design a SQLite schema for runs, events, summaries and errors. Build a Streamlit dashboard to visualise current state, party data, action timeline, goals and performance metrics.
   * Expose metrics for CPU usage, memory usage and API latency.

### Best Practices for Roo Code & Multi‑Session Development

* **Plan and Modularise**: Break tasks into small, testable modules. Before each session, review `pokemon_blue_agent_prd.md` and `pokemon_blue_implementation_plan.md` to plan your goals. At the end, summarise what was accomplished and outline next steps.
* **Document Everything**: Include docstrings, inline comments, and type hints. Keep your PRD and implementation documents up to date.
* **Write Tests Early**: For each module (memory map, FSM, pathfinder), write unit tests before integrating into the agent. Maintain high code coverage to prevent regressions.
* **Use Version Control**: Commit often with descriptive messages. Push changes regularly and use branches for features.
* **Summarise Context**: At the end of each coding session, create a brief summary of what was done and what remains. This helps the next session pick up seamlessly.
* **Handle Secrets Carefully**: Store API keys (e.g., Mistral) and ROM checksums in environment variables or secrets management.
* **Stay Within Limits**: Monitor token counts, API rate limits, and system resources. Adjust prompts, summarisation, or frame skipping accordingly.
* **Quality over Speed**: Prioritise robustness and reliability, especially in long‑running loops. Avoid hacks that might break after many hours of runtime.

### Using MCP Servers

* **web-search-prime**: An MCP server for web searches. Use it when you need up‑to‑date information—e.g., to confirm memory addresses, game mechanics, or tool parameters. Always cite sources in the code comments or documentation.
* **zai-mcp-server**: A visual understanding MCP. Use it for analysing screenshots or videos captured from the emulator—for example, recognising Pokémon sprites or validating map layouts. Integrate it into debugging workflows or future features requiring image understanding.

### Deliverables & Next Steps

1. **Initial repository skeleton** with the modules outlined above, passing preliminary tests for memory reading and state detection. Use uv to manage the environment.
2. **Automated build & test pipeline** via Docker and CI.
3. **Incremental integration** of prompt management, Mistral API calls, and tool invocations.
4. **Regular check‑ins** with `pokemon_blue_agent_prd.md` and `pokemon_blue_implementation_plan.md` to ensure alignment.

Begin by setting up the project environment with uv and verifying the provided ROM file at `roms/pokemon-blue-version.gb`. Implement the memory map module and unit tests to confirm that money, party sizes, and Pokémon stats are read correctly. Document your progress thoroughly and plan the next session once you complete these tasks.
