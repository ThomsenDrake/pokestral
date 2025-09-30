#!/usr/bin/env python3
"""
Setup script for linting tools and pre-commit hooks.

This script helps set up the development environment with all necessary linting tools
and pre-commit hooks for automated code quality checks.

Usage:
    python scripts/setup_linting.py [--dev] [--pre-commit]

Arguments:
    --dev           Install development dependencies (linting tools)
    --pre-commit    Set up pre-commit hooks

Examples:
    python scripts/setup_linting.py --dev           # Install linting tools
    python scripts/setup_linting.py --pre-commit    # Setup pre-commit hooks
    python scripts/setup_linting.py --dev --pre-commit  # Do both
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str, check: bool = True) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, capture_output=False, text=True, check=check)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} failed - command not found: {command[0]}")
        return False


def install_dev_dependencies() -> bool:
    """Install development dependencies."""
    print("📦 Installing development dependencies...")

    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("⚠️  Warning: Not in a virtual environment. Consider using one for development.")

    # Try using uv first (preferred method)
    if Path("uv.lock").exists() or Path("pyproject.toml").exists():
        print("🔍 Detected uv project configuration")

        # Install development dependencies using uv
        success = run_command(
            ["uv", "sync", "--dev"],
            "Install development dependencies using uv sync --dev"
        )

        if success:
            # Also ensure pre-commit is available
            success = run_command(
                ["uv", "add", "--dev", "pre-commit"],
                "Add pre-commit as development dependency"
            )
            return success
        else:
            print("⚠️  uv sync failed, falling back to pip...")
    else:
        print("ℹ️  Using legacy pip-based installation")

    # Fallback to consolidated requirements.txt if it exists
    if Path("requirements.txt").exists():
        success = run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Install all dependencies from requirements.txt"
        )
        if not success:
            return False
    else:
        print("❌ Neither uv project nor requirements.txt found")
        return False

    # Install pre-commit (should already be in requirements.txt but ensure it's available)
    success = run_command(
        [sys.executable, "-m", "pip", "install", "pre-commit"],
        "Install pre-commit"
    )

    return success


def setup_pre_commit() -> bool:
    """Set up pre-commit hooks."""
    print("🔗 Setting up pre-commit hooks...")

    # Check if .pre-commit-config.yaml exists
    if not Path(".pre-commit-config.yaml").exists():
        print("❌ .pre-commit-config.yaml not found")
        return False

    # Install pre-commit hooks
    success = run_command(
        ["pre-commit", "install"],
        "Install pre-commit hooks"
    )

    if success:
        print("🎉 Pre-commit hooks installed successfully!")
        print("✅ Code will now be automatically linted before each commit")

    return success


def validate_installation() -> bool:
    """Validate that all tools are properly installed."""
    print("🔍 Validating installation...")

    tools = [
        ("black", ["python", "-m", "black", "--version"]),
        ("isort", ["python", "-m", "isort", "--version"]),
        ("flake8", ["python", "-m", "flake8", "--version"]),
        ("mypy", ["python", "-m", "mypy", "--version"]),
        ("pre-commit", ["pre-commit", "--version"]),
    ]

    all_passed = True
    for tool_name, command in tools:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"✅ {tool_name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool_name} is not available")
            all_passed = False

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup linting tools and pre-commit hooks")
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Install development dependencies"
    )
    parser.add_argument(
        "--pre-commit",
        action="store_true",
        help="Set up pre-commit hooks"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate installation"
    )

    args = parser.parse_args()

    if not any([args.dev, args.pre_commit, args.validate]):
        print("❓ No action specified. Use --dev, --pre-commit, or --validate")
        print("💡 Use --dev --pre-commit to set up everything")
        return

    success = True

    if args.dev:
        success &= install_dev_dependencies()

    if args.pre_commit:
        success &= setup_pre_commit()

    if args.validate:
        success &= validate_installation()

    if success:
        print("\n🎉 Setup completed successfully!")
        print("\n📖 Usage tips:")
        print("  • Run linting: python scripts/lint.py")
        print("  • Run specific tool: python scripts/lint.py --tool black --fix")
        print("  • Manual check: python scripts/lint.py --check-only")
        print("  • Pre-commit will run automatically on git commit")
    else:
        print("\n💥 Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()