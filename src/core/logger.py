"""
Logger module for Discord Server Cloner.
Provides structured logging with color support.
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pystyle import Colors


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class ColorFormatter(logging.Formatter):
    """Custom formatter with color support."""
    
    COLORS = {
        'DEBUG': Colors.cyan,
        'INFO': Colors.white,
        'SUCCESS': Colors.green,
        'WARNING': Colors.yellow,
        'ERROR': Colors.red,
        'CRITICAL': Colors.red,
    }
    
    SYMBOLS = {
        'DEBUG': '[~]',
        'INFO': '[*]',
        'SUCCESS': '[+]',
        'WARNING': '[!]',
        'ERROR': '[-]',
        'CRITICAL': '[X]',
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, Colors.white)
        symbol = self.SYMBOLS.get(record.levelname, '[*]')
        reset = Colors.white
        blue = Colors.dark_blue
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        return f"                {blue}[{reset}{timestamp}{blue}]{reset} {color}{symbol}{reset} {record.getMessage()}"


class Logger:
    """Application logger with console and file support."""
    
    _instance: Optional['Logger'] = None
    
    def __new__(cls, name: str = "DiscordCloner") -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, name: str = "DiscordCloner") -> None:
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Add SUCCESS level
        logging.addLevelName(25, "SUCCESS")
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColorFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        self._file_handler: Optional[logging.FileHandler] = None
    
    def enable_file_logging(self, log_dir: Path) -> None:
        """Enable logging to file."""
        if self._file_handler:
            return
            
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"discord_cloner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self._file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(self._file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def success(self, message: str) -> None:
        """Log success message."""
        self.logger.log(25, message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)


def get_logger() -> Logger:
    """Get the singleton logger instance."""
    return Logger()
