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
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        print(f"🔄 Updating {filename}...")
        print(f"📂 Repo: {GITHUB_REPO}")
        print(f"🔑 Token exists: {bool(GITHUB_TOKEN)}")
        
        # Get current file
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📥 GET response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to get file: {response.text}")
            return False
        
        file_data = response.json()
        sha = file_data.get('sha')
        
        if not sha:
            print("❌ No SHA in response")
            return False
        
        print(f"✅ Got SHA: {sha[:10]}...")
        
        # Update file
        data = {
            "message": f"Update {filename} via Discord Bot",
            "content": base64.b64encode(content.encode()).decode(),
            "sha": sha
        }
        
        update_response = requests.put(url, headers=headers, json=data, timeout=10)
        print(f"📤 PUT response: {update_response.status_code}")
        
        if update_response.status_code in [200, 201]:
            print(f"✅ Successfully updated {filename}")
            return True
        else:
            print(f"❌ Failed to update: {update_response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Exception in update_github_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
        update_response = requests.put(url, headers=headers, json=data, timeout=10)
        update_response.raise_for_status()
        
        print(f"✅ Updated {filename} successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {filename}: {str(e)}")
        return False

def get_blacklist():
    """Get blacklist from GitHub"""
    try:
        # Add timestamp to bypass cache
        import time
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json?t={int(time.time())}"
        
        print(f"📥 Getting blacklist from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        print(f"📄 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text[:200]}")
        
        # Remove BOM if exists
        text = response.text
        if text.startswith('\ufeff'):
            text = text[1:]
        
        # Parse JSON
        data = json.loads(text)
        print(f"✅ Parsed data: {data}")
        
        # Ensure userids exists
        if 'userids' not in data:
            data['userids'] = []
        
        print(f"📊 Current banned users: {data['userids']}")
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        print(f"Response text: {response.text}")
        return {"userids": []}
    except Exception as e:
        print(f"❌ Error getting blacklist: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"userids": []}

@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user}')
    print(f'📝 Command prefix: !')

@bot.command()
async def ban(ctx, userid: str):
    """Ban UserID - Usage: !ban 123456789"""
    try:
        # Validate UserID
        if not userid.isdigit():
            await ctx.send("❌ UserID phải là số!")
            return
        
        # Get current blacklist
        data = get_blacklist()
        
        # Check if already banned
        if userid in data['userids']:
            await ctx.send(f"❌ UserID `{userid}` đã bị ban rồi!")
            return
        
        # Get Roblox user info
        username = f"User {userid}"
        display_name = username
        avatar_url = None
        
        try:
            # Get username
            user_response = requests.get(f"https://users.roblox.com/v1/users/{userid}", timeout=5)
            if user_response.status_code == 200:
                user_data = user_response.json()
                username = user_data.get('name', f"User {userid}")
                display_name = user_data.get('displayName', username)
            
            # Get avatar
            avatar_response = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={userid}&size=420x420&format=Png", timeout=5)
            if avatar_response.status_code == 200:
                avatar_data = avatar_response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    avatar_url = avatar_data['data'][0].get('imageUrl')
        except Exception as e:
            print(f"⚠️ Failed to get user info: {e}")
        
        # Send confirmation message
        confirm_embed = discord.Embed(
            title="⚠️ Xác nhận Ban User",
            description=f"Bạn có chắc muốn ban user này?",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        confirm_embed.add_field(name="👤 Username", value=username, inline=True)
        confirm_embed.add_field(name="📱 Display Name", value=display_name, inline=True)
        confirm_embed.add_field(name="🆔 UserID", value=userid, inline=True)
        
        if avatar_url:
            confirm_embed.set_thumbnail(url=avatar_url)
        
        confirm_embed.set_footer(text="React ✅ để xác nhận, ❌ để hủy (30s)")
        
        confirm_msg = await ctx.send(embed=confirm_embed)
        
        # Add reactions
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')
        
        # Wait for reaction
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '❌':
                cancel_embed = discord.Embed(
                    title="🚫 Đã Hủy",
                    description="Hủy ban user",
                    color=0x95a5a6
                )
                await confirm_msg.edit(embed=cancel_embed)
                await confirm_msg.clear_reactions()
                return
                
        except Exception:
            timeout_embed = discord.Embed(
                title="⏱️ Hết Thời Gian",
                description="Không có phản hồi sau 30 giây",
                color=0x95a5a6
            )
            await confirm_msg.edit(embed=timeout_embed)
            await confirm_msg.clear_reactions()
            return
        
        # User confirmed, proceed with ban
        print(f"🔨 Banning user {userid}...")
        data['userids'].append(userid)
        
        success = update_github_file('blacklist.json', json.dumps(data, indent=2))
        
        if not success:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description="Không thể cập nhật GitHub!\nCheck Railway logs để xem chi tiết.",
                color=0xff0000
            )
            await confirm_msg.edit(embed=error_embed)
            await confirm_msg.clear_reactions()
            return
        
        # Send success message
        success_embed = discord.Embed(
            title="🔨 User Banned",
            description=f"**{username}** đã bị ban khỏi script",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(name="👤 Username", value=username, inline=True)
        success_embed.add_field(name="📱 Display Name", value=display_name, inline=True)
        success_embed.add_field(name="🆔 UserID", value=userid, inline=True)
        success_embed.add_field(name="📊 Total Bans", value=str(len(data['userids'])), inline=False)
        success_embed.set_footer(text=f"Banned by {ctx.author.name}")
        
        if avatar_url:
            success_embed.set_thumbnail(url=avatar_url)
        
        await confirm_msg.edit(embed=success_embed)
        await confirm_msg.clear_reactions()
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")
        print(f"❌ Ban command error: {str(e)}")
        import traceback
        traceback.print_exc()

@bot.command()
async def unban(ctx, userid: str):
    """Unban UserID - Usage: !unban 123456789"""
    try:
        # Validate UserID
        if not userid.isdigit():
            await ctx.send("❌ UserID phải là số!")
            return
        
        # Get current blacklist
        data = get_blacklist()
        
        # Check if banned
        if userid not in data['userids']:
            await ctx.send(f"❌ UserID `{userid}` không bị ban!")
            return
        
        # Get Roblox user info
        username = f"User {userid}"
        display_name = username
        avatar_url = None
        
        try:
            user_response = requests.get(f"https://users.roblox.com/v1/users/{userid}", timeout=5)
            if user_response.status_code == 200:
                user_data = user_response.json()
                username = user_data.get('name', f"User {userid}")
                display_name = user_data.get('displayName', username)
            
            avatar_response = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={userid}&size=420x420&format=Png", timeout=5)
            if avatar_response.status_code == 200:
                avatar_data = avatar_response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    avatar_url = avatar_data['data'][0].get('imageUrl')
        except Exception as e:
            print(f"⚠️ Failed to get user info: {e}")
        
        # Send confirmation
        confirm_embed = discord.Embed(
            title="⚠️ Xác nhận Unban User",
            description=f"Bạn có chắc muốn unban user này?",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        confirm_embed.add_field(name="👤 Username", value=username, inline=True)
        confirm_embed.add_field(name="📱 Display Name", value=display_name, inline=True)
        confirm_embed.add_field(name="🆔 UserID", value=userid, inline=True)
        
        if avatar_url:
            confirm_embed.set_thumbnail(url=avatar_url)
        
        confirm_embed.set_footer(text="React ✅ để xác nhận, ❌ để hủy (30s)")
        
        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')
        
        # Wait for reaction
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '❌':
                cancel_embed = discord.Embed(
                    title="🚫 Đã Hủy",
                    description="Hủy unban user",
                    color=0x95a5a6
                )
                await confirm_msg.edit(embed=cancel_embed)
                await confirm_msg.clear_reactions()
                return
                
        except Exception:
            timeout_embed = discord.Embed(
                title="⏱️ Hết Thời Gian",
                description="Không có phản hồi sau 30 giây",
                color=0x95a5a6
            )
            await confirm_msg.edit(embed=timeout_embed)
            await confirm_msg.clear_reactions()
            return
        
        # Proceed with unban
        print(f"✅ Unbanning user {userid}...")
        data['userids'].remove(userid)
        
        success = update_github_file('blacklist.json', json.dumps(data, indent=2))
        
        if not success:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description="Không thể cập nhật GitHub!\nCheck Railway logs để xem chi tiết.",
                color=0xff0000
            )
            await confirm_msg.edit(embed=error_embed)
            await confirm_msg.clear_reactions()
            return
        
        # Success message
        success_embed = discord.Embed(
            title="✅ User Unbanned",
            description=f"**{username}** đã được unban",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        success_embed.add_field(name="👤 Username", value=username, inline=True)
        success_embed.add_field(name="📱 Display Name", value=display_name, inline=True)
        success_embed.add_field(name="🆔 UserID", value=userid, inline=True)
        success_embed.set_footer(text=f"Unbanned by {ctx.author.name}")
        
        if avatar_url:
            success_embed.set_thumbnail(url=avatar_url)
        
        await confirm_msg.edit(embed=success_embed)
        await confirm_msg.clear_reactions()
        
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)}")
        print(f"❌ Unban command error: {str(e)}")
        import traceback
        traceback.print_exc()

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
async def testgithub(ctx):
    """Test GitHub connection và permissions"""
    try:
        embed = discord.Embed(
            title="🧪 GitHub Connection Test",
            color=0x3498db
        )
        
        # Check env vars
        embed.add_field(
            name="🔑 Environment Variables",
            value=f"GITHUB_REPO: `{GITHUB_REPO or 'NOT SET'}`\nGITHUB_TOKEN: `{'SET' if GITHUB_TOKEN else 'NOT SET'}`",
            inline=False
        )
        
        # Test read blacklist
        try:
            data = get_blacklist()
            embed.add_field(
                name="📥 Read Blacklist",
                value=f"✅ Success\nBanned users: {len(data.get('userids', []))}",
                inline=False
            )
        except Exception as e:
            embed.add_field(
                name="📥 Read Blacklist",
                value=f"❌ Failed: {str(e)}",
                inline=False
            )
        
        # Test GitHub API
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/blacklist.json"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                embed.add_field(
                    name="🔗 GitHub API",
                    value=f"✅ Connected (Status: {response.status_code})",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔗 GitHub API",
                    value=f"❌ Failed (Status: {response.status_code})\n{response.text[:100]}",
                    inline=False
                )
        except Exception as e:
            embed.add_field(
                name="🔗 GitHub API",
                value=f"❌ Error: {str(e)}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Test failed: {str(e)}")

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
