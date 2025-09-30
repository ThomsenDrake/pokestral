# Developer Documentation

## Getting Started

### Prerequisites
- Python 3.12+
- uv package manager (recommended) or pip
- Valid Pokémon Blue ROM file

### Environment Setup

#### Using uv (Recommended)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

#### Using pip
```bash
# Create virtual environment
python -m venv .venv

# Activate environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
pokestral/
├── agent_core/           # Main agent logic and API integration
│   ├── agent_core.py     # Core agent class and main loop
│   └── mistral_api.py    # Mistral API client
├── emulator/            # PyBoy emulator wrapper
│   └── emulator.py       # Emulator interface and input handling
├── memory_map/           # Game memory access
│   └── pokemon_memory_map.py  # RAM addresses and helpers
├── state_detector/      # Game state detection
│   └── game_state.py     # State machine and detection logic
├── prompt_manager/       # Context and prompt management
│   └── prompt_manager.py  # Prompt construction and history
├── tools/                # Specialized game tools
│   ├── battle_helper.py  # Battle strategy
│   ├── pathfinder.py     # Navigation and pathfinding
│   └── puzzle_solver.py  # Game puzzle solutions
├── docs/                 # Documentation files
├── roms/                 # Game ROMs (not included)
├── tests/                # Unit and integration tests
├── screenshots/         # Game screenshots (generated)
├── checkpoints/          # Game state saves (generated)
├── main.py              # Main entry point and orchestrator
├── requirements.txt     # Project dependencies
├── .env                 # Configuration (not included)
└── README.md           # Project documentation
```

## Key Components

### 1. PokemonEmulator Class

Located in `emulator/emulator.py`, this class wraps PyBoy to provide:
- Visual game window with configurable scaling
- Input action handling with button press/release methods
- Memory access through PyBoy's memory view
- Screenshot capture and saving capabilities
- Frame management and rate control

**Key Methods:**
- `__init__()`: Initialize emulator with ROM loading
- `send_input()`: Send button inputs to the game
- `get_screenshot()`: Capture current game state as image
- `tick()`: Advance game by specified number of frames

### 2. AgentCore Class

Located in `agent_core/agent_core.py`, this is the main AI agent controller:
- Coordinates all system components
- Implements main game loop logic
- Handles AI decision making through Mistral API
- Manages game state detection and action execution
- Processes AI responses and converts to emulator inputs

**Key Methods:**
- `__init__()`: Initialize all agent components
- `run()`: Main agent execution loop
- `execute_actions()`: Convert AI responses to emulator inputs
- `main_game_loop()`: Process single iteration of game loop

### 3. MistralAPI Class

Located in `agent_core/mistral_api.py`, handles communication with Mistral:
- Secure API key management
- Structured JSON requests and responses
- Error handling and retry logic
- Rate limiting compliance

**Key Methods:**
- `query()`: Send text prompt to Mistral API
- `chat_completion()`: Create chat completion with JSON mode

## Development Guidelines

### Code Standards
1. **PEP 8 Compliance**: Follow Python style guide
2. **Type Hints**: Use type annotations throughout
3. **Docstrings**: Document all public classes and methods
4. **Error Handling**: Proper exception handling and logging
5. **Modularity**: Keep functions focused and reusable

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=agent_core --cov=emulator tests/

# Run specific test file
pytest tests/test_battle_helper.py

# Run tests with verbose output
pytest -v tests/
```

### Code Quality
```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check code style with flake8
flake8 .

# Type checking with mypy
mypy .
```

## API Integration

### Mistral API Client
The `MistralAPI` class in `agent_core/mistral_api.py` provides:

**Initialization:**
```python
api = MistralAPI(api_key="your-api-key")
```

**Text Queries:**
```python
response = api.query("What should I do next?")
```

**Structured Responses:**
The API is configured to return JSON responses for predictable parsing.

### Response Format
AI responses should follow this JSON structure:
```json
{
  "action": "move_up|move_down|move_left|move_right|open_menu|...",
  "reason": "Explanation for why this action was chosen"
}
```

## Emulator Integration

### Input Handling
The emulator supports these button actions:
- Directional: 'up', 'down', 'left', 'right'
- Action: 'a', 'b', 'start', 'select'

### Memory Access
Use the `PokemonMemoryMap` class to read game state:
```python
memory_map = PokemonMemoryMap()
party_species = memory_map.get_party_pokemon_species(memory_view)
player_x, player_y = memory_map.get_player_coordinates(memory_view)
```

### Screenshot Capture
Screenshots are automatically saved to the `screenshots/` directory and can be captured manually:
```python
emulator.save_screenshot("screenshots/current_state.png")
```

## State Management

### Game States
The system detects these game states:
- `TITLE_SCREEN`: Initial game screen
- `OVERWORLD`: Normal gameplay
- `BATTLE`: Pokémon battle
- `MENU`: Menu navigation
- `DIALOG`: Text display

### Context Management
The `PromptManager` handles:
- Maintaining action history
- Managing context window size
- Compressing old information
- Building structured prompts

## Performance Optimization

### Frame Rate Control
- Configurable frame skipping for performance
- Automatic rate limiting to prevent API overload
- Efficient memory access patterns

### Memory Management
- Efficient memory view access for real-time detection
- Caching of frequently accessed game state
- Lazy loading of non-critical components

### Input Processing
- Queue-based input handling for smooth gameplay
- Duration-based button presses for precise control
- Validation of all input actions before execution

## Troubleshooting

### Common Development Issues

**Module Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv pip install -r requirements.txt
```

**PyBoy Installation Issues**
```bash
# Install PyBoy directly
pip install pyboy
```

**API Key Problems**
- Verify `.env` file contains correct `MISTRAL_API_KEY`
- Check API key permissions in Mistral dashboard
- Ensure network connectivity to API endpoint

**Emulator Not Responding**
- Check that ROM file is valid and accessible
- Verify that emulator window has focus (non-headless mode)
- Ensure sufficient system resources are available

## Contributing

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make changes with proper documentation
4. Add/update tests as needed
5. Run all tests to ensure no regressions
6. Submit pull request with clear description

### Code Review Guidelines
- All new functionality must include unit tests
- Public APIs must be documented with docstrings
- Code must pass all quality checks (black, isort, flake8, mypy)
- Changes should maintain backward compatibility when possible
- Complex logic should be broken into smaller, testable functions

### Testing Requirements
- Unit tests for all new classes and methods
- Integration tests for component interactions
- Performance tests for critical paths
- Edge case testing for error conditions