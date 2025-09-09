#!/usr/bin/env python3
"""
Universal Python Code Quality Fixer
Unified code quality solution that replaces fragmented tools

This script implements the "kill-the-chaos" workflow:
- Ruff (Rust-speed formatting and linting)
- Bandit (security scanning)
- pip-audit (dependency vulnerability scanning)
- pyclean (cache cleanup)

Usage:
    python pyfix.py [folder]     # Defaults to current directory
    python pyfix.py --help       # Show help
    python pyfix.py --security-only  # Only run security checks
    python pyfix.py --format-only    # Only run formatting
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Constants following project specifications
DEFAULT_FOLDER: str = "."
TIMEOUT_SECONDS: int = 300
MAX_RETRIES: int = 3


class PyFixRunner:
    """Unified Python code quality fixer."""

    def __init__(self, folder: str = DEFAULT_FOLDER, verbose: bool = True):
        self.folder = Path(folder)
        self.verbose = verbose
        self.start_time = time.time()

        # Handle both files and directories
        if self.folder.is_file():
            # If it's a file, use its parent directory and target the specific
            # file
            self.target_path = str(self.folder)
            self.folder = self.folder.parent
        else:
            # If it's a directory, target the whole directory
            self.target_path = str(self.folder)

    def _print(self, message: str, emoji: str = "🔧") -> None:
        """Print message with timestamp if verbose."""
        if self.verbose:
            elapsed = time.time() - self.start_time
            print(f"{emoji}  [{elapsed:6.1f}s] {message}")

    def _run_command(
        self, cmd: list[str], description: str, check_success: bool = True
    ) -> subprocess.CompletedProcess:
        """Run command with error handling and timeout."""
        self._print(f"Running {description}...")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.folder,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,  # Don't raise on non-zero exit
            )

            if result.returncode == 0:
                self._print(f"✅ {description} completed successfully")
                if result.stdout and self.verbose:
                    print(f"   Output: {result.stdout.strip()[:200]}")
            else:
                self._print(f"⚠️  {description} completed with warnings", "⚠️")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()[:200]}")

            return result

        except subprocess.TimeoutExpired:
            self._print(
                f"❌ {description} timed out after {TIMEOUT_SECONDS}s", "❌"
            )
            raise
        except Exception as e:
            self._print(f"❌ {description} failed: {e}", "❌")
            if check_success:
                raise
            return subprocess.CompletedProcess(cmd, 1, "", str(e))

    def format_code(self) -> bool:
        """Format code using ruff (replaces black + isort)."""
        self._print("🧽 FORMAT - Formatting Python code", "🧽")

        try:
            # Ruff format (replaces black)
            format_result = self._run_command(
                ["ruff", "format", self.target_path],
                "ruff format",
                check_success=False,
            )

            # Ruff check --fix (replaces isort and fixes other issues)
            fix_result = self._run_command(
                ["ruff", "check", "--fix", self.target_path],
                "ruff check --fix",
                check_success=False,
            )

            return format_result.returncode == 0 and fix_result.returncode == 0

        except Exception as e:
            self._print(f"❌ Formatting failed: {e}", "❌")
            return False

    def lint_code(self) -> bool:
        """Lint code using ruff."""
        self._print("🔍 LINT - Checking code quality", "🔍")

        try:
            result = self._run_command(
                ["ruff", "check", self.target_path],
                "ruff check",
                check_success=False,
            )

            if result.returncode == 0:
                self._print("✅ No linting issues found")
            else:
                self._print(
                    f"⚠️  Found {result.stdout.count('error')} linting issues"
                )

            return result.returncode == 0

        except Exception as e:
            self._print(f"❌ Linting failed: {e}", "❌")
            return False

    def security_scan(self) -> bool:
        """Security scan using bandit."""
        self._print("🛡️ SECURITY - Scanning for security issues", "🛡️")

        try:
            # For single files, bandit doesn't need -r flag
            if Path(self.target_path).is_file():
                cmd = ["bandit", self.target_path, "-f", "txt"]
            else:
                cmd = ["bandit", "-r", self.target_path, "-f", "txt"]

            result = self._run_command(
                cmd, "bandit security scan", check_success=False
            )

            if result.returncode == 0:
                self._print("✅ No security issues found")
            else:
                # Bandit returns 1 if issues found, which is expected
                lines = result.stdout.split("\n") if result.stdout else []
                issue_lines = [
                    l for l in lines if "Issue" in l or "Severity" in l
                ]
                if issue_lines:
                    self._print(f"⚠️  Found {len(issue_lines)} security issues")
                    if self.verbose:
                        for line in issue_lines[:5]:  # Show first 5 issues
                            print(f"     {line.strip()}")
                        if len(issue_lines) > 5:
                            print(f"     ... and {len(issue_lines) - 5} more")

            return True  # Security scan completed, even if issues found

        except Exception as e:
            self._print(f"❌ Security scan failed: {e}", "❌")
            return False

    def audit_dependencies(self) -> bool:
        """Audit dependencies using pip-audit."""
        self._print(
            "📦 DEPENDENCY-AUDIT - Checking for vulnerable packages", "📦"
        )

        try:
            result = self._run_command(
                ["pip-audit", "--desc", "--format=json"],
                "pip-audit dependency scan",
                check_success=False,
            )

            if result.returncode == 0:
                self._print("✅ No vulnerable dependencies found")
            # Parse JSON output to count vulnerabilities
            elif "vulnerabilities" in result.stdout:
                vuln_count = result.stdout.count('"id"')
                self._print(f"⚠️  Found {vuln_count} vulnerable dependencies")

            return True  # Audit completed, even if vulnerabilities found

        except Exception as e:
            self._print(f"❌ Dependency audit failed: {e}", "❌")
            return False

    def clean_cache(self) -> bool:
        """Clean Python cache files using pyclean."""
        self._print("🗑️ CACHE-CLEAN - Removing Python cache files", "🗑️")

        try:
            result = self._run_command(
                [
                    "pyclean",
                    "-v",
                    str(self.folder),
                ],  # Always clean the folder, not individual files
                "pyclean cache cleanup",
                check_success=False,
            )

            if result.returncode == 0:
                # Count cleaned files from output
                lines = result.stdout.split("\n") if result.stdout else []
                cleaned_files = [
                    l for l in lines if "Removing" in l or "removed" in l
                ]
                self._print(
                    f"✅ Cleaned {len(cleaned_files)} cache files/directories"
                )

            return True  # Cleanup completed

        except Exception as e:
            self._print(f"❌ Cache cleanup failed: {e}", "❌")
            return False

    def run_full_workflow(self) -> bool:
        """Run the complete code quality workflow."""
        self._print("🚀 Starting Python Code Quality Workflow", "🚀")
        self._print(f"📁 Target folder: {self.folder.absolute()}")

        results = []

        # Step 1: Format code
        results.append(self.format_code())

        # Step 2: Lint code
        results.append(self.lint_code())

        # Step 3: Security scan
        results.append(self.security_scan())

        # Step 4: Audit dependencies
        results.append(self.audit_dependencies())

        # Step 5: Clean cache
        results.append(self.clean_cache())

        # Summary
        elapsed = time.time() - self.start_time
        success_count = sum(results)
        total_count = len(results)

        if success_count == total_count:
            self._print(
                f"✅ DONE - All {total_count} steps completed successfully in {elapsed:.1f}s",
                "✅",
            )
            return True
        self._print(
            f"⚠️  DONE - {success_count}/{total_count} steps completed in {elapsed:.1f}s",
            "⚠️",
        )
        return False

    def run_security_only(self) -> bool:
        """Run only security-related checks."""
        self._print("🛡️ Running Security-Only Workflow", "🛡️")

        results = []
        results.append(self.security_scan())
        results.append(self.audit_dependencies())

        elapsed = time.time() - self.start_time
        success_count = sum(results)

        if success_count == len(results):
            self._print(
                f"✅ Security checks completed in {elapsed:.1f}s", "✅"
            )
            return True
        self._print(
            f"⚠️  Security checks completed with issues in {elapsed:.1f}s",
            "⚠️",
        )
        return False

    def run_format_only(self) -> bool:
        """Run only formatting."""
        self._print("🧽 Running Format-Only Workflow", "🧽")

        success = self.format_code()
        elapsed = time.time() - self.start_time

        if success:
            self._print(f"✅ Formatting completed in {elapsed:.1f}s", "✅")
        else:
            self._print(
                f"⚠️  Formatting completed with issues in {elapsed:.1f}s", "⚠️"
            )

        return success


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Python Code Quality Fixer - Kill the Chaos!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pyfix.py                    # Fix current directory
  python pyfix.py src/               # Fix src directory
  python pyfix.py --security-only    # Only security checks
  python pyfix.py --format-only      # Only formatting
  python pyfix.py --quiet src/       # Quiet mode

This tool replaces fragmented code quality tools with one unified solution.
        """,
    )

    parser.add_argument(
        "folder",
        nargs="?",
        default=DEFAULT_FOLDER,
        help=f"Target folder to fix (default: {DEFAULT_FOLDER})",
    )

    parser.add_argument(
        "--security-only",
        action="store_true",
        help="Run only security checks (bandit + pip-audit)",
    )

    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Run only code formatting (ruff format + ruff check --fix)",
    )

    parser.add_argument(
        "--quiet", action="store_true", help="Quiet mode - minimal output"
    )

    args = parser.parse_args()

    # Validate folder exists
    folder_path = Path(args.folder)
    if not folder_path.exists():
        print(f"❌ Error: Folder '{folder_path}' does not exist")
        return 1

    # Initialize runner
    runner = PyFixRunner(folder=args.folder, verbose=not args.quiet)

    try:
        # Run appropriate workflow
        if args.security_only:
            success = runner.run_security_only()
        elif args.format_only:
            success = runner.run_format_only()
        else:
            success = runner.run_full_workflow()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
