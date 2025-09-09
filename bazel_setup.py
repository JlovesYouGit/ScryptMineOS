#!/usr/bin/env python3
"""
Script to initialize and test Bazel setup for the scrypt_doge project.
"""

import os
import subprocess
import sys


def run_command(cmd, cwd=None):
    """Run a command and return its result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e}")
        print(f"stderr: {e.stderr}")
        return None


def check_bazel():
    """Check if Bazel is installed."""
    result = run_command("bazel --version")
    if result:
        print(f"Bazel version: {result}")
        return True
    print("Bazel is not installed or not in PATH")
    return False


def initialize_bazel():
    """Initialize Bazel workspace."""
    print("Initializing Bazel workspace...")

    # Check if we're in the right directory
    if not os.path.exists("WORKSPACE"):
        print(
            "Error: WORKSPACE file not found. "
            "Please run this script from the project root."
        )
        return False

    # Run bazel info to initialize
    print("Running bazel info...")
    result = run_command("bazel info")
    if result:
        print("Bazel workspace initialized successfully")
        return True
    print("Failed to initialize Bazel workspace")
    return False


def build_project():
    """Build the project with Bazel."""
    print("Building project with Bazel...")
    result = run_command("bazel build //...")
    if result is not None:
        print("Project built successfully")
        return True
    print("Failed to build project")
    return False


def main():
    """Main function."""
    print("Setting up Bazel for scrypt_doge project...")

    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Check Bazel installation
    if not check_bazel():
        print("Please install Bazel to continue:")
        print("https://docs.bazel.build/versions/main/install.html")
        return 1

    # Initialize Bazel
    if not initialize_bazel():
        return 1

    # Try to build the project
    if build_project():
        print("\nBazel setup completed successfully!")
        print("You can now use Bazel commands like:")
        print("  bazel build //...          # Build all targets")
        print("  bazel run //:runner        # Run the main miner")
        print("  bazel test //...           # Run all tests")
        return 0
    print("\nBazel setup completed with build errors.")
    print("You may need to fix some issues in the BUILD files.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
