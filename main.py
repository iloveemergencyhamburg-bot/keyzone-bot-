import discord
from discord.ext import commands
import datetime

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# CHANNEL IDS (YOUR SERVER)
# ======================
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

# ======================
# INVITE TRACKING
# ======================
invites = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    for guild in bot.guilds:
        invites[guild.id] = await guild.invites()

# ======================
# MEMBER JOIN
# ======================
@bot.event
async def on_member_join(member):
    guild = member.guild

    welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
    invite_channel = guild.get_channel(INVITE_CHANNEL_ID)

    # Detect invite used
    new_invites = await guild.invites()
    used_invite = None

    for invite in invites[guild.id]:
        for new in new_invites:
            if invite.code == new.code and invite.uses < new.uses:
                used_invite = invite
                break

    invites[guild.id] = new_invites

    inviter = used_invite.inviter if used_invite else None

    # Premium embed
    embed = discord.Embed(
        title="👋 Welcome to KeyZone",
        description=f"Hello {member.mention}, welcome to our server!",
        color=0x2F3136,
        timestamp=datetime.datetime.utcnow()
    )

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    embed.add_field(name="📊 Member Count", value=str(len(guild.members)), inline=True)

    if inviter:
        embed.add_field(name="📩 Invited By", value=inviter.mention, inline=True)
    else:
        embed.add_field(name="📩 Invited By", value="Unknown", inline=True)

    embed.set_footer(text="KeyZone System")

    if welcome_channel:
        await welcome_channel.send(embed=embed)

    if invite_channel:
        log = discord.Embed(
            title="📩 Invite Tracking",
            description=f"{member.mention} joined the server",
            color=0x2F3136
        )
        if inviter:
            log.add_field(name="Invited By", value=inviter.mention, inline=True)
        else:
            log.add_field(name="Invited By", value="Unknown", inline=True)

        await invite_channel.send(embed=log)

# ======================
# MEMBER LEAVE
# ======================
@bot.event
async def on_member_remove(member):
    guild = member.guild
    leave_channel = guild.get_channel(LEAVE_CHANNEL_ID)

    embed = discord.Embed(
        title="👋 Member Left",
        description=f"{member} has left the server.",
        color=0xED4245,
        timestamp=datetime.datetime.utcnow()
    )

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text="KeyZone System")

    if leave_channel:
        await leave_channel.send(embed=embed)

# ======================
# BAN LOG
# ======================
@bot.event
async def on_member_ban(guild, user):
    channel = guild.get_channel(BANNED_CHANNEL_ID)

    embed = discord.Embed(
        title="⛔ Member Banned",
        description=f"{user} was banned from the server.",
        color=0xED4245,
        timestamp=datetime.datetime.utcnow()
    )

    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.set_footer(text="KeyZone System")

    if channel:
        await channel.send(embed=embed)

# ======================
# ANTI-RAID SYSTEM
# ======================
join_log = {}

@bot.event
async def on_member_join(member):
    guild = member.guild

    now = datetime.datetime.utcnow().timestamp()

    if guild.id not in join_log:
        join_log[guild.id] = []

    join_log[guild.id].append(now)

    # Remove old joins (last 10 seconds)
    join_log[guild.id] = [t for t in join_log[guild.id] if now - t < 10]

    # If too many joins
    if len(join_log[guild.id]) >= 5:
        channel = guild.system_channel

        if channel:
            embed = discord.Embed(
                title="⚠️ Anti-Raid Alert",
                description="Possible raid detected! Too many users joined quickly.",
                color=0xFFA500
            )
            await channel.send(embed=embed)

# ======================
# COMMANDS (LOCK / UNLOCK)
# ======================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    for channel in ctx.guild.channels:
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except:
            pass

    await ctx.send("🔒 Server locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    for channel in ctx.guild.channels:
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except:
            pass

    await ctx.send("🔓 Server unlocked.")

# ======================
# RUN BOT
# ======================
import os
bot.run(os.getenv("DISCORD_TOKEN"))
