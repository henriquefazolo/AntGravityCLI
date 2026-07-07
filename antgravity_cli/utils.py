import os
import sys

def get_base_path() -> str:
    """Returns the base path of the project, compatible with PyInstaller standalone executable format."""
    if getattr(sys, 'frozen', False):
        # PyInstaller temp folder where execution assets are unpacked
        return sys._MEIPASS
    # Normal execution, resolve folder relative to utils.py location
    return os.path.dirname(os.path.abspath(__file__))
