import tiktoken
from rich.console import Console
from rich.style import Style
from rich.tree import Tree


class Plain2CodeConsole(Console):
    INFO_STYLE = Style()
    WARNING_STYLE = Style(color="yellow", bold=True)
    ERROR_STYLE = Style(color="red", bold=True)
    INPUT_STYLE = Style(color="#4169E1")  # Royal Blue
    OUTPUT_STYLE = Style(color="green")
    DEBUG_STYLE = Style(color="purple")

    def __init__(self):
        super().__init__()
        self.llm_encoding = tiktoken.get_encoding("cl100k_base")

    def info(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.INFO_STYLE)

    def warning(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.WARNING_STYLE)

    def error(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.ERROR_STYLE)

    def input(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.INPUT_STYLE)

    def output(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.OUTPUT_STYLE)

    def debug(self, *args, **kwargs):
        super().print(*args, **kwargs, style=self.DEBUG_STYLE)

    def print_list(self, items, style=None):
        for item in items:
            super().print(f"{item}", style=style)

    def print_files(self, header, root_folder, files, style=None):
        if not files:
            return

        tree = self._create_tree_from_files(root_folder, files)
        super().print(f"\n[b]{header}[/b]", style=style)

        super().print(tree, style=style)

        super().print()

    def _create_tree_from_files(self, root_folder, files):
        """
        Creates a Tree structure from a dictionary of files using the rich library.

        Args:
            files (dict): A dictionary where keys are file paths (strings)
                            and values are file content (strings).

        Returns:
            Tree: The root of the created tree structure.
        """
        tree = Tree(root_folder)
        for path, content in files.items():
            parts = path.split("/")
            current_level = tree
            for part in parts:
                existing_level = None
                for child in current_level.children:
                    if child.label == part:
                        existing_level = child
                        break

                if existing_level is None:
                    if part == parts[-1]:
                        if files[path] is None:
                            current_level = current_level.add(f"{part} [red]deleted[/red]")
                        else:
                            file_lines = len(content.splitlines())
                            file_tokens = len(self.llm_encoding.encode(content))
                            current_level = current_level.add(
                                f"{part} [b]({file_lines} lines, {file_tokens} tokens)[/b]"
                            )
                    else:
                        current_level = current_level.add(part)
                else:
                    current_level = existing_level

        return tree

    def print_resources(self, resources_list, linked_resources):
        if len(resources_list) == 0:
            console.input("\nNo linked resources found.")
            return

        self.input("\nLinked resources:")
        for resource_name in resources_list:
            if resource_name["target"] in linked_resources:
                file_tokens = len(self.llm_encoding.encode(linked_resources[resource_name["target"]]))
                console.input(
                    f"- {resource_name['text']} [b][#4169E1]({resource_name['target']}, {file_tokens} tokens)[/#4169E1][/b]"
                )

        self.input()


console = Plain2CodeConsole()
