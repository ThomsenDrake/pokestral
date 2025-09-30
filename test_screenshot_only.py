#!/usr/bin/env python3
"""
Simple test to isolate screenshot capture issues.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from emulator.emulator import PokemonEmulator

def main():
    print("Testing screenshot capture only...")
    
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
            window_title="Screenshot Test",
            scale=2,
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
        
        print("Emulator started. Testing screenshot capture...")
        
        # Run for a few frames and test screenshots
        for i in range(10):
            emulator.tick()
            print(f"Frame {i+1}")
            
            # Try to get screenshot
            screenshot = emulator.get_screenshot()
            if screenshot is not None:
                print(f"  Screenshot captured: {type(screenshot)}, shape: {getattr(screenshot, 'shape', 'unknown')}")
                
                # Try to save it
                filepath = f"screenshots/test_frame_{i+1}.png"
                success = emulator.save_screenshot(filepath)
                print(f"  Save result: {success}")
            else:
                print("  Screenshot capture failed")
            
            time.sleep(0.1)
        
        print("Test completed successfully!")
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
    sys.exit(0 if success else 1)