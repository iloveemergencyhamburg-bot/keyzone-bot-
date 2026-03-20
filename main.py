import discord
from discord.ext import commands
import datetime
import os

# SETUP INTENTS
intents = discord.Intents.default()
intents.members = True       
intents.message_content = True 
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CONFIGURATION (Ensure IDs are correct) ---
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_LOG_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

# This link should point to your new clean banner
BANNER_URL = "https://raw.githubusercontent.com/iloveemer/keyzone-bot/main/welcome_bg.png"

invites = {}

@bot.event
async def on_ready():
    print(f"✅ KeyZone Guard is ACTIVE!")
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
    
    # Track Inviter
    used_invite = None
    invite_uses = "Unknown"
    try:
        new_invites = await guild.invites()
        for old_inv in invites.get(guild.id, []):
            for new_inv in new_invites:
                if old_inv.code == new_inv.code and old_inv.uses < new_inv.uses:
                    used_invite = new_inv
                    invite_uses = new_inv.uses
                    break
        invites[guild.id] = new_invites
    except: pass
    
    inviter_text = used_invite.inviter.mention if used_invite else "Unknown"

    # 1. WELCOME EMBED (Using Raw Banner)
    if welcome_chan:
        w_embed = discord.Embed(
            title="👋 Welcome to KeyZone",
            description=f"Hey {member.mention}, welcome to the server 🎉\n\n"
                        f"🛒 **Here you’ll find:**\n"
                        f"• Cheap game keys\n"
                        f"• Fast delivery\n"
                        f"• Trusted service\n\n"
                        f"📌 **Please take a moment to:**\n"
                        f"• Check the rules\n"
                        f"• Browse the store\n"
                        f"• Open a ticket if you need help\n\n"
                        f"💬 **Enjoy your stay and don’t miss the deals 🔥**",
            color=0xff0000,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        w_embed.set_thumbnail(url=member.display_avatar.url)
        w_embed.set_image(url=BANNER_URL) # Sends the banner exactly as it is
        w_embed.set_footer(text=f"Member #{guild.member_count}")
        await welcome_chan.send(content=f"Welcome {member.mention}!", embed=w_embed)

    # 2. INVITE TRACKER EMBED
    if invite_chan:
        i_embed = discord.Embed(
            title="📩 New Member Joined",
            description=f"👤 **User:** {member.mention}\n"
                        f"📨 **Invited by:** {inviter_text}\n"
                        f"🔗 **Invite uses:** {invite_uses}\n\n"
                        f"🎉 **Welcome to KeyZone**",
            color=0x2ecc71,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        i_embed.set_thumbnail(url=member.display_avatar.url)
        await invite_chan.send(embed=i_embed)

@bot.event
async def on_member_remove(member):
    chan = member.guild.get_channel(LEAVE_CHANNEL_ID)
    if chan:
        # 3. LEAVE EMBED
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
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                reason = entry.reason if entry.reason else reason
                moderator = entry.user.mention
                break

        # 4. BAN EMBED
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

bot.run(os.getenv("DISCORD_TOKEN"))
