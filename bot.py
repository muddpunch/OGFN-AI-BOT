import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import datetime
import itertools
from dotenv import load_dotenv

load_dotenv()

# Config
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
DONATE_CHANNEL_ID = os.getenv("DONATE_CHANNEL_ID")
MOD_LOG_CHANNEL_ID = int(os.getenv("MOD_LOG_CHANNEL_ID"))
EXCLUDED_ROLE_IDS = [
    int(rid.strip())
    for rid in os.getenv("EXCLUDED_ROLE_IDS", "").split(",")
    if rid.strip().isdigit()
]
BLUE = 0x3B82F6
RED = 0xEF4444
WARNS_FILE = "warns.json"

# Warns storage
def load_warns() -> dict:
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r") as f:
        return json.load(f)

def save_warns(data: dict):
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_warn(user_id: int, moderator, reason: str) -> int:
    data = load_warns()
    key = str(user_id)
    if key not in data:
        data[key] = []
    case_number = sum(len(v) for v in data.values()) + 1
    data[key].append({
        "case": case_number,
        "moderator_id": moderator.id,
        "moderator_name": str(moderator),
        "reason": reason,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    save_warns(data)
    return case_number

def get_warns(user_id: int) -> list:
    data = load_warns()
    return data.get(str(user_id), [])

# Banned words
BANNED_WORDS = [
    "faggot",
    "nigger",
    "nigga",
    "fag"
    "Faggot"
    "nga"
    "nig"
    "Fag"
    "cocksucker"
    "dickhead"
    "fuck jews"
    "hate niggers"
    "hate ngas"
]

# Responses
# emoji_name: server emoji to prepend to the title (resolved at runtime)
KEYWORDS = {
    "vbucks": {
        "emoji_name": "exclusive",
        "title": "How to get V-Bucks?",
        "description": (
            "In our project you can earn V-Bucks in **3 ways**:\n\n"
            "🔫 **Getting kills**\n"
            "You earn V-Bucks for every enemy you eliminate.\n\n"
            "🏆 **Leveling up in the Battle Pass**\n"
            "Every new Battle Pass level rewards you with V-Bucks.\n\n"
            "📋 **Completing quests**\n"
            "Daily and weekly quests are a great way to stack V-Bucks fast!\n\n"
            "> Combine all three methods to maximize your earnings! 💎"
        ),
    },
    "android": {
        "emoji_name": "droidwave",
        "title": "Android",
        "description": (
            "We currently **do not have** an Android version.\n\n"
            "📱 However, we are planning to introduce Android support in the future!\n\n"
            "> Stay tuned to our announcements so you don't miss the Android launch! 🔔"
        ),
    },
    "ios": {
        "emoji_name": "Apple",
        "title": "iOS",
        "description": (
            "No, the project is **not and will not be** available on iOS.\n\n"
            "🚫 The `.ipa` file is **impossible to obtain** — there is no official "
            "or unofficial way to run the project on an Apple device.\n\n"
            "> Please do not ask for IPA files — such requests will be ignored. ❌"
        ),
    },
    "release": {
        "emoji_name": "notify",
        "title": "Release Date",
        "description": (
            "The planned release of the project is **end of May**! 🎉\n\n"
            "We are working hard to deliver the best experience possible.\n\n"
            "> Get ready — the release is just around the corner! 🚀"
        ),
    },
    "donate": {
        "emoji_name": "devs",
        "title": "Support the Project",
        "description": (
            "Want to support our project? We really appreciate it! 🙏\n\n"
            "💳 Head over to our donation channel:\n"
            f"👉 <#{DONATE_CHANNEL_ID}>\n"
            "or click here: [Donation Channel](https://discord.com/channels/1493829175772184746/1493830589693038823)\n\n"
            "> Every bit of support helps us grow the project! 💙"
        ),
    },
}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Rotating status on discord
STATUSES = itertools.cycle([
    "Flow is listening...",
    "Flow is moderating...",
])

# Emojis
def get_emoji(name: str) -> str:
    """Return the formatted server emoji string, or empty string if not found."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return ""
    e = discord.utils.get(guild.emojis, name=name)
    return str(e) if e else ""

# Helpers 
def blue_embed(title: str, description: str) -> discord.Embed:
    flow = get_emoji("Flow")
    embed = discord.Embed(title=title, description=description, color=BLUE)
    embed.set_footer(text=f"{flow} Flow • AI Assistant".strip())
    return embed

def red_embed(title: str, description: str) -> discord.Embed:
    flow = get_emoji("Flow")
    embed = discord.Embed(title=title, description=description, color=RED)
    embed.set_footer(text=f"{flow} Flow • Moderation".strip())
    return embed

async def resolve_user(guild: discord.Guild, user_input: str) -> discord.Member | None:
    uid = user_input.strip("<@!>")
    try:
        return guild.get_member(int(uid)) or await guild.fetch_member(int(uid))
    except (ValueError, discord.NotFound):
        return None

async def log_warn(guild: discord.Guild, target: discord.Member,
                   moderator, reason: str, case: int):
    log_channel = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_channel:
        return
    flow = get_emoji("Flow")
    embed = discord.Embed(title="⚠️ Member Warned", color=RED)
    embed.add_field(name="Case", value=f"#{case}", inline=True)
    embed.add_field(name="User", value=f"{target.mention} (`{target.id}`)", inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.mention}", inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=f"{flow} Flow • Moderation".strip())
    await log_channel.send(embed=embed)

# Rotating status
@tasks.loop(seconds=10) # Changes every 10 seconds, if you want to change it. Change the number in seconds.
async def rotate_status():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=next(STATUSES),
        )
    )

# Bot ready event
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    rotate_status.start()
    print("✅ Slash commands synced. Flow is listening...")

# /warn
@tree.command(
    name="warn",
    description="Warn a user. Accepts @mention or user ID.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(
    user="@mention or user ID",
    reason="Reason for the warning",
)
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, user: str, reason: str):
    target = await resolve_user(interaction.guild, user)
    if not target:
        await interaction.response.send_message(
            embed=red_embed("❌ User not found", f"Could not find a member matching `{user}`."),
            ephemeral=True,
        )
        return

    case = add_warn(target.id, interaction.user, reason)
    total = len(get_warns(target.id))

    flow = get_emoji("Flow")
    embed = discord.Embed(title="⚠️ Warning Issued", color=RED)
    embed.add_field(name="User", value=f"{target.mention} (`{target.id}`)", inline=True)
    embed.add_field(name="Case", value=f"#{case}", inline=True)
    embed.add_field(name="Total warns", value=str(total), inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.timestamp = datetime.datetime.utcnow()
    embed.set_footer(text=f"Warned by {interaction.user} • {flow} Flow".strip())
    await interaction.response.send_message(embed=embed)

    try:
        dm_embed = red_embed(
            title="⚠️ You have been warned",
            description=(
                f"You received a warning in **{interaction.guild.name}**.\n\n"
                f"**Reason:** {reason}\n"
                f"**Total warnings:** {total}"
            ),
        )
        await target.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    await log_warn(interaction.guild, target, interaction.user, reason, case)

# /modlogs
@tree.command(
    name="modlogs",
    description="View mod logs for a user. Accepts @mention or user ID.",
    guild=discord.Object(id=GUILD_ID),
)
@app_commands.describe(user="@mention or user ID")
@app_commands.checks.has_permissions(manage_messages=True)
async def modlogs(interaction: discord.Interaction, user: str):
    target = await resolve_user(interaction.guild, user)
    if not target:
        await interaction.response.send_message(
            embed=red_embed("❌ User not found", f"Could not find a member matching `{user}`."),
            ephemeral=True,
        )
        return

    warns = get_warns(target.id)
    flow = get_emoji("Flow")

    embed = discord.Embed(
        title=f"📋 Mod Logs — {target.display_name}",
        description=f"**User:** {target.mention} (`{target.id}`)\n**Total warns:** {len(warns)}",
        color=BLUE,
    )
    embed.set_thumbnail(url=target.display_avatar.url)

    if not warns:
        embed.add_field(name="No records", value="This user has no warnings.", inline=False)
    else:
        for w in warns[-10:]:
            ts = w["timestamp"][:10]
            embed.add_field(
                name=f"Case #{w['case']} — {ts}",
                value=f"**Reason:** {w['reason']}\n**Moderator:** {w['moderator_name']}",
                inline=False,
            )
        if len(warns) > 10:
            embed.set_footer(text=f"Showing last 10 of {len(warns)} warnings • {flow} Flow".strip())
        else:
            embed.set_footer(text=f"{flow} Flow • Moderation".strip())

    embed.timestamp = datetime.datetime.utcnow()
    await interaction.response.send_message(embed=embed)

# Errors
@warn.error
@modlogs.error
async def mod_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            embed=red_embed("❌ Missing Permissions", "You need **Manage Messages** to use this command."),
            ephemeral=True,
        )

# Message listener
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    content_lower = message.content.lower()

    # Auto mod
    author_role_ids = {role.id for role in message.author.roles}
    is_excluded = bool(author_role_ids & set(EXCLUDED_ROLE_IDS))

    if not is_excluded:
        for word in BANNED_WORDS:
            if word.lower() in content_lower:
                try:
                    await message.delete()
                except discord.Forbidden:
                    print(f"❌ [AUTOMOD] Missing 'Manage Messages' in #{message.channel.name}")
                    return
                except Exception as e:
                    print(f"❌ [AUTOMOD] Failed to delete message: {e}")
                    return

                embed = red_embed(
                    title="⚠️ Auto-Moderation",
                    description=(
                        f"{message.author.mention}, your message was deleted "
                        f"because it contained a banned word.\n\n"
                        "Please follow the server rules!"
                    ),
                )
                warning = await message.channel.send(embed=embed)
                await warning.delete(delay=8)

                try:
                    case = add_warn(message.author.id, bot.user, "Using banned words (automod)")
                    await log_warn(message.guild, message.author, bot.user, "Using banned words (automod)", case)
                    print(f"✅ [AUTOMOD] Warned {message.author} — Case #{case}")
                except Exception as e:
                    print(f"❌ [AUTOMOD] Warn/log error: {e}")

                return

    # Key words
    for keyword, data in KEYWORDS.items():
        if keyword in content_lower:
            emoji = get_emoji(data["emoji_name"])
            title = f"{emoji} {data['title']}".strip() if emoji else data["title"]
            embed = blue_embed(title=title, description=data["description"])
            await message.channel.send(embed=embed)
            return

    await bot.process_commands(message)

bot.run(TOKEN)