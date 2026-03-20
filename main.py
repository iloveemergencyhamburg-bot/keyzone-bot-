import discord
from discord.ext import commands
import datetime
import os
import asyncio

# 1. SETUP INTENTS (Ensure these are ON in your Developer Portal)
intents = discord.Intents.default()
intents.members = True       
intents.message_content = True 
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONFIGURATION (Channel IDs) ---
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_LOG_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

# Direct link to your clean banner on GitHub
BANNER_URL = "https://raw.githubusercontent.com/iloveemer/keyzone-bot/main/welcome_bg.png"

invites = {}

@bot.event
async def on_ready():
    print(f"✅ KeyZone Guard is ONLINE and watching!")
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            invites[guild.id] = []

@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_chan = guild.get_channel(WELCOME_CHANNEL_ID)
    invite_chan = guild.get_channel(INVITE_LOG_CHANNEL_ID)
    
    # Track Invite Data
    inviter_mention = "Unknown"
    invite_uses = "Unknown"
    try:
        new_invites = await guild.invites()
        for old_inv in invites.get(guild.id, []):
            for new_inv in new_invites:
                if old_inv.code == new_inv.code and old_inv.uses < new_inv.uses:
                    inviter_mention = new_inv.inviter.mention
                    invite_uses = new_inv.uses
                    break
        invites[guild.id] = new_invites
    except: pass

    # --- 1. WELCOME CHANNEL MESSAGE ---
    if welcome_chan:
        w_embed = discord.Embed(
            title="👋 Welcome to KeyZone",
            description=f"Hey {member.mention}, welcome to the server 🎉\n\n"
                        f"🛒 **Here you’ll find:**\n• Cheap game keys\n• Fast delivery\n• Trusted service\n\n"
                        f"📌 **Please take a moment to:**\n• Check the rules\n• Browse the store\n• Open a ticket if you need help\n\n"
                        f"💬 **Enjoy your stay and don’t miss the deals 🔥**",
            color=0xff0000,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        w_embed.set_thumbnail(url=member.display_avatar.url)
        w_embed.set_image(url=BANNER_URL)
        w_embed.set_footer(text=f"Member #{guild.member_count}")
        await welcome_chan.send(content=f"Welcome {member.mention}!", embed=w_embed)

    # --- 2. INVITE TRACKER MESSAGE ---
    if invite_chan:
        i_embed = discord.Embed(
            title="📩 New Member Joined",
            description=f"👤 **User:** {member.mention}\n"
                        f"📨 **Invited by:** {inviter_mention}\n"
                        f"🔗 **Invite uses:** {invite_uses}\n\n"
                        f"🎉 **Welcome to KeyZone**",
            color=0x2ecc71,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        i_embed.set_thumbnail(url=member.display_avatar.url)
        await invite_chan.send(embed=i_embed)

@bot.event
async def on_member_remove(member):
    # Wait to see if it's a ban to prevent double logging
    await asyncio.sleep(1)
    try:
        await member.guild.fetch_ban(member)
        return 
    except discord.NotFound:
        pass 

    chan = member.guild.get_channel(LEAVE_CHANNEL_ID)
    if chan:
        # --- 3. LEAVE CHANNEL MESSAGE ---
        l_embed = discord.Embed(
            title="🚪 User Left",
            description=f"{member.mention} just left KeyZone\n\n💔 **One less member… but we keep growing 🔥**",
            color=0x34495e,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        l_embed.set_thumbnail(url=member.display_avatar.url)
        await chan.send(embed=l_embed)

@bot.event
async def on_member_ban(guild, user):
    chan = guild.get_channel(BANNED_CHANNEL_ID)
    if chan:
        reason = "No reason provided"
        moderator = "Unknown Moderator"
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                reason = entry.reason if entry.reason else reason
                moderator = entry.user.mention
                break

        # --- 4. BANNED CHANNEL MESSAGE ---
        b_embed = discord.Embed(
            title="⛔ User Banned",
            description=f"👤 **User:** {user.mention}\n"
                        f"🛡 **Banned by:** {moderator}\n"
                        f"🚫 **Reason:** {reason}\n\n"
                        f"📌 **Please follow the rules to avoid this**",
            color=0x000000,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        b_embed.set_thumbnail(url=user.display_avatar.url)
        await chan.send(embed=b_embed)

# --- TEST COMMAND (Type !testwelcome in Discord) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def testwelcome(ctx):
    await on_member_join(ctx.author)
    await ctx.send("✅ Sent a test welcome message!")

bot.run(os.getenv("DISCORD_TOKEN"))
