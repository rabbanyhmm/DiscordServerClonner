"""
Token Checker feature for Discord Server Cloner.
Validates Discord tokens and displays user info.
"""

from typing import Dict, Optional

from ..api.discord_client import DiscordClient
from ..core.console import Console
from ..core.exceptions import TokenInvalidError


class TokenChecker:
    """Check validity of Discord tokens."""
    
    def __init__(self, client: DiscordClient) -> None:
        """Initialize the token checker."""
        self.client = client
        self.console = Console
    
    async def check(self) -> bool:
        """
        Check if the current token is valid.
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            is_valid = await self.client.validate_token()
            
            if is_valid:
                self.console.success("Token is Valid")
                
                # Try to get user info
                try:
                    user = await self.client.get_current_user()
                    username = user.get('username', 'Unknown')
                    discriminator = user.get('discriminator', '0000')
                    user_id = user.get('id', 'Unknown')
                    email = user.get('email', 'Not available')
                    
                    print()
                    self.console.success(f"Username: {username}#{discriminator}")
                    self.console.success(f"User ID: {user_id}")
                    if email != 'Not available':
                        self.console.success(f"Email: {email}")
                except Exception:
                    pass
                
                return True
            else:
                self.console.error("Token is Invalid")
                return False
                
        except TokenInvalidError:
            self.console.error("Token is Invalid")
            return False
        except Exception as e:
            self.console.error(f"Error checking token: {e}")
            return False


async def run_token_checker(client: DiscordClient) -> None:
    """Interactive token checker function."""
    Console.clear()
    Console.logo()
    
    checker = TokenChecker(client)
    await checker.check()
    
    print()
    Console.wait_for_enter()
