"""
Server Cloner feature for Discord Server Cloner.
Clones channels, roles, webhooks, emojis, stickers, and settings.
"""

import asyncio
import base64
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..api.discord_client import DiscordClient
from ..core.console import Console
from ..core.exceptions import DiscordAPIError


@dataclass
class CloneStats:
    """Track cloning statistics."""
    roles_created: int = 0
    roles_failed: int = 0
    roles_skipped: int = 0
    channels_created: int = 0
    channels_failed: int = 0
    categories_created: int = 0
    categories_failed: int = 0
    deleted_channels: int = 0
    deleted_roles: int = 0
    webhooks_created: int = 0
    webhooks_failed: int = 0
    emojis_created: int = 0
    emojis_failed: int = 0
    emojis_deleted: int = 0
    stickers_created: int = 0
    stickers_failed: int = 0
    stickers_deleted: int = 0
    
    start_time: float = 0
    failed_items: List[Tuple[str, str, str]] = field(default_factory=list)
    
    def add_failure(self, item_type: str, name: str, reason: str = "Unknown"):
        self.failed_items.append((item_type, name, reason[:50]))
    
    def get_elapsed(self) -> str:
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    
    def display_summary(self, console):
        console.info("")
        console.info("=" * 50)
        console.info(f"CLONE SUMMARY (Time: {self.get_elapsed()})")
        console.info("=" * 50)
        
        if self.deleted_channels > 0 or self.deleted_roles > 0:
            console.info(f"Deleted: {self.deleted_channels} channels, {self.deleted_roles} roles")
        
        total_roles = self.roles_created + self.roles_failed
        if total_roles > 0:
            console.success(f"Roles: {self.roles_created}/{total_roles} created")
            if self.roles_skipped > 0:
                console.warning(f"  - {self.roles_skipped} skipped (managed)")
        
        total_cats = self.categories_created + self.categories_failed
        if total_cats > 0:
            console.success(f"Categories: {self.categories_created}/{total_cats} created")
        
        total_channels = self.channels_created + self.channels_failed
        if total_channels > 0:
            console.success(f"Channels: {self.channels_created}/{total_channels} created")
        
        if self.webhooks_created > 0:
            console.success(f"Webhooks: {self.webhooks_created} created")
        
        if self.emojis_created > 0 or self.emojis_deleted > 0:
            console.success(f"Emojis: {self.emojis_created} uploaded" + (f", {self.emojis_deleted} replaced" if self.emojis_deleted else ""))
        
        if self.stickers_created > 0 or self.stickers_deleted > 0:
            console.success(f"Stickers: {self.stickers_created} uploaded" + (f", {self.stickers_deleted} replaced" if self.stickers_deleted else ""))
        
        if self.failed_items:
            console.error(f"Failed: {len(self.failed_items)} items")
        
        console.info("=" * 50)


