"""
Console utilities for Discord Server Cloner.
Provides colorful output and UI elements.
"""

import os
from datetime import datetime
from pystyle import Colors, Colorate


class ConsoleColors:
    """Color constants for console output."""
    
    BLUE = Colors.dark_blue
    RED = Colors.red
    GREEN = Colors.green
    YELLOW = Colors.yellow
    WHITE = Colors.white
    CYAN = Colors.cyan
    
    # Shorthand aliases
    b = Colors.dark_blue
    r = Colors.red
    g = Colors.green
    y = Colors.yellow
    w = Colors.white


class Console:
    """Console utilities for the application."""
    
    # Color shortcuts for easy access
    b = ConsoleColors.b
    r = ConsoleColors.r
    g = ConsoleColors.g
    y = ConsoleColors.y
    w = ConsoleColors.w
    
    LOGO = r"""
 __  __           ______          _         _                                      
|  \/  |         |  ____|        (_)       | |                                     
| \  / |  _   _  | |__    __  __  _   ___  | |_    ___   _ __     ___    ___   ___ 
| |\/| | | | | | |  __|   \ \/ / | | / __| | __|  / _ \ | '_ \   / __|  / _ \ / __|
| |  | | | |_| | | |____   >  <  | | \__ \ | |_  |  __/ | | | | | (__  |  __/ \__ \  
|_|  |_|  \__, | |______| /_/\_\ |_| |___/  \__|  \___| |_| |_|  \___|  \___| |___/   

                              MADE BY @myexistences
                      Github : https://github.com/myexistences
           """
    
    @staticmethod
    def clear() -> None:
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def current_time() -> str:
        """Get the current time formatted as HH:MM:SS."""
        return datetime.now().strftime("%H:%M:%S")
    
    @classmethod
    def logo(cls) -> None:
        """Display the application logo."""
        colored_logo = Colorate.Horizontal(Colors.blue_to_purple, cls.LOGO)
        print(colored_logo)
        
        # Attribution footer
        print(f"{Colors.dark_blue}{'='*80}{Colors.white}")
        print(f"{Colors.cyan}>> Original Author: @myexistences{Colors.white}")
        print(f"{Colors.cyan}>> GitHub: https://github.com/myexistences{Colors.white}")
        print(f"{Colors.dark_blue}{'='*80}{Colors.white}\n")
    
    @classmethod
    def success(cls, message: str) -> None:
        """Print a success message."""
        t = cls.current_time()
        print(f"                {cls.b}[{cls.w}{t}{cls.b}]{cls.w} {cls.g}[+]{cls.w} {message}")
    
    @classmethod
    def error(cls, message: str) -> None:
        """Print an error message."""
        t = cls.current_time()
        print(f"                {cls.b}[{cls.w}{t}{cls.b}]{cls.w} {cls.r}[-]{cls.w} {message}")
    
    @classmethod
    def warning(cls, message: str) -> None:
        """Print a warning message."""
        t = cls.current_time()
        print(f"                {cls.b}[{cls.w}{t}{cls.b}]{cls.w} {cls.y}[x]{cls.w} {message}")
    
    @classmethod
    def info(cls, message: str) -> None:
        """Print an info message."""
        t = cls.current_time()
        print(f"                {cls.b}[{cls.w}{t}{cls.b}]{cls.w} {cls.b}[*]{cls.w} {message}")
    
    @classmethod
    def prompt(cls, text: str) -> str:
        """Display a prompt and return user input."""
        return input(f"                {cls.b}[{cls.w}{text}{cls.b}]{cls.w} >> ")
    
    @classmethod
    def wait_for_enter(cls, message: str = "Press ENTER to go back") -> None:
        """Wait for user to press enter."""
        input(f"                {cls.b}[{cls.w}#{cls.b}]{cls.w} {message}")
