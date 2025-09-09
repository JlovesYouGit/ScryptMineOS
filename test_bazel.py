#!/usr/bin/env python3
"""
Simple test to verify Bazel setup.
"""

import subprocess
import sys


def test_bazel_setup():
    """Test if Bazel setup is working."""
    try:
        # Test if bazel is available
        result = subprocess.run(
            ["bazel", "version"], capture_output=True, text=True, check=True
        )
        print(f"Bazel is available: {result.stdout.strip()}")

        # Test if workspace is properly configured
        result = subprocess.run(
            ["bazel", "info", "workspace"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Workspace path: {result.stdout.strip()}")

        print("Bazel setup verification successful!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("Bazel setup verification failed!")
        return False
    except FileNotFoundError:
        print("Error: Bazel is not installed or not in PATH")
        return False


if __name__ == "__main__":
    success = test_bazel_setup()
    sys.exit(0 if success else 1)
