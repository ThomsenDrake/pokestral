#!/usr/bin/env python3
"""
Pokemon Blue AI Agent - Main Integration Orchestrator

This script serves as the main entry point for the Pokemon Blue autonomous agent system.
It integrates all core components and provides a clean interface for launching the visual
gameplay automation with Mistral AI control.

Key Features:
- Component initialization and dependency management
- Visual gameplay monitoring window
- Mistral API integration for AI decision-making
- Memory mapping and state detection systems
- Tool integration (battle helper, pathfinder, puzzle solver)
- Error handling and graceful shutdown
- Real-time performance monitoring

Usage:
    python main.py [--rom PATH] [--headless] [--debug]

Arguments:
    --rom PATH      Path to Pokemon Blue ROM file (searches common locations if not provided)
    --headless      Run without visual window (for testing)
    --debug         Enable debug logging
"""

import argparse
import logging
import signal
import sys
import os
import time
from pathlib import Path
from typing import Optional

# Import core components
from agent_core.agent_core import AgentCore
from emulator.emulator import PokemonEmulator
from memory_map.pokemon_memory_map import PokemonMemoryMap
from state_detector.game_state import StateDetector
from prompt_manager.prompt_manager import PromptManager
from agent_core.mistral_api import MistralAPI
from tools.battle_helper import BattleHelper
from tools.pathfinder import Pathfinder
from tools.puzzle_solver import PuzzleSolver

