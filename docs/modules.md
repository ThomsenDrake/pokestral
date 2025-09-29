# Module Documentation

## Emulator Interface

### Purpose
Handles all interaction with the PyBoy emulator, including game loop management, input handling, and memory access.

### Key Functions

```python
def initialize_emulator(rom_path: str, headless: bool = False) -> PyBoy
```

Initializes the PyBoy emulator with the specified ROM.

**Parameters:**
- `rom_path`: Path to Pokémon Blue ROM file
- `headless`: Whether to run without video output

**Returns:**
Configured PyBoy instance

---

```python
def tick(emulator: PyBoy, frames: int = 1) -> None
```

Advances the emulator by specified number of frames.

**Parameters:**
- `emulator`: PyBoy instance
- `frames`: Number of frames to advance

---

```python
def press_button(emulator: PyBoy, button: str, duration: int = 1) -> None
```

Simulates button press for specified duration.

**Parameters:**
- `emulator`: PyBoy instance
- `button`: Button name ('A', 'B', 'START', etc.)
- `duration`: Number of frames to hold button

---

```python
def get_memory(emulator: PyBoy) -> memoryview
```

Returns memory view for direct RAM access.

## Memory Map

### Key Addresses

| Symbol | Address | Type | Description |
|--------|---------|------|-------------|
| `NUM_POKEMON_PARTY` | 0xD163 | byte | Number of Pokémon in party |
| `PARTY_POKEMON_START` | 0xD164 | byte[] | Start of party species list |
| `PLAYER_X` | 0xD362 | byte | X coordinate |
| `PLAYER_Y` | 0xD361 | byte | Y coordinate |
| `CURRENT_MAP` | 0xD35E | byte | Current map ID |
| `BADGES_FLAGS` | 0xD356 | byte | Gym badge flags |
| `PLAYER_MONEY` | 0xD347-0xD349 | bytes | Money (BCD format) |

### Helper Functions

```python
def get_party_species(memory: memoryview) -> list[int]
```

Returns list of Pokémon species IDs in party.

```python
def get_player_position(memory: memoryview) -> tuple[int, int]
```

Returns (x, y) coordinates of player.

## State Detector

### Game States

- `TITLE_SCREEN`: Initial game screen
- `OVERWORLD`: Normal gameplay
- `BATTLE`: Pokémon battle
- `MENU`: Menu navigation
- `DIALOG`: Text display
- `POKE_CENTER`: Inside Poké Center
- `POKE_MART`: Inside Poké Mart

### Detection Logic

```python
def detect_state(memory: memoryview) -> GameState
```

Determines current game state from memory.

**State Detection Criteria:**
- Battle: `memory[0xD057] != 0`
- Overworld: `memory[0xD35E] != 0` and not in battle
- Menu: Specific dialog flags set
- Poké Center: `memory[0xD35E] == 0x1C` (Pallet Town center)

## Agent Core

### Main Loop

1. Initialize components
2. Load checkpoint (if available)
3. While game not completed:
   - Tick emulator
   - Detect game state
   - Build context
   - Query Mistral API
   - Execute response
   - Log results
4. Save final state

### Configuration

```python
class AgentConfig:
    fast_forward: bool = False
    checkpoint_interval: int = 300  # seconds
    max_context_tokens: int = 8000
    log_level: str = "INFO"
```

## Tools

### Pathfinder

```python
def find_path(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]
```

Finds optimal path between coordinates using BFS.

### Battle Helper

```python
def get_best_move(attacker: Pokemon, defender: Pokemon) -> str
```

Recommends best move based on type matchups.

### Puzzle Solver

```python
def solve_boulder_puzzle(map_data: list[list[int]]) -> list[str]
```

Solves Strength boulder puzzles using A* search.