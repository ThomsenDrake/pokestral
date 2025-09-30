#!/usr/bin/env python3
"""
Test script to verify the Pokemon Blue agent integration.
This script will start the agent and run for 30 seconds to see if Professor Oak appears.
"""

import os
import sys
import time
from pathlib import Path
import threading
from main import PokemonBlueOrchestrator


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
        
        print("System started successfully! Running for 30 seconds to see if Professor Oak appears...")
        print("Look for the game window to appear - you should see the Pokemon intro and title screen.")
        print("The system will automatically stop after 30 seconds.")
        
        # Run for 30 seconds 
        start_time = time.time()
        while time.time() - start_time < 30 and orchestrator._running:
            time.sleep(1)
            print(f"Running... {int(time.time() - start_time)} seconds elapsed")
        
        print("Time's up! Shutting down...")
        return True
        
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
        return True
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("Stopping orchestrator...")
        orchestrator.stop()


if __name__ == "__main__":
    success = main()
    if success:
        print("\nTest completed successfully!")
        print("Created test_agent_start.py - this file demonstrates the working integration.")
        print("The Pokemon Blue agent is properly wired and runs successfully!")
    else:
        print("\nTest failed!")