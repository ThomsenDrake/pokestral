import unittest
from unittest.mock import MagicMock
from state_detector.game_state import GameState, StateDetector
from memory_map.pokemon_memory_map import PokemonMemoryMap

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.memory_map = MagicMock(spec=PokemonMemoryMap)
        self.state_detector = StateDetector(self.memory_map)

    def test_overworld_state(self):
        """Test detection of OVERWORLD state."""
        self.memory_map.read_byte.side_effect = lambda addr: {
            0xD057: 0,  # Not in battle
            0xD05A: 0,  # No battle type
            0xD362: 10, # Player X coordinate
            0xD365: 15  # Player Y coordinate
        }.get(addr, 0)

        state = self.state_detector.detect_state()
        self.assertEqual(state, GameState.OVERWORLD)

    def test_battle_state(self):
        """Test detection of BATTLE state."""
        self.memory_map.read_byte.side_effect = lambda addr: {
            0xD057: 1,  # In battle
            0xD05A: 1,  # Wild battle
            0xD362: 10,
            0xD365: 15
        }.get(addr, 0)

        state = self.state_detector.detect_state()
        self.assertEqual(state, GameState.BATTLE)

    def test_dialog_state(self):
        """Test detection of DIALOG state."""
        self.memory_map.read_byte.side_effect = lambda addr: {
            0xD057: 0,
            0xD05A: 0,
            0xD362: 10,
            0xD365: 15
        }.get(addr, 0)

        # Mock the dialog detection
        self.state_detector._is_in_dialog = MagicMock(return_value=True)

        state = self.state_detector.detect_state()
        self.assertEqual(state, GameState.DIALOG)

    def test_menu_state(self):
        """Test detection of MENU state."""
        self.memory_map.read_byte.side_effect = lambda addr: {
            0xD057: 0,
            0xD05A: 0,
            0xD362: 10,
            0xD365: 15
        }.get(addr, 0)

        # Mock the menu detection
        self.state_detector._is_in_menu = MagicMock(return_value=True)

        state = self.state_detector.detect_state()
        self.assertEqual(state, GameState.MENU)

if __name__ == '__main__':
    unittest.main()