#!/usr/bin/env python3
"""
Build script for Discord Server Cloner.
Creates standalone executables for Windows, Linux, and macOS.

Usage:
    python build.py           (builds for current platform)
    python build.py --onefile (single file exe)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True


def get_platform():
    """Get current platform name."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def build(onefile=False):
    """Build the executable."""
    check_pyinstaller()
    
    # Base directory
    base_dir = Path(__file__).parent
    main_file = base_dir / "main.py"
    
    # Output name
    platform = get_platform()
    exe_name = f"DiscordServerCloner_{platform}"
    if platform == "windows":
        exe_name += ".exe"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", exe_name,
        "--clean",
        "--noconfirm",
    ]
    
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # Add hidden imports
    cmd.extend([
        "--hidden-import", "aiohttp",
        "--hidden-import", "colorama",
        "--hidden-import", "pystyle",
    ])
    
    # Add icon if exists (Windows)
    icon_file = base_dir / "icon.ico"
    if icon_file.exists() and platform == "windows":
        cmd.extend(["--icon", str(icon_file)])
    
    # Add main file
    cmd.append(str(main_file))
    
    print(f"Building for {platform}...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run build
    result = subprocess.run(cmd, cwd=str(base_dir))
    
    if result.returncode == 0:
        dist_dir = base_dir / "dist"
        print(f"\n✓ Build successful!")
        print(f"  Output: {dist_dir}")
        print(f"\n  Note: Copy token.txt to the same folder as the exe")
    else:
        print(f"\n✗ Build failed with code {result.returncode}")
    
    return result.returncode


def clean():
    """Clean build artifacts."""
    base_dir = Path(__file__).parent
    
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    for d in dirs_to_remove:
        path = base_dir / d
        if path.exists():
            shutil.rmtree(path)
            print(f"Removed: {d}")
    
    for pattern in files_to_remove:
        for f in base_dir.glob(pattern):
            f.unlink()
            print(f"Removed: {f.name}")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    elif "--onefile" in sys.argv:
        build(onefile=True)
    else:
        build(onefile=False)