class PokemonBlueOrchestrator:
    """
    Main integration orchestrator for Pokemon Blue AI agent system.

    This class coordinates all components and provides a unified interface
    for launching and controlling the autonomous gameplay system.
    """

    def __init__(self,
                 rom_path: Optional[str] = None,
                 headless: bool = False,
                 debug: bool = False):
        """
        Initialize the orchestrator with all components.

        Args:
            rom_path: Path to Pokemon Blue ROM file
            headless: Whether to run without visual window
            debug: Enable debug logging
        """
        self.rom_path = rom_path or self._find_rom()
        self.headless = headless
        self.debug = debug

        # Core components (initialized on demand)
        self.emulator: Optional[PokemonEmulator] = None
        self.agent_core: Optional[AgentCore] = None
        self.memory_map: Optional[PokemonMemoryMap] = None
        self.state_detector: Optional[StateDetector] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.mistral_api: Optional[MistralAPI] = None
        self.battle_helper: Optional[BattleHelper] = None
        self.pathfinder: Optional[Pathfinder] = None
        self.puzzle_solver: Optional[PuzzleSolver] = None

        # Control flags
        self._running = False
        self._shutdown_requested = False

        # Performance tracking
        self.start_time = 0
        self.frames_processed = 0

        # Setup logging
        self._setup_logging()

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        self.logger.info("Pokemon Blue Orchestrator initialized")

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

    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.DEBUG if self.debug else logging.INFO

        # Create logs directory if it doesn't exist
        Path("logs").mkdir(exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/pokemon_blue_agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger("PokemonBlueOrchestrator")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
            self._shutdown_requested = True
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def initialize_components(self) -> bool:
        """
        Initialize all system components.

        Returns:
            bool: True if all components initialized successfully
        """
        try:
            self.logger.info("Initializing system components...")

            # Initialize core components
            self.memory_map = PokemonMemoryMap()
            self.state_detector = StateDetector(self.memory_map)
            self.prompt_manager = PromptManager()
            self.mistral_api = MistralAPI()
            self.battle_helper = BattleHelper()
            self.pathfinder = Pathfinder([])  # Pass an empty grid as required
            self.puzzle_solver = PuzzleSolver()

            # Initialize emulator with visual display
            self.emulator = PokemonEmulator(
                rom_path=self.rom_path,
                window_title="Pokemon Blue - AI Agent",
                scale=3 if not self.headless else 1,
                sound=False,  # Disable sound for better performance
                auto_tick_rate=60
            )

            # Load ROM
            if not self.emulator.load_rom():
                self.logger.error("Failed to load Pokemon Blue ROM")
                return False

            # Initialize agent core
            self.agent_core = AgentCore(
                rom_path=self.rom_path,
                headless=self.headless
            )
            
            # Connect the emulator to the agent core
            self.agent_core.connect_emulator(self.emulator)

            # Setup emulator callbacks for integration
            self._setup_emulator_callbacks()

            self.logger.info("All components initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            return False

    def _setup_emulator_callbacks(self):
        """Setup callbacks for emulator-agent integration."""
        if not self.emulator or not self.agent_core:
            return

        def on_frame_callback(frame_count):
            """Called after each frame is processed."""
            self.frames_processed += 1

            # Log progress periodically
            if frame_count % 3600 == 0:  # Every minute at 60fps
                elapsed = time.time() - self.start_time
                fps_avg = frame_count / elapsed if elapsed > 0 else 0
                # Skip state detection here to avoid error; state detection should happen in agent core
                self.logger.info(f"Frame {frame_count}: Avg FPS={fps_avg:.1f}, "
                               f"State=Unknown (detected in agent core)")

        def on_input_callback(button, duration):
            """Called when input is processed."""
            self.logger.debug(f"Input: {button} for {duration}s")

        def on_error_callback(error_message):
            """Called when errors occur."""
            self.logger.error(f"Emulator error: {error_message}")

        self.emulator.set_callbacks(
            on_frame=on_frame_callback,
            on_input=on_input_callback,
            on_error=on_error_callback
        )

    def start(self) -> bool:
        """
        Start the Pokemon Blue AI agent system.

        Returns:
            bool: True if started successfully
        """
        if self._running:
            self.logger.warning("System is already running")
            return False

        try:
            self.logger.info("Starting Pokemon Blue AI Agent system...")

            # Initialize components if not already done
            if not self.initialize_components():
                return False

            # Start emulator
            if not self.emulator.start(auto_tick=False):  # We'll control ticking manually
                self.logger.error("Failed to start emulator")
                return False

            self._running = True
            self.start_time = time.time()

            self.logger.info("System started successfully. Launching game loop...")

            # Start main game loop
            return self._run_game_loop()

        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            self._running = False
            return False

    def _run_game_loop(self) -> bool:
        """
        Main game loop coordinating all components.

        Returns:
            bool: True if loop completed successfully
        """
        if not self.emulator or not self.agent_core:
            self.logger.error("Components not initialized")
            return False

        try:
            # Main loop
            while self._running and not self._shutdown_requested:
                if not self.emulator.is_running():
                    break

                # Let the agent handle the game loop instead of just ticking
                # The agent is responsible for coordinating with the emulator
                self.agent_core.main_game_loop()

            return True

        except KeyboardInterrupt:
            self.logger.info("Game loop interrupted by user")
            return True
        except Exception as e:
            self.logger.error(f"Error in game loop: {e}")
            return False

    def _perform_periodic_tasks(self):
        """Perform periodic maintenance tasks."""
        try:
            # Update performance stats
            if self.emulator:
                game_state = self.emulator.get_game_state()
                self.logger.debug(f"Game state: {game_state}")

            # Log system status every 10 seconds
            if self.emulator.frame_count % 600 == 0:
                elapsed = time.time() - self.start_time
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

    def stop(self):
        """Stop the system and cleanup resources."""
        if not self._running:
            return

        self.logger.info("Stopping Pokemon Blue AI Agent system...")
        self._running = False

        # Stop emulator
        if self.emulator:
            self.emulator.stop()

        # Stop agent core
        if self.agent_core:
            # Agent core cleanup would go here
            pass

        # Log final statistics
        if self.start_time > 0:
            total_time = time.time() - self.start_time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = int(total_time % 60)

            self.logger.info(
                "System stopped. Final stats: "
                f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d} | "
                f"Total frames: {self.frames_processed:,} | "
                f"Average FPS: {self.frames_processed/total_time:.1f}"
            )

    def pause(self):
        """Pause the system."""
        if self.emulator:
            self.emulator.pause()
        self.logger.info("System paused")

    def resume(self):
        """Resume the system."""
        if self.emulator:
            self.emulator.resume()
        self.logger.info("System resumed")

    def reset(self) -> bool:
        """
        Reset the game to initial state.

        Returns:
            bool: True if reset successfully
        """
        if not self.emulator:
            self.logger.error("Cannot reset: emulator not initialized")
            return False

        success = self.emulator.reset()
        if success:
            self.frames_processed = 0
            self.start_time = time.time()
            self.logger.info("Game reset successfully")
        else:
            self.logger.error("Failed to reset game")

        return success

    def get_system_status(self) -> dict:
        """
        Get current system status.

        Returns:
            dict: System status information
        """
        status = {
            'running': self._running,
            'rom_loaded': self.rom_path is not None,
            'components_initialized': all([
                self.emulator is not None,
                self.agent_core is not None,
                self.memory_map is not None,
                self.state_detector is not None,
                self.mistral_api is not None
            ]),
            'performance': {}
        }

        if self.emulator:
            status['performance'] = self.emulator.get_game_state()
            status['performance']['frames_processed'] = self.frames_processed
            status['performance']['runtime_seconds'] = time.time() - self.start_time if self.start_time > 0 else 0

        if self.start_time > 0:
            status['performance']['average_fps'] = self.frames_processed / (time.time() - self.start_time)

        return status

    def save_screenshot(self, filepath: str = None) -> bool:
        """
        Save current game screenshot.

        Args:
            filepath: Path to save screenshot (auto-generated if not provided)

        Returns:
            bool: True if saved successfully
        """
        if not self.emulator:
            self.logger.error("Cannot save screenshot: emulator not initialized")
            return False

        if filepath is None:
            import time
            timestamp = int(time.time())
            filepath = f"screenshots/game_state_{timestamp}.png"

        return self.emulator.save_screenshot(filepath)

def main():
    """Main entry point for the Pokemon Blue AI agent system."""
    parser = argparse.ArgumentParser(description="Pokemon Blue AI Agent - Autonomous Gameplay System")
    parser.add_argument('--rom', type=str, help='Path to Pokemon Blue ROM file')
    parser.add_argument('--headless', action='store_true', help='Run without visual window')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--reset', action='store_true', help='Reset game to initial state')

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = PokemonBlueOrchestrator(
        rom_path=args.rom,
        headless=args.headless,
        debug=args.debug
    )

    try:
        # Start the system
        if not orchestrator.start():
            sys.exit(1)

        # Handle reset if requested
        if args.reset:
            import time
            time.sleep(2)  # Wait for system to stabilize
            orchestrator.reset()

        # Keep main thread alive
        while orchestrator._running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main()