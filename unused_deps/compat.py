import sys

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    import tomllib as toml
else:  # pragma: <3.11 cover
    import tomli as toml

__all__ = ("toml",)
