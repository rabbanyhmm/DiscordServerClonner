# Discord Server Cloner

A powerful Discord server cloning tool that copies channels, roles, emojis, stickers, webhooks, and settings.

## ✨ Features

- **Full Server Clone**: Channels, roles, categories, permissions
- **Emoji & Sticker Upload**: With capacity checking and duplicate handling
- **Webhook Cloning**: Names and avatars
- **Server Settings**: Icon, banner, verification level, AFK settings
- **Standalone Emoji/Sticker Cloning**: Menu options 02 and 03
- **Cross-Platform**: Windows, Linux, macOS

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Windows
pip install -r requirements.txt

# Linux/macOS
pip3 install -r requirements.txt
```

### 2. Add Your Token
Create `token.txt` in the project root with your Discord token:
```
your_discord_token_here
```
Or set environment variable: `DISCORD_TOKEN=your_token`

### 3. Run
```bash
# Windows
python main.py

# Linux/macOS
python3 main.py
```

## 📦 Build Standalone EXE

Want a single executable file? No Python needed to run!

### Quick Build
```bash
# Windows
build.bat --onefile

# Linux/macOS
chmod +x build.sh
./build.sh --onefile
```

### Manual Build
```bash
pip install pyinstaller
python build.py --onefile
```

The executable will be in the `dist/` folder.

**Note**: Copy `token.txt` next to the exe when distributing.

## 📋 Menu Options

| Option | Description |
|--------|-------------|
| 01 | Clone Server (full clone) |
| 02 | Clone Stickers Only |
| 03 | Clone Emojis Only |
| 04 | Server Info |
| 05 | Token Checker |
| 00 | Exit |

## 🔧 What Gets Cloned

- ✅ Server name, icon, banner
- ✅ Verification level
- ✅ Default notification settings
- ✅ AFK channel and timeout
- ✅ System channel (welcome messages)
- ✅ All roles with permissions and hierarchy
- ✅ All categories and channels
- ✅ Channel permissions
- ✅ Webhooks with avatars
- ✅ Emojis (animated included)
- ✅ Stickers (PNG/GIF)

## ⚠️ Notes

- **Community Features**: If source has Community enabled but target doesn't, announcement channels become text channels
- **Managed Roles**: Bot/integration roles are skipped (can't be cloned)
- **Emoji/Sticker Limits**: Respects server boost level limits
- **Rate Limits**: Automatically handled with retries

## 📁 Project Structure

```
DiscordServerCloner/
├── main.py              # Entry point
├── token.txt            # Your Discord token
├── requirements.txt     # Dependencies
├── build.py            # Build script
├── build.bat           # Windows build
├── build.sh            # Linux/Mac build
└── src/
    ├── api/            # Discord API client
    ├── core/           # Config, console, exceptions
    └── features/       # Cloning features
```

## 🖥️ Platform Support

| Platform | Run | Build EXE |
|----------|-----|-----------|
| Windows 10/11 | ✅ | ✅ |
| Linux (Ubuntu/Debian) | ✅ | ✅ |
| macOS (Intel/M1) | ✅ | ✅ |

## 📝 License

MIT License - Use freely, credit appreciated.

---
Made by [@myexistences](https://github.com/myexistences)
