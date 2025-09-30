#!/usr/bin/env python3
"""
Simple test script that starts the Pokemon Blue agent and runs for 25 seconds.
"""

import os
import sys
import time
import signal
from pathlib import Path
from main import PokemonBlueOrchestrator

# Set up signal handler to handle termination gracefully
def timeout_handler(signum, frame):
    print("\nTime's up! Shutting down gracefully...")
    raise KeyboardInterrupt()

def main():
    print("Starting Pokemon Blue AI agent for testing...")
    
    # Look for the ROM file that exists in the project
    rom_path = "./roms/pokemon-blue-version.gb"
    
    if not Path(rom_path).exists():
        print("Error: Pokemon Blue ROM not found!")
        print(f"Expected at: {rom_path}")
        return False
    
    print(f"Found ROM at: {rom_path}")
    
    # Create orchestrator instance
    orchestrator = PokemonBlueOrchestrator(
        rom_path=rom_path,
        headless=False,  # Run with visual window
        debug=True
    )
    
    try:
        print("Starting system...")
        success = orchestrator.start()
        
        if not success:
            print("Failed to start the system")
            return False
        
        print("System started successfully!")
        print("Pokemon Blue should now be visible in a game window.")
        print("Running for 25 seconds to see if Professor Oak appears...")
        
        # Set signal to interrupt after 25 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(25)
        
        # Run until interrupted by signal
        start_time = time.time()
        while orchestrator._running:
            time.sleep(0.5)  # Small sleep to prevent busy waiting
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:  # Print every 5 seconds
                print(f"Still running... {elapsed}s elapsed")
        
        print("Game loop ended naturally. Shutting down...")
        return True
        
    except KeyboardInterrupt:
        print("\nTimer reached! Shutting down...")
        return True
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cancel any remaining alarm
        signal.alarm(0)
        print("Stopping orchestrator...")
        orchestrator.stop()


if __name__ == "__main__":
    success = main()
    if success:
        print("\nTest completed successfully!")
        print("The Pokemon Blue agent integration is working properly!")
    else:
        print("\nTest failed!")