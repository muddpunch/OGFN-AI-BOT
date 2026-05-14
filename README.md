# Flow AI Discord Bot

Discord moderation and utility bot built with `discord.py`.

## Features

- Slash command moderation: `/warn`, `/modlogs`
- Auto-moderation for banned words
- Warning persistence in `warns.json`
- Moderator log channel support
- Keyword-triggered embed responses
- Rotating Discord presence status
- Environment-based configuration via `.env`

## Requirements

- Python 3.10+
- Discord bot token
- Discord server with the bot invited
- Enabled Discord Developer Portal intents:
  - Server Members Intent
  - Message Content Intent

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/flowAI.git
cd flowAI
python -m venv .venv
```

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
GUILD_ID=your_discord_server_id
DONATE_CHANNEL_ID=your_donation_channel_id
MOD_LOG_CHANNEL_ID=your_mod_log_channel_id
EXCLUDED_ROLE_IDS=role_id_1,role_id_2
```

## Running

```bash
python bot.py
```

## Commands

```txt
/warn user:<mention|id> reason:<text>
/modlogs user:<mention|id>
```

## Security

```txt
.env is ignored by Git and must never be committed.
Rotate the Discord bot token immediately if it was ever pushed publicly.
Do not share production server IDs, channel IDs, or moderation data unless required.
```
