"""
Emoji Cloner feature for Discord Server Cloner.
Downloads all emojis from a Discord server.
"""

import re
from pathlib import Path
from typing import Dict, Set

from ..api.discord_client import DiscordClient
from ..core.console import Console
from ..core.exceptions import DiscordAPIError


class EmojiCloner:
    """Download all emojis from a Discord server."""
    
    def __init__(self, client: DiscordClient) -> None:
        """Initialize the emoji cloner."""
        self.client = client
        self.console = Console
    
    def _validate_guild_id(self, guild_id: str) -> bool:
        """Validate that a string is a valid Discord snowflake ID."""
        if not guild_id:
            return False
        return bool(re.match(r'^\d{17,20}$', guild_id))
    
    def _get_unique_filename(self, name: str, ext: str, existing: Set[str]) -> str:
        """Get a unique filename, adding number suffix if needed."""
        base_name = name
        counter = 1
        filename = f"{base_name}.{ext}"
        
        while filename.lower() in existing:
            filename = f"{base_name}_{counter}.{ext}"
            counter += 1
        
        existing.add(filename.lower())
        return filename
    
    async def clone(self, guild_id: str, output_dir: Path = None) -> int:
        """
        Download all emojis from a guild.
        
        Args:
            guild_id: The guild ID to download emojis from
            output_dir: Optional output directory
            
        Returns:
            Number of emojis downloaded
        """
        # Validate input
        if not self._validate_guild_id(guild_id):
            self.console.error(f"Invalid guild ID: {guild_id}")
            return 0
        
        downloaded = 0
        existing_files: Set[str] = set()
        
        try:
            # Get guild info for folder naming
            guild = await self.client.get_guild(guild_id)
            guild_name = guild['name'].replace('/', '_').replace('\\', '_').replace(':', '_')
            
            # Get emojis
            emojis = await self.client.get_emojis(guild_id)
            
            if not emojis:
                self.console.warning("No emojis found in this server")
                return 0
            
            # Create output directory
            if output_dir is None:
                output_dir = Path(f"emojis_{guild_name}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            total = len(emojis)
            self.console.info(f"Found {total} emojis. Downloading...")
            
            for i, emoji in enumerate(emojis, 1):
                try:
                    emoji_id = emoji['id']
                    emoji_name = emoji['name'].replace('/', '_').replace('\\', '_')
                    is_animated = emoji.get('animated', False)
                    
                    # Determine extension and URL
                    ext = 'gif' if is_animated else 'webp'
                    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size=128"
                    
                    # Get unique filename
                    filename = self._get_unique_filename(emoji_name, ext, existing_files)
                    
                    # Download
                    data = await self.client.download_asset(url)
                    
                    # Save file
                    file_path = output_dir / filename
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    
                    self.console.success(f"[{i}/{total}] Downloaded: {emoji_name}")
                    downloaded += 1
                    
                except DiscordAPIError as e:
                    self.console.error(f"[{i}/{total}] Failed: {emoji.get('name', 'unknown')}")
            
            self.console.success(f"Downloaded {downloaded}/{total} emojis to {output_dir}")
            
        except DiscordAPIError as e:
            self.console.error(f"Failed to fetch emojis: {e}")
        
        return downloaded


async def run_emoji_cloner(client: DiscordClient) -> None:
    """Interactive emoji cloner function."""
    Console.clear()
    Console.logo()
    
    guild_id = Console.prompt("Guild ID")
    
    Console.clear()
    Console.logo()
    
    cloner = EmojiCloner(client)
    await cloner.clone(guild_id)
    
    Console.wait_for_enter()
