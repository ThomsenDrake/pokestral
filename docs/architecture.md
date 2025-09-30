# Architecture Overview

## System Components

The Pokémon Blue AI Agent consists of several core components that work together to achieve autonomous gameplay:

### 1. Emulator Interface

Handles interaction with the PyBoy emulator, including:
- Game loop management with visual display
- Frame skipping and rendering optimization
- Input injection using new PyBoy API (button_press/button_release)
- Memory access and screenshot capture
- Error handling and graceful shutdown

**Key Classes:**
- `PokemonEmulator`: Main emulator wrapper with visual window
- `BUTTONS`: Button mapping constants for new PyBoy API
- Input queue management for asynchronous button presses

**Features:**
- Non-headless mode for visual monitoring
- Automatic frame ticking with rate control
- Screenshot capture for state detection
- Input action handling for AI agent control

### 2. Memory Map

Provides access to game state through RAM addresses:
- Party Pokémon data extraction
- Player position and status monitoring
- Battle state detection
- Inventory and money tracking
- Game progress flags monitoring

**Key Classes:**
- `PokemonMemoryMap`: RAM address constants and helper functions
- Memory reading utilities for PyBoy integration
- Game state extraction methods

**Features:**
- Accurate RAM address mapping for Pokémon Blue
- Helper functions for common game state queries
- Type-safe memory access with error handling

### 3. State Detector

Implements finite state machine for game context:
- Title screen detection
- Overworld navigation state
- Battle state identification
- Menu navigation tracking
- Dialog handling recognition
- Special locations (Poké Centers, Marts)

**Key Classes:**
- `StateDetector`: Game state detection logic
- `GameState`: Enum for different game states
- State transition logic and validation

**Features:**
- Real-time state detection from memory mapping
- Robust state classification with fallbacks
- Performance-optimized detection algorithms

### 4. Agent Core

Main decision-making loop that:
- Queries game state through emulator integration
- Builds context for Mistral API
- Processes API responses with JSON parsing
- Executes actions through emulator interface
- Manages tool usage and coordination

**Key Classes:**
- `AgentCore`: Main agent logic and control loop
- Action parsing and execution engine
- Game state monitoring and response handling

**Features:**
- Mistral API integration with structured JSON responses
- Action validation and error handling
- Performance monitoring and logging
- Graceful shutdown and error recovery

### 5. Prompt Manager

Handles context and prompt construction:
- Maintains action history and game state
- Manages context window size optimization
- Compresses old information for efficiency
- Validates responses and formats for API

**Key Classes:**
- `PromptManager`: Context management and prompt building
- History tracking and summarization
- Response validation and formatting

**Features:**
- Dynamic prompt construction based on game state
- Context window management to stay under token limits
- Action history compression for long runs

### 6. Tools

Specialized modules for game tasks:
- Pathfinding and navigation
- Battle strategy and move selection
- Puzzle solving for in-game challenges
- Item management and inventory tracking

**Key Classes:**
- `BattleHelper`: Combat decision making and strategy
- `Pathfinder`: Navigation and movement planning
- `PuzzleSolver`: Game challenge solutions

**Features:**
- Type advantage calculation for battles
- Optimal pathfinding with obstacle avoidance
- Puzzle-solving algorithms for game challenges

### 7. Mistral API Integration

Handles communication with Mistral language model:
- JSON schema for structured requests and responses
- Rate limiting and error handling
- Retry mechanisms for reliability
- Tool calling convention support

**Key Classes:**
- `MistralAPI`: API client with authentication and error handling
- Request/response validation and formatting
- Rate limiting and retry logic

**Features:**
- Secure API key management
- Structured JSON responses for predictable parsing
- Comprehensive error handling and logging

## Data Flow

1. **Emulator Initialization**: PyBoy loads ROM and starts game loop
2. **Memory Access**: Agent reads game state from RAM addresses
3. **State Detection**: FSM classifies current game context
4. **Prompt Construction**: Context manager builds query for Mistral
5. **API Query**: Agent sends structured request to Mistral API
6. **Response Processing**: JSON response is parsed and validated
7. **Action Execution**: Valid actions are sent to emulator as inputs
8. **Tool Coordination**: Specialized tools handle complex tasks
9. **Logging**: Results are recorded for monitoring and debugging

## Key Interfaces

### Mistral API Integration
- JSON schema for requests and responses
- Tool calling convention with structured parameters
- Error handling and automatic retries
- Rate limiting compliance

### Memory Map Interface
```python
class PokemonMemoryMap:
    def get_party_pokemon_species(self, memory: memoryview) -> list[int]:
        """Returns list of Pokémon species IDs in party."""

    def get_player_coordinates(self, memory: memoryview) -> tuple[int, int]:
        """Returns (x, y) coordinates of player."""

    def is_in_battle(self, memory: memoryview) -> bool:
        """Returns True if currently in battle."""

    def get_player_money(self, memory: memoryview) -> int:
        """Returns current player money amount."""
```

### Emulator Interface
```python
class PokemonEmulator:
    def send_input(self, button: str, duration: float = 0.1) -> bool:
        """Send input action to the emulator."""

    def get_screenshot(self) -> Optional[np.ndarray]:
        """Get current game screenshot."""

    def save_screenshot(self, filepath: str) -> bool:
        """Save current screenshot to file."""
```

## Performance Considerations

- **Memory Access Optimization**: Reads only necessary RAM addresses
- **Frame Skipping**: Maintains real-time performance with rate control
- **Context Management**: Prevents token overflow with smart windowing
- **Database Operations**: Batched where possible for efficiency
- **API Calls**: Cached responses for repeated states
- **Input Queuing**: Asynchronous input processing for smooth gameplay