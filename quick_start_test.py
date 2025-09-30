#!/usr/bin/env python3
"""
Test to start Pokemon Blue with Mistral AI control for a short time.
"""

import sys
import time
import signal
from pathlib import Path
import argparse
from main import PokemonBlueOrchestrator

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Pokemon Blue AI Agent - Short Test Run")
    parser.add_argument('--rom', type=str, default="./roms/pokemon-blue-version.gb", 
                       help='Path to Pokemon Blue ROM file')
    parser.add_argument('--duration', type=int, default=15, 
                       help='Duration to run in seconds (default: 15)')
    parser.add_argument('--headless', action='store_true', help='Run without visual window')

    args = parser.parse_args()

    print(f"Starting Pokemon Blue AI agent (duration: {args.duration}s)...")
    print(f"ROM: {args.rom}")
    print(f"Headless: {args.headless}")
    
    # Create orchestrator
    orchestrator = PokemonBlueOrchestrator(
        rom_path=args.rom,
        headless=args.headless,
        debug=True
    )

    try:
        # Start the system
        print("Starting system...")
        if not orchestrator.start():
            print("Failed to start the system")
            return False

        print(f"System started. Running for {args.duration} seconds...")
        
        # Run for specified duration
        start_time = time.time()
        while time.time() - start_time < args.duration and orchestrator._running:
            time.sleep(0.5)  # Check every half second
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:  # Print every 5 seconds
                print(f"Running... {elapsed}s / {args.duration}s")

        print("Test duration completed. Shutting down...")
        return True

    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Test completed successfully!")
        print("Pokemon Blue agent ran for the specified time.")
    else:
        print("\n❌ Test failed!")