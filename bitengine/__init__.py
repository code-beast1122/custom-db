"""
BitEngine - A lightweight, high-performance key-value database engine.
"""

from .engine import BitEngine
from .cli import run_cli as main_cli
from .server import run_server as main_server
from .client import run_client as main_client

__version__ = "0.1.6"
__all__ = ["BitEngine", "main_cli", "main_server", "main_client"]
