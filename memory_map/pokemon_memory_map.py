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


class PokemonMemoryMap:
    """Pokemon memory mapping class with methods to read memory values."""
    
    def __init__(self):
        """Initialize the PokemonMemoryMap."""
        pass
    
    def read_byte(self, memory, address):
        """Read a single byte from memory."""
        # Handle PyBoy API differences
        try:
            # For newer PyBoy versions, memory might need to be accessed differently
            if isinstance(memory, (list, tuple)):
                return memory[address]
            elif hasattr(memory, '__getitem__'):
                return memory[address]
            else:
                # If memory is a mapping-like object
                return getattr(memory, 'get', lambda x: memory[x])(address)
        except (TypeError, IndexError, KeyError):
            # Fallback if direct access fails
            if hasattr(memory, '__getitem__'):
                return memory[address]
            else:
                return 0  # Default value if access fails
    
    def get_num_party_pokemon(self, memory):
        """Get the number of Pokémon in the player's party."""
        return memory[NUM_PARTY_POKÉMON]
    
    def get_party_pokemon_species(self, memory):
        """Get the list of Pokémon species in the player's party."""
        num_pokemon = self.get_num_party_pokemon(memory)
        return memory[PARTY_POKÉMON_SPECIES_START:PARTY_POKÉMON_SPECIES_START + num_pokemon]
    
    def get_player_money(self, memory):
        """Get the player's money as an integer value."""
        # Money is stored in 3 bytes (little-endian)
        money_bytes = memory[PLAYER_MONEY_START:PLAYER_MONEY_END + 1]
        return money_bytes[0] + (money_bytes[1] << 8) + (money_bytes[2] << 16)
    
    def get_current_map_number(self, memory):
        """Get the current map number."""
        return memory[CURRENT_MAP_NUMBER]
    
    def get_player_coordinates(self, memory):
        """Get the player's X and Y coordinates."""
        x = memory[PLAYER_X_COORD]
        y = memory[PLAYER_Y_COORD]
        return (x, y)
    
    def get_block_coordinates(self, memory):
        """Get the block X and Y coordinates."""
        block_x = memory[BLOCK_X_COORD]
        block_y = memory[BLOCK_Y_COORD]
        return (block_x, block_y)
    
    def is_in_battle(self, memory):
        """Check if the player is in battle."""
        return memory[IN_BATTLE_FLAG] != 0
    
    def get_battle_type(self, memory):
        """Get the current battle type."""
        return memory[BATTLE_TYPE]

    def get_battle_pokemon_data(self, memory, is_player=True):
        """Get comprehensive battle Pokemon data."""
        if is_player:
            base_addr = 0xCF95  # PLAYER_BATTLE_POKEMON_1_SPECIES from below
        else:
            base_addr = 0xCFF1  # ENEMY_BATTLE_POKEMON_SPECIES from below

        species = memory[base_addr]
        level = memory[base_addr + 2]
        hp = int.from_bytes(memory[base_addr + 7:base_addr + 9], byteorder='little')
        max_hp = int.from_bytes(memory[base_addr + 9:base_addr + 11], byteorder='little')
        status = memory[base_addr + 10]
        type1 = memory[base_addr + 11]
        type2 = memory[base_addr + 12]

        # Get moves
        moves = []
        for i in range(4):
            move_id = int.from_bytes(memory[base_addr + 13 + (i * 2):base_addr + 15 + (i * 2)], byteorder='little')
            if move_id > 0:
                move_data = self.get_move_data(memory, move_id)
                if move_data:
                    moves.append(move_data)

        # Get stats
        attack = int.from_bytes(memory[base_addr + 17:base_addr + 19], byteorder='little')
        defense = int.from_bytes(memory[base_addr + 19:base_addr + 21], byteorder='little')
        speed = int.from_bytes(memory[base_addr + 21:base_addr + 23], byteorder='little')
        special = int.from_bytes(memory[base_addr + 23:base_addr + 25], byteorder='little')

        return {
            'species': species,
            'level': level,
            'hp': hp,
            'max_hp': max_hp,
            'status': status,
            'types': [type1, type2] if type2 != 0 else [type1],
            'moves': moves,
            'attack': attack,
            'defense': defense,
            'speed': speed,
            'special': special
        }

    def get_move_data(self, memory, move_id):
        """Get move data from ROM."""
        if move_id == 0:
            return None

        # This is a simplified version - in practice, move data is in ROM
        move_addr = 0x3800 + (move_id - 1) * 7
        try:
            # For now, just return basic info
            move_types = {
                1: 0x00,  # Normal
                22: 0x0A,  # Fire
                35: 0x0F,  # Water
                36: 0x17,  # Electric
                73: 0x04,  # Poison
                76: 0x19,  # Ice
                91: 0x0C,  # Psychic
                100: 0x15,  # Rock
            }
            
            move_type = move_types.get(move_id, 0x00)
            return {
                'id': move_id,
                'name': f"Move_{move_id:03d}",
                'type': move_type,
                'category': 'Physical' if move_type in [0x00, 0x01, 0x02, 0x04, 0x05, 0x06, 0x07, 0x08, 0x0A] else 'Special',
                'power': 40,  # Default power
                'pp': 15,     # Default PP
                'accuracy': 100
            }
        except IndexError:
            return None


