#!/usr/bin/env python3
"""
pyobfuscate - A polymorphic Python code obfuscator CLI tool.

Usage:
    pyobfuscate <input_file> [output_file] [-o] [--debug]
    pyobfuscate --help

Options:
    <input_file>       Path to the Python file to obfuscate.
    <output_file>      Path to save the obfuscated code (optional). Defaults to input_file.obfuscated.py.
    -o, --output       Force overwrite output file.
    --debug            Enable debug output (show obfuscated names and encryption keys).
    --version          Show version.
    --help             Show this help.
"""

import sys
import os
import argparse
import ast
import astor
import random
import string
import base64
import inspect
from typing import Dict, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
RANDOM_NAME_LENGTH = 8
DECRYPT_FUNC_NAME = "decrypt"
DECRYPT_FUNC_TEMPLATE = f"""
def {DECRYPT_FUNC_NAME}(data, key):
    return ''.join(chr(ord(c) ^ key) for c in data)
"""

# Global obfuscation state
class Obfuscator:
    def __init__(self):
        self.name_counter = 0
        self.obfuscated_names: Dict[str, str] = {}
        self.string_encryption_map: Dict[str, Tuple[str, int]] = {}
        self.used_names = set()
        self.dead_code_lines = []
        self.debug_info = {}

    def generate_random_name(self, prefix: str = "var") -> str:
        """Generate a unique random name."""
        while True:
            name = prefix + ''.join(random.choices(string.ascii_lowercase + string.digits, k=RANDOM_NAME_LENGTH))
            if name not in self.used_names:
                self.used_names.add(name)
                return name

    def obfuscate_name(self, original_name: str) -> str:
        """Obfuscate a name."""
        if original_name in self.obfuscated_names:
            return self.obfuscated_names[original_name]
        new_name = self.generate_random_name()
        self.obfuscated_names[original_name] = new_name
        return new_name

    def encrypt_string(self, s: str) -> Tuple[str, int]:
        """Encrypt string using XOR with a random key."""
        key = random.randint(1, 255)
        encrypted = ''.join(chr(ord(c) ^ key) for c in s)
        return base64.b64encode(encrypted.encode()).decode(), key

    def inject_dead_code(self, node: ast.AST) -> None:
        """Inject dead code after the node."""
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            return
        self.dead_code_lines.append(f"    if False: pass")
        self.dead_code_lines.append(f"    # DEAD CODE: {random.randint(1000, 9999)}")

    def generate_obfuscated_ast(self, tree: ast.AST) -> ast.AST:
        """Transform AST with obfuscation."""
        class ObfuscationVisitor(ast.NodeTransformer):
            def __init__(self, obfuscator: Obfuscator):
                self.obfuscator = obfuscator
                self.in_string = False
                self.string_literal = ""

            def visit_Name(self, node: ast.Name) -> ast.AST:
                if node.id in self.obfuscator.obfuscated_names:
                    return ast.Name(id=self.obfuscator.obfuscated_names[node.id], ctx=node.ctx)
                return node

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
                node.name = self.obfuscator.obfuscate_name(node.name)
                return self.generic_visit(node)

            def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
                node.name = self.obfuscator.obfuscate_name(node.name)
                return self.generic_visit(node)

            def visit_Str(self, node: ast.Str) -> ast.AST:
                s = node.s
                if s not in self.obfuscator.string_encryption_map:
                    encrypted, key = self.obfuscator.encrypt_string(s)
                    self.obfuscator.string_encryption_map[s] = (encrypted, key)
                    self.obfuscator.debug_info[s] = (encrypted, key)
                else:
                    encrypted, key = self.obfuscator.string_encryption_map[s]
                return ast.Call(
                    func=ast.Name(id=self.obfuscator.obfuscate_name(DECRYPT_FUNC_NAME), ctx=ast.Load()),
                    args=[
                        ast.Str(s=encrypted),
                        ast.Num(n=key)
                    ],
                    keywords=[]
                )

            def visit_Expr(self, node: ast.Expr) -> ast.Expr:
                self.obfuscator.inject_dead_code(node)
                return self.generic_visit(node)

            def visit_Module(self, node: ast.Module) -> ast.Module:
                self.obfuscator.inject_dead_code(node)
                return self.generic_visit(node)

        return ObfuscationVisitor(self.obfuscator).visit(tree)

    def get_obfuscated_code(self, source_code: str) -> str:
        """Generate obfuscated code."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

        obfuscated_tree = self.generate_obfuscated_ast(tree)

        # Add decryption function
        decryption_func = ast.parse(DECRYPT_FUNC_TEMPLATE).body[0]
        obfuscated_tree.body.insert(0, decryption_func)

        # Add dead code at the end
        for _ in range(random.randint(5, 15)):
            self.dead_code_lines.append(f"    # DEAD CODE: {random.randint(1000, 9999)}")

        # Convert AST to source
        code = astor.to_source(obfuscated_tree)
        return code


def main():
    parser = argparse.ArgumentParser(
        description="Polymorphic Python code obfuscator CLI tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pyobfuscate license.py
  pyobfuscate license.py license_obfuscated.py
  pyobfuscate license.py -o
"""
    )
    parser.add_argument("input_file", help="Input Python file to obfuscate.")
    parser.add_argument("output_file", nargs="?", help="Output file (optional).")
    parser.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite output file if it exists."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show obfuscation details (names, keys)."
    )
    parser.add_argument(
        "--version", action="version", version="pyobfuscate 1.0.0"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)

    # Read input
    with open(args.input_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Determine output
    if args.output_file:
        output_file = args.output_file
    else:
        base, ext = os.path.splitext(args.input_file)
        output_file = f"{base}.obfuscated.py"

    # Check if output exists and we're not allowing overwrite
    if os.path.exists(output_file) and not args.overwrite:
        logger.error(f"Output file already exists: {output_file}. Use -o to overwrite.")
        sys.exit(1)

    # Obfuscate
    try:
        obfuscator = Obfuscator()
        obfuscated_code = obfuscator.get_obfuscated_code(source_code)

        # Write output
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(obfuscated_code)

        logger.info(f"Obfuscated code saved to: {output_file}")

        # Debug info
        if args.debug:
            print("\n=== Debug Info ===")
            print(f"Decryption function: {DECRYPT_FUNC_NAME}")
            print(f"Number of strings encrypted: {len(obfuscator.string_encryption_map)}")
            for s, (enc, key) in obfuscator.string_encryption_map.items():
                print(f"  '{s}' -> {enc} (key: {key})")
            print(f"Random variable names used: {len(obfuscator.obfuscated_names)}")
            print("Dead code injected: ", len(obfuscator.dead_code_lines))
            print("==================")

    except Exception as e:
        logger.error(f"Error during obfuscation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