class ServerCloner:
    """Clone a Discord server's structure."""
    
    CHANNEL_TYPE_TEXT = 0
    CHANNEL_TYPE_VOICE = 2
    CHANNEL_TYPE_CATEGORY = 4
    CHANNEL_TYPE_ANNOUNCEMENT = 5
    CHANNEL_TYPE_STAGE = 13
    CHANNEL_TYPE_FORUM = 15
    
    # Emoji limits by boost level
    EMOJI_LIMITS = {0: 50, 1: 100, 2: 150, 3: 250}
    STICKER_LIMITS = {0: 5, 1: 15, 2: 30, 3: 60}
    
    def __init__(self, client: DiscordClient) -> None:
        self.client = client
        self.console = Console
        
        self.role_map: Dict[str, str] = {}
        self.category_map: Dict[str, str] = {}
        self.channel_map: Dict[str, str] = {}
        
        self.stats = CloneStats()
        self.created_roles: List[Tuple[str, int]] = []
        self._cancelled = False
        
        self.target_has_community = False
        self.source_has_community = False
        self.target_boost_level = 0
    
    def _validate_guild_id(self, guild_id: str) -> bool:
        return bool(guild_id and re.match(r'^\d{17,20}$', guild_id))
    
    def _check_cancelled(self) -> bool:
        if self._cancelled:
            self.console.warning("Operation cancelled")
            return True
        return False
    
    async def clone(self, source_id: str, target_id: str) -> None:
        """Clone a server's structure."""
        self._cancelled = False
        self.stats = CloneStats()
        self.stats.start_time = time.time()
        self.role_map.clear()
        self.category_map.clear()
        self.channel_map.clear()
        self.created_roles.clear()
        
        if not self._validate_guild_id(source_id):
            self.console.error(f"Invalid source guild ID: {source_id}")
            return
        if not self._validate_guild_id(target_id):
            self.console.error(f"Invalid target guild ID: {target_id}")
            return
        if source_id == target_id:
            self.console.error("Source and target cannot be the same!")
            return
        
        self.console.info("Starting server clone... (Press Ctrl+C to cancel)")
        
        try:
            if not await self._sync_community(source_id, target_id):
                return
            if self._check_cancelled(): return
            
            self.console.info("Clearing target server...")
            await self._clear_target_channels(target_id)
            if self._check_cancelled(): return
            await self._clear_target_roles(target_id)
            if self._check_cancelled(): return
            
            await self._copy_server_settings(source_id, target_id)
            if self._check_cancelled(): return
            
            await self._clone_roles(source_id, target_id)
            if self._check_cancelled(): return
            await self._reorder_roles(target_id)
            if self._check_cancelled(): return
            
            await self._clone_channels(source_id, target_id)
            if self._check_cancelled(): return
            
            await self._clone_webhooks(source_id, target_id)
            if self._check_cancelled(): return
            
            await self._clone_emojis(source_id, target_id)
            if self._check_cancelled(): return
            
            await self._clone_stickers(source_id, target_id)
            if self._check_cancelled(): return
            
            await self._set_system_channels(source_id, target_id)
            
            await self._verify_clone(source_id, target_id)
            self.console.success("Server clone completed!")
            
        except KeyboardInterrupt:
            self._cancelled = True
            self.console.warning("Clone cancelled (Ctrl+C)")
        except Exception as e:
            self.console.error(f"Clone failed: {e}")
        finally:
            self.stats.display_summary(self.console)
    
    async def _sync_community(self, source_id: str, target_id: str) -> bool:
        """Check community settings."""
        try:
            source = await self.client.get_guild(source_id)
            target = await self.client.get_guild(target_id)
            
            source_name = source.get('name', source_id)
            target_name = target.get('name', target_id)
            
            self.source_has_community = 'COMMUNITY' in source.get('features', [])
            self.target_has_community = 'COMMUNITY' in target.get('features', [])
            self.target_boost_level = target.get('premium_tier', 0)
            
            self.console.info("")
            self.console.info("=" * 50)
            self.console.info("SERVER STATUS")
            self.console.info("=" * 50)
            
            if self.source_has_community:
                self.console.success(f"Source [{source_name}]: Community ENABLED")
            else:
                self.console.info(f"Source [{source_name}]: Community DISABLED")
            
            if self.target_has_community:
                self.console.success(f"Target [{target_name}]: Community ENABLED")
            else:
                self.console.info(f"Target [{target_name}]: Community DISABLED")
            
            self.console.info(f"Target Boost Level: {self.target_boost_level}")
            self.console.info(f"  Emoji Limit: {self.EMOJI_LIMITS.get(self.target_boost_level, 50)}")
            self.console.info(f"  Sticker Limit: {self.STICKER_LIMITS.get(self.target_boost_level, 5)}")
            self.console.info("=" * 50)
            
            if self.source_has_community and not self.target_has_community:
                self.console.warning("⚠ Community mismatch - Announcement→Text")
            else:
                self.console.success("✓ Ready to clone!")
            
            self.console.info("")
            self.console.prompt("Press ENTER to continue")
            return True
            
        except DiscordAPIError as e:
            self.console.error(f"Failed to check servers: {e}")
            return False
    
    async def _clear_target_channels(self, guild_id: str) -> None:
        try:
            channels = await self.client.get_channels(guild_id)
            total = len(channels)
            for i, ch in enumerate(channels, 1):
                if self._check_cancelled(): return
                try:
                    await self.client.delete_channel(ch['id'])
                    self.stats.deleted_channels += 1
                    self.console.success(f"[{i}/{total}] Deleted: {ch['name'][:30]}")
                    await asyncio.sleep(0.15)
                except DiscordAPIError:
                    pass
        except DiscordAPIError:
            pass
    
    async def _clear_target_roles(self, guild_id: str) -> None:
        try:
            roles = await self.client.get_roles(guild_id)
            deletable = [r for r in roles if r['name'] != '@everyone' and not r.get('managed')]
            total = len(deletable)
            for i, role in enumerate(deletable, 1):
                if self._check_cancelled(): return
                try:
                    await self.client.delete_role(guild_id, role['id'])
                    self.stats.deleted_roles += 1
                    self.console.success(f"[{i}/{total}] Deleted role: {role['name'][:25]}")
                    await asyncio.sleep(0.15)
                except DiscordAPIError:
                    pass
        except DiscordAPIError:
            pass
    
    async def _copy_server_settings(self, source_id: str, target_id: str) -> None:
        try:
            source = await self.client.get_guild(source_id)
            
            data = {
                "name": source['name'],
                "verification_level": source.get('verification_level', 0),
                "default_message_notifications": source.get('default_message_notifications', 0),
                "explicit_content_filter": source.get('explicit_content_filter', 0),
                "afk_timeout": source.get('afk_timeout', 300),
            }
            
            icon = await self.client.get_guild_icon(source)
            if icon:
                data["icon"] = icon
                self.console.success("Icon copied")
            
            if source.get('banner'):
                try:
                    url = f"https://cdn.discordapp.com/banners/{source_id}/{source['banner']}.png?size=512"
                    banner_bytes = await self.client.download_asset(url)
                    data["banner"] = f"data:image/png;base64,{base64.b64encode(banner_bytes).decode()}"
                    self.console.success("Banner copied")
                except:
                    pass
            
            await self.client.update_guild(target_id, **data)
            self.console.success(f"Server settings copied: {source['name']}")
            
            levels = ["None", "Low", "Medium", "High", "Highest"]
            self.console.info(f"  Verification: {levels[data['verification_level']]}")
            
        except DiscordAPIError as e:
            self.console.warning(f"Settings error: {e}")
    
    async def _clone_roles(self, source_id: str, target_id: str) -> None:
        try:
            source_roles = await self.client.get_roles(source_id)
            target_roles = await self.client.get_roles(target_id)
            
            src_everyone = next((r for r in source_roles if r['name'] == '@everyone'), None)
            tgt_everyone = next((r for r in target_roles if r['name'] == '@everyone'), None)
            if src_everyone and tgt_everyone:
                self.role_map[src_everyone['id']] = tgt_everyone['id']
            
            roles = [r for r in source_roles if r['name'] != '@everyone' and not r.get('managed')]
            roles.sort(key=lambda x: x['position'])
            
            managed_count = len([r for r in source_roles if r.get('managed')])
            self.stats.roles_skipped = managed_count
            if managed_count:
                self.console.warning(f"Skipping {managed_count} managed roles")
            
            total = len(roles)
            for i, role in enumerate(roles, 1):
                if self._check_cancelled(): return
                try:
                    new_role = await self.client.create_role(
                        target_id, name=role['name'], permissions=role['permissions'],
                        color=role['color'], hoist=role['hoist'], mentionable=role['mentionable']
                    )
                    self.role_map[role['id']] = new_role['id']
                    self.created_roles.append((new_role['id'], role['position']))
                    self.stats.roles_created += 1
                    self.console.success(f"[{i}/{total}] Role: {role['name'][:25]}")
                    await asyncio.sleep(0.35)
                except DiscordAPIError as e:
                    self.stats.roles_failed += 1
                    self.stats.add_failure("role", role['name'], str(e))
        except DiscordAPIError as e:
            self.console.error(f"Roles error: {e}")
    
    async def _reorder_roles(self, target_id: str) -> None:
        if not self.created_roles:
            return
        try:
            self.created_roles.sort(key=lambda x: x[1], reverse=True)
            positions = [{"id": rid, "position": len(self.created_roles) - i} 
                        for i, (rid, _) in enumerate(self.created_roles)]
            await self.client.update_role_positions(target_id, positions)
            self.console.success("Role hierarchy set")
        except DiscordAPIError:
            pass
    
    def _map_overwrites(self, overwrites: List[Dict]) -> List[Dict]:
        mapped = []
        for ow in overwrites:
            if ow.get('type') == 0 and ow['id'] in self.role_map:
                new_ow = ow.copy()
                new_ow['id'] = self.role_map[ow['id']]
                mapped.append(new_ow)
        return mapped
    
    async def _clone_channels(self, source_id: str, target_id: str) -> None:
        try:
            channels = await self.client.get_channels(source_id)
            
            categories = sorted([c for c in channels if c['type'] == 4], key=lambda x: x['position'])
            total_cats = len(categories)
            if total_cats:
                self.console.info(f"Creating {total_cats} categories...")
            
            for i, cat in enumerate(categories, 1):
                if self._check_cancelled(): return
                try:
                    created = await self.client.create_channel(
                        target_id, name=cat['name'], type=4, position=i-1,
                        permission_overwrites=self._map_overwrites(cat.get('permission_overwrites', []))
                    )
                    self.category_map[cat['id']] = created['id']
                    self.stats.categories_created += 1
                    self.console.success(f"[{i}/{total_cats}] Category: {cat['name'][:25]}")
                    await asyncio.sleep(0.2)
                except DiscordAPIError as e:
                    self.stats.categories_failed += 1
                    self.stats.add_failure("category", cat['name'], str(e))
            
            other = sorted([c for c in channels if c['type'] not in [4, 10, 11, 12]], 
                          key=lambda x: (x.get('parent_id') or '', x['position']))
            total = len(other)
            if total:
                self.console.info(f"Creating {total} channels...")
            
            for i, ch in enumerate(other, 1):
                if self._check_cancelled(): return
                await self._create_channel(target_id, ch, i, total)
        except DiscordAPIError as e:
            self.console.error(f"Channels error: {e}")
    
    async def _create_channel(self, target_id: str, ch: Dict, idx: int, total: int) -> None:
        try:
            channel_type = ch['type']
            if channel_type == 5 and not self.target_has_community:
                channel_type = 0
            
            data = {'name': ch['name'], 'type': channel_type,
                    'permission_overwrites': self._map_overwrites(ch.get('permission_overwrites', []))}
            
            if ch.get('parent_id') and ch['parent_id'] in self.category_map:
                data['parent_id'] = self.category_map[ch['parent_id']]
            
            if channel_type in [0, 5]:
                data['topic'] = ch.get('topic') or ''
                data['nsfw'] = ch.get('nsfw', False)
            elif channel_type == 2:
                data['bitrate'] = ch.get('bitrate', 64000)
                data['user_limit'] = ch.get('user_limit', 0)
            
            created = await self.client.create_channel(target_id, **data)
            self.channel_map[ch['id']] = created['id']
            self.stats.channels_created += 1
            self.console.success(f"[{idx}/{total}] Channel: {ch['name'][:25]}")
            await asyncio.sleep(0.2)
        except DiscordAPIError as e:
            self.stats.channels_failed += 1
            self.stats.add_failure("channel", ch['name'], str(e))
    
    async def _clone_webhooks(self, source_id: str, target_id: str) -> None:
        try:
            webhooks = await self.client.get_webhooks(source_id)
            if not webhooks:
                return
            
            self.console.info(f"Cloning {len(webhooks)} webhooks...")
            for i, wh in enumerate(webhooks, 1):
                if self._check_cancelled(): return
                if wh['channel_id'] not in self.channel_map:
                    continue
                try:
                    avatar = None
                    if wh.get('avatar'):
                        try:
                            url = f"https://cdn.discordapp.com/avatars/{wh['id']}/{wh['avatar']}.png"
                            avatar_bytes = await self.client.download_asset(url)
                            avatar = f"data:image/png;base64,{base64.b64encode(avatar_bytes).decode()}"
                        except:
                            pass
                    
                    await self.client.create_webhook(self.channel_map[wh['channel_id']], wh['name'], avatar)
                    self.stats.webhooks_created += 1
                    self.console.success(f"[{i}/{len(webhooks)}] Webhook: {wh['name'][:25]}")
                    await asyncio.sleep(0.3)
                except DiscordAPIError as e:
                    self.stats.webhooks_failed += 1
        except DiscordAPIError:
            pass
    
    async def _clone_emojis(self, source_id: str, target_id: str) -> None:
        """Clone emojis - keep existing, ask if over capacity."""
        try:
            source_emojis = await self.client.get_emojis(source_id)
            if not source_emojis:
                return
            
            target_emojis = await self.client.get_emojis(target_id)
            target_emoji_names = {e['name']: e['id'] for e in target_emojis}
            
            limit = self.EMOJI_LIMITS.get(self.target_boost_level, 50)
            current_count = len(target_emojis)
            available = limit - current_count
            
            # Filter out duplicates (already exist on target)
            to_upload = []
            for emoji in source_emojis:
                name = re.sub(r'[^a-zA-Z0-9_]', '', emoji['name'])[:32]
                if len(name) < 2:
                    name = f"emoji_{len(to_upload)}"
                
                # Skip if already exists with same name
                if name not in target_emoji_names:
                    to_upload.append((emoji, name))
            
            if not to_upload:
                self.console.info(f"Emojis: All {len(source_emojis)} already exist on target")
                return
            
            self.console.info(f"Emojis: {len(to_upload)} new, {current_count}/{limit} on target")
            
            # Check if we need to delete to make room
            need_space = len(to_upload) - available
            if need_space > 0:
                self.console.warning(f"Need {need_space} more slots (limit: {limit})")
                response = self.console.prompt(f"Delete {need_space} existing emojis? (y/n)")
                
                if response.lower() == 'y':
                    # Delete oldest emojis (first in list)
                    deleted = 0
                    for emoji in target_emojis:
                        if deleted >= need_space:
                            break
                        try:
                            await self.client.delete_emoji(target_id, emoji['id'])
                            self.stats.emojis_deleted += 1
                            available += 1
                            deleted += 1
                            self.console.info(f"Deleted: {emoji['name']}")
                            await asyncio.sleep(0.2)
                        except:
                            pass
                else:
                    self.console.info(f"Uploading only {available} emojis")
            
            # Upload within capacity
            uploaded = 0
            for i, (emoji, name) in enumerate(to_upload, 1):
                if self._check_cancelled(): return
                if uploaded >= available:
                    self.console.warning(f"Emoji limit ({limit}) - skipping rest")
                    break
                
                try:
                    ext = 'gif' if emoji.get('animated') else 'png'
                    url = f"https://cdn.discordapp.com/emojis/{emoji['id']}.{ext}"
                    emoji_bytes = await self.client.download_asset(url)
                    image_data = f"data:image/{ext};base64,{base64.b64encode(emoji_bytes).decode()}"
                    
                    await self.client.create_emoji(target_id, name, image_data)
                    self.stats.emojis_created += 1
                    uploaded += 1
                    self.console.success(f"[{uploaded}/{min(len(to_upload), available)}] Emoji: {name[:20]}")
                    await asyncio.sleep(0.5)
                except DiscordAPIError as e:
                    self.stats.emojis_failed += 1
                    if "Maximum" in str(e):
                        self.console.warning("Emoji limit reached")
                        break
        except DiscordAPIError:
            self.console.warning("Could not clone emojis")
    
    async def _clone_stickers(self, source_id: str, target_id: str) -> None:
        """Clone stickers - keep existing, ask if over capacity."""
        try:
            source_stickers = await self.client.get_stickers(source_id)
            if not source_stickers:
                return
            
            target_stickers = await self.client.get_stickers(target_id)
            target_sticker_names = {s['name']: s['id'] for s in target_stickers}
            
            limit = self.STICKER_LIMITS.get(self.target_boost_level, 5)
            current_count = len(target_stickers)
            available = limit - current_count
            
            # Filter: skip duplicates and Lottie
            to_upload = []
            for sticker in source_stickers:
                if sticker.get('format_type') == 3:  # Skip Lottie
                    continue
                if sticker['name'] not in target_sticker_names:
                    to_upload.append(sticker)
            
            if not to_upload:
                self.console.info(f"Stickers: All already exist on target")
                return
            
            self.console.info(f"Stickers: {len(to_upload)} new, {current_count}/{limit} on target")
            
            # Check if we need to delete to make room
            need_space = len(to_upload) - available
            if need_space > 0:
                self.console.warning(f"Need {need_space} more slots (limit: {limit})")
                response = self.console.prompt(f"Delete {need_space} existing stickers? (y/n)")
                
                if response.lower() == 'y':
                    deleted = 0
                    for sticker in target_stickers:
                        if deleted >= need_space:
                            break
                        try:
                            await self.client.delete_sticker(target_id, sticker['id'])
                            self.stats.stickers_deleted += 1
                            available += 1
                            deleted += 1
                            self.console.info(f"Deleted: {sticker['name']}")
                            await asyncio.sleep(0.2)
                        except:
                            pass
                else:
                    self.console.info(f"Uploading only {available} stickers")
            
            # Upload
            uploaded = 0
            for i, sticker in enumerate(to_upload, 1):
                if self._check_cancelled(): return
                if uploaded >= available:
                    self.console.warning(f"Sticker limit ({limit}) - skipping rest")
                    break
                
                try:
                    fmt = sticker.get('format_type', 1)
                    ext = 'gif' if fmt == 2 else 'png'
                    
                    url = f"https://cdn.discordapp.com/stickers/{sticker['id']}.{ext}"
                    sticker_bytes = await self.client.download_asset(url)
                    
                    await self.client.create_sticker(
                        target_id, sticker['name'],
                        sticker.get('description', ''),
                        sticker.get('tags', '😀'),
                        sticker_bytes, ext
                    )
                    self.stats.stickers_created += 1
                    uploaded += 1
                    self.console.success(f"[{uploaded}/{min(len(to_upload), available)}] Sticker: {sticker['name'][:20]}")
                    await asyncio.sleep(0.5)
                except DiscordAPIError as e:
                    self.stats.stickers_failed += 1
                    if "Maximum" in str(e):
                        self.console.warning("Sticker limit reached")
                        break
        except DiscordAPIError:
            self.console.warning("Could not clone stickers")
    
    async def _set_system_channels(self, source_id: str, target_id: str) -> None:
        try:
            source = await self.client.get_guild(source_id)
            data = {}
            
            if source.get('system_channel_id') and source['system_channel_id'] in self.channel_map:
                data['system_channel_id'] = self.channel_map[source['system_channel_id']]
            
            if source.get('afk_channel_id') and source['afk_channel_id'] in self.channel_map:
                data['afk_channel_id'] = self.channel_map[source['afk_channel_id']]
            
            if data:
                await self.client.update_guild(target_id, **data)
                self.console.success("System channels set")
        except DiscordAPIError:
            pass
    
    async def _verify_clone(self, source_id: str, target_id: str) -> None:
        self.console.info("")
        self.console.info("Verifying...")
        try:
            src_ch = await self.client.get_channels(source_id)
            tgt_ch = await self.client.get_channels(target_id)
            src_roles = await self.client.get_roles(source_id)
            tgt_roles = await self.client.get_roles(target_id)
            
            src_cats = len([c for c in src_ch if c['type'] == 4])
            tgt_cats = len([c for c in tgt_ch if c['type'] == 4])
            self.console.success(f"Categories: {tgt_cats}/{src_cats}")
            
            src_chans = len([c for c in src_ch if c['type'] != 4])
            tgt_chans = len([c for c in tgt_ch if c['type'] != 4])
            self.console.success(f"Channels: {tgt_chans}/{src_chans}")
            
            src_r = len([r for r in src_roles if r['name'] != '@everyone' and not r.get('managed')])
            tgt_r = len([r for r in tgt_roles if r['name'] != '@everyone' and not r.get('managed')])
            self.console.success(f"Roles: {tgt_r}/{src_r}")
        except:
            pass


async def run_server_cloner(client: DiscordClient) -> None:
    """Interactive server cloner."""
    Console.clear()
    Console.logo()
    
    source_id = Console.prompt("Source Guild ID")
    target_id = Console.prompt("Target Guild ID")
    
    Console.clear()
    Console.logo()
    
    cloner = ServerCloner(client)
    
    try:
        await cloner.clone(source_id, target_id)
    except KeyboardInterrupt:
        Console.warning("Cancelled")
    
    Console.wait_for_enter()