# Battle-specific memory addresses for Pokemon Blue
# Player Pokemon in Battle
PLAYER_BATTLE_POKEMON_1_SPECIES = 0xCF95
PLAYER_BATTLE_POKEMON_1_LEVEL = 0xCF97
PLAYER_BATTLE_POKEMON_1_HP = 0xCF9C  # 2 bytes
PLAYER_BATTLE_POKEMON_1_MAX_HP = 0xCF9E  # 2 bytes
PLAYER_BATTLE_POKEMON_1_STATUS = 0xCFA1
PLAYER_BATTLE_POKEMON_1_TYPE1 = 0xCFA2
PLAYER_BATTLE_POKEMON_1_TYPE2 = 0xCFA3
PLAYER_BATTLE_POKEMON_1_MOVES = 0xCFA4  # 4 moves, 2 bytes each
PLAYER_BATTLE_POKEMON_1_PP = 0xCFAC  # 4 PP values
PLAYER_BATTLE_POKEMON_1_ATTACK = 0xCFB2  # 2 bytes
PLAYER_BATTLE_POKEMON_1_DEFENSE = 0xCFB4  # 2 bytes
PLAYER_BATTLE_POKEMON_1_SPEED = 0xCFB6  # 2 bytes
PLAYER_BATTLE_POKEMON_1_SPECIAL = 0xCFB8  # 2 bytes

# Enemy Pokemon in Battle
ENEMY_BATTLE_POKEMON_SPECIES = 0xCFF1
ENEMY_BATTLE_POKEMON_LEVEL = 0xCFF3
ENEMY_BATTLE_POKEMON_HP = 0xCFF8  # 2 bytes
ENEMY_BATTLE_POKEMON_MAX_HP = 0xCFFA  # 2 bytes
ENEMY_BATTLE_POKEMON_STATUS = 0xCFFD
ENEMY_BATTLE_POKEMON_TYPE1 = 0xCFFE
ENEMY_BATTLE_POKEMON_TYPE2 = 0xCFFF
ENEMY_BATTLE_POKEMON_MOVES = 0xD000  # 4 moves, 2 bytes each
ENEMY_BATTLE_POKEMON_PP = 0xD008  # 4 PP values
ENEMY_BATTLE_POKEMON_ATTACK = 0xD00E  # 2 bytes
ENEMY_BATTLE_POKEMON_DEFENSE = 0xD010  # 2 bytes
ENEMY_BATTLE_POKEMON_SPEED = 0xD012  # 2 bytes
ENEMY_BATTLE_POKEMON_SPECIAL = 0xD014  # 2 bytes

# Battle state information
BATTLE_CURRENT_TURN = 0xD056
BATTLE_MENU_SELECTION = 0xD058
BATTLE_SELECTED_MOVE = 0xD059
BATTLE_PARTY_SELECTION = 0xD05B
BATTLE_TEXT_BOX_STATE = 0xD05C
BATTLE_ANIMATION_STATE = 0xD05D

# Battle result/status
BATTLE_RESULT = 0xD05E
BATTLE_END_FLAG = 0xD05F

# Player party information during battle
PLAYER_PARTY_COUNT = 0xD163
PLAYER_PARTY_SPECIES = 0xD164  # 6 Pokemon, 1 byte each
PLAYER_PARTY_LEVELS = 0xD18C  # 6 Pokemon, 1 byte each
PLAYER_PARTY_HP_START = 0xD16B  # 6 Pokemon, 2 bytes each

