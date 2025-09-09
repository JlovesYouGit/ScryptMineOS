#!/usr/bin/env python3
"""
Script to create a production package for the scrypt_doge mining project.
This script copies all essential files to a deployment directory.
"""

import shutil
import sys
from pathlib import Path

# Constants
DEPLOYMENT_DIR_NAME = "DEPLOYMENT_PACKAGE"
MANIFEST_FILE_NAME = "PRODUCTION_MANIFEST.txt"


def create_production_package():
    """Create a production package with all essential files."""

    # Define the source directory (current directory)
    source_dir = Path.cwd()

    # Define the deployment directory
    deploy_dir = source_dir / DEPLOYMENT_DIR_NAME

    # Create the deployment directory
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()

    # List of all essential files for production
    essential_files = [
        # Configuration files
        ".env.example",
        "params/scrypt_doge.toml",
        "pyproject.toml",
        "requirements.txt",
        "requirements.lock",
        # Build system files
        ".bazelrc",
        "BUILD",
        "WORKSPACE",
        "kernels/BUILD",
        "params/BUILD",
        "src/BUILD",
        # Main Python modules
        "asic_monitor.py",
        "asic_virtualization.py",
        "continuous_miner.py",
        "economic_config.py",
        "economic_guardian.py",
        "extract_constants.py",
        "extracted_constants.py",
        "gpu_asic_hybrid.py",
        "mining_constants.py",
        "performance_optimizer.py",
        "professional_asic_api.py",
        "resolver.py",
        "runner.py",
        "runner_continuous.py",
        "runner_fixed.py",
        "start_continuous_mining.py",
        # OpenCL kernel files
        "kernels/asic_optimized_scrypt.cl.jinja",
        "kernels/scrypt_core.cl.jinja",
        "kernels/scrypt_l2_optimized.cl",
        # C source files
        "src/gl4_hash.c",
        "src/sha256.comp",
        # Executable scripts
        "RUN_AUTO.py",
        "RUN_NOW.bat",
        "RUN_SIMPLE.bat",
        "SIMPLE_RUN.py",
        "START_COMPLETE_SYSTEM.bat",
        "START_CONTINUOUS_MINING.bat",
        "STOP_CONTINUOUS_MINING.bat",
        "launch_hybrid_miner.bat",
        "launch_optimization.bat",
        "start_professional_miner.bat",
        "hardware_control.sh",
        # Quality assurance & testing
        "test_asic_virtualization.py",
        "test_bazel.py",
        "test_economic_safety.py",
        "test_educational_mode.py",
        "test_f2pool.py",
        # Documentation files
        "README.md",
        "README_SIMPLE.md",
        "HOW_TO_RUN.md",
        "LAUNCH_GUIDE.md",
        "ECONOMIC_SAFETY_GUIDE.md",
        "ASIC_VIRTUALIZATION_GUIDE.md",
        "PRODUCTION_READINESS_ANALYSIS.md",
        "SYSTEM_ARCHITECTURE_ANALYSIS.md",
        "PERFORMANCE_OPTIMIZATION_COMPLETE.md",
        "SUCCESS_SUMMARY.md",
        # Quality control & development tools
        "pyfix.py",
        "pyfix.ps1",
        "PYFIX_UNIVERSAL.bat",
        "PYFIX_CHEATSHEET.md",
        ".pre-commit-config.yaml",
        ".deepsource.toml",
        # Essential hidden files
        ".gitignore",
    ]

    # Copy each essential file to the deployment directory
    copied_files = 0
    failed_files = []

    for file_path in essential_files:
        source_file = source_dir / file_path
        dest_file = deploy_dir / file_path

        # Create destination directory if it doesn't exist
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                copied_files += 1
                print(f"Copied: {file_path}")
            else:
                print(f"Warning: File not found - {file_path}")
                failed_files.append(file_path)
        except Exception as e:
            print(f"Error copying {file_path}: {e}")
            failed_files.append(file_path)

    # Create a manifest file listing all copied files
    manifest_file = deploy_dir / MANIFEST_FILE_NAME
    with open(manifest_file, "w") as f:
        f.write("Production Package Manifest\n")
        f.write("==========================\n\n")
        f.write(f"Total files copied: {copied_files}\n")
        if failed_files:
            f.write(f"Failed files: {len(failed_files)}\n")
            for file_path in failed_files:
                f.write(f"  - {file_path}\n")
        f.write("\nFiles included:\n")
        for file_path in essential_files:
            if file_path not in failed_files:
                f.write(f"  - {file_path}\n")

    print("\nProduction package created successfully!")
    print(f"Location: {deploy_dir}")
    print(f"Files copied: {copied_files}")
    if failed_files:
        print(f"Files failed: {len(failed_files)}")
        for file_path in failed_files:
            print(f"  - {file_path}")

    return deploy_dir


def main():
    """Main entry point for the script."""
    try:
        package_dir = create_production_package()
        print(f"\nPackage ready at: {package_dir}")
    except Exception as e:
        print(f"Error creating production package: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
