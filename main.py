import discord
from discord.ext import commands
import os
import json
import requests
import base64
from datetime import datetime

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

GITHUB_REPO = os.getenv('GITHUB_REPO')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def update_github_file(filename, content):
    """Update file on GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha')
    
    data = {
        "message": f"Update {filename} via Discord Bot",
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha
    }
    
    return requests.put(url, headers=headers, json=data)

def get_github_file(filename):
    """Get file from GitHub"""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{filename}"
    response = requests.get(url)
    return json.loads(response.text)

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    print(f'📝 Command prefix: !')

@bot.command()
async def whitelist(ctx, username: str):
    """Add user to whitelist"""
    try:
        data = get_github_file('whitelist.json')
        
        if username in data['users']:
            await ctx.send(f"❌ `{username}` đã có trong whitelist!")
            return
        
        data['users'].append(username)
        update_github_file('whitelist.json', json.dumps(data, indent=2))
        
        embed = discord.Embed(
            title="✅ Whitelist Updated",
            description=f"Đã thêm **{username}** vào whitelist",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="Total Users", value=str(len(data['users'])), inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def unwhitelist(ctx, username: str):
    """Remove user from whitelist"""
    try:
        data = get_github_file('whitelist.json')
        
        if username not in data['users']:
            await ctx.send(f"❌ `{username}` không có trong whitelist!")
            return
        
        data['users'].remove(username)
        update_github_file('whitelist.json', json.dumps(data, indent=2))
        
        embed = discord.Embed(
            title="🗑️ Whitelist Updated",
            description=f"Đã xóa **{username}** khỏi whitelist",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def ban(ctx, userid: str):
    """Ban UserID"""
    try:
        data = get_github_file('blacklist.json')
        
        if userid in data['userids']:
            await ctx.send(f"❌ UserID `{userid}` đã bị ban!")
            return
        
        data['userids'].append(userid)
        update_github_file('blacklist.json', json.dumps(data, indent=2))
        
        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"UserID **{userid}** đã bị ban",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="UserID", value=userid, inline=True)
        embed.add_field(name="Total Bans", value=str(len(data['userids'])), inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def unban(ctx, userid: str):
    """Unban UserID"""
    try:
        data = get_github_file('blacklist.json')
        
        if userid not in data['userids']:
            await ctx.send(f"❌ UserID `{userid}` không bị ban!")
            return
        
        data['userids'].remove(userid)
        update_github_file('blacklist.json', json.dumps(data, indent=2))
        
        embed = discord.Embed(
            title="✅ User Unbanned",
            description=f"UserID **{userid}** đã được unban",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def listusers(ctx, list_type: str = "whitelist"):
    """View whitelist or blacklist"""
    try:
        if list_type.lower() == "whitelist":
            data = get_github_file('whitelist.json')
            users = data['users']
            
            embed = discord.Embed(
                title="📋 Whitelist",
                description="\n".join([f"• `{user}`" for user in users]) if users else "*Trống*",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Total: {len(users)} users")
            
        elif list_type.lower() == "blacklist":
            data = get_github_file('blacklist.json')
            userids = data['userids']
            
            embed = discord.Embed(
                title="📋 Blacklist",
                description="\n".join([f"• `{uid}`" for uid in userids]) if userids else "*Trống*",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Total: {len(userids)} banned")
        else:
            await ctx.send("❌ Sử dụng: `!listusers whitelist` hoặc `!listusers blacklist`")
            return
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def commands(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="🎮 UTG Auth Bot - Commands",
        description="Quản lý whitelist/blacklist cho UTG Script",
        color=0x3498db
    )
    
    embed.add_field(
        name="📝 Whitelist Commands",
        value=(
            "`!whitelist <username>` - Thêm user\n"
            "`!unwhitelist <username>` - Xóa user\n"
            "`!listusers whitelist` - Xem danh sách"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔨 Blacklist Commands",
        value=(
            "`!ban <userid>` - Ban UserID\n"
            "`!unban <userid>` - Unban UserID\n"
            "`!listusers blacklist` - Xem danh sách"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Info",
        value="`!commands` - Hiện commands này",
        inline=False
    )
    
    embed.set_footer(text="UTG Auth System • Powered by Railway")
    
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
