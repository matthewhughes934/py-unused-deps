from __future__ import annotations

import ast
from collections.abc import Generator


def get_import_bases(file_contents: str, filename: str) -> Generator[str, None, None]:
    module = ast.parse(file_contents, filename)

    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            yield node.names[0].name.partition(".")[0]
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.level == 0
        ):
            yield node.module.partition(".")[0]
