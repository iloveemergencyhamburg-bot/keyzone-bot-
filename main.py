import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import os
import asyncio
import io
import requests

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.invites = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# CHANNEL IDS
# ======================
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

invites = {}

@bot.event
async def on_ready():
    print(f"KeyZone Guard is online!")
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            invites[guild.id] = []

@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_chan = guild.get_channel(WELCOME_CHANNEL_ID)
    invite_chan = guild.get_channel(INVITE_CHANNEL_ID)
    
    # 1. Invite Tracking
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
    inviter_name = used_invite.inviter.name if used_invite else "Unknown"

    # 2. Invite Channel Log
    if invite_chan:
        await invite_chan.send(f"📩 **{member.name}** was invited by **{inviter_name}**")

    # 3. Image Generation
    try:
        # Load Background
        bg = Image.open("welcome_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        # Load Font (Tries font.ttf, then Arial, then default)
        try:
            font_name = ImageFont.truetype("font.ttf", 60)
            font_sub = ImageFont.truetype("font.ttf", 40)
        except:
            print("Warning: font.ttf not found. Using default.")
            font_name = font_sub = ImageFont.load_default()

        # Avatar Processing
        url = member.avatar.url if member.avatar else member.default_avatar.url
        response = requests.get(url)
        avatar_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        avatar_img = avatar_img.resize((260, 260), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 260, 260), fill=255)
        
        # Draw on template
        bg.paste(avatar_img, (652, 280), mask) 
        draw.text((70, 410), f"{member.name}", fill="white", font=font_name)
        draw.text((715, 712), f"{inviter_name}", fill="white", font=font_sub)
        draw.text((455, 905), f"Member #{len(guild.members)}", fill="white", font=font_sub)

        # Send Image
        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            if welcome_chan:
                await welcome_chan.send(f"Welcome {member.mention}!", file=discord.File(out, "welcome.png"))
                
    except Exception as e:
        print(f"IMAGE ERROR DETAILS: {e}") # Check Railway logs for this message!
        if welcome_chan:
            await welcome_chan.send(f"Welcome {member.mention} to KeyZone! (Image failed to load)")

# ======================
# LEAVE & BAN LOGS
# ======================
@bot.event
async def on_member_remove(member):
    await asyncio.sleep(1)
    try:
        await member.guild.fetch_ban(member)
        return 
    except discord.NotFound:
        chan = member.guild.get_channel(LEAVE_CHANNEL_ID)
        if chan:
            await chan.send(f"👋 **{member.name}** left the server.")

@bot.event
async def on_member_ban(guild, user):
    chan = guild.get_channel(BANNED_CHANNEL_ID)
    if chan:
        reason = "No reason provided."
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
            if entry.target.id == user.id:
                reason = entry.reason or reason
                break
        await chan.send(f"⛔ **{user.name}** was banned. Reason: {reason}")

bot.run(os.getenv("DISCORD_TOKEN"))
