#!/usr/bin/env python3
"""
Test script to debug environment variable loading.
"""

import os
from pathlib import Path

# Test the same logic as in mistral_api.py
print("Testing environment variable loading...")

# Check current working directory
print(f"Current working directory: {os.getcwd()}")

# Check the path calculation (simulating agent_core/mistral_api.py perspective)
env_path = Path(__file__).parent / '.env'  # .env is in current directory
print(f"Calculated .env path: {env_path}")
print(f".env file exists: {env_path.exists()}")

if env_path.exists():
    print(f".env file contents:")
    with open(env_path, 'r') as f:
        print(f.read())
    
    # Try manual loading first
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Manual .env loading successful")
    except Exception as e:
        print(f"❌ Manual .env loading failed: {e}")
    
    # Try loading with dotenv as fallback
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print("✅ dotenv loaded successfully")
    except ImportError as e:
        print(f"❌ dotenv import failed: {e}")
else:
    print("❌ .env file not found at calculated path")

# Check if the environment variable is set
api_key = os.getenv("MISTRAL_API_KEY")
print(f"MISTRAL_API_KEY from environment: {'SET' if api_key else 'NOT SET'}")
if api_key:
    print(f"API key length: {len(api_key)}")
    print(f"API key preview: {api_key[:10]}...")

# Try loading from current directory
try:
    from dotenv import load_dotenv
    load_dotenv()  # Try to load from current directory
    print("✅ dotenv loaded from current directory")
    api_key2 = os.getenv("MISTRAL_API_KEY")
    print(f"MISTRAL_API_KEY after current dir load: {'SET' if api_key2 else 'NOT SET'}")
except Exception as e:
    print(f"❌ dotenv from current dir failed: {e}")

# Manual environment variable setting for testing
os.environ["MISTRAL_API_KEY"] = "test_key_12345"
api_key3 = os.getenv("MISTRAL_API_KEY")
print(f"MISTRAL_API_KEY after manual set: {'SET' if api_key3 else 'NOT SET'}")
print(f"Manual API key: {api_key3}")