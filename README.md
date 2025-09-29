# Pokémon Blue AI Agent

A fully autonomous agent that completes Pokémon Blue using the Mistral language model, PyBoy emulator, and specialized tools for gameplay.

## Overview

This project implements an AI agent capable of playing Pokémon Blue from start to finish with minimal human intervention. The system combines:

- Mistral language model for high-level decision making
- PyBoy Game Boy emulator for game execution
- Memory mapping for accurate game state detection
- Pathfinding algorithms for efficient navigation
- Specialized tools for battles and puzzle solving

The agent is designed to complete the game in under 300 hours with >99.5% valid actions while maintaining context length under 10k tokens.

## System Requirements

- Python 3.12+
- 16GB RAM recommended
- Modern CPU with good single-thread performance
- Stable internet connection for Mistral API access

## Installation

### Using uv (recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with the following variables:

```ini
MISTRAL_API_KEY=your_api_key_here
ROM_PATH=roms/pokemon-blue-version.gb
LOG_LEVEL=INFO
```

2. Ensure you have a valid Pokémon Blue ROM in the `roms/` directory

## Usage

Run the agent with:

```bash
python -m agent_core
```

### Command Line Options

```bash
usage: agent.py [-h] [--headless] [--fast-forward] [--debug] [--checkpoint CHECKPOINT]

options:
  -h, --help            show this help message
  --headless            Run without displaying game window
  --fast-forward        Skip frames for faster execution
  --debug               Enable debug logging
  --checkpoint CHECKPOINT
                        Load from checkpoint file
```

## Project Structure

```
emulator/         # Emulator interface and game loop
memory_map/       # RAM addresses and helpers
state_detector/   # Game state detection
prompt_manager/   # Context management
agent_core/       # Main agent logic
tools/            # Pathfinding, battles, puzzles
database/         # Logging and data storage
dashboard/        # Monitoring interface
tests/            # Unit and integration tests
```

## Key Features

- Complete game automation from start to Elite Four victory
- Accurate game state detection using memory mapping
- Intelligent pathfinding and navigation
- Battle strategy with type advantage calculation
- Puzzle solving for in-game challenges
- Checkpointing and resume capability for long runs
- Performance monitoring dashboard with real-time metrics
- Context management to maintain under 10k tokens

## Performance Metrics

| Metric | Target |
|--------|--------|
| Game completion time | < 300 hours |
| Valid action rate | > 99.5% |
| Context length | ≤ 10k tokens |
| Continuous runtime | ≥ 48 hours without crashes |
| State detection accuracy | > 95% |

## Troubleshooting

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

## Contribution Guidelines

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description
4. Ensure all tests pass
5. Update documentation as needed

### Code Standards

- Follow PEP 8 style guide
- Use type hints
- Write unit tests for new functionality
- Document public APIs
- Keep functions small and focused

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.