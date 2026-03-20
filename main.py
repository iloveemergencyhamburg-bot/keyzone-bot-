import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps
import datetime
import os
import asyncio
import io
import requests

# Enable all required intents
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
join_log = {}

@bot.event
async def on_ready():
    print(f"KeyZone Guard is online as {bot.user}")
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            invites[guild.id] = []

# ======================
# MEMBER JOIN (Welcome Image + Invite Tracker)
# ======================
@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_chan = guild.get_channel(WELCOME_CHANNEL_ID)
    invite_chan = guild.get_channel(INVITE_CHANNEL_ID)
    
    # 1. ANTI-RAID
    now = datetime.datetime.utcnow().timestamp()
    if guild.id not in join_log: join_log[guild.id] = []
    join_log[guild.id].append(now)
    join_log[guild.id] = [t for t in join_log[guild.id] if now - t < 10]
    if len(join_log[guild.id]) >= 5 and guild.system_channel:
        await guild.system_channel.send("⚠️ **Anti-Raid Alert!** Multiple users joined quickly.")

    # 2. INVITE TRACKER LOGIC
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

    # 3. SEND TO INVITE CHANNEL
    if invite_chan:
        msg = f"📩 **{member.name}** joined using invite from **{inviter.mention if inviter else 'Unknown'}**"
        await invite_chan.send(msg)

    # 4. GENERATE WELCOME IMAGE
    try:
        bg = Image.open("welcome_bg.png").convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        try:
            font_name = ImageFont.truetype("font.ttf", 65)
            font_info = ImageFont.truetype("font.ttf", 40)
        except:
            font_name = font_info = ImageFont.load_default()

        # Process Avatar
        url = member.avatar.url if member.avatar else member.default_avatar.url
        avatar_img = Image.open(io.BytesIO(requests.get(url).content)).convert("RGBA")
        avatar_img = avatar_img.resize((260, 260), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (260, 260), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 260, 260), fill=255)
        
        # Paste data over the template
        bg.paste(avatar_img, (652, 280), mask) 
        draw.text((70, 410), f"{member.name}", fill="white", font=font_name)
        draw.text((715, 712), f"{inviter_name}", fill="white", font=font_info)
        draw.text((455, 905), f"Member #{len(guild.members)}", fill="white", font=font_info)

        with io.BytesIO() as out:
            bg.save(out, format="PNG")
            out.seek(0)
            if welcome_chan:
                await welcome_chan.send(f"Welcome {member.mention}!", file=discord.File(out, "welcome.png"))
    except Exception as e:
        print(f"Image Error: {e}")
        if welcome_chan: await welcome_chan.send(f"Welcome {member.mention} to KeyZone!")

# ======================
# MEMBER LEAVE (No Double-Post)
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
            embed = discord.Embed(title="👋 Member Left", description=f"{member.mention} left KeyZone.", color=0xED4245)
            embed.set_thumbnail(url=member.display_avatar.url)
            await chan.send(embed=embed)

# ======================
# BAN LOG
# ======================
@bot.event
async def on_member_ban(guild, user):
    chan = guild.get_channel(BANNED_CHANNEL_ID)
    if chan:
        reason = "No reason provided."
        moderator = "Unknown"
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
            if entry.target.id == user.id:
                reason = entry.reason or reason
                moderator = entry.user.mention
                break
        embed = discord.Embed(title="⛔ Member Banned", color=0xED4245)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Banned By", value=moderator, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await chan.send(embed=embed)

# ======================
# LOCK / UNLOCK
# ======================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel unlocked.")

bot.run(os.getenv("DISCORD_TOKEN"))
