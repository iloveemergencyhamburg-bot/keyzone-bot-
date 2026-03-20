import discord
from discord.ext import commands
import datetime
import os
import asyncio # Required for the ban-check delay

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True
intents.moderation = True # Required to read Audit Logs for ban reasons

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# CHANNEL IDS
# ======================
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

invites = {}
join_log = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Cache invites so the tracker works
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            invites[guild.id] = []

# ======================
# MEMBER JOIN (Welcome + Invite Tracking + Anti-Raid)
# ======================
@bot.event
async def on_member_join(member):
    guild = member.guild
    now = datetime.datetime.utcnow().timestamp()

    # 1. Anti-Raid Logic
    if guild.id not in join_log:
        join_log[guild.id] = []
    join_log[guild.id].append(now)
    join_log[guild.id] = [t for t in join_log[guild.id] if now - t < 10]

    if len(join_log[guild.id]) >= 5:
        alert_channel = guild.system_channel
        if alert_channel:
            await alert_channel.send("⚠️ **Anti-Raid Alert:** Too many users joining quickly!")

    # 2. Invite Tracking Logic
    welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)
    invite_channel = guild.get_channel(INVITE_CHANNEL_ID)
    
    used_invite = None
    try:
        new_invites = await guild.invites()
        for old_inv in invites.get(guild.id, []):
            for new_inv in new_invites:
                if old_inv.code == new_inv.code and old_inv.uses < new_inv.uses:
                    used_invite = new_inv
                    break
        invites[guild.id] = new_invites
    except:
        pass

    inviter = used_invite.inviter if used_invite else None

    # 3. Send Welcome Embed
    if welcome_channel:
        embed = discord.Embed(
            title="👋 Welcome to KeyZone",
            description=f"Hello {member.mention}, welcome to our server!",
            color=0x2F3136,
            timestamp=datetime.datetime.utcnow()
        )
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="📊 Member Count", value=str(len(guild.members)), inline=True)
        embed.add_field(name="📩 Invited By", value=inviter.mention if inviter else "Unknown", inline=True)
        embed.set_footer(text="KeyZone System")
        await welcome_channel.send(embed=embed)

# ======================
# MEMBER LEAVE (Filtered to prevent double-posting on Ban)
# ======================
@bot.event
async def on_member_remove(member):
    # Wait 1 second to see if this "remove" is actually a "ban"
    await asyncio.sleep(1)
    
    try:
        # Check if the user is in the server ban list
        await member.guild.fetch_ban(member)
        return # They are banned, so we stop here (the ban function handles it)
    except discord.NotFound:
        # User was NOT banned (they just left or were kicked)
        leave_channel = member.guild.get_channel(LEAVE_CHANNEL_ID)
        if leave_channel:
            embed = discord.Embed(
                title="👋 Member Left",
                description=f"{member.mention} has left the server.\n**Hope to see you again soon!**",
                color=0xED4245,
                timestamp=datetime.datetime.utcnow()
            )
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text="KeyZone System")
            await leave_channel.send(embed=embed)

# ======================
# BAN LOG (With Reason & Moderator)
# ======================
@bot.event
async def on_member_ban(guild, user):
    channel = guild.get_channel(BANNED_CHANNEL_ID)
    if channel:
        reason = "No reason provided."
        moderator = "Unknown Moderator"
        
        # Search Audit Logs for the specific ban details
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
                if entry.target.id == user.id:
                    reason = entry.reason if entry.reason else "No reason provided."
                    moderator = entry.user.mention
                    break
        except:
            pass

        embed = discord.Embed(
            title="⛔ Member Banned",
            description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Banned By:** {moderator}",
            color=0xED4245,
            timestamp=datetime.datetime.utcnow()
        )
        avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text="KeyZone System")
        await channel.send(embed=embed)

# ======================
# COMMANDS
# ======================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    for channel in ctx.guild.text_channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        except:
            continue
    await ctx.send("🔒 Server locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    for channel in ctx.guild.text_channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        except:
            continue
    await ctx.send("🔓 Server unlocked.")

# ======================
# RUN BOT
# ======================
bot.run(os.getenv("DISCORD_TOKEN"))
