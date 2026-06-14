"""
Discord Server Cloner - Production Level
A professional tool for cloning Discord server structures.

Made by @rabbanyhmm
GitHub: https://github.com/rabbanyhmm
"""

import asyncio
import sys
from typing import NoReturn

from src.api.discord_client import DiscordClient
from src.core.config import get_config
from src.core.console import Console
from src.core.exceptions import DiscordClonerError

# Feature imports
from src.features.server_cloner import run_server_cloner
from src.features.sticker_cloner import run_sticker_cloner
from src.features.emoji_cloner import run_emoji_cloner
from src.features.guild_info import run_guild_info
from src.features.token_checker import run_token_checker


class DiscordServerCloner:
    """Main application class for Discord Server Cloner."""
    
    def __init__(self) -> None:
        """Initialize the application."""
        self.config = get_config()
        self.console = Console
        self.client: DiscordClient = None
    
    async def run(self) -> None:
        """Run the main application loop."""
        try:
            # Validate configuration
            self.config.validate()
            
            # Create Discord client
            async with DiscordClient(self.config) as client:
                self.client = client
                await self._main_menu()
                
        except ValueError as e:
            self.console.error(str(e))
            sys.exit(1)
        except KeyboardInterrupt:
            self.console.info("Goodbye!")
        except DiscordClonerError as e:
            self.console.error(str(e))
            sys.exit(1)
    
    async def _main_menu(self) -> None:
        """Display and handle the main menu."""
        # Color shortcuts
        b = self.console.b
        w = self.console.w
        
        while True:
            self.console.clear()
            self.console.logo()
            
            # Display menu options
            menu = f"""
                {b}[{w}01{b}]{w} Clone Server    {b}[{w}04{b}]{w} Server Info
                {b}[{w}02{b}]{w} Clone Sticker's {b}[{w}05{b}]{w} Token Checker
                {b}[{w}03{b}]{w} Clone Emoji's   {b}[{w}00{b}]{w} Exit"""
            print(menu)
            
            choice = self.console.prompt("@rabbanyhmm")
            
            try:
                if choice == "1":
                    await run_server_cloner(self.client)
                elif choice == "2":
                    await run_sticker_cloner(self.client)
                elif choice == "3":
                    await run_emoji_cloner(self.client)
                elif choice == "4":
                    await run_guild_info(self.client)
                elif choice == "5":
                    await run_token_checker(self.client)
                elif choice == "0" or choice.lower() == "exit":
                    self.console.info("Goodbye!")
                    break
            except KeyboardInterrupt:
                # Ctrl+C returns to home screen instead of exiting
                self.console.warning("Operation cancelled - returning to menu...")
                await asyncio.sleep(0.5)
                continue
            except DiscordClonerError as e:
                self.console.error(str(e))
                self.console.wait_for_enter()
            except Exception as e:
                self.console.error(f"An unexpected error occurred: {e}")
                self.console.wait_for_enter()


def main() -> None:
    """Application entry point."""
    app = DiscordServerCloner()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()