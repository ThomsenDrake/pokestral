# Architecture Overview

## System Components

The Pokémon Blue AI Agent consists of several core components that work together to achieve autonomous gameplay:

### 1. Emulator Interface
Handles interaction with the PyBoy emulator, including:
- Game loop management
- Frame skipping and rendering
- Input injection
- Memory access

### 2. Memory Map
Provides access to game state through RAM addresses:
- Party Pokémon data
- Player position and status
- Battle state
- Inventory
- Game progress flags

### 3. State Detector
Implements finite state machine for game context:
- Title screen
- Overworld
- Battle
- Menu navigation
- Dialog handling
- Special locations (Poké Centers, Marts)

### 4. Agent Core
Main decision-making loop that:
- Queries game state
- Builds context for Mistral
- Processes API responses
- Executes actions
- Manages tool usage

### 5. Prompt Manager
Handles context and prompt construction:
- Maintains action history
- Manages context window
- Compresses old information
- Validates responses

### 6. Tools
Specialized modules for game tasks:
- Pathfinding and navigation
- Battle strategy
- Puzzle solving
- Item management

### 7. Database
Stores runtime data and metrics:
- Action logs
- Game state checkpoints
- Performance metrics
- Error tracking

### 8. Dashboard
Provides monitoring and control interface:
- Real-time game state
- Action history
- Performance metrics
- Configuration

## Data Flow

1. Emulator advances game state and provides memory access
2. State Detector analyzes memory to determine current context
3. Prompt Manager assembles relevant context and history
4. Agent Core queries Mistral API with constructed prompt
5. Response is parsed and validated
6. Actions are executed through emulator interface or tools
7. Results are logged to database
8. Dashboard updates with new state

## Key Interfaces

### Mistral API Integration
- JSON schema for requests and responses
- Tool calling convention
- Error handling and retries
- Rate limiting

### Database Schema
Main tables:
- `runs` - Session metadata
- `events` - Action history
- `state_snapshots` - Game state checkpoints
- `metrics` - Performance data

### Memory Map Interface
```python
class MemoryMap:
    def get_party(self) -> list[Pokemon]:
        """Returns current party with species, levels, HP"""

    def get_position(self) -> tuple[int, int]:
        """Returns current (x, y) coordinates"""

    def in_battle(self) -> bool:
        """Returns True if in battle"""

    def get_badges(self) -> int:
        """Returns bitmask of obtained badges"""
```

## Performance Considerations

- Memory access is optimized to read only necessary addresses
- Frame skipping maintains real-time performance
- Context management prevents token overflow
- Database operations are batched where possible
- API calls are cached for repeated states