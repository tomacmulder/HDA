from .txt import parse_txt
try:
    from .md import parse_md
except Exception:
    parse_md = None
from .auto import parse_auto

__all__ = ["parse_txt", "parse_md", "parse_auto"]
