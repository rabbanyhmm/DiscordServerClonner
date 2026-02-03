"""
Discord API Client for Discord Server Cloner.
Provides a centralized async client with rate limiting and error handling.
"""

import asyncio
import base64
from typing import Any, Dict, List, Optional

import aiohttp

from ..core.config import Config, get_config
from ..core.exceptions import (
    DiscordAPIError,
    GuildNotFoundError,
    RateLimitError,
    TokenInvalidError,
)
from ..core.logger import get_logger


class DiscordClient:
    """Async Discord API client with automatic rate limiting."""
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize the Discord client."""
        self.config = config or get_config()
        self.logger = get_logger()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> 'DiscordClient':
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.config.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
            )
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        **kwargs: Any
    ) -> Dict:
        """Make an API request with automatic retry on rate limit."""
        await self._ensure_session()
        
        url = f"{self.config.api_url}/{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                async with self._session.request(method, url, json=json, **kwargs) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = float(response.headers.get("Retry-After", 1))
                        self.logger.warning(f"Rate limited. Retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle other errors
                    if response.status == 401:
                        raise TokenInvalidError()
                    
                    if response.status == 404:
                        raise GuildNotFoundError(endpoint.split('/')[-1])
                    
                    if response.status >= 400:
                        text = await response.text()
                        raise DiscordAPIError(text, response.status)
                    
                    # Return JSON for successful responses
                    if response.status in [200, 201]:
                        return await response.json()
                    
                    return {}
                    
            except aiohttp.ClientError as e:
                self.logger.error(f"Network error: {e}")
                if attempt == self.config.max_retries - 1:
                    raise DiscordAPIError(str(e))
                await asyncio.sleep(self.config.retry_delay)
        
        raise DiscordAPIError("Max retries exceeded")
    
    # ==================== Guild Operations ====================
    
    async def get_guild(self, guild_id: str) -> Dict:
        """Get guild information."""
        return await self._request("GET", f"guilds/{guild_id}")
    
    async def update_guild(self, guild_id: str, **data: Any) -> Dict:
        """Update guild settings."""
        return await self._request("PATCH", f"guilds/{guild_id}", json=data)
    
    # ==================== Channel Operations ====================
    
    async def get_channels(self, guild_id: str) -> List[Dict]:
        """Get all channels in a guild."""
        return await self._request("GET", f"guilds/{guild_id}/channels")
    
    async def create_channel(self, guild_id: str, **data: Any) -> Dict:
        """Create a new channel in a guild."""
        return await self._request("POST", f"guilds/{guild_id}/channels", json=data)
    
    async def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel."""
        try:
            await self._request("DELETE", f"channels/{channel_id}")
            return True
        except DiscordAPIError:
            return False
    
    # ==================== Role Operations ====================
    
    async def get_roles(self, guild_id: str) -> List[Dict]:
        """Get all roles in a guild."""
        return await self._request("GET", f"guilds/{guild_id}/roles")
    
    async def create_role(self, guild_id: str, **data: Any) -> Dict:
        """Create a new role in a guild."""
        return await self._request("POST", f"guilds/{guild_id}/roles", json=data)
    
    async def delete_role(self, guild_id: str, role_id: str) -> bool:
        """Delete a role."""
        try:
            await self._request("DELETE", f"guilds/{guild_id}/roles/{role_id}")
            return True
        except DiscordAPIError as e:
            if e.status_code == 400:  # Can't delete @everyone
                return False
            raise
    
    async def update_role_positions(self, guild_id: str, positions: List[Dict]) -> List[Dict]:
        """
        Update role positions in bulk.
        
        Args:
            guild_id: The guild ID
            positions: List of {"id": role_id, "position": position}
        """
        return await self._request("PATCH", f"guilds/{guild_id}/roles", json=positions)
    
    async def update_channel_positions(self, guild_id: str, positions: List[Dict]) -> None:
        """
        Update channel positions in bulk.
        
        Args:
            guild_id: The guild ID
            positions: List of {"id": channel_id, "position": position, "parent_id": optional}
        """
        await self._request("PATCH", f"guilds/{guild_id}/channels", json=positions)
    
    # ==================== Emoji Operations ====================
    
    async def get_emojis(self, guild_id: str) -> List[Dict]:
        """Get all emojis in a guild."""
        return await self._request("GET", f"guilds/{guild_id}/emojis")
    
    async def download_asset(self, url: str) -> bytes:
        """Download an asset (emoji, sticker, icon)."""
        await self._ensure_session()
        async with self._session.get(url) as response:
            if response.status == 200:
                return await response.read()
            raise DiscordAPIError(f"Failed to download asset: {url}", response.status)
    
    # ==================== Sticker Operations ====================
    
    async def get_stickers(self, guild_id: str) -> List[Dict]:
        """Get all stickers in a guild."""
        return await self._request("GET", f"guilds/{guild_id}/stickers")
    
    # ==================== User Operations ====================
    
    async def get_current_user(self) -> Dict:
        """Get the current user (token validation)."""
        return await self._request("GET", "users/@me")
    
    async def validate_token(self) -> bool:
        """Validate the current token."""
        try:
            await self.get_current_user()
            return True
        except TokenInvalidError:
            return False
    
    # ==================== Utility Methods ====================
    
    async def get_guild_icon(self, guild: Dict) -> Optional[str]:
        """Get guild icon as base64 data URI."""
        if not guild.get('icon'):
            return None
        
        icon_url = f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png"
        try:
            icon_data = await self.download_asset(icon_url)
            icon_base64 = base64.b64encode(icon_data).decode('utf-8')
            return f"data:image/png;base64,{icon_base64}"
        except DiscordAPIError:
            return None
    
    # ==================== Webhook Operations ====================
    
    async def get_webhooks(self, guild_id: str) -> List[Dict]:
        """Get all webhooks in a guild."""
        return await self._request("GET", f"guilds/{guild_id}/webhooks")
    
    async def create_webhook(self, channel_id: str, name: str, avatar: Optional[str] = None) -> Dict:
        """Create a webhook in a channel."""
        data = {"name": name}
        if avatar:
            data["avatar"] = avatar
        return await self._request("POST", f"channels/{channel_id}/webhooks", json=data)
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        try:
            await self._request("DELETE", f"webhooks/{webhook_id}")
            return True
        except DiscordAPIError:
            return False
    
    # ==================== Emoji Upload Operations ====================
    
    async def create_emoji(self, guild_id: str, name: str, image_data: str, roles: List[str] = None) -> Dict:
        """
        Create an emoji in a guild.
        
        Args:
            guild_id: The guild ID
            name: Emoji name (2-32 chars, alphanumeric/underscore)
            image_data: Base64 encoded image data URI
            roles: Optional list of role IDs that can use this emoji
        """
        data = {"name": name, "image": image_data}
        if roles:
            data["roles"] = roles
        return await self._request("POST", f"guilds/{guild_id}/emojis", json=data)
    
    async def delete_emoji(self, guild_id: str, emoji_id: str) -> bool:
        """Delete an emoji from a guild."""
        try:
            await self._request("DELETE", f"guilds/{guild_id}/emojis/{emoji_id}")
            return True
        except DiscordAPIError:
            return False
    
    # ==================== Sticker Upload Operations ====================
    
    async def create_sticker(self, guild_id: str, name: str, description: str, tags: str, file_data: bytes, file_type: str = "png") -> Dict:
        """
        Create a sticker in a guild.
        
        Args:
            guild_id: The guild ID
            name: Sticker name
            description: Sticker description
            tags: Related emoji (e.g. "wave")
            file_data: Raw file bytes
            file_type: File type (png, apng, gif, lottie)
        """
        await self._ensure_session()
        
        # Multipart form data for sticker upload
        data = aiohttp.FormData()
        data.add_field('name', name)
        data.add_field('description', description or '')
        data.add_field('tags', tags or '😀')
        data.add_field('file', file_data, filename=f'sticker.{file_type}', content_type=f'image/{file_type}')
        
        url = f"{self.config.api_url}/guilds/{guild_id}/stickers"
        
        async with self._session.post(url, data=data) as response:
            if response.status == 429:
                retry_after = float(response.headers.get("Retry-After", 1))
                await asyncio.sleep(retry_after)
                return await self.create_sticker(guild_id, name, description, tags, file_data, file_type)
            
            if response.status >= 400:
                text = await response.text()
                raise DiscordAPIError(text, response.status)
            
            return await response.json()
    
    async def delete_sticker(self, guild_id: str, sticker_id: str) -> bool:
        """Delete a sticker from a guild."""
        try:
            await self._request("DELETE", f"guilds/{guild_id}/stickers/{sticker_id}")
            return True
        except DiscordAPIError:
            return False


