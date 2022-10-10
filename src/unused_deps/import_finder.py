from __future__ import annotations

import ast
from collections.abc import Generator


def get_import_bases(filename: str) -> Generator[str, None, None]:
    with open(filename) as f:
        file_contents = f.read()

    module = ast.parse(file_contents, filename)

    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            yield node.names[0].name.partition(".")[0]
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            # Ignore relative imports
            and node.level == 0
        ):
            yield node.module.partition(".")[0]