# Item information
PLAYER_ITEMS_START = 0xD31D  # 20 items, 2 bytes each (item ID + quantity)
BAG_ITEMS_COUNT = 0xD31C

# Status conditions
STATUS_CONDITIONS = {
    0x00: "None",
    0x01: "Sleep",
    0x02: "Poison",
    0x04: "Burn",
    0x08: "Freeze",
    0x10: "Paralysis",
    0x20: "Badly Poisoned",
    0x40: "Frozen",  # Different from Freeze?
    0x80: "Fainted"
}

# Move information mapping
MOVE_DATA_START = 0x3800  # Moves start at this address in ROM
MOVE_TYPE_OFFSET = 0x02  # Type offset in move data
MOVE_CATEGORY_OFFSET = 0x03  # Physical/Special/Status
MOVE_POWER_OFFSET = 0x04  # Base power
MOVE_PP_OFFSET = 0x05  # Base PP
MOVE_ACCURACY_OFFSET = 0x06  # Accuracy

# Complete Generation 1 move names dictionary (165 moves)
MOVE_NAMES = {
    0x01: "Pound", 0x02: "Karate Chop", 0x03: "Double Slap", 0x04: "Comet Punch",
    0x05: "Mega Punch", 0x06: "Pay Day", 0x07: "Fire Punch", 0x08: "Ice Punch",
    0x09: "Thunder Punch", 0x0A: "Scratch", 0x0B: "Vice Grip", 0x0C: "Guillotine",
    0x0D: "Razor Wind", 0x0E: "Swords Dance", 0x0F: "Cut", 0x10: "Gust",
    0x11: "Wing Attack", 0x12: "Whirlwind", 0x13: "Fly", 0x14: "Bind",
    0x15: "Slam", 0x16: "Vine Whip", 0x17: "Stomp", 0x18: "Double Kick",
    0x19: "Mega Kick", 0x1A: "Jump Kick", 0x1B: "Rolling Kick", 0x1C: "Sand Attack",
    0x1D: "Headbutt", 0x1E: "Horn Attack", 0x1F: "Fury Attack", 0x20: "Horn Drill",
    0x21: "Tackle", 0x22: "Body Slam", 0x23: "Wrap", 0x24: "Take Down",
    0x25: "Thrash", 0x26: "Double-Edge", 0x27: "Tail Whip", 0x28: "Poison Sting",
    0x29: "Twineedle", 0x2A: "Pin Missile", 0x2B: "Leer", 0x2C: "Bite",
    0x2D: "Growl", 0x2E: "Roar", 0x2F: "Sing", 0x30: "Supersonic",
    0x31: "Sonic Boom", 0x32: "Disable", 0x33: "Acid", 0x34: "Ember",
    0x35: "Flamethrower", 0x36: "Mist", 0x37: "Water Gun", 0x38: "Hydro Pump",
    0x39: "Surf", 0x3A: "Ice Beam", 0x3B: "Blizzard", 0x3C: "Psybeam",
    0x3D: "Bubble Beam", 0x3E: "Aurora Beam", 0x3F: "Hyper Beam", 0x40: "Peck",
    0x41: "Drill Peck", 0x42: "Submission", 0x43: "Low Kick", 0x44: "Counter",
    0x45: "Seismic Toss", 0x46: "Strength", 0x47: "Absorb", 0x48: "Mega Drain",
    0x49: "Leech Seed", 0x4A: "Growth", 0x4B: "Razor Leaf", 0x4C: "Solar Beam",
    0x4D: "Poison Powder", 0x4E: "Stun Spore", 0x4F: "Sleep Powder", 0x50: "Petal Dance",
    0x51: "String Shot", 0x52: "Dragon Rage", 0x53: "Fire Spin", 0x54: "Thunder Shock",
    0x55: "Thunderbolt", 0x56: "Thunder Wave", 0x57: "Thunder", 0x58: "Rock Throw",
    0x59: "Earthquake", 0x5A: "Fissure", 0x5B: "Dig", 0x5C: "Toxic",
    0x5D: "Confusion", 0x5E: "Psychic", 0x5F: "Hypnosis", 0x60: "Meditate",
    0x61: "Agility", 0x62: "Quick Attack", 0x63: "Rage", 0x64: "Teleport",
    0x65: "Night Shade", 0x66: "Mimic", 0x67: "Screech", 0x68: "Double Team",
    0x69: "Recover", 0x6A: "Harden", 0x6B: "Minimize", 0x6C: "Smokescreen",
    0x6D: "Confuse Ray", 0x6E: "Withdraw", 0x6F: "Defense Curl", 0x70: "Barrier",
    0x71: "Light Screen", 0x72: "Haze", 0x73: "Reflect", 0x74: "Focus Energy",
    0x75: "Bide", 0x76: "Metronome", 0x77: "Mirror Move", 0x78: "Self-Destruct",
    0x79: "Egg Bomb", 0x7A: "Lick", 0x7B: "Smog", 0x7C: "Sludge",
    0x7D: "Bone Club", 0x7E: "Fire Blast", 0x7F: "Waterfall", 0x80: "Clamp",
    0x81: "Swift", 0x82: "Skull Bash", 0x83: "Spike Cannon", 0x84: "Constrict",
    0x85: "Amnesia", 0x86: "Kinesis", 0x87: "Soft-Boiled", 0x88: "High Jump Kick",
    0x89: "Glare", 0x8A: "Dream Eater", 0x8B: "Poison Gas", 0x8C: "Barrage",
    0x8D: "Leech Life", 0x8E: "Lovely Kiss", 0x8F: "Sky Attack", 0x90: "Transform",
    0x91: "Bubble", 0x92: "Dizzy Punch", 0x93: "Spore", 0x94: "Flash",
    0x95: "Psywave", 0x96: "Splash", 0x97: "Acid Armor", 0x98: "Crabhammer",
    0x99: "Explosion", 0x9A: "Fury Swipes", 0x9B: "Bonemerang", 0x9C: "Rest",
    0x9D: "Rock Slide", 0x9E: "Hyper Fang", 0x9F: "Sharpen", 0xA0: "Conversion",
    0xA1: "Tri Attack", 0xA2: "Super Fang", 0xA3: "Slash", 0xA4: "Substitute",
    0xA5: "Struggle"
}

