import sys
import os

# Add the parent directory to the path so we can import plain2code_arguments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plain2code_arguments import create_parser

# Get the parser and generate help text
parser = create_parser()
help_text = parser.format_help()

# Create markdown
md = "# CLI Reference\n\n```text\n" + help_text + "\n```"

# Generate cli.md in the docs folder
docs_dir = os.path.dirname(os.path.abspath(__file__))
cli_md_path = os.path.join(docs_dir, "plain2code_cli.md")

with open(cli_md_path, "w", encoding="utf-8") as f:
    f.write(md)
    