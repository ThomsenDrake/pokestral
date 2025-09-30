"""
Pokemon Blue Emulator Wrapper

This module provides a comprehensive wrapper around PyBoy for Pokemon Blue emulation,
enabling visual gameplay monitoring and AI agent control through input actions.
"""

import logging
import os
import time
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import numpy as np
from PIL import Image
import threading
import queue

# Do not import PyBoy at module level to avoid issues with import timing
logger = logging.getLogger(__name__)

class PokemonEmulator:
    """
    Comprehensive Pokemon Blue emulator wrapper with visual display and AI control capabilities.

    This class provides:
    - Non-headless PyBoy emulation with visual window
    - Input action handling for AI agent control
    - Screenshot capture for state detection
    - Frame management and speed control
    - Proper error handling and logging
    - Integration points for agent system
    """

    def __init__(self,
                 rom_path: Optional[str] = None,
                 window_title: str = "Pokemon Blue - AI Agent",
                 scale: int = 3,
                 sound: bool = False,
                 auto_tick_rate: int = 60,
                 max_frame_skips: int = 10):
        """
        Initialize the Pokemon emulator.

        Args:
            rom_path: Path to Pokemon Blue ROM file
            window_title: Title for the game window
            scale: Window scale factor (1-4)
            sound: Enable/disable game sound
            auto_tick_rate: Target frame rate for automatic ticking
            max_frame_skips: Maximum frames to skip for performance
        """
        # Check PyBoy availability at runtime and set button mappings
        try:
            from pyboy import PyBoy
            print("PyBoy imported successfully!")  # Debug print
            
            # Set PyBoy class reference
            self.PyBoyClass = PyBoy
            
            # Define button constants for the new API (strings)
            # These will be used with button_press/button_release methods
            self.BUTTON_NAMES = [
                'up', 'down', 'left', 'right', 
                'a', 'b', 'start', 'select'
            ]
            
        except ImportError as e:
            print(f"PyBoy import failed: {e}")  # Debug print
            raise ImportError("PyBoy is not installed. Please install with: pip install pyboy")
        except Exception as e:
            print(f"Unexpected error during PyBoy import: {e}")  # Debug print
            raise ImportError(f"Error importing PyBoy: {e}")

        self.rom_path = rom_path or self._find_rom()
        self.window_title = window_title
        self.scale = scale
        self.sound = sound
        self.auto_tick_rate = auto_tick_rate
        self.max_frame_skips = max_frame_skips

        # Core PyBoy instance
        self.pyboy: Optional[PyBoy] = None

        # Control flags
        self._running = False
        self._paused = False
        self._auto_tick = False

        # Frame management
        self.frame_count = 0
        self.last_frame_time = 0
        self.target_frame_time = 1.0 / auto_tick_rate

        # Input handling
        self.input_queue = queue.Queue()
        self.input_thread: Optional[threading.Thread] = None
        self._processing_inputs = False
        self._input_lock = threading.Lock()

        # Screenshot cache
        self.last_screenshot: Optional[np.ndarray] = None
        self.screenshot_interval = 10  # Take screenshot every N frames

        # Button names for validation
        self.BUTTON_NAMES = [
            'up', 'down', 'left', 'right', 
            'a', 'b', 'start', 'select'
        ]

        # Callbacks for agent integration
        self.on_frame_callback = None
        self.on_input_callback = None
        self.on_error_callback = None

        # Performance tracking
        self.performance_stats = {
            'frames_rendered': 0,
            'inputs_processed': 0,
            'avg_frame_time': 0.0,
            'screenshots_taken': 0
        }

        logger.info(f"PokemonEmulator initialized with scale={scale}, sound={sound}")

    def _find_rom(self) -> str:
        """Find Pokemon Blue ROM file in common locations."""
        common_paths = [
            "roms/pokemon-blue-version.gb",  # Actual ROM file name in the project
            "roms/pokemon_blue.gb",
            "roms/pokemon_blue.gbc",
            "pokemon-blue-version.gb",      # Also check in root directory
            "pokemon_blue.gb",
            "pokemon_blue.gbc",
            "~/pokemon_blue.gb",
            "~/roms/pokemon_blue.gb"
        ]

        for path in common_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                print(f"Found ROM at: {expanded_path}")  # Use print instead of logger
                return str(expanded_path)

        # Ask user for ROM path if not found
        raise FileNotFoundError(
            "Pokemon Blue ROM not found. Please provide the path to pokemon_blue.gb or pokemon_blue.gbc"
        )

    def load_rom(self, rom_path: Optional[str] = None) -> bool:
        """
        Load Pokemon Blue ROM.

        Args:
            rom_path: Optional path to ROM (uses instance path if not provided)

        Returns:
            bool: True if loaded successfully
        """
        if rom_path:
            self.rom_path = rom_path

        if not os.path.exists(self.rom_path):
            raise FileNotFoundError(f"ROM file not found: {self.rom_path}")

        try:
            # Stop existing emulation if running
            if self.pyboy:
                self.stop()

            # Create PyBoy instance with visual window
            self.pyboy = self.PyBoyClass(
                self.rom_path,
                window="SDL2",  # Use SDL2 for better performance (replaces window_type)
                scale=self.scale,
                sound=self.sound
                # hide_window is no longer supported, non-headless is default
            )

            # Set window title
            if hasattr(self.pyboy, 'set_title'):
                self.pyboy.set_title(self.window_title)

            logger.info(f"Successfully loaded ROM: {self.rom_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load ROM: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            return False

    def start(self, auto_tick: bool = True) -> bool:
        """
        Start the emulator.

        Args:
            auto_tick: Whether to enable automatic frame ticking

        Returns:
            bool: True if started successfully
        """
        if not self.pyboy:
            logger.error("Cannot start: ROM not loaded")
            return False

        try:
            self._running = True
            self._auto_tick = auto_tick

            # Start input processing thread
            self._start_input_thread()

            logger.info("Emulator started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start emulator: {e}")
            self._running = False
            return False

    def stop(self):
        """Stop the emulator and cleanup resources."""
        logger.info("Stopping emulator...")

        self._running = False
        self._auto_tick = False

        # Stop input thread
        self._stop_input_thread()

        # Stop PyBoy
        if self.pyboy:
            try:
                self.pyboy.stop()
            except:
                pass  # PyBoy might already be stopped

        logger.info("Emulator stopped")

    def pause(self):
        """Pause emulation."""
        self._paused = True
        logger.info("Emulator paused")

    def resume(self):
        """Resume emulation."""
        self._paused = False
        logger.info("Emulator resumed")

    def is_running(self) -> bool:
        """Check if emulator is running."""
        return self._running and self.pyboy is not None

    def is_paused(self) -> bool:
        """Check if emulator is paused."""
        return self._paused

    def tick(self, frames: int = 1) -> bool:
        """
        Advance emulation by specified number of frames.

        Args:
            frames: Number of frames to advance

        Returns:
            bool: True if successful
        """
        if not self.pyboy or not self._running or self._paused:
            return False

        try:
            for _ in range(frames):
                if not self._running:
                    break

                # Tick the emulator
                self.pyboy.tick()

                # Update frame counter
                self.frame_count += 1

                # Process inputs periodically
                if self.frame_count % 5 == 0:  # Every 5 frames
                    self._process_input_queue()

                # Take screenshot periodically
                if self.frame_count % self.screenshot_interval == 0:
                    self._update_screenshot()

                # Call frame callback if set
                if self.on_frame_callback:
                    self.on_frame_callback(self.frame_count)

                # Auto-tick rate control
                if self._auto_tick:
                    self._manage_frame_timing()

            return True

        except Exception as e:
            logger.error(f"Error during tick: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
            return False

    def run(self, max_frames: Optional[int] = None) -> int:
        """
        Run the emulator until stopped or max_frames reached.

        Args:
            max_frames: Maximum frames to run (None for unlimited)

        Returns:
            int: Actual frames run
        """
        frames_run = 0

        try:
            while self._running and (max_frames is None or frames_run < max_frames):
                if not self.tick():
                    break
                frames_run += 1

        except KeyboardInterrupt:
            logger.info("Emulation interrupted by user")
        except Exception as e:
            logger.error(f"Error during run: {e}")
            if self.on_error_callback:
                self.on_error_callback(str(e))

        return frames_run

    def _manage_frame_timing(self):
        """Manage frame timing for consistent frame rate."""
        current_time = time.time()
        elapsed = current_time - self.last_frame_time

        if elapsed < self.target_frame_time:
            time.sleep(self.target_frame_time - elapsed)

        self.last_frame_time = time.time()

    def send_input(self, button: str, duration: float = 0.1) -> bool:
        """
        Send input action to the emulator.

        Args:
            button: Button name ('up', 'down', 'left', 'right', 'a', 'b', 'start', 'select')
            duration: How long to hold the button (seconds)

        Returns:
            bool: True if input was queued successfully
        """
        if not self.is_running():
            logger.warning("Cannot send input: emulator not running")
            return False

        button_lower = button.lower()
        # Check if button is valid - use hardcoded list for safety
        valid_buttons = ['up', 'down', 'left', 'right', 'a', 'b', 'start', 'select']
        if button_lower not in valid_buttons:
            logger.error(f"Invalid button: {button}")
            logger.debug(f"Available buttons: {valid_buttons}")
            return False

        try:
            # Add to input queue with thread safety
            with self._input_lock:
                self.input_queue.put((button_lower, duration))

            if self.on_input_callback:
                self.on_input_callback(button, duration)

            return True

        except Exception as e:
            logger.error(f"Error queuing input: {e}")
            return False

    def send_input_sequence(self, sequence: List[Tuple[str, float]]) -> bool:
        """
        Send a sequence of input actions.

        Args:
            sequence: List of (button, duration) tuples

        Returns:
            bool: True if sequence was queued successfully
        """
        for button, duration in sequence:
            if not self.send_input(button, duration):
                return False
        return True

    def _process_input_queue(self):
        """Process queued input actions."""
        with self._input_lock:
            if self._processing_inputs or not self.pyboy:
                return

            self._processing_inputs = True

        try:
            while not self.input_queue.empty():
                button, duration = self.input_queue.get_nowait()

                # Press button using the new API
                if hasattr(self.pyboy, 'button_press'):
                    self.pyboy.button_press(button)

                # Hold for specified duration
                if duration > 0:
                    time.sleep(duration)

                # Release button using the new API
                if hasattr(self.pyboy, 'button_release'):
                    self.pyboy.button_release(button)

                self.performance_stats['inputs_processed'] += 1

        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error processing inputs: {e}")
        finally:
            with self._input_lock:
                self._processing_inputs = False

    def _start_input_thread(self):
        """Start the input processing thread."""
        if hasattr(self, 'input_thread') and self.input_thread:
            if self.input_thread.is_alive():
                return

        self.input_thread = threading.Thread(target=self._input_thread_main, daemon=True)
        self.input_thread.start()

    def _stop_input_thread(self):
        """Stop the input processing thread."""
        if hasattr(self, 'input_thread') and self.input_thread:
            self.input_thread.join(timeout=1.0)

    def _input_thread_main(self):
        """Main loop for input processing thread."""
        while self._running:
            try:
                self._process_input_queue()
                time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Error in input thread: {e}")
                break

    def get_screenshot(self) -> Optional[np.ndarray]:
        """
        Get current game screenshot.

        Returns:
            np.ndarray: RGB screenshot array, or None if unavailable
        """
        if not self.pyboy:
            return None

        try:
            # Get screen buffer from PyBoy
            screen = self.pyboy.screen

            if hasattr(screen, 'screen_ndarray'):
                # Convert to numpy array
                screenshot = screen.screen_ndarray()
                self.last_screenshot = screenshot.copy()
                self.performance_stats['screenshots_taken'] += 1
                return screenshot
            else:
                # Fallback method - properly handle image access
                try:
                    # First, try accessing image as an attribute
                    image_attr = getattr(screen, 'image', None)
                    if image_attr is not None:
                        if callable(image_attr):
                            # If it's a method, call it
                            pil_image = image_attr()
                        else:
                            # If it's an attribute, use it directly
                            pil_image = image_attr
                        
                        if pil_image is not None:
                            screenshot_array = np.array(pil_image.convert('RGB'))
                        else:
                            # If all else fails, return None
                            return None
                    else:
                        # If screen.image doesn't exist, try another approach
                        # Use the screenshot method if available
                        if hasattr(self.pyboy, 'screenshot'):
                            import io
                            screenshot_bytes = self.pyboy.screenshot()
                            from PIL import Image
                            # Use context manager to ensure proper cleanup
                            with io.BytesIO(screenshot_bytes) as byte_stream:
                                with Image.open(byte_stream) as pil_image:
                                    screenshot_array = np.array(pil_image.convert('RGB'))
                        else:
                            # If all else fails, return None
                            return None
                except Exception:
                    # If there's still an issue, return None
                    return None
                    
                if screenshot_array is not None:
                    self.last_screenshot = screenshot_array.copy()
                    self.performance_stats['screenshots_taken'] += 1
                return screenshot_array

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    def _update_screenshot(self):
        """Update cached screenshot (called periodically during ticks)."""
        self.get_screenshot()

    def save_screenshot(self, filepath: str) -> bool:
        """
        Save current screenshot to file.

        Args:
            filepath: Path to save screenshot

        Returns:
            bool: True if saved successfully
        """
        screenshot = self.last_screenshot if self.last_screenshot is not None else self.get_screenshot()
        if screenshot is None:
            return False

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Convert to PIL Image and save
            # Check the number of dimensions safely
            try:
                if screenshot is None:
                    logger.error("Screenshot is None")
                    return False
                    
                if hasattr(screenshot, 'ndim'):
                    if screenshot.ndim == 3:
                        image = Image.fromarray(screenshot)
                    elif screenshot.ndim == 2:
                        image = Image.fromarray(screenshot, mode='L')
                    else:
                        logger.error(f"Unexpected screenshot dimensions: {screenshot.ndim}")
                        return False
                else:
                    # Fallback for unknown array types
                    image = Image.fromarray(screenshot)
                    
            except Exception as e:
                logger.error(f"Error converting screenshot to PIL Image: {e}")
                return False

            image.save(filepath)
            logger.info(f"Screenshot saved to: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return False

    def get_game_state(self) -> Dict[str, Any]:
        """
        Get current game state information.

        Returns:
            dict: Game state information
        """
        if not self.pyboy:
            return {}

        try:
            return {
                'frame_count': self.frame_count,
                'running': self._running,
                'paused': self._paused,
                'rom_loaded': self.rom_path is not None,
                'window_title': self.window_title,
                'scale': self.scale,
                'sound_enabled': self.sound,
                'performance_stats': self.performance_stats.copy()
            }
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return {}

    def set_frame_rate(self, fps: int):
        """
        Set target frame rate.

        Args:
            fps: Target frames per second
        """
        self.auto_tick_rate = fps
        self.target_frame_time = 1.0 / fps if fps > 0 else 0
        logger.info(f"Frame rate set to: {fps} FPS")

    def reset(self) -> bool:
        """
        Reset the emulator to initial state.

        Returns:
            bool: True if reset successfully
        """
        if not self.pyboy:
            return False

        try:
            self.pyboy.reset()
            self.frame_count = 0
            self.last_frame_time = time.time()
            logger.info("Emulator reset")
            return True
        except Exception as e:
            logger.error(f"Error resetting emulator: {e}")
            return False

    def set_callbacks(self,
                     on_frame: Optional[callable] = None,
                     on_input: Optional[callable] = None,
                     on_error: Optional[callable] = None):
        """
        Set callback functions for emulator events.

        Args:
            on_frame: Called after each frame (receives frame_count)
            on_input: Called when input is processed (receives button, duration)
            on_error: Called when errors occur (receives error_message)
        """
        self.on_frame_callback = on_frame
        self.on_input_callback = on_input
        self.on_error_callback = on_error

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop()