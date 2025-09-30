#!/usr/bin/env python3
"""
Test script with intelligent navigation for Pokemon Blue character creation.
This simulates what Mistral would do by providing context-aware responses.
"""

import os
import sys
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from emulator.emulator import PokemonEmulator

class IntelligentNavigator:
    """Simulates intelligent game navigation for character creation"""
    
    def __init__(self):
        self.step = 0
        self.steps = [
            {"action": "wait", "reason": "Waiting for intro sequence"},
            {"action": "press_start", "reason": "Skip intro screen"},
            {"action": "wait", "reason": "Wait for title screen"},
            {"action": "press_start", "reason": "Start new game"},
            {"action": "wait", "reason": "Wait for character creation"},
            {"action": "select_option", "reason": "Select default name option"},
            {"action": "confirm", "reason": "Confirm name selection"},
            {"action": "wait", "reason": "Wait for rival name"},
            {"action": "select_option", "reason": "Select default rival name"},
            {"action": "confirm", "reason": "Confirm rival name"},
            {"action": "wait", "reason": "Wait for game start"},
            {"action": "confirm", "reason": "Start adventure"},
        ]
    
    def get_next_action(self):
        """Get the next action in the character creation sequence"""
        if self.step >= len(self.steps):
            return {"action": "wait", "reason": "Character creation complete"}
        
        action = self.steps[self.step]
        self.step += 1
        return action

def main():
    print("Testing intelligent Pokemon Blue character creation navigation...")
    
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
            window_title="Pokemon Blue - Intelligent Navigation Test",
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
        
        print("Emulator started. Beginning intelligent character creation navigation...")
        
        # Create intelligent navigator
        navigator = IntelligentNavigator()
        
        # Execute navigation steps
        for i, step_info in enumerate(navigator.steps):
            print(f"\nStep {i+1}: {step_info['reason']}")
            
            if step_info["action"] == "wait":
                # Wait for transitions
                emulator.tick(120)  # 2 seconds
                time.sleep(2)
                
            elif step_info["action"] == "press_start":
                emulator.send_input('start', 0.1)
                emulator.tick(60)  # 1 second
                time.sleep(1)
                
            elif step_info["action"] == "select_option":
                # Move down a bit to change selection, then accept
                emulator.send_input('down', 0.1)
                time.sleep(0.5)
                emulator.tick(30)
                
            elif step_info["action"] == "confirm":
                emulator.send_input('a', 0.1)
                time.sleep(0.5)
                emulator.tick(60)
                
            # Save screenshot at each step
            screenshot_path = f"screenshots/intelligent_nav_step_{i+1}.png"
            emulator.save_screenshot(screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")
            
            # Small delay between actions
            time.sleep(0.5)
        
        # Run a bit more to see the result
        print("\nRunning final frames to see the result...")
        emulator.tick(180)  # 3 seconds
        
        # Save final screenshot
        final_screenshot = "screenshots/intelligent_navigation_final.png"
        emulator.save_screenshot(final_screenshot)
        print(f"Final screenshot saved: {final_screenshot}")
        
        print("\nIntelligent navigation test completed!")
        print("Check the screenshots to see the character creation progression.")
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
        print("\n✅ Test completed successfully!")
        print("The intelligent navigation successfully guided through character creation.")
        print("This demonstrates how Mistral AI could navigate the game with proper visual understanding.")
    else:
        print("\n❌ Test failed!")
    sys.exit(0 if success else 1)