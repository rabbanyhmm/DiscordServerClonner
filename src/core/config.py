"""
Configuration module for Discord Server Cloner.
Handles token loading and application settings.
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration with environment-based settings."""
    
    # Discord API settings
    api_base_url: str = "https://discord.com/api"
    api_version: str = "v10"
    request_timeout: int = 30
    
    # Rate limiting
    max_retries: int = 5
    retry_delay: float = 1.0
    
    # Token
    token: Optional[str] = field(default=None, repr=False)
    
    # Paths - Handle PyInstaller frozen exe
    base_dir: Path = field(default_factory=lambda: Path(
        getattr(sys, '_MEIPASS', None) or Path(__file__).parent.parent.parent
    ).resolve())
    
    def __post_init__(self) -> None:
        """Load environment variables and token after initialization."""
        load_dotenv()
        self._load_token()
    
    def _load_token(self) -> None:
        """Load Discord token from environment or token.txt file."""
        # Try environment variable first
        self.token = os.getenv("DISCORD_TOKEN")
        
        if not self.token:
            # Fall back to token.txt
            token_file = self.base_dir / "token.txt"
            if token_file.exists():
                with open(token_file, "r", encoding="utf-8") as f:
                    content = f.readline().strip()
                    if content:
                        self.token = content
        
        # If still no token, prompt user
        if not self.token:
            self._prompt_for_token()
    
    def _prompt_for_token(self) -> None:
        """Prompt user to enter their Discord token."""
        print("\n" + "="*60)
        print("  Discord Token Not Found!")
        print("="*60)
        print("\nPlease paste your Discord token below.")
        print("(It will be saved to token.txt for future use)\n")
        
        token = input("Token >> ").strip()
        
        if token:
            # Save to token.txt
            token_file = self.base_dir / "token.txt"
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(token)
            self.token = token
            print("\n✓ Token saved successfully!\n")
    
    @property
    def api_url(self) -> str:
        """Get the full API URL."""
        return f"{self.api_base_url}/{self.api_version}"
    
    @property
    def headers(self) -> dict:
        """Get default headers for API requests."""
        return {
            "Authorization": self.token or "",
            "Content-Type": "application/json",
            "User-Agent": "DiscordServerCloner/2.0 (Python)"
        }
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        if not self.token:
            raise ValueError("Discord token not found. Set DISCORD_TOKEN env var or create token.txt")
        return True


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
