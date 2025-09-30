from enum import Enum, auto
from memory_map.pokemon_memory_map import PokemonMemoryMap

class GameState(Enum):
    OVERWORLD = auto()
    BATTLE = auto()
    DIALOG = auto()
    MENU = auto()
    # Add other states as needed

class StateDetector:
    def __init__(self, memory_map: PokemonMemoryMap):
        self.memory_map = memory_map

    def detect_state(self, memory=None) -> GameState:
        """Detect the current game state based on RAM flags and player coordinates."""
        if memory is None:
            # If no memory access is provided, return default state
            return GameState.OVERWORLD
            
        # Read RAM flags
        in_battle_flag = self.memory_map.read_byte(memory, 0xD057)
        battle_type = self.memory_map.read_byte(memory, 0xD05A)

        # Get player coordinates (example addresses, adjust as needed)
        player_x = self.memory_map.read_byte(memory, 0xD362)
        player_y = self.memory_map.read_byte(memory, 0xD365)

        # State detection logic
        if in_battle_flag == 1:
            return GameState.BATTLE
        elif battle_type in [1, 2, 3]:  # Wild, trainer, or gym battle
            return GameState.BATTLE
        elif self._is_in_dialog(memory):
            return GameState.DIALOG
        elif self._is_in_menu(memory):
            return GameState.MENU
        else:
            return GameState.OVERWORLD

    def _is_in_dialog(self, memory) -> bool:
        """Check if the game is in a dialog state."""
        # Implement dialog detection logic using RAM flags
        # Check for dialog box flags
        text_box_state = self.memory_map.read_byte(memory, 0xC058)  # Common text box flag
        text_box_active = self.memory_map.read_byte(memory, 0xCD6A)  # Another text flag
        return text_box_state != 0 or text_box_active != 0

    def _is_in_menu(self, memory) -> bool:
        """Check if the game is in a menu state."""
        # Implement menu detection logic using RAM flags
        # Check for menu-related flags
        menu_open = self.memory_map.read_byte(memory, 0xCC26)  # Menu state flag
        inventory_menu = self.memory_map.read_byte(memory, 0xD31E)  # Inventory menu flag
        return menu_open != 0 or inventory_menu != 0