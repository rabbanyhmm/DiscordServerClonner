"""
Custom exceptions for Discord Server Cloner.
Provides specific error types for better error handling.
"""


class DiscordClonerError(Exception):
    """Base exception for Discord Server Cloner."""
    pass


class DiscordAPIError(DiscordClonerError):
    """Raised when Discord API returns an error."""
    
    def __init__(self, message: str, status_code: int = 0, response: str = ""):
        self.status_code = status_code
        self.response = response
        super().__init__(f"Discord API Error ({status_code}): {message}")


class RateLimitError(DiscordAPIError):
    """Raised when rate limited by Discord API."""
    
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(
            f"Rate limited. Retry after {retry_after} seconds",
            status_code=429
        )


class TokenInvalidError(DiscordClonerError):
    """Raised when the Discord token is invalid."""
    
    def __init__(self):
        super().__init__("Invalid Discord token. Please check your token.")


class GuildNotFoundError(DiscordClonerError):
    """Raised when a guild cannot be found."""
    
    def __init__(self, guild_id: str):
        self.guild_id = guild_id
        super().__init__(f"Guild not found: {guild_id}")


class ChannelNotFoundError(DiscordClonerError):
    """Raised when a channel cannot be found."""
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__(f"Channel not found: {channel_id}")


class PermissionError(DiscordClonerError):
    """Raised when lacking permissions for an operation."""
    
    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"Missing permission for: {operation}")
