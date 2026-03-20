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

# --- LEADERBOARD COMMAND ---
@bot.command()
async def leaderboard(ctx):
    """Displays the top 10 inviters in the server."""
    try:
        current_invites = await ctx.guild.invites()
        # Create a dictionary to sum up uses per inviter
        counts = {}
        for inv in current_invites:
            if inv.inviter:
                counts[inv.inviter.name] = counts.get(inv.inviter.name, 0) + inv.uses
        
        # Sort and take top 10
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        description = ""
        for i, (name, count) in enumerate(sorted_counts, 1):
            description += f"**{i}. {name}** — {count} invites\n"
        
        embed = discord.Embed(
            title="🏆 KeyZone Invite Leaderboard",
            description=description or "No invites recorded yet.",
            color=0xf1c40f,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Keep inviting to reach the top!")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error fetching leaderboard: {e}")

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
        embed = discord.Embed(title="📩 New Member Joined", color=0x2ecc71)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Invited By", value=inviter.mention if inviter else "Unknown", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await invite_chan.send(embed=embed)

    # 2. WELCOME IMAGE (Your Custom PNG)
    try:
        bg = Image.open("welcome_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        try:
            font_name = ImageFont.truetype("font.ttf", 60)
            font_sub = ImageFont.truetype("font.ttf", 40)
        except:
            font_name = font_sub = ImageFont.load_default()

        # Avatar circle
        url = member.display_avatar.url
        avatar_data = io.BytesIO(requests.get(url).content)
        avatar_img = Image.open(avatar_data).convert("RGBA").resize((260, 260), Image.Resampling.LANCZOS)
        mask = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 260, 260), fill=255)
        
        bg.paste(avatar_img, (652, 280), mask) 
        draw.text((70, 410), f"{member.name}", fill="white", font=font_name)
        draw.text((715, 712), f"{inviter_name}", fill="white", font=font_sub)
        draw.text((455, 905), f"Member #{guild.member_count}", fill="white", font=font_sub)

        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            if welcome_chan:
                await welcome_chan.send(content=f"Welcome {member.mention} to **KeyZone**!", file=discord.File(out, "welcome.png"))
                
    except Exception as e:
        print(f"Error: {e}")

@bot.event
async def on_member_remove(member):
    chan = member.guild.get_channel(LEAVE_CHANNEL_ID)
    if chan:
        embed = discord.Embed(title="👋 Member Left", description=f"**{member.name}** left the server.", color=0xe74c3c)
        embed.set_thumbnail(url=member.display_avatar.url)
        await chan.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))
