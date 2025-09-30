# Testing Documentation

## Test Suite Overview

The Pokémon Blue AI Agent includes comprehensive testing to ensure reliability, performance, and correctness. The test suite is organized into several categories:

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **System Tests**: End-to-end workflow testing
4. **Performance Tests**: Speed and resource usage validation
5. **Regression Tests**: Prevention of previously fixed issues

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_emulator.py     # Emulator interface tests
│   ├── test_memory_map.py   # Memory mapping tests
│   ├── test_state_detector.py # State detection tests
│   ├── test_mistral_api.py  # Mistral API integration tests
│   ├── test_battle_helper.py # Battle strategy tests
│   ├── test_pathfinder.py   # Pathfinding algorithm tests
│   └── test_puzzle_solver.py # Puzzle solving tests
├── integration/             # Integration tests
│   ├── test_agent_emulator.py # Agent-emulator integration
│   ├── test_memory_state.py # Memory-state integration
│   └── test_tool_coordination.py # Tool coordination tests
├── system/                  # End-to-end system tests
│   └── test_full_workflow.py # Complete agent workflow tests
├── performance/             # Performance benchmarking
│   ├── test_emulator_speed.py # Emulator performance tests
│   ├── test_api_latency.py  # API response time tests
│   └── test_memory_usage.py # Memory consumption tests
├── fixtures/                # Test data and mock objects
│   ├── mock_memory.py       # Mock memory views for testing
│   ├── sample_responses.py  # Sample API responses
│   └── test_roms/           # Minimal test ROMs (if applicable)
└── conftest.py             # pytest configuration and fixtures
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests in a specific directory
pytest tests/unit/

# Run a specific test file
pytest tests/unit/test_emulator.py

# Run tests matching a pattern
pytest -k "test_send_input"
```

### Test Coverage
```bash
# Run with coverage reporting
pytest --cov=.

# Run with detailed coverage report
pytest --cov=. --cov-report=html

# Run with coverage requirements
pytest --cov=. --cov-fail-under=80
```

### Parallel Test Execution
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

## Unit Testing

### Emulator Tests
Located in `tests/unit/test_emulator.py`:

```python
def test_emulator_initialization():
    """Test emulator initialization with valid ROM"""
    emulator = PokemonEmulator("test_rom.gb")
    assert emulator.is_running() == True

def test_send_input_valid_buttons():
    """Test sending valid button inputs"""
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("up", 0.1)
    assert result == True

def test_send_input_invalid_buttons():
    """Test sending invalid button inputs"""
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("invalid_button", 0.1)
    assert result == False

def test_get_screenshot():
    """Test screenshot capture functionality"""
    emulator = PokemonEmulator("test_rom.gb")
    screenshot = emulator.get_screenshot()
    assert screenshot is not None
    assert isinstance(screenshot, np.ndarray)
```

### Memory Map Tests
Located in `tests/unit/test_memory_map.py`:

```python
def test_get_party_pokemon_species():
    """Test extracting party Pokémon species from memory"""
    memory_map = PokemonMemoryMap()
    mock_memory = create_mock_memory({
        0xD163: 2,  # 2 Pokémon in party
        0xD164: 1,  # Bulbasaur
        0xD165: 4   # Charmander
    })
    
    species = memory_map.get_party_pokemon_species(mock_memory)
    assert species == [1, 4]

def test_get_player_coordinates():
    """Test extracting player coordinates from memory"""
    memory_map = PokemonMemoryMap()
    mock_memory = create_mock_memory({
        0xD361: 10,  # Y coordinate
        0xD362: 20   # X coordinate
    })
    
    x, y = memory_map.get_player_coordinates(mock_memory)
    assert x == 20
    assert y == 10

def test_is_in_battle():
    """Test battle state detection"""
    memory_map = PokemonMemoryMap()
    
    # Test in battle
    mock_memory_battle = create_mock_memory({0xD057: 1})
    assert memory_map.is_in_battle(mock_memory_battle) == True
    
    # Test not in battle
    mock_memory_no_battle = create_mock_memory({0xD057: 0})
    assert memory_map.is_in_battle(mock_memory_no_battle) == False
```

### State Detector Tests
Located in `tests/unit/test_state_detector.py`:

```python
def test_detect_title_screen():
    """Test title screen detection"""
    state_detector = StateDetector()
    mock_memory = create_mock_memory({
        0xD35E: 0,      # No map loaded
        0xD057: 0       # Not in battle
    })
    
    state = state_detector.detect_state(mock_memory)
    assert state == GameState.TITLE_SCREEN

def test_detect_overworld():
    """Test overworld state detection"""
    state_detector = StateDetector()
    mock_memory = create_mock_memory({
        0xD35E: 1,      # Map loaded
        0xD057: 0       # Not in battle
    })
    
    state = state_detector.detect_state(mock_memory)
    assert state == GameState.OVERWORLD

