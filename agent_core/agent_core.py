import logging
import time
import os
import json
from typing import Optional, Dict, Any
from pyboy import PyBoy
from memory_map.pokemon_memory_map import PokemonMemoryMap
from state_detector.game_state import StateDetector, GameState
from prompt_manager.prompt_manager import PromptManager
from .mistral_api import MistralAPI
from tools.battle_helper import BattleHelper, PyBoyBattleIntegration
from tools.pathfinder import Pathfinder
from tools.puzzle_solver import PuzzleSolver

class AgentCore:
    def __init__(self, rom_path: str, headless: bool = False):
        self.rom_path = rom_path
        self.headless = headless
        # Initialize with emulator instead of PyBoy directly
        self.pyboy = None
        self.emulator = None  # Will be set when emulator is connected
        self.memory_map = PokemonMemoryMap()
        self.state_detector = StateDetector(self.memory_map)
        self.prompt_manager = PromptManager()
        self.mistral_api = MistralAPI()
        self.battle_helper = BattleHelper()
        self.pathfinder = Pathfinder([])
        self.puzzle_solver = PuzzleSolver()
        
        # Battle integration
        self.battle_integration = None
        
        self.frame_skip = 1
        self.max_frames_to_skip = 60
        self.last_screenshot_frame = 0
        self.screenshot_interval = 300  # Take screenshot every 5 seconds at 60fps
        self.checkpoint_interval = 600  # Create checkpoint every 10 seconds at 60fps
        self.last_checkpoint_frame = 0
        self.start_time = time.time()
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

    def get_memory(self):
        """
        Unified memory access method that handles different PyBoy API versions.
        
        Returns:
            Memory object or None if access fails
        """
        if not self.pyboy:
            return None
            
        try:
            # Try the newer PyBoy API first
            memory = self.pyboy.memory
            return memory
        except (AttributeError, TypeError):
            try:
                # Fallback to older API
                memory = self.pyboy.get_memory()
                return memory
            except (AttributeError, TypeError):
                # For latest PyBoy versions, try alternative access
                try:
                    if hasattr(self.pyboy, '_memory'):
                        return self.pyboy._memory
                    elif hasattr(self.pyboy, 'mbc'):
                        return self.pyboy.mbc
                except:
                    pass
                self.logger.warning("Could not access PyBoy memory - API compatibility issue")
                return None

    def connect_emulator(self, emulator):
        """Connect to the emulator instance"""
        self.emulator = emulator
        self.pyboy = emulator.pyboy  # Access the underlying PyBoy instance
        self.battle_integration = PyBoyBattleIntegration(self.pyboy)

    def run(self):
        """Run the agent using the connected emulator"""
        if not self.emulator:
            self.logger.error("Emulator not connected. Use connect_emulator() first.")
            return

        self.logger.info("Starting Pokémon Blue AI Agent")
        try:
            # Use emulator's tick method instead of PyBoy directly
            while self.emulator.is_running() and not self.emulator._paused:
                self.main_game_loop()
        except Exception as e:
            self.logger.error(f"Error in main game loop: {e}")
        finally:
            self.logger.info("Agent run loop ended")

    def main_game_loop(self):
        current_frame = self.emulator.frame_count if self.emulator else 0

        # Dynamic frame skipping
        self.adjust_frame_skip()

        # Only process every frame_skip frames
        if current_frame % self.frame_skip != 0:
            # Still tick the emulator to keep gameplay running
            self.emulator.tick(1)
            return

        # State detection
        game_state = None
        try:
            # Get the PyBoy memory view using unified method
            memory = self.get_memory()
            if memory:
                game_state = self.state_detector.detect_state(memory)
                self.logger.debug(f"Detected game state: {game_state}")
        except Exception as e:
            self.logger.error(f"Error detecting state: {e}")
            # Still tick the emulator to keep gameplay running
            self.emulator.tick(1)
            return

        # Screenshot capture
        if current_frame - self.last_screenshot_frame >= self.screenshot_interval:
            self.capture_screenshot()
            self.last_screenshot_frame = current_frame

        # Checkpointing
        if current_frame - self.last_checkpoint_frame >= self.checkpoint_interval:
            self.create_checkpoint()
            self.last_checkpoint_frame = current_frame

        # Handle different game states differently
        if game_state and game_state == GameState.BATTLE:
            self.handle_battle_state()
        else:
            # Build prompt based on current state (only if memory access is working)
            try:
                # Try to access memory to build the state using unified method
                memory = self.get_memory()

                if memory:
                    location = f"Map: {self.memory_map.get_current_map_number(memory)}, X: {self.memory_map.get_player_coordinates(memory)[0]}, Y: {self.memory_map.get_player_coordinates(memory)[1]}"
                    party_info = {'species': self.memory_map.get_party_pokemon_species(memory), 
                                 'count': self.memory_map.get_num_party_pokemon(memory)}
                    items = {}  # Placeholder - would implement item reading
                    money = self.memory_map.get_player_money(memory)
                    badges = []  # Placeholder - would implement badge reading
                    goals = self.prompt_manager.goals if hasattr(self.prompt_manager, 'goals') else []
                    
                    # Determine game state for prompt construction
                    game_state_name = str(game_state).lower() if game_state else "overworld"
                    game_state_for_prompt = "overworld"
                    
                    if "battle" in game_state_name:
                        game_state_for_prompt = "battle"
                    elif "menu" in game_state_name or "dialog" in game_state_name:
                        game_state_for_prompt = "menu"
                    elif "title" in location.lower() or "start" in location.lower():
                        game_state_for_prompt = "title"
                    elif "character" in location.lower() or "name" in location.lower():
                        game_state_for_prompt = "character_creation"
                    
                    self.prompt_manager.update_state(location, party_info, items, money, badges, goals)
                    prompt = self.prompt_manager.construct_prompt(game_state_for_prompt)
                    self.logger.debug(f"Built prompt: {prompt[:100]}...")  # Just log first 100 chars to avoid spam
                else:
                    # If we can't access memory, still try to get some basic information
                    prompt = f"Current game state detected as {game_state}. Please provide next action."
                    
                    # Add a small delay to prevent rate limiting when memory access fails
                    time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error building prompt: {e}")
                # Add a delay to prevent rapid API calls when there are errors
                time.sleep(0.5)
                prompt = f"Current game state detected as {game_state}. Please provide next action."

            # Only query API every few cycles to avoid rate limiting
            if current_frame % 120 == 0:  # Every 2 seconds at 60fps (instead of every frame)
                # Capture a screenshot to send with the prompt
                screenshot_path = None
                try:
                    screenshot_path = f"screenshots/frame_{current_frame}.png"
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    
                    # Use emulator's save_screenshot method, but wrap it more carefully
                    # to avoid the array comparison issue 
                    try:
                        success = self.emulator.save_screenshot(screenshot_path)
                    except Exception as inner_e:
                        # If save_screenshot fails with array comparison error, 
                        # skip screenshot for this call
                        self.logger.warning(f"Screenshot capture failed, continuing without image: {inner_e}")
                        success = False
                    
                    if not success:
                        self.logger.warning("Failed to capture screenshot for API")
                        screenshot_path = None
                except Exception as e:
                    self.logger.error(f"Error capturing screenshot: {e}")
                    screenshot_path = None
                
                # Query Mistral API (but only if we have a valid prompt and memory access is working)
                if prompt and not prompt.startswith("Current game state detected as None"):
                    try:
                        response = self.mistral_api.query(prompt, image_path=screenshot_path)
                        self.logger.info(f"Non-battle Mistral response: {response}")
                    except Exception as e:
                        self.logger.error(f"Error querying Mistral API: {e}")
                        response = '{"action": "wait", "reason": "API error occurred"}'

                    # Parse response and execute actions
                    try:
                        actions = self.parse_response(response)
                        self.execute_actions(actions)
                    except Exception as e:
                        self.logger.error(f"Error executing actions: {e}")
                else:
                    # If we're having memory access issues, wait to avoid rapid API calls
                    time.sleep(0.2)
            
            # Tick the emulator to advance the game
            self.emulator.tick(1)

        # Perform periodic tasks
        if current_frame % 60 == 0:  # Every 60 frames (1 second at 60fps)
            self._perform_periodic_tasks(current_frame)
        
        # Add a small delay to prevent overwhelming the system
        time.sleep(0.01)  # 10ms delay to prevent excessive resource usage

    def handle_battle_state(self):
        """Handle battle-specific logic when in battle state"""
        try:
            # Get battle state from emulator
            battle_decision = self.battle_integration.get_battle_decision_from_memory()
            
            if "error" in battle_decision:
                self.logger.error(f"Battle decision error: {battle_decision['error']}")
                # Fallback to general AI
                self.handle_general_battle_fallback()
                return

            self.logger.info(f"Battle decision: {battle_decision}")

            # Execute the battle decision
            success = self.battle_integration.execute_battle_decision(battle_decision)
            if not success:
                self.logger.error("Failed to execute battle decision")
                # Fallback to general AI
                self.handle_general_battle_fallback()

        except Exception as e:
            self.logger.error(f"Error in battle state handling: {e}")
            # Fallback to general AI
            self.handle_general_battle_fallback()

    def handle_general_battle_fallback(self):
        """Fallback for battle state when specific battle logic fails"""
        # Build a battle-specific prompt
        try:
            prompt = (
                "You are currently in a Pokémon battle. "
                "The player's active Pokémon is facing an opponent. "
                "Please respond in JSON format with either:\n"
                "1. {\"action\": \"use_move\", \"move\": \"move_name\", \"reason\": \"why this move\"}\n"
                "2. {\"action\": \"switch_pokemon\", \"pokemon\": \"pokemon_name\", \"reason\": \"why switch\"}\n"
                "3. {\"action\": \"use_item\", \"item\": \"item_name\", \"reason\": \"why use item\"}\n"
                "4. {\"action\": \"run\", \"reason\": \"why run\"}\n"
            )
            
            # Capture a screenshot to send with the prompt
            screenshot_path = None
            try:
                current_frame = self.emulator.frame_count if self.emulator else 0
                screenshot_path = f"screenshots/battle_frame_{current_frame}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                # Use emulator's screenshot method
                success = self.emulator.save_screenshot(screenshot_path)
                if not success:
                    self.logger.warning("Failed to capture battle screenshot for API")
                    screenshot_path = None
            except Exception as e:
                self.logger.error(f"Error capturing battle screenshot: {e}")
                screenshot_path = None
            
            response = self.mistral_api.query(prompt, image_path=screenshot_path)
            self.logger.info(f"Battle fallback response: {response}")
            
            # Parse and execute the response
            actions = self.parse_response(response)
            self.execute_actions(actions)
            
        except Exception as e:
            self.logger.error(f"Error in battle fallback: {e}")

    def adjust_frame_skip(self):
        """Dynamically adjust frame skip based on game state and performance"""
        # Simple heuristic: skip more frames when in battle or menu
        try:
            # Try to get memory from emulator for state detection using unified method
            memory = self.get_memory()
            game_state = self.state_detector.detect_state(memory)
            if str(game_state).lower() in ['battle', 'menu', 'dialog']:
                self.frame_skip = min(self.frame_skip + 1, self.max_frames_to_skip)
            else:
                self.frame_skip = max(1, self.frame_skip - 1)
        except Exception as e:
            self.logger.warning(f"Could not adjust frame skip: {e}")
            self.frame_skip = 1  # Default to no skipping if state detection fails

    def capture_screenshot(self):
        """Capture screenshot when needed for state detection"""
        if not self.emulator:
            return
            
        screenshot_path = f"screenshots/frame_{self.emulator.frame_count}.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        
        # Use emulator's screenshot method
        self.emulator.save_screenshot(screenshot_path)
        self.logger.info(f"Screenshot captured: {screenshot_path}")

    def create_checkpoint(self):
        """Create game state checkpoint for recovery"""
        if not self.emulator or not self.pyboy:
            return
            
        checkpoint_path = f"checkpoints/checkpoint_{self.emulator.frame_count}.state"
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # Save state using PyBoy - newer versions might have different API
        try:
            # Try the newer API first
            if hasattr(self.pyboy, 'save_state') and callable(getattr(self.pyboy, 'save_state')):
                self.pyboy.save_state(checkpoint_path)
            else:
                # Fallback to the older API
                self.pyboy.save_state(open(checkpoint_path, 'wb'))
        except TypeError:
            # If checkpoint_path doesn't work, try with file object
            self.pyboy.save_state(open(checkpoint_path, 'wb'))
            
        self.logger.info(f"Checkpoint created: {checkpoint_path}")

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral API response into actionable format"""
        try:
            # Try to parse as JSON first
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError:
            # If not JSON, return a default structure
            self.logger.warning(f"Response not JSON: {response}")
            return {
                'action': 'wait',
                'reason': 'Invalid response format'
            }

    def execute_actions(self, actions: Dict[str, Any]):
        """Execute parsed actions via the emulator"""
        if not self.emulator or not self.pyboy:
            return
            
        try:
            action = actions.get('action', 'wait')
            self.logger.info(f"Executing action: {action}")

            if action == 'use_move':
                # Battle-specific action handled separately in battle state
                self.logger.info("Move action detected in battle context")
                pass  # Handled by battle integration
            elif action == 'switch_pokemon':
                # Battle-specific action handled separately in battle state
                self.logger.info("Switch action detected in battle context")
                pass  # Handled by battle integration
            elif action == 'use_item':
                # Battle-specific action handled separately in battle state
                self.logger.info("Item action detected in battle context")
                pass  # Handled by battle integration
            elif action == 'run':
                # Battle-specific action handled separately in battle state
                self.logger.info("Run action detected in battle context")
                pass  # Handled by battle integration
            elif action == 'move' or action in ['move_up', 'move_down', 'move_left', 'move_right']:
                # If the action is one of the move_* types, use it as the direction
                if action in ['move_up', 'move_down', 'move_left', 'move_right']:
                    # Extract direction from the action name
                    direction = action.replace('move_', '')
                else:
                    # If action is just 'move', get the direction from the dict
                    direction = actions.get('direction', actions.get('move', 'up'))
                    # Map to standard directions if needed
                    dir_map = {
                        'move_up': 'up', 'move_down': 'down', 
                        'move_left': 'left', 'move_right': 'right'
                    }
                    direction = dir_map.get(direction, direction)
                
                # Make sure direction is a valid button name
                if direction not in ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']:
                    self.logger.warning(f"Invalid direction: {direction}")
                    return
                    
                duration = actions.get('duration', 5)
                # Check if the button is valid (using new API approach)
                valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
                if direction in valid_buttons:
                    self.emulator.send_input(direction, duration)
                else:
                    self.logger.warning(f"Button '{direction}' not available in emulator. Available buttons: {valid_buttons}")
            elif action in ['menu_up', 'menu_down', 'menu_left', 'menu_right']:
                # Map menu navigation to directional inputs
                direction_map = {
                    'menu_up': 'up',
                    'menu_down': 'down',
                    'menu_left': 'left',
                    'menu_right': 'right'
                }
                direction = direction_map.get(action, 'up')  # Default to up if not found
                duration = actions.get('duration', 0.1)
                # Ensure the direction is valid and available before sending
                if direction in ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']:
                    # Check if the button is valid (using new API approach)
                    valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
                    if direction in valid_buttons:
                        self.emulator.send_input(direction, duration)
                    else:
                        self.logger.warning(f"Button '{direction}' not available in emulator. Available buttons: {valid_buttons}")
                else:
                    self.logger.warning(f"Invalid menu navigation direction: {direction}")
            elif action in ['menu_select', 'interact']:
                # Map to A button for menu selection/interaction
                duration = actions.get('duration', 0.1)
                self.emulator.send_input('a', duration)
            elif action == 'menu_back':
                # Map to B button for going back in menus
                duration = actions.get('duration', 0.1)
                self.emulator.send_input('b', duration)
            elif action == 'open_menu':
                # Map to Start button for opening main menu
                duration = actions.get('duration', 0.1)
                self.emulator.send_input('start', duration)
            elif action in ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']:
                # Direct button press
                duration = actions.get('duration', 0.1)
                # Check if the button is valid (using new API approach)
                valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
                if action in valid_buttons:
                    self.emulator.send_input(action, duration)
                else:
                    self.logger.warning(f"Button '{action}' not available in emulator. Available buttons: {valid_buttons}")
            elif action == 'wait':
                # Do nothing, just wait for next loop
                pass
            else:
                self.logger.warning(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error executing actions: {e}")

    def get_emulator_state(self):
        """Get current emulator state for debugging"""
        if self.emulator:
            return self.emulator.get_game_state()
        return {}
    
    def _perform_periodic_tasks(self, frame_count):
        """Perform periodic maintenance tasks."""
        try:
            # Update performance stats
            if self.emulator:
                game_state = self.emulator.get_game_state()
                self.logger.debug(f"Game state: {game_state}")

            # Log system status every 10 seconds
            if frame_count % 600 == 0:  # Every 600 frames (10 seconds at 60fps)
                elapsed = time.time() - self.start_time if hasattr(self, 'start_time') else 0
                if elapsed > 0:
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    seconds = int(elapsed % 60)

                    self.logger.info(
                        f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d} | "
                        f"Frames: {self.emulator.frame_count:,} | "
                        f"FPS: {self.emulator.frame_count/elapsed:.1f} | "
                        f"Inputs: {self.emulator.performance_stats['inputs_processed']}"
                    )

        except Exception as e:
            self.logger.error(f"Error in periodic tasks: {e}")