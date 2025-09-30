#!/usr/bin/env python3
"""
Linting script for Pokemon Blue AI Agent.

This script provides a convenient way to run all linting tools with a single command.
It supports running individual tools or all tools at once.

Usage:
    python scripts/lint.py [--tool TOOL] [--fix] [--check-only] [--verbose]

Arguments:
    --tool TOOL         Run specific tool (black, isort, flake8, mypy, all)
    --fix               Automatically fix issues where possible
    --check-only        Only check for issues, don't fix (CI mode)
    --verbose          Verbose output

Examples:
    python scripts/lint.py --tool all --fix          # Fix all issues
    python scripts/lint.py --check-only             # Check only (CI mode)
    python scripts/lint.py --tool black --fix       # Format with black
    python scripts/lint.py --tool flake8            # Check style with flake8
"""

import argparse
import subprocess
import sys
from pathlib import Path


class LintingError(Exception):
    """Custom exception for linting errors."""
    pass


class Linter:
    """Manages linting tool execution."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent

    def run_command(self, command: list, description: str) -> bool:
        """Run a command and return success status."""
        if self.verbose:
            print(f"Running: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=False,
                text=True,
                check=False
            )

            if result.returncode != 0:
                print(f"❌ {description} failed with exit code {result.returncode}")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return False
            else:
                print(f"✅ {description} passed")
                return True

        except FileNotFoundError:
            print(f"❌ {description} failed - command not found: {command[0]}")
            return False
        except Exception as e:
            print(f"❌ {description} failed with error: {e}")
            return False

    def run_black(self, fix: bool = False) -> bool:
        """Run Black code formatter."""
        command = ["python", "-m", "black"]
        if fix:
            command.append("--check")
        else:
            command.extend(["--diff", "--color"])

        command.append(".")

        description = "Black code formatting check" if fix else "Black code formatting"
        return self.run_command(command, description)

    def run_isort(self, fix: bool = False) -> bool:
        """Run isort import sorter."""
        command = ["python", "-m", "isort", "--check-only", "--diff"] if fix else ["python", "-m", "isort"]
        command.append(".")

        description = "Import sorting check" if fix else "Import sorting"
        return self.run_command(command, description)

    def run_flake8(self) -> bool:
        """Run Flake8 style checker."""
        command = ["python", "-m", "flake8"]
        description = "Style check (Flake8)"
        return self.run_command(command, description)

    def run_mypy(self) -> bool:
        """Run MyPy type checker."""
        command = ["python", "-m", "mypy"]
        description = "Type check (MyPy)"
        return self.run_command(command, description)

    def run_all_checks(self, fix: bool = False) -> bool:
        """Run all linting checks."""
        print("🔍 Running all linting checks...")
        print()

        checks = [
            ("Black", lambda: self.run_black(fix)),
            ("isort", lambda: self.run_isort(fix)),
            ("Flake8", self.run_flake8),
            ("MyPy", self.run_mypy),
        ]

        results = []
        for name, check_func in checks:
            print(f"\n{'='*50}")
            print(f"Running {name}...")
            print('='*50)
            results.append(check_func())

        print(f"\n{'='*50}")
        print("LINTING SUMMARY")
        print('='*50)

        passed = sum(results)
        total = len(results)

        for i, (name, _) in enumerate(checks):
            status = "✅ PASSED" if results[i] else "❌ FAILED"
            print(f"{name:15} {status}")

        print(f"\nOverall: {passed}/{total} checks passed")

        if passed == total:
            print("🎉 All linting checks passed!")
            return True
        else:
            print("💥 Some linting checks failed!")
            if not fix:
                print("\n💡 Tip: Run with --fix to automatically fix issues where possible")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Linting script for Pokemon Blue AI Agent")
    parser.add_argument(
        "--tool",
        choices=["black", "isort", "flake8", "mypy", "all"],
        default="all",
        help="Specific tool to run (default: all)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for issues, don't fix (CI mode)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Override fix behavior for check-only mode
    fix = args.fix and not args.check_only

    try:
        linter = Linter(verbose=args.verbose)

        if args.tool == "all":
            success = linter.run_all_checks(fix=fix)
        else:
            success = getattr(linter, f"run_{args.tool}")(fix=fix)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Linting interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()