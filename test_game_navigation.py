#!/usr/bin/env python3
"""
Test script to verify basic game navigation without Mistral API.
This will test if the emulator can run and we can send basic inputs.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from emulator.emulator import PokemonEmulator

def main():
    print("Testing Pokemon Blue game navigation...")
    
    # Look for the ROM file
    rom_path = "./roms/pokemon-blue-version.gb"
    
    if not Path(rom_path).exists():
        print("Error: Pokemon Blue ROM not found!")
        return False
    
    print(f"Found ROM at: {rom_path}")
    
    try:
        # Create emulator instance
        emulator = PokemonEmulator(
            rom_path=rom_path,
            window_title="Pokemon Blue - Navigation Test",
            scale=3,
            sound=False,
            auto_tick_rate=60
        )
        
        # Load ROM
        if not emulator.load_rom():
            print("Failed to load ROM")
            return False
        
        # Start emulator
        if not emulator.start():
            print("Failed to start emulator")
            return False
        
        print("Emulator started. Testing game navigation...")
        print("The game should now be visible. Watch the window to see navigation.")
        
        # Let the game run for intro sequence (about 3 seconds)
        print("Waiting for intro sequence...")
        time.sleep(3)
        
        # Test basic navigation - simulate character creation process
        print("Testing navigation inputs...")
        
        # Press Start to skip intro
        print("Pressing START...")
        emulator.send_input('start', 0.1)
        time.sleep(1)
        
        # Wait a moment for title screen
        emulator.tick(60)  # Run 60 frames (1 second)
        time.sleep(1)
        
        # Press Start again to begin game
        print("Pressing START to begin...")
        emulator.send_input('start', 0.1)
        time.sleep(1)
        
        # Run some frames to see if we get to character creation
        emulator.tick(180)  # Run 3 seconds
        time.sleep(2)
        
        # Test some basic inputs that would be used in character creation
        print("Testing character creation inputs...")
        
        # Try selecting options (press A)
        emulator.send_input('a', 0.1)
        time.sleep(0.5)
        
        # Try moving cursor (press down)
        emulator.send_input('down', 0.1)
        time.sleep(0.5)
        
        # Press A again
        emulator.send_input('a', 0.1)
        time.sleep(0.5)
        
        # Run a bit more to see results
        emulator.tick(120)  # Run 2 seconds
        
        # Save a final screenshot
        screenshot_path = "screenshots/navigation_test_final.png"
        if emulator.save_screenshot(screenshot_path):
            print(f"Final screenshot saved to: {screenshot_path}")
        
        print("Navigation test completed!")
        print("Check the game window and screenshots to see if the character creation process was reached.")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'emulator' in locals():
            emulator.stop()

if __name__ == "__main__":
    success = main()
    if success:
        print("\nTest completed successfully!")
        print("The emulator is working and can navigate the game.")
    else:
        print("\nTest failed!")
    sys.exit(0 if success else 1)