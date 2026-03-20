import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import datetime
import os
import io
import requests

# 1. SETUP INTENTS (Requires switches ON in Dev Portal)
intents = discord.Intents.default()
intents.members = True       
intents.message_content = True 
intents.guilds = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CHANNEL IDS ---
WELCOME_CHANNEL_ID = 1484477611987046511
# Add your other channel IDs here...

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
    
    # Track Inviter logic
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

    try:
        # 2. WELCOME IMAGE (Using the NEW, CLEAN welcome_bg.png)
        bg = Image.open("welcome_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        # Load Font (Ensure font.ttf exists on GitHub)
        try:
            font_name = ImageFont.truetype("font.ttf", 60)
            font_sub = ImageFont.truetype("font.ttf", 40)
        except:
            font_name = font_sub = ImageFont.load_default()

        # Download & Resize Avatar
        avatar_resp = requests.get(member.display_avatar.url)
        avatar_img = Image.open(io.BytesIO(avatar_resp.content)).convert("RGBA").resize((260, 260), Image.Resampling.LANCZOS)
        
        # Create Circle Mask
        mask = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 260, 260), fill=255)
        
        # --- IMPROVED COORDINATES ---
        # The clean template makes it easy to paste the avatar cleanly.
        bg.paste(avatar_img, (652, 280), mask) 
        
        draw.text((70, 410), f"{member.name}", fill="white", font=font_name)
        draw.text((715, 712), f"{inviter_name}", fill="white", font=font_sub)
        draw.text((455, 905), f"Member #{guild.member_count}", fill="white", font=font_sub)

        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            if welcome_chan:
                await welcome_chan.send(
                    content=f"Welcome {member.mention} to **KeyZone**!", 
                    file=discord.File(out, "welcome.png")
                )
                
    except Exception as e:
        print(f"❌ Error generating image: {e}")

bot.run(os.getenv("DISCORD_TOKEN"))
