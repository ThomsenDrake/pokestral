import unittest
from memory_map.pokemon_memory_map import (
    get_num_party_pokemon,
    get_party_pokemon_species,
    get_player_money,
    get_current_map_number,
    get_player_coordinates,
    get_block_coordinates,
    is_in_battle,
    get_battle_type
)

class TestPokemonMemoryMap(unittest.TestCase):
    def setUp(self):
        """Create a mock memory array for testing."""
        self.memory = bytearray(0x10000)  # 64KB memory

        # Set up test values
        self.memory[0xD163] = 3  # 3 Pokémon in party
        self.memory[0xD164:0xD167] = [0x01, 0x04, 0x07]  # Bulbasaur, Charmander, Squirtle
        self.memory[0xD347:0xD350] = [0xE1, 0x03, 0x00]  # 1000 in money (little-endian)
        self.memory[0xD35E] = 0x0A  # Map number 10
        self.memory[0xD361] = 0x14  # X coordinate 20
        self.memory[0xD362] = 0x0F  # Y coordinate 15
        self.memory[0xD363] = 0x01  # Block X 1
        self.memory[0xD364] = 0x02  # Block Y 2
        self.memory[0xD057] = 0x01  # In battle
        self.memory[0xD05A] = 0x02  # Battle type 2

    def test_get_num_party_pokemon(self):
        self.assertEqual(get_num_party_pokemon(self.memory), 3)

    def test_get_party_pokemon_species(self):
        self.assertEqual(get_party_pokemon_species(self.memory), [0x01, 0x04, 0x07])

    def test_get_player_money(self):
        self.assertEqual(get_player_money(self.memory), 1000)

    def test_get_current_map_number(self):
        self.assertEqual(get_current_map_number(self.memory), 0x0A)

    def test_get_player_coordinates(self):
        self.assertEqual(get_player_coordinates(self.memory), (0x14, 0x0F))

    def test_get_block_coordinates(self):
        self.assertEqual(get_block_coordinates(self.memory), (0x01, 0x02))

    def test_is_in_battle(self):
        self.assertTrue(is_in_battle(self.memory))

    def test_get_battle_type(self):
        self.assertEqual(get_battle_type(self.memory), 0x02)

if __name__ == '__main__':
    unittest.main()