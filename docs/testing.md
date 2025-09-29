# Testing Strategy and Coverage

## Overview

The testing strategy ensures reliability and correctness of the Pokémon Blue AI agent through unit tests, integration tests, and end-to-end validation.

## Test Types

### Unit Tests
Test individual components in isolation.

**Coverage:**
- Memory map functions
- State detection logic
- Pathfinding algorithms
- Tool implementations
- API client

**Example:**
```python
def test_get_party_species():
    memory = mock_memory([3, 25, 6, 9])  # 3 Pokémon: Pikachu, Squirtle, Charizard
    assert get_party_species(memory) == [25, 6, 9]
```

### Integration Tests
Test component interactions.

**Coverage:**
- Emulator interface
- State detection with real memory
- Agent decision loop
- Database logging
- Dashboard integration

**Example:**
```python
def test_battle_flow():
    with PyBoy('rom.gb') as emulator:
        # Simulate battle state
        emulator.memory[0xD057] = 1
        state = detect_state(emulator.memory)
        assert state == GameState.BATTLE
```

### End-to-End Tests
Validate complete gameplay sequences.

**Coverage:**
- Pallet Town to Viridian City
- First gym battle
- Item purchasing
- Pokémon capture
- Major story progression

## Test Framework

### pytest Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
```

### Test Structure

```
tests/
  test_memory_map.py
  test_state_detector.py
  test_pathfinder.py
  test_agent_core.py
  test_tools.py
  test_api.py
  integration/
    test_emulator.py
    test_agent_loop.py
  e2e/
    test_pallet_town.py
    test_first_gym.py
```

## Key Test Cases

### Memory Map Validation

```python
def test_player_position():
    memory = mock_memory([0x05, 0x0A])  # x=10, y=5
    x, y = get_player_position(memory)
    assert (x, y) == (10, 5)
```

### State Detection

```python
def test_battle_detection():
    memory = mock_memory([1])  # IN_BATTLE_FLAG = 1
    assert detect_state(memory) == GameState.BATTLE
```

### Pathfinding

```python
def test_simple_path():
    grid = [[0, 0, 0], [1, 1, 0], [0, 0, 0]]
    path = find_path((0, 0), (2, 2), grid)
    assert path == [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)]
```

### API Integration

```python
@patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "A"}}]
    }
    response = mistral_client.query("Test prompt")
    assert response == "A"
```

## Test Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Memory Map | 100% |
| State Detector | 95% |
| Pathfinding | 90% |
| Agent Core | 85% |
| Tools | 90% |
| API Client | 95% |
| Database | 80% |

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=./ --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Performance Testing

### Stress Test

```python
def test_long_run():
    agent = Agent()
    for _ in range(10000):  # 10,000 actions
        agent.tick()
        assert agent.state != GameState.GAME_OVER
```

### Benchmarking

```python
def benchmark_frame_rate():
    with measure_time() as t:
        for _ in range(1000):
            emulator.tick()
    assert t.elapsed < 1.0  # > 1000 FPS
```

## Debugging Tests

### Common Issues

**Test for memory misalignment:**
```python
def test_memory_bounds():
    with pytest.raises(IndexError):
        get_invalid_memory(emulator.memory)
```

**Test for state detection failures:**
```python
def test_unknown_state():
    memory = mock_memory([0xFF] * 0x1000)  # Garbage memory
    with pytest.raises(ValueError):
        detect_state(memory)
```

## Test Data Management

### Fixtures

```python
@pytest.fixture
def emulator():
    with PyBoy('rom.gb', headless=True) as emu:
        yield emu
```

### Mock Data

```python
def mock_memory(values):
    return memoryview(bytearray(values))
```

## Reporting

Test results are stored in:
- `test-results/` directory
- JUnit XML format
- Coverage HTML report

**Generating Reports:**
```bash
pytest --junitxml=test-results/results.xml --cov-report=html