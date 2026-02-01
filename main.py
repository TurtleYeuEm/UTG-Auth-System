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

def get_blacklist():
    """Get blacklist from GitHub"""
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json"
    response = requests.get(url)
    return json.loads(response.text)

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    print(f'📝 Command prefix: !')

@bot.command()
async def ban(ctx, userid: str):
    """Ban UserID - Usage: !ban 123456789"""
    try:
        data = get_blacklist()
        
        if userid in data['userids']:
            await ctx.send(f"❌ UserID `{userid}` đã bị ban rồi!")
            return
        
        data['userids'].append(userid)
        update_github_file('blacklist.json', json.dumps(data, indent=2))
        
        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"UserID **{userid}** đã bị ban khỏi script",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Banned UserID", value=userid, inline=True)
        embed.add_field(name="Total Bans", value=str(len(data['userids'])), inline=True)
        embed.set_footer(text="UTG Anti-Cheat System")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command()
async def unban(ctx, userid: str):
    """Unban UserID - Usage: !unban 123456789"""
    try:
        data = get_blacklist()
        
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
        embed.add_field(name="Unbanned UserID", value=userid, inline=True)
        embed.set_footer(text="UTG Anti-Cheat System")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command()
async def banlist(ctx):
    """Xem danh sách bị ban"""
    try:
        data = get_blacklist()
        userids = data['userids']
        
        if not userids:
            embed = discord.Embed(
                title="📋 Blacklist",
                description="*Không có ai bị ban*",
                color=0x95a5a6,
                timestamp=datetime.utcnow()
            )
        else:
            embed = discord.Embed(
                title="📋 Blacklist",
                description="\n".join([f"• `{uid}`" for uid in userids]),
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Total: {len(userids)} banned users")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")

@bot.command()
async def commands(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="🎮 UTG Auth Bot - Commands",
        description="Quản lý blacklist cho UTG Script",
        color=0x3498db
    )
    
    embed.add_field(
        name="🔨 Ban Commands",
        value=(
            "`!ban <userid>` - Ban UserID khỏi script\n"
            "`!unban <userid>` - Unban UserID\n"
            "`!banlist` - Xem danh sách bị ban"
        ),
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Info",
        value=(
            "`!commands` - Hiện menu này\n\n"
            "**Lưu ý:** Mọi người đều dùng được script,\n"
            "chỉ những UserID bị ban mới không dùng được."
        ),
        inline=False
    )
    
    embed.set_footer(text="UTG Auth System • Powered by Railway")
    
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
