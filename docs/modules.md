# Module Documentation

## Emulator Interface

### Purpose
Handles all interaction with the PyBoy emulator, including game loop management, input handling, and memory access using the new PyBoy API.

### Key Functions

```python
def __init__(self, rom_path: str, window_title: str = "Pokemon Blue - AI Agent", scale: int = 3, sound: bool = False) -> None
```

Initializes the Pokemon emulator with visual window.

**Parameters:**
- `rom_path`: Path to Pokemon Blue ROM file
- `window_title`: Title for the game window
- `scale`: Window scale factor (1-4)
- `sound`: Enable/disable game sound

---

```python
def load_rom(self, rom_path: Optional[str] = None) -> bool
```

Load Pokemon Blue ROM.

**Parameters:**
- `rom_path`: Optional path to ROM (uses instance path if not provided)

**Returns:**
True if loaded successfully

---

```python
def send_input(self, button: str, duration: float = 0.1) -> bool
```

Send input action to the emulator using new PyBoy API.

**Parameters:**
- `button`: Button name ('up', 'down', 'left', 'right', 'a', 'b', 'start', 'select')
- `duration`: How long to hold the button (seconds)

**Returns:**
True if input was queued successfully

---

```python
def get_screenshot(self) -> Optional[np.ndarray]
```

Get current game screenshot using PyBoy screen buffer.

**Returns:**
RGB screenshot array, or None if unavailable

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
def get_party_pokemon_species(self, memory: memoryview) -> list[int]
```

Returns list of Pokémon species IDs in party.

```python
def get_player_coordinates(self, memory: memoryview) -> tuple[int, int]
```

Returns (x, y) coordinates of player.

```python
def get_player_money(self, memory: memoryview) -> int
```

Returns current player money amount.

```python
def is_in_battle(self, memory: memoryview) -> bool
```

Returns True if currently in battle.

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
def detect_state(self, memory: Optional[memoryview] = None) -> GameState
```

Determines current game state from memory.

**Detection Criteria:**
- Battle: `memory[0xD057] == 1`
- Overworld: `memory[0xD35E] != 0` and not in battle
- Menu: Specific dialog flags set
- Poké Center: `memory[0xD35E] == 0x1C` (Pallet Town center)

## Agent Core

### Main Loop

1. Initialize components (emulator, memory map, state detector, etc.)
2. Start emulator with ROM loading
3. While running:
   - Tick emulator to advance game state
   - Detect current game state from memory
   - Build context for AI decision making
   - Query Mistral API with structured prompt
   - Parse and validate JSON response
   - Execute actions through emulator interface
   - Log results and performance metrics
4. Graceful shutdown on interruption or error

### Configuration

```python
class AgentConfig:
    frame_skip: int = 1
    max_frame_skips: int = 60
    screenshot_interval: int = 300  # frames
    checkpoint_interval: int = 600   # frames
    log_level: str = "INFO"
```

## Tools

### Battle Helper

```python
def get_battle_recommendation(self, player_pokemon: Pokemon, opponent_pokemon: Pokemon) -> Dict[str, Any]
```

Provides battle strategy recommendation based on type advantages.

**Returns:**
Dictionary with recommended action and reasoning.

### Pathfinder

```python
def find_path(self, start: tuple[int, int], end: tuple[int, int], grid: List[List[int]]) -> Optional[List[str]]
```

Finds optimal path between coordinates using A* search.

**Returns:**
List of directions ('up', 'down', 'left', 'right') or None if no path.

### Puzzle Solver

```python
def solve_puzzle(self, puzzle_type: str, puzzle_data: Any) -> List[str]
```

Solves game puzzles like boulder pushing or strength challenges.

**Returns:**
List of actions to solve the puzzle.

## Mistral API Integration

### Key Methods

```python
def query(self, prompt: str, image_path: Optional[str] = None) -> str
```

Query Mistral API with text prompt and optional image.

**Parameters:**
- `prompt`: Text prompt for the AI
- `image_path`: Optional path to image to include with prompt

**Returns:**
JSON-formatted response from Mistral API

```python
def chat_completion(self, messages: list, model: str = "mistral-medium-latest", response_format: Optional[dict] = None) -> Dict[str, Any]
```

Create chat completion with JSON mode support.

## Performance Optimization

### Memory Management
- Efficient memory view access for real-time state detection
- Caching of frequently accessed game state information
- Lazy loading of non-critical memory regions

### Frame Rate Control
- Dynamic frame skipping based on game state
- Automatic rate limiting to prevent API overload
- Configurable frame intervals for screenshots and checkpoints

### Input Handling
- Queue-based input processing for smooth gameplay
- Duration-based button presses for precise control
- Validation of all input actions before execution

### API Communication
- Structured JSON requests and responses for predictability
- Automatic retry logic for failed API calls
- Rate limiting compliance to prevent service disruption
- Image encoding for visual context when needed