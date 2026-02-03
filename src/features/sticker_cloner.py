"""
Sticker Cloner feature for Discord Server Cloner.
Downloads all stickers from a Discord server.
"""

import re
from pathlib import Path
from typing import Set

from ..api.discord_client import DiscordClient
from ..core.console import Console
from ..core.exceptions import DiscordAPIError


class StickerCloner:
    """Download all stickers from a Discord server."""
    
    # Sticker format types
    FORMAT_PNG = 1
    FORMAT_APNG = 2
    FORMAT_LOTTIE = 3
    FORMAT_GIF = 4
    
    def __init__(self, client: DiscordClient) -> None:
        """Initialize the sticker cloner."""
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
        Download all stickers from a guild.
        
        Args:
            guild_id: The guild ID to download stickers from
            output_dir: Optional output directory
            
        Returns:
            Number of stickers downloaded
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
            
            # Get stickers
            stickers = await self.client.get_stickers(guild_id)
            
            if not stickers:
                self.console.warning("No stickers found in this server")
                return 0
            
            # Create output directory
            if output_dir is None:
                output_dir = Path(f"stickers_{guild_name}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            total = len(stickers)
            self.console.info(f"Found {total} stickers. Downloading...")
            
            for i, sticker in enumerate(stickers, 1):
                try:
                    sticker_id = sticker['id']
                    sticker_name = sticker['name'].replace('/', '_').replace('\\', '_')
                    format_type = sticker.get('format_type', self.FORMAT_PNG)
                    
                    # Determine URL and extension based on format
                    if format_type == self.FORMAT_GIF:
                        url = f"https://media.discordapp.net/stickers/{sticker_id}.gif?size=240"
                        ext = 'gif'
                    elif format_type == self.FORMAT_LOTTIE:
                        url = f"https://discord.com/stickers/{sticker_id}.json"
                        ext = 'json'
                    else:
                        url = f"https://media.discordapp.net/stickers/{sticker_id}.webp?size=240&quality=lossless"
                        ext = 'webp'
                    
                    # Get unique filename
                    filename = self._get_unique_filename(sticker_name, ext, existing_files)
                    
                    # Download
                    data = await self.client.download_asset(url)
                    
                    # Save file
                    file_path = output_dir / filename
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    
                    self.console.success(f"[{i}/{total}] Downloaded: {sticker_name}")
                    downloaded += 1
                    
                except DiscordAPIError as e:
                    self.console.error(f"[{i}/{total}] Failed: {sticker.get('name', 'unknown')}")
            
            self.console.success(f"Downloaded {downloaded}/{total} stickers to {output_dir}")
            
        except DiscordAPIError as e:
            self.console.error(f"Failed to fetch stickers: {e}")
        
        return downloaded


async def run_sticker_cloner(client: DiscordClient) -> None:
    """Interactive sticker cloner function."""
    Console.clear()
    Console.logo()
    
    guild_id = Console.prompt("Guild ID")
    
    Console.clear()
    Console.logo()
    
    cloner = StickerCloner(client)
    await cloner.clone(guild_id)
    
    Console.wait_for_enter()
