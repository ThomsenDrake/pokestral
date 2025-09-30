import unittest
from memory_map.pokemon_memory_map import PokemonMemoryMap

class TestPokemonMemoryMap(unittest.TestCase):
    def setUp(self):
        """Create a mock memory array for testing."""
        self.memory_map = PokemonMemoryMap()
        self.memory = bytearray(0x10000)  # 64KB memory

        # Set up test values
        self.memory[0xD163] = 3  # 3 Pokémon in party
        self.memory[0xD164:0xD167] = [0x01, 0x04, 0x07]  # Bulbasaur, Charmander, Squirtle
        self.memory[0xD347:0xD349] = [0x01, 0x0F, 0x00]  # 3841 in money (little-endian: 0x000F01 = 1 + 15*256)
        self.memory[0xD35E] = 0x0A  # Map number 10
        self.memory[0xD361] = 0x0F  # X coordinate 15 (address 0xD361 is PLAYER_X_COORD)
        self.memory[0xD362] = 0x14  # Y coordinate 20 (address 0xD362 is PLAYER_Y_COORD)
        self.memory[0xD363] = 0x01  # Block X 1
        self.memory[0xD364] = 0x02  # Block Y 2
        self.memory[0xD057] = 0x01  # In battle
        self.memory[0xD05A] = 0x02  # Battle type 2

    def test_get_num_party_pokemon(self):
        self.assertEqual(self.memory_map.get_num_party_pokemon(self.memory), 3)

    def test_get_party_pokemon_species(self):
        result = self.memory_map.get_party_pokemon_species(self.memory)
        # Convert bytearray to list for comparison
        self.assertEqual(list(result), [0x01, 0x04, 0x07])

    def test_get_player_money(self):
        self.assertEqual(self.memory_map.get_player_money(self.memory), 3841)

    def test_get_current_map_number(self):
        self.assertEqual(self.memory_map.get_current_map_number(self.memory), 0x0A)

    def test_get_player_coordinates(self):
        self.assertEqual(self.memory_map.get_player_coordinates(self.memory), (0x0F, 0x14))  # (X=15, Y=20)

    def test_get_block_coordinates(self):
        self.assertEqual(self.memory_map.get_block_coordinates(self.memory), (0x01, 0x02))

    def test_is_in_battle(self):
        self.assertTrue(self.memory_map.is_in_battle(self.memory))

    def test_get_battle_type(self):
        self.assertEqual(self.memory_map.get_battle_type(self.memory), 0x02)

if __name__ == '__main__':
    unittest.main()