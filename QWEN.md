# Pokestral - Pokémon Blue AI Agent

## Project Overview

Pokestral is a fully autonomous AI agent that plays Pokémon Blue from start to finish using the Mistral language model, PyBoy Game Boy emulator, and specialized tools for gameplay automation. The system is designed to complete the game in under 300 hours with >99.5% valid actions while maintaining context length under 10k tokens.

### 🎉 CURRENT STATUS: **FULLY OPERATIONAL!**

The system is now successfully integrated and running! The AI agent:
- ✅ Loads and runs Pokémon Blue ROM
- ✅ Connects to Mistral API for decision making  
- ✅ Sends proper button inputs to navigate menus and gameplay
- ✅ Receives intelligent responses and executes actions
- ✅ Takes screenshots and saves game progress

## 🏗️ System Architecture

The Pokémon Blue AI Agent consists of several core components that work together to achieve autonomous gameplay:

### 1. Emulator Interface (`emulator/`)
Handles interaction with the PyBoy emulator, including:
- Game loop management with visual display
- Frame skipping and rendering optimization  
- Input injection using new PyBoy API (button_press/button_release)
- Memory access and screenshot capture
- Error handling and graceful shutdown

### 2. Memory Map (`memory_map/`)
Provides access to game state through RAM addresses:
- Party Pokémon data extraction
- Player position and status monitoring
- Battle state detection
- Inventory and money tracking
- Game progress flags monitoring

### 3. State Detector (`state_detector/`)
Implements finite state machine for game context:
- Title screen detection
- Overworld navigation state
- Battle state identification
- Menu navigation tracking
- Dialog handling recognition
- Special locations (Poké Centers, Marts)

### 4. Agent Core (`agent_core/`)
Main decision-making loop that:
- Queries game state through emulator integration
- Builds context for Mistral API
- Processes API responses with JSON parsing
- Executes actions through emulator interface
- Manages tool usage and coordination

### 5. Prompt Manager (`prompt_manager/`)
Handles context and prompt construction:
- Maintains action history and game state
- Manages context window size optimization
- Compresses old information for efficiency
- Validates responses and formats for API

### 6. Tools (`tools/`)
Specialized modules for game tasks:
- **Battle Helper**: Intelligent combat decision making
- **Pathfinder**: Navigation and movement planning
- **Puzzle Solver**: Game challenge solutions

### 7. Mistral API Integration (`agent_core/mistral_api.py`)
Handles communication with Mistral language model:
- JSON schema for structured requests and responses
- Rate limiting and error handling
- Retry mechanisms for reliability
- Tool calling convention support

## 🚀 Quick Start Guide

### System Requirements
- Python 3.12+
- 16GB RAM recommended
- Modern CPU with good single-thread performance
- Stable internet connection for Mistral API access

### Installation

#### Using uv (recommended)
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

#### Using pip
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

1. Create a `.env` file in the project root with the following variables:

```ini
MISTRAL_API_KEY=your_api_key_here
ROM_PATH=roms/pokemon-blue-version.gb
LOG_LEVEL=INFO
```

2. Ensure you have a valid Pokémon Blue ROM in the `roms/` directory

### Running the Agent

```bash
# Basic usage
python main.py [--rom PATH] [--headless] [--debug]

# Examples:
python main.py --rom ./roms/pokemon-blue-version.gb
python main.py --headless  # Run without visual window
python main.py --debug     # Enable debug logging
```

## 🎮 Key Features

- **Complete Game Automation**: From start to Elite Four victory
- **Accurate Game State Detection**: Using memory mapping and RAM analysis
- **Intelligent Pathfinding**: Efficient navigation through game world
- **Battle Strategy**: Type advantage calculation and move selection
- **Puzzle Solving**: In-game challenge solutions
- **Checkpointing**: Save and resume capability for long runs
- **Performance Monitoring**: Real-time metrics dashboard
- **Context Management**: Maintain under 10k tokens for API efficiency

## 📊 Performance Metrics

| Metric | Target | Current Status |
|--------|--------|----------------|
| Game completion time | < 300 hours | Running successfully |
| Valid action rate | > 99.5% | High accuracy |
| Context length | ≤ 10k tokens | Managed properly |
| Continuous runtime | ≥ 48 hours without crashes | Stable operation |
| State detection accuracy | > 95% | Working with memory mapping |

## 🔧 Development & Testing

### Code Standards
- Follow PEP 8 style guide
- Use type hints throughout
- Write unit tests for new functionality
- Document public APIs
- Keep functions small and focused

### Project Structure
```
emulator/         # Emulator interface and game loop
memory_map/       # RAM addresses and helpers
state_detector/   # Game state detection
prompt_manager/   # Context management and prompt building
agent_core/       # Main agent logic and Mistral API integration
tools/            # Pathfinding, battle helpers, puzzle solvers
database/         # Logging and data storage
dashboard/        # Monitoring interface
tests/            # Unit and integration tests
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=agent_core --cov=emulator tests/

# Run specific test files
pytest tests/test_battle_helper.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description
4. Ensure all tests pass
5. Update documentation as needed

### Development Guidelines
- Maintain backward compatibility where possible
- Write comprehensive unit tests for new features
- Document all public APIs and interfaces
- Follow established code patterns and conventions
- Keep dependencies minimal and well-justified

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Emulator crashes on startup**
- Ensure you have a valid Pokémon Blue ROM
- Verify ROM checksum matches known good values
- Check that all dependencies are installed

**Agent gets stuck in game**
- Increase debug logging to identify state detection issues
- Check memory map for correct address values
- Verify pathfinding algorithms for the current map

**API connection errors**
- Verify your Mistral API key is correct
- Check network connectivity
- Ensure you haven't hit rate limits

**Button input not working**
- Check that PyBoy is properly installed (`pip install pyboy`)
- Verify that the emulator can send inputs to the game
- Ensure the game window has focus for non-headless mode

**Screenshot capture fails**
- Check that the screenshots directory is writable
- Verify that PyBoy can capture screen buffer
- Ensure sufficient disk space is available