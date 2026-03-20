import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import os
import asyncio
import io
import requests

# SETUP INTENTS
intents = discord.Intents.default()
intents.members = True       
intents.message_content = True 
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CHANNEL IDS ---
WELCOME_CHANNEL_ID = 1484477611987046511
INVITE_CHANNEL_ID = 1484477672993067018
LEAVE_CHANNEL_ID = 1484477721303056405
BANNED_CHANNEL_ID = 1484477767604109312

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
    invite_chan = guild.get_channel(INVITE_CHANNEL_ID)
    
    # Track Inviter
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
    inviter_name = inviter.name if inviter else "Unknown"

    # 1. INVITE LOG (EMBED)
    if invite_chan:
        embed = discord.Embed(title="📩 New Invite Used", color=0x2ecc71, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Member", value=member.mention, inline=True)
        embed.add_field(name="Invited By", value=inviter.mention if inviter else "Unknown", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await invite_chan.send(embed=embed)

    # 2. IMAGE GENERATION (The Graphic)
    try:
        bg = Image.open("welcome_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        try:
            font_name = ImageFont.truetype("font.ttf", 60)
            font_sub = ImageFont.truetype("font.ttf", 40)
        except:
            font_name = font_sub = ImageFont.load_default()

        # Avatar
        url = member.display_avatar.url
        avatar_data = io.BytesIO(requests.get(url).content)
        avatar_img = Image.open(avatar_data).convert("RGBA").resize((260, 260), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 260, 260), fill=255)
        
        # Paste everything
        bg.paste(avatar_img, (652, 280), mask) 
        draw.text((70, 410), f"{member.name}", fill="white", font=font_name)
        draw.text((715, 712), f"{inviter_name}", fill="white", font=font_sub)
        draw.text((455, 905), f"Member #{guild.member_count}", fill="white", font=font_sub)

        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            if welcome_chan:
                # Send the image as an attachment with a mention
                await welcome_chan.send(f"Welcome {member.mention} to **KeyZone**!", file=discord.File(out, "welcome.png"))
                
    except Exception as e:
        print(f"Error: {e}")
        if welcome_chan:
            await welcome_chan.send(f"Welcome {member.mention} to KeyZone!")

@bot.event
async def on_member_remove(member):
    await asyncio.sleep(1)
    try:
        await member.guild.fetch_ban(member)
        return 
    except:
        chan = member.guild.get_channel(LEAVE_CHANNEL_ID)
        if chan:
            embed = discord.Embed(title="👋 Member Left", description=f"**{member.name}** has left the server.", color=0xe74c3c)
            embed.set_thumbnail(url=member.display_avatar.url)
            await chan.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    chan = guild.get_channel(BANNED_CHANNEL_ID)
    if chan:
        reason = "No reason provided."
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
            if entry.target.id == user.id:
                reason = entry.reason or reason
                break
        embed = discord.Embed(title="⛔ Member Banned", color=0x000000)
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await chan.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
