"""
Memory mapping module for Pokémon Blue AI agent.
Defines constants for key RAM addresses and helper functions
to convert byte sequences into meaningful values.
"""

# RAM address constants
NUM_PARTY_POKÉMON = 0xD163
PARTY_POKÉMON_SPECIES_START = 0xD164
PLAYER_MONEY_START = 0xD347
PLAYER_MONEY_END = 0xD349
CURRENT_MAP_NUMBER = 0xD35E
PLAYER_X_COORD = 0xD361
PLAYER_Y_COORD = 0xD362
BLOCK_X_COORD = 0xD363
BLOCK_Y_COORD = 0xD364
IN_BATTLE_FLAG = 0xD057
BATTLE_TYPE = 0xD05A

def get_num_party_pokemon(memory):
    """Get the number of Pokémon in the player's party."""
    return memory[NUM_PARTY_POKÉMON]

def get_party_pokemon_species(memory):
    """Get the list of Pokémon species in the player's party."""
    num_pokemon = get_num_party_pokemon(memory)
    return memory[PARTY_POKÉMON_SPECIES_START:PARTY_POKÉMON_SPECIES_START + num_pokemon]

def get_player_money(memory):
    """Get the player's money as an integer value."""
    # Money is stored in 3 bytes (little-endian)
    money_bytes = memory[PLAYER_MONEY_START:PLAYER_MONEY_END + 1]
    return money_bytes[0] + (money_bytes[1] << 8) + (money_bytes[2] << 16)

def get_current_map_number(memory):
    """Get the current map number."""
    return memory[CURRENT_MAP_NUMBER]

def get_player_coordinates(memory):
    """Get the player's X and Y coordinates."""
    x = memory[PLAYER_X_COORD]
    y = memory[PLAYER_Y_COORD]
    return (x, y)

def get_block_coordinates(memory):
    """Get the block X and Y coordinates."""
    block_x = memory[BLOCK_X_COORD]
    block_y = memory[BLOCK_Y_COORD]
    return (block_x, block_y)

def is_in_battle(memory):
    """Check if the player is in battle."""
    return memory[IN_BATTLE_FLAG] != 0

def get_battle_type(memory):
    """Get the current battle type."""
    return memory[BATTLE_TYPE]