def test_detect_battle():
    """Test battle state detection"""
    state_detector = StateDetector()
    mock_memory = create_mock_memory({
        0xD057: 1       # In battle flag set
    })
    
    state = state_detector.detect_state(mock_memory)
    assert state == GameState.BATTLE
```

### Mistral API Tests
Located in `tests/unit/test_mistral_api.py`:

```python
def test_query_with_valid_prompt():
    """Test querying Mistral API with valid prompt"""
    with patch('agent_core.mistral_api.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"action": "move_up", "reason": "Test reason"}'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        api = MistralAPI("test_key")
        result = api.query("Test prompt")
        
        assert "action" in result
        assert "move_up" in result

def test_query_with_api_error():
    """Test handling API errors"""
    with patch('agent_core.mistral_api.requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        api = MistralAPI("test_key")
        result = api.query("Test prompt")
        
        assert "error" in result

def test_chat_completion_json_mode():
    """Test chat completion with JSON response format"""
    api = MistralAPI("test_key")
    
    messages = [{"role": "user", "content": "Test prompt"}]
    response_format = {"type": "json_object"}
    
    # This should not raise an exception
    # Actual testing would require mocking the API call
```

## Integration Testing

### Agent-Emulator Integration
Located in `tests/integration/test_agent_emulator.py`:

```python
def test_agent_emulator_connection():
    """Test agent can connect to and control emulator"""
    emulator = PokemonEmulator("test_rom.gb")
    agent = AgentCore(rom_path="test_rom.gb", headless=True)
    
    # Connect agent to emulator
    agent.connect_emulator(emulator)
    
    # Test basic interaction
    assert agent.emulator == emulator
    assert agent.pyboy is not None

def test_execute_simple_action():
    """Test agent can execute simple actions through emulator"""
    emulator = PokemonEmulator("test_rom.gb")
    agent = AgentCore(rom_path="test_rom.gb", headless=True)
    agent.connect_emulator(emulator)
    
    # Execute a simple action
    actions = {"action": "move_up", "duration": 0.1}
    agent.execute_actions(actions)
    
    # Verify input was sent (this would require mocking the emulator's input method)
```

### Memory-State Integration
Located in `tests/integration/test_memory_state.py`:

```python
def test_memory_state_consistency():
    """Test consistency between memory mapping and state detection"""
    emulator = PokemonEmulator("test_rom.gb")
    memory_map = PokemonMemoryMap()
    state_detector = StateDetector()
    
    # Get memory view from emulator
    memory = emulator.pyboy.get_memory()
    
    # Test that memory mapping and state detection are consistent
    party_species = memory_map.get_party_pokemon_species(memory)
    game_state = state_detector.detect_state(memory)
    
    # Both should operate on the same memory without conflicts
    assert party_species is not None
    assert game_state is not None
```

## Performance Testing

### Emulator Performance
Located in `tests/performance/test_emulator_speed.py`:

```python
def test_emulator_frame_rate():
    """Test emulator maintains target frame rate"""
    emulator = PokemonEmulator("test_rom.gb")
    
    start_time = time.time()
    frames_processed = 0
    
    # Run emulator for 1 second
    while time.time() - start_time < 1.0:
        emulator.tick()
        frames_processed += 1
    
    # Should maintain at least 30 FPS
    assert frames_processed >= 30

def test_memory_access_performance():
    """Test memory access speed"""
    emulator = PokemonEmulator("test_rom.gb")
    memory_map = PokemonMemoryMap()
    memory = emulator.pyboy.get_memory()
    
    # Time multiple memory accesses
    start_time = time.time()
    for _ in range(1000):
        memory_map.get_party_pokemon_species(memory)
        memory_map.get_player_coordinates(memory)
    
    elapsed = time.time() - start_time
    # Should complete 1000 accesses in under 1 second
    assert elapsed < 1.0
```

### API Performance
Located in `tests/performance/test_api_latency.py`:

```python
def test_api_response_time():
    """Test API response time is within acceptable limits"""
    api = MistralAPI("test_key")
    
    start_time = time.time()
    response = api.query("Quick test prompt")
    elapsed = time.time() - start_time
    
    # Should respond within 5 seconds
    assert elapsed < 5.0
    assert len(response) > 0

def test_concurrent_api_requests():
    """Test handling concurrent API requests"""
    api = MistralAPI("test_key")
    
    def make_request():
        return api.query("Test prompt")
    
    # Make concurrent requests
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(3)]
        results = [future.result() for future in futures]
    
    # All requests should succeed
    assert all(len(result) > 0 for result in results)
```

## Test Fixtures and Mocks

### Memory Mocking
Located in `tests/fixtures/mock_memory.py`:

```python
def create_mock_memory(address_values: Dict[int, int]) -> memoryview:
    """Create mock memory view for testing"""
    # Create a bytearray to simulate memory
    mock_memory_data = bytearray(0x10000)  # 64KB of memory
    
    # Set specified address values
    for address, value in address_values.items():
        if 0 <= address < len(mock_memory_data):
            mock_memory_data[address] = value
    
    # Return as memoryview
    return memoryview(mock_memory_data)

def create_mock_pyboy() -> Mock:
    """Create mock PyBoy instance for testing"""
    mock_pyboy = Mock()
    mock_pyboy.get_memory.return_value = create_mock_memory({})
    mock_pyboy.tick.return_value = True
    return mock_pyboy
```

### API Response Mocking
Located in `tests/fixtures/sample_responses.py`:

```python
VALID_ACTION_RESPONSES = [
    '{"action": "move_up", "reason": "Moving up to explore"}',
    '{"action": "open_menu", "reason": "Opening menu to check status"}',
    '{"action": "interact", "reason": "Interacting with NPC"}'
]

INVALID_RESPONSES = [
    '{"invalid": "format"}',
    '{"action": "unknown_action"}',
    '{"action": "move_up"',  # Malformed JSON
    ''  # Empty response
]
```

## Continuous Integration

### GitHub Actions Workflow
Located in `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## Test Best Practices

### Writing Effective Tests

1. **Keep Tests Independent**
```python
# Good - each test can run independently
def test_valid_input():
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("up")
    assert result == True

def test_invalid_input():
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("invalid")
    assert result == False
```

2. **Use Descriptive Test Names**
```python
# Good - clear what is being tested
def test_send_input_returns_false_for_invalid_button():
    pass

# Bad - unclear what the test covers
def test_input():
    pass
```

3. **Test Edge Cases**
```python
def test_send_input_with_zero_duration():
    """Test sending input with zero duration"""
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("up", 0.0)
    assert result == True  # Should still work

def test_send_input_with_negative_duration():
    """Test sending input with negative duration"""
    emulator = PokemonEmulator("test_rom.gb")
    result = emulator.send_input("up", -1.0)
    # Should handle gracefully, perhaps default to 0.1
    assert result == True
```

### Mocking External Dependencies

```python
def test_mistral_api_with_network_error():
    """Test handling network errors in Mistral API"""
    with patch('agent_core.mistral_api.requests.post') as mock_post:
        mock_post.side_effect = requests.ConnectionError("Network error")
        
        api = MistralAPI("test_key")
        response = api.query("Test prompt")
        
        # Should return error response
        assert "error" in response
        assert "Network error" in response

def test_emulator_without_visual_display():
    """Test emulator can run without visual display"""
    # This would test headless mode functionality
    emulator = PokemonEmulator("test_rom.gb", headless=True)
    assert emulator.is_running() == True
```

## Code Coverage Requirements

### Minimum Coverage Thresholds
- **Overall**: 80%
- **Core Components**: 90%
  - `emulator/emulator.py`: 90%
  - `agent_core/agent_core.py`: 90%
  - `memory_map/pokemon_memory_map.py`: 95%
- **Critical Paths**: 95%
  - API integration
  - Input handling
  - State detection

### Coverage Reporting
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Generate XML for CI/CD
pytest --cov=. --cov-report=xml

# Fail if coverage below threshold
pytest --cov=. --cov-fail-under=80
```

## Regression Testing

### Tracking Previously Fixed Issues
Maintain a regression test suite that includes tests for previously discovered and fixed bugs:

```python
def test_regression_button_input_validation():
    """Regression test for button input validation bug"""
    # This test ensures that issue #123 (invalid button inputs
    # causing crashes) doesn't reoccur
    
    emulator = PokemonEmulator("test_rom.gb")
    
    # Test cases that previously caused crashes
    invalid_inputs = ["", None, 123, "UPPERCASE", "invalid_button"]
    
    for invalid_input in invalid_inputs:
        # Should return False, not crash
        result = emulator.send_input(invalid_input)
        assert result == False
```

## Performance Benchmarks

### Baseline Measurements
Track performance metrics to detect regressions:

```python
def test_performance_baseline():
    """Performance baseline test"""
    # Record baseline performance measurements
    baseline_fps = 60.0
    baseline_memory_mb = 500.0
    baseline_api_response_ms = 1000.0
    
    # Run performance test
    current_fps, current_memory, current_api_time = run_performance_test()
    
    # Allow 10% variance from baseline
    assert current_fps >= baseline_fps * 0.9
    assert current_memory <= baseline_memory_mb * 1.1
    assert current_api_time <= baseline_api_response_ms * 1.1
```

This comprehensive testing documentation provides a solid foundation for maintaining the quality and reliability of the Pokémon Blue AI Agent system.