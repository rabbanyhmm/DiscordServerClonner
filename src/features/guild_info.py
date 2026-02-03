"""
Guild Info feature for Discord Server Cloner.
Displays detailed information about a Discord server.
"""

import re
from typing import Dict, List

from ..api.discord_client import DiscordClient
from ..core.console import Console
from ..core.exceptions import DiscordAPIError


class GuildInfo:
    """Display detailed information about a Discord server."""
    
    # Verification level names
    VERIFICATION_LEVELS = {
        0: "None",
        1: "Low",
        2: "Medium",
        3: "High",
        4: "Very High"
    }
    
    # Premium tier names
    PREMIUM_TIERS = {
        0: "No Boosts",
        1: "Tier 1",
        2: "Tier 2",
        3: "Tier 3"
    }
    
    def __init__(self, client: DiscordClient) -> None:
        """Initialize the guild info viewer."""
        self.client = client
        self.console = Console
    
    def _validate_guild_id(self, guild_id: str) -> bool:
        """Validate that a string is a valid Discord snowflake ID."""
        if not guild_id:
            return False
        return bool(re.match(r'^\d{17,20}$', guild_id))
    
    async def display(self, guild_id: str) -> Dict:
        """
        Display detailed guild information.
        
        Args:
            guild_id: The guild ID to get info for
            
        Returns:
            Guild data dictionary
        """
        # Validate input
        if not self._validate_guild_id(guild_id):
            self.console.error(f"Invalid guild ID: {guild_id}")
            return {}
        
        try:
            guild = await self.client.get_guild(guild_id)
            
            # Extract information
            guild_name = guild.get('name', 'Unknown')
            guild_icon = guild.get('icon')
            owner_id = guild.get('owner_id', 'Unknown')
            verification_level = self.VERIFICATION_LEVELS.get(
                guild.get('verification_level', 0), 'Unknown'
            )
            max_members = guild.get('max_members', 'Unknown')
            premium_tier = self.PREMIUM_TIERS.get(
                guild.get('premium_tier', 0), 'Unknown'
            )
            description = guild.get('description') or 'No Description'
            banner = guild.get('banner')
            features = guild.get('features', [])
            afk_channel_id = guild.get('afk_channel_id') or 'None'
            afk_timeout = guild.get('afk_timeout', 0)
            
            # Build URLs
            icon_url = (
                f"https://cdn.discordapp.com/icons/{guild_id}/{guild_icon}.png"
                if guild_icon else "No Icon"
            )
            banner_url = (
                f"https://cdn.discordapp.com/banners/{guild_id}/{banner}.png?size=512"
                if banner else "No Banner"
            )
            
            # Display information
            print()
            self.console.success("Guild Information:")
            self.console.success(f"Guild Name: {guild_name}")
            self.console.success(f"Guild Icon: {icon_url}")
            self.console.success(f"Owner ID: {owner_id}")
            self.console.success(f"AFK Channel ID: {afk_channel_id}")
            self.console.success(f"AFK Timeout: {afk_timeout} seconds")
            self.console.success(f"Verification Level: {verification_level}")
            self.console.success(f"Max Members: {max_members}")
            self.console.success(f"Premium Tier: {premium_tier}")
            self.console.success(f"Description: {description}")
            self.console.success(f"Banner: {banner_url}")
            
            if features:
                self.console.success(f"Features: {', '.join(features)}")
            else:
                self.console.success("Features: None")
            
            return guild
            
        except DiscordAPIError as e:
            self.console.error(f"Failed to fetch guild info: {e}")
            return {}


async def run_guild_info(client: DiscordClient) -> None:
    """Interactive guild info function."""
    Console.clear()
    Console.logo()
    
    guild_id = Console.prompt("Guild ID")
    
    Console.clear()
    Console.logo()
    
    viewer = GuildInfo(client)
    await viewer.display(guild_id)
    
    Console.wait_for_enter()