# Pokemon species to type mapping (first type, second type)
POKEMON_TYPES = {
    0x01: (0x19, 0x00),  # Bulbasaur: Grass
    0x02: (0x19, 0x04),  # Ivysaur: Grass, Poison
    0x03: (0x19, 0x04),  # Venusaur: Grass, Poison
    0x04: (0x0A, 0x00),  # Charmander: Fire
    0x05: (0x0A, 0x00),  # Charmeleon: Fire
    0x06: (0x0A, 0x18),  # Charizard: Fire, Flying
    0x07: (0x0F, 0x00),  # Squirtle: Water
    0x08: (0x0F, 0x00),  # Wartortle: Water
    0x09: (0x0F, 0x00),  # Blastoise: Water
    0x0A: (0x07, 0x00),  # Caterpie: Bug
    0x0B: (0x07, 0x00),  # Metapod: Bug
    0x0C: (0x07, 0x18),  # Butterfree: Bug, Flying
    0x0D: (0x07, 0x04),  # Weedle: Bug, Poison
    0x0E: (0x07, 0x04),  # Kakuna: Bug, Poison
    0x0F: (0x07, 0x04),  # Beedrill: Bug, Poison
    0x10: (0x07, 0x00),  # Pidgey: Normal, Flying
    0x11: (0x07, 0x00),  # Pidgeotto: Normal, Flying
    0x12: (0x07, 0x00),  # Pidgeot: Normal, Flying
    0x13: (0x00, 0x00),  # Rattata: Normal
    0x14: (0x00, 0x00),  # Raticate: Normal
    0x15: (0x07, 0x00),  # Spearow: Normal, Flying
    0x16: (0x07, 0x00),  # Fearow: Normal, Flying
    0x17: (0x04, 0x00),  # Ekans: Poison
    0x18: (0x04, 0x00),  # Arbok: Poison
    0x19: (0x0C, 0x00),  # Pikachu: Electric
    0x1A: (0x0C, 0x00),  # Raichu: Electric
    0x1B: (0x15, 0x00),  # Sandshrew: Ground
    0x1C: (0x15, 0x00),  # Sandslash: Ground
    0x1D: (0x04, 0x00),  # Nidoran♀: Poison
    0x1E: (0x04, 0x00),  # Nidorina: Poison
    0x1F: (0x04, 0x15),  # Nidoqueen: Poison, Ground
    0x20: (0x04, 0x00),  # Nidoran♂: Poison
    0x21: (0x04, 0x00),  # Nidorino: Poison
    0x22: (0x04, 0x15),  # Nidoking: Poison, Ground
    0x23: (0x19, 0x00),  # Clefairy: Fairy (Normal in Gen 1)
    0x24: (0x19, 0x00),  # Clefable: Fairy (Normal in Gen 1)
    0x25: (0x0A, 0x00),  # Vulpix: Fire
    0x26: (0x0A, 0x00),  # Ninetales: Fire
    0x27: (0x19, 0x00),  # Jigglypuff: Normal, Fairy (Normal in Gen 1)
    0x28: (0x19, 0x00),  # Wigglytuff: Normal, Fairy (Normal in Gen 1)
    0x29: (0x04, 0x15),  # Zubat: Poison, Flying
    0x2A: (0x04, 0x15),  # Golbat: Poison, Flying
    0x2B: (0x19, 0x00),  # Oddish: Grass, Poison
    0x2C: (0x19, 0x00),  # Gloom: Grass, Poison
    0x2D: (0x19, 0x00),  # Vileplume: Grass, Poison
    0x2E: (0x19, 0x00),  # Paras: Bug, Grass
    0x2F: (0x07, 0x19),  # Parasect: Bug, Grass
    0x30: (0x04, 0x00),  # Venonat: Bug, Poison
    0x31: (0x07, 0x04),  # Venomoth: Bug, Poison
    0x32: (0x15, 0x00),  # Diglett: Ground
    0x33: (0x15, 0x00),  # Dugtrio: Ground
    0x34: (0x19, 0x00),  # Meowth: Normal
    0x35: (0x19, 0x00),  # Persian: Normal
    0x36: (0x19, 0x00),  # Psyduck: Water
    0x37: (0x19, 0x00),  # Golduck: Water
    0x38: (0x19, 0x00),  # Mankey: Fighting
    0x39: (0x19, 0x00),  # Primeape: Fighting
    0x3A: (0x0A, 0x00),  # Growlithe: Fire
    0x3B: (0x0A, 0x00),  # Arcanine: Fire
    0x3C: (0x0F, 0x00),  # Poliwag: Water
    0x3D: (0x0F, 0x00),  # Poliwhirl: Water
    0x3E: (0x0F, 0x19),  # Poliwrath: Water, Fighting
    0x3F: (0x19, 0x00),  # Abra: Psychic
    0x40: (0x19, 0x00),  # Kadabra: Psychic
    0x41: (0x19, 0x00),  # Alakazam: Psychic
    0x42: (0x19, 0x00),  # Machop: Fighting
    0x43: (0x19, 0x00),  # Machoke: Fighting
    0x44: (0x19, 0x00),  # Machamp: Fighting
    0x45: (0x19, 0x00),  # Bellsprout: Grass, Poison
    0x46: (0x19, 0x00),  # Weepinbell: Grass, Poison
    0x47: (0x19, 0x00),  # Victreebel: Grass, Poison
    0x48: (0x19, 0x00),  # Tentacool: Water, Poison
    0x49: (0x19, 0x00),  # Tentacruel: Water, Poison
    0x4A: (0x19, 0x00),  # Geodude: Rock, Ground
    0x4B: (0x19, 0x00),  # Graveler: Rock, Ground
    0x4C: (0x19, 0x00),  # Golem: Rock, Ground
    0x4D: (0x19, 0x00),  # Ponyta: Fire
    0x4E: (0x19, 0x00),  # Rapidash: Fire
    0x4F: (0x19, 0x00),  # Slowpoke: Water, Psychic
    0x50: (0x19, 0x00),  # Slowbro: Water, Psychic
    0x51: (0x19, 0x00),  # Doduo: Normal, Flying
    0x52: (0x19, 0x00),  # Dodrio: Normal, Flying
    0x53: (0x19, 0x00),  # Seel: Water
    0x54: (0x19, 0x00),  # Dewgong: Water, Ice
    0x55: (0x04, 0x00),  # Grimer: Poison
    0x56: (0x04, 0x00),  # Muk: Poison
    0x57: (0x19, 0x00),  # Shellder: Water
    0x58: (0x19, 0x00),  # Cloyster: Water, Ice
    0x59: (0x19, 0x00),  # Gastly: Ghost, Poison
    0x5A: (0x19, 0x00),  # Haunter: Ghost, Poison
    0x5B: (0x19, 0x00),  # Gengar: Ghost, Poison
    0x5C: (0x19, 0x00),  # Onix: Rock, Ground
    0x5D: (0x19, 0x00),  # Drowzee: Psychic
    0x5E: (0x19, 0x00),  # Hypno: Psychic
    0x5F: (0x19, 0x00),  # Krabby: Water
    0x60: (0x19, 0x00),  # Kingler: Water
    0x61: (0x0C, 0x00),  # Voltorb: Electric
    0x62: (0x0C, 0x00),  # Electrode: Electric
    0x63: (0x19, 0x00),  # Exeggcute: Grass, Psychic
    0x64: (0x19, 0x00),  # Exeggutor: Grass, Psychic
    0x65: (0x19, 0x00),  # Cubone: Ground
    0x66: (0x19, 0x00),  # Marowak: Ground
    0x67: (0x19, 0x00),  # Hitmonlee: Fighting
    0x68: (0x19, 0x00),  # Hitmonchan: Fighting
    0x69: (0x19, 0x00),  # Lickitung: Normal
    0x6A: (0x04, 0x00),  # Koffing: Poison
    0x6B: (0x04, 0x00),  # Weezing: Poison
    0x6C: (0x19, 0x00),  # Rhyhorn: Ground, Rock
    0x6D: (0x19, 0x00),  # Rhydon: Ground, Rock
    0x6E: (0x19, 0x00),  # Chansey: Normal
    0x6F: (0x19, 0x00),  # Tangela: Grass
    0x70: (0x19, 0x00),  # Kangaskhan: Normal
    0x71: (0x19, 0x00),  # Seaking: Water
    0x72: (0x19, 0x00),  # Staryu: Water
    0x73: (0x19, 0x00),  # Starmie: Water, Psychic
    0x74: (0x19, 0x00),  # Mr. Mime: Psychic, Fairy (Psychic in Gen 1)
    0x75: (0x19, 0x00),  # Scyther: Bug, Flying
    0x76: (0x19, 0x00),  # Jynx: Ice, Psychic
    0x77: (0x0C, 0x00),  # Electabuzz: Electric
    0x78: (0x0A, 0x00),  # Magmar: Fire
    0x79: (0x19, 0x00),  # Pinsir: Bug
    0x7A: (0x19, 0x00),  # Tauros: Normal
    0x7B: (0x19, 0x00),  # Magikarp: Water
    0x7C: (0x19, 0x00),  # Gyarados: Water, Flying
    0x7D: (0x19, 0x00),  # Lapras: Water, Ice
    0x7E: (0x19, 0x00),  # Ditto: Normal
    0x7F: (0x19, 0x00),  # Eevee: Normal
    0x80: (0x19, 0x00),  # Vaporeon: Water
    0x81: (0x19, 0x00),  # Jolteon: Electric
    0x82: (0x19, 0x00),  # Flareon: Fire
    0x83: (0x19, 0x00),  # Porygon: Normal
    0x84: (0x19, 0x00),  # Omanyte: Rock, Water
    0x85: (0x19, 0x00),  # Omastar: Rock, Water
    0x86: (0x19, 0x00),  # Kabuto: Rock, Water
    0x87: (0x19, 0x00),  # Kabutops: Rock, Water
    0x88: (0x19, 0x00),  # Aerodactyl: Rock, Flying
    0x89: (0x19, 0x00),  # Snorlax: Normal
    0x8A: (0x19, 0x00),  # Articuno: Ice, Flying
    0x8B: (0x19, 0x00),  # Zapdos: Electric, Flying
    0x8C: (0x19, 0x00),  # Moltres: Fire, Flying
    0x8D: (0x19, 0x00),  # Dratini: Dragon
    0x8E: (0x19, 0x00),  # Dragonair: Dragon
    0x8F: (0x19, 0x00),  # Dragonite: Dragon, Flying
    0x90: (0x19, 0x00),  # Mewtwo: Psychic
    0x91: (0x19, 0x00),  # Mew: Psychic
    # Add more Pokemon types as needed
}

# Type ID to name mapping
TYPE_NAMES = {
    0x00: "Normal",
    0x01: "Fighting",
    0x02: "Flying",
    0x03: "Poison",
    0x04: "Ground",
    0x05: "Rock",
    0x07: "Bug",
    0x08: "Ghost",
    0x14: "Fire",
    0x15: "Water",
    0x16: "Grass",
    0x17: "Electric",
    0x18: "Psychic",
    0x19: "Ice",
    0x1A: "Dragon"
}


# End of PokemonMemoryMap class