import sys
import os
import re
import argparse

# Add the parent directory to the path so we can import plain2code_arguments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plain2code_arguments import create_parser

parser = create_parser()

help_text = parser.format_help()


cleaned = re.sub(r'(--[a-zA-Z0-9-]+)\s+([A-Z][A-Z0-9_]+)', r'\1', help_text)

def add_defaults(line: str) -> str:
    
    match = re.match(r'\s{2}(-{1,2}[a-zA-Z0-9-]+)', line)
    if not match:
        return line

    option = match.group(1)

    # Find the parser action for this option
    for action in parser._actions:
        if option in action.option_strings:
           
            if "--api-key" in action.option_strings:
                break
            if action.default not in (None, argparse.SUPPRESS, False):
                line = line.rstrip() + f" (default: {action.default})"
            break
    return line

new_lines = [add_defaults(line) for line in cleaned.splitlines()]
help_text_final = "\n".join(new_lines)

# Create markdown
md = "# Plain2Code CLI Reference\n\n```text\n" + help_text_final + "\n```"

# Generate cli.md in the docs folder
docs_dir = os.path.dirname(os.path.abspath(__file__))
cli_md_path = os.path.join(docs_dir, "plain2code_cli.md")

with open(cli_md_path, "w", encoding="utf-8") as f:
    f.write(md)