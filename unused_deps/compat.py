import sys

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    import tomllib as toml
else:  # pragma: <3.11 cover
    import tomli as toml

if sys.version_info >= (3, 8):  # pragma: >=3.8 cover
    import importlib.metadata as importlib_metadata
else:  # pragma: <3.8 cover
    import importlib_metadata

__all__ = ("toml", "importlib_metadata")
