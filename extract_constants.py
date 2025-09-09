#!/usr/bin/env python3
"""
Automated Constants Extraction Tool
Analyzes Python files and identifies magic numbers that should be constants.

This tool helps speed up the constant extraction process by:
1. Scanning Python files for magic numbers
2. Suggesting constant names based on context
3. Generating replacement code automatically
4. Following the Constants Definition Standard
"""

import argparse
import ast
from pathlib import Path


class ConstantExtractor(ast.NodeVisitor):
    """AST visitor to extract magic numbers and suggest constants"""

    def __init__(self, filename: str):
        self.filename = filename
        self.magic_numbers: list[tuple[int, int, str, str]] = []
        self.current_function: str | None = None
        self.current_class: str | None = None

        # Numbers to ignore (common non-magic numbers)
        self.ignore_numbers = {0, 1, 2, -1, 100, 1000}

        # Context-based naming suggestions
        self.context_mappings = {
            "timeout": "TIMEOUT",
            "port": "PORT",
            "max": "MAX",
            "min": "MIN",
            "limit": "LIMIT",
            "size": "SIZE",
            "count": "COUNT",
            "rate": "RATE",
            "interval": "INTERVAL",
            "wait": "WAIT",
            "retry": "RETRY",
            "restart": "RESTART",
            "hash": "HASH",
            "power": "POWER",
            "temp": "TEMP",
            "voltage": "VOLTAGE",
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track current function for context"""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track current class for context"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit numeric constants and record magic numbers"""
        if isinstance(node.value, (int, float)):
            if node.value not in self.ignore_numbers:
                context = self._get_context(node)
                suggested_name = self._suggest_constant_name(
                    node.value, context
                )

                self.magic_numbers.append(
                    (
                        node.lineno,
                        node.col_offset,
                        str(node.value),
                        suggested_name,
                    )
                )

        self.generic_visit(node)

    def _get_context(self, node: ast.Constant) -> str:
        """Get context around the constant for better naming"""
        context_parts = []

        if self.current_class:
            context_parts.append(self.current_class.lower())
        if self.current_function:
            context_parts.append(self.current_function.lower())

        return "_".join(context_parts)

    def _suggest_constant_name(self, value: float, context: str) -> str:
        """Suggest a constant name based on value and context"""
        # Special cases for common mining values
        mining_constants = {
            # Stratum: Ensure error handling  # Stratum: Ensure error handling
            STRATUM_PORT: "STRATUM_PORT",
            # Stratum: Ensure error handling  # Stratum: Ensure error handling
            STRATUM_SSL_PORT: "STRATUM_SSL_PORT",
            9100: "PROMETHEUS_PORT",
            SCRYPT_N_PARAM: "SCRYPT_N_PARAM",
            SCRATCHPAD_SIZE: "SCRATCHPAD_SIZE",
            LINE_LENGTH_LIMIT: "LINE_LENGTH_LIMIT",
            OPTIMAL_TEMP_C: "OPTIMAL_TEMP_CELSIUS",
            MAX_TEMP_C: "MAX_TEMP_CELSIUS",
            TARGET_HASHRATE_GHS: "TARGET_HASHRATE_GHS",
            TARGET_POWER_W: "TARGET_POWER_WATTS",
            0.36: "TARGET_EFFICIENCY_JTH",
        }

        if value in mining_constants:
            return mining_constants[value]

        # Context-based suggestions
        context_lower = context.lower()
        for keyword, prefix in self.context_mappings.items():
            if keyword in context_lower:
                if isinstance(value, int):
                    return f"{prefix}_{abs(value)}"
                safe_value = str(value).replace(".", "_")
                return f"{prefix}_{safe_value}"

        # Generic fallback
        if isinstance(value, int):
            return f"MAGIC_NUMBER_{abs(value)}"
        safe_value = str(value).replace(".", "_").replace("-", "NEG_")
        return f"MAGIC_FLOAT_{safe_value}"


def analyze_file(file_path: Path) -> list[tuple[int, int, str, str]]:
    """Analyze a Python file and extract magic numbers"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        extractor = ConstantExtractor(str(file_path))
        extractor.visit(tree)

        return extractor.magic_numbers
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return []


def generate_constants_module(
    all_constants: dict[str, list[tuple[int, int, str, str]]],
) -> str:
    """Generate a constants module from extracted magic numbers"""

    # Collect unique constants
    unique_constants = {}
    for filename, constants in all_constants.items():
        for line, col, value, name in constants:
            if name not in unique_constants:
                unique_constants[name] = value

    # Generate module content
    module_content = [
        '"""',
        "Extracted Constants Module",
        "Auto-generated constants from magic number analysis.",
        "",
        "This module centralizes magic numbers found throughout the codebase",
        "following the Constants Definition Standard.",
        '"""',
        "",
        "from typing import Final",
        "",
    ]

    # Sort constants by category
    categories = {"Network": [], "System": [], "Mining": [], "Generic": []}

    for name, value in sorted(unique_constants.items()):
        if any(keyword in name for keyword in ["PORT", "TIMEOUT", "STRATUM"]):
            categories["Network"].append((name, value))
        elif any(
            keyword in name for keyword in ["MAX", "MIN", "LIMIT", "SIZE"]
        ):
            categories["System"].append((name, value))
        elif any(
            keyword in name for keyword in ["HASH", "POWER", "TEMP", "SCRYPT"]
        ):
            categories["Mining"].append((name, value))
        else:
            categories["Generic"].append((name, value))

    # Generate categorized constants
    for category, constants in categories.items():
        if constants:
            module_content.append(f"# {category} Constants")
            for name, value in constants:
                module_content.append(f"{name}: Final = {value}")
            module_content.append("")

    return "\n".join(module_content)


def main() -> int:
    """Main entry point for constants extraction"""
    parser = argparse.ArgumentParser(
        description="Extract magic numbers and suggest constants"
    )
    parser.add_argument("files", nargs="+", help="Python files to analyze")
    parser.add_argument("--output", "-o", help="Output constants module file")
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        default=5,
        help="Minimum occurrences to suggest constant",
    )

    args = parser.parse_args()

    print("🔍 Extracting constants from Python files...")

    all_constants = {}
    total_magic_numbers = 0

    for file_path in args.files:
        path = Path(file_path)
        if path.exists() and path.suffix == ".py":
            constants = analyze_file(path)
            if constants:
                all_constants[str(path)] = constants
                total_magic_numbers += len(constants)
                print(f"📄 {path.name}: {len(constants)} magic numbers found")

    print(f"\n📊 Total magic numbers found: {total_magic_numbers}")

    # Display analysis results
    if all_constants:
        print("\n🎯 Magic Numbers by File:")
        for filename, constants in all_constants.items():
            print(f"\n{Path(filename).name}:")
            for line, col, value, suggested_name in constants[
                :MAX_RETRIES
            ]:  # Show first MAX_RETRIES
                print(f"  Line {line}: {value} → {suggested_name}")
            if len(constants) > MAX_RETRIES:
                print(f"  ... and {len(constants) - MAX_RETRIES} more")

    # Generate constants module if requested
    if args.output:
        module_content = generate_constants_module(all_constants)
        with open(args.output, "w") as f:
            f.write(module_content)
        print(f"\n✅ Constants module generated: {args.output}")

    return 0 if total_magic_numbers == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
