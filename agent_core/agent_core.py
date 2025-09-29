import logging
import time
import os
from typing import Optional, Dict, Any
from pyboy import PyBoy, WindowEvent
from memory_map.pokemon_memory_map import PokemonMemoryMap
from state_detector.game_state import GameStateDetector
from prompt_manager.prompt_manager import PromptManager
from mistral_api import MistralAPI
from tools.battle_helper import BattleHelper
from tools.pathfinder import Pathfinder
from tools.puzzle_solver import PuzzleSolver

class AgentCore:
    def __init__(self, rom_path: str, headless: bool = False):
        self.rom_path = rom_path
        self.headless = headless
        self.pyboy = PyBoy(rom_path, window_type='headless' if headless else 'SDL2')
        self.memory_map = PokemonMemoryMap()
        self.state_detector = GameStateDetector(self.pyboy, self.memory_map)
        self.prompt_manager = PromptManager()
        self.mistral_api = MistralAPI()
        self.battle_helper = BattleHelper()
        self.pathfinder = Pathfinder()
        self.puzzle_solver = PuzzleSolver()
        self.frame_skip = 1
        self.max_frames_to_skip = 60
        self.last_screenshot_frame = 0
        self.screenshot_interval = 300  # Take screenshot every 5 seconds at 60fps
        self.checkpoint_interval = 600  # Create checkpoint every 10 seconds at 60fps
        self.last_checkpoint_frame = 0
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Starting Pokémon Blue AI Agent")
        try:
            while not self.pyboy.tick():
                self.main_game_loop()
        except Exception as e:
            self.logger.error(f"Error in main game loop: {e}")
        finally:
            self.pyboy.stop()

    def main_game_loop(self):
        current_frame = self.pyboy.get_frame_count()

        # Dynamic frame skipping
        self.adjust_frame_skip()

        # Only process every frame_skip frames
        if current_frame % self.frame_skip != 0:
            return

        # State detection
        game_state = self.state_detector.detect_state()
        self.logger.debug(f"Detected game state: {game_state}")

        # Screenshot capture
        if current_frame - self.last_screenshot_frame >= self.screenshot_interval:
            self.capture_screenshot()
            self.last_screenshot_frame = current_frame

        # Checkpointing
        if current_frame - self.last_checkpoint_frame >= self.checkpoint_interval:
            self.create_checkpoint()
            self.last_checkpoint_frame = current_frame

        # Build prompt based on current state
        prompt = self.prompt_manager.build_prompt(game_state)
        self.logger.debug(f"Built prompt: {prompt}")

        # Query Mistral API
        response = self.mistral_api.query(prompt)
        self.logger.info(f"Mistral response: {response}")

        # Parse response and execute actions
        actions = self.parse_response(response)
        self.execute_actions(actions)

    def adjust_frame_skip(self):
        """Dynamically adjust frame skip based on game state and performance"""
        # Simple heuristic: skip more frames when in battle or menu
        game_state = self.state_detector.detect_state()
        if 'battle' in game_state or 'menu' in game_state:
            self.frame_skip = min(self.frame_skip + 1, self.max_frames_to_skip)
        else:
            self.frame_skip = max(1, self.frame_skip - 1)

    def capture_screenshot(self):
        """Capture screenshot when needed for state detection"""
        screenshot_path = f"screenshots/frame_{self.pyboy.get_frame_count()}.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        self.pyboy.screen().screen_image().save(screenshot_path)
        self.logger.info(f"Screenshot captured: {screenshot_path}")

    def create_checkpoint(self):
        """Create game state checkpoint for recovery"""
        checkpoint_path = f"checkpoints/checkpoint_{self.pyboy.get_frame_count()}.state"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        self.pyboy.save_state(checkpoint_path)
        self.logger.info(f"Checkpoint created: {checkpoint_path}")

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral API response into actionable format"""
        # Simple parsing - in practice this would be more sophisticated
        return {
            'action': 'move',
            'direction': 'right',
            'duration': 10
        }

    def execute_actions(self, actions: Dict[str, Any]):
        """Execute parsed actions via PyBoy"""
        if actions['action'] == 'move':
            direction_map = {
                'up': WindowEvent.PRESS_ARROW_UP,
                'down': WindowEvent.PRESS_ARROW_DOWN,
                'left': WindowEvent.PRESS_ARROW_LEFT,
                'right': WindowEvent.PRESS_ARROW_RIGHT,
                'a': WindowEvent.PRESS_BUTTON_A,
                'b': WindowEvent.PRESS_BUTTON_B,
                'start': WindowEvent.PRESS_BUTTON_START,
                'select': WindowEvent.PRESS_BUTTON_SELECT
            }

            if actions['direction'] in direction_map:
                for _ in range(actions.get('duration', 1)):
                    self.pyboy.send_input(direction_map[actions['direction']])
                    self.pyboy.tick()
                self.pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)  # Release all buttons