import discord
from discord.ext import commands, tasks
import os
import sys
import logging
from dotenv import load_dotenv
import asyncio

# Load environment variables FIRST
load_dotenv()

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

# Setup Django BEFORE importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crwn.settings')

try:
    import django
    django.setup()
    print("✅ Django setup complete")
    
    from django.utils import timezone
    from asgiref.sync import sync_to_async
    from crownie.models import User, DiscordChatSession, ReputationLog, UserQuestProgress
    MODELS_AVAILABLE = True
    print("✅ Models imported successfully")
    
except Exception as e:
    print(f"❌ Django setup error: {e}")
    import traceback
    traceback.print_exc()
    MODELS_AVAILABLE = False
    timezone = None
    sync_to_async = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store active sessions in memory
active_sessions = {}

# Configuration
MIN_SESSION_DURATION = 5  # minutes
POINTS_PER_MINUTE = 0.5

class ChatSession:
    def __init__(self, user_id, channel_id):
        self.user_id = user_id
        self.channel_id = channel_id
        if MODELS_AVAILABLE and timezone:
            self.start_time = timezone.now()
            self.last_message_time = timezone.now()
        else:
            from datetime import datetime
            self.start_time = datetime.now()
            self.last_message_time = datetime.now()
        self.message_count = 0
        self.is_active = True

# ASYNC DATABASE FUNCTIONS - These wrap Django queries for async use
if MODELS_AVAILABLE:
    @sync_to_async
    def get_user_by_discord_id(discord_id):
        """Get user from database (async wrapper)"""
        if not MODELS_AVAILABLE:
            return None
        return User.objects.filter(discord_id=discord_id).first()

    @sync_to_async  
    def update_user_stats(user, messages=0, last_activity=None):
        """Update user stats (async wrapper)"""
        if not MODELS_AVAILABLE or not user:
            return
        user.discord_total_messages += messages
        if last_activity:
            user.discord_last_activity = last_activity
        user.save()

    @sync_to_async
    def save_chat_session(user, session_data):
        """Save chat session to database (async wrapper)"""
        if not MODELS_AVAILABLE or not user:
            return None
        
        session = DiscordChatSession.objects.create(
            user=user,
            session_id=session_data['session_id'],
            start_time=session_data['start_time'],
            end_time=session_data['end_time'],
            duration_minutes=session_data['duration_minutes'],
            message_count=session_data['message_count'],
            points_earned=session_data['points_earned'],
            channel_id=session_data['channel_id'],
            channel_name=session_data['channel_name'],
        )
        return session

    @sync_to_async
    def update_user_points(user, points, duration_minutes):
        """Update user's points and reputation (async wrapper)"""
        if not MODELS_AVAILABLE or not user:
            return
        
        user.discord_chat_points += points
        user.reputation_score += points
        user.total_chat_minutes += duration_minutes
        user.chat_sessions_count += 1
        user.save()
        
        # Create reputation log
        ReputationLog.objects.create(
            user=user,
            action='discord_chat',
            points=points,
            metadata={'session_id': 'temp'}
        )

    @sync_to_async
    def update_quest_progress_sync(user, message_count=0, voice_minutes=0):
        """Update user's quest progress based on Discord activity (sync version)"""
        try:
            # Get all active quests for this user
            quests_progress = UserQuestProgress.objects.filter(
                user=user,
                quest__is_active=True,
                status__in=['in_progress', 'completed']
            ).select_related('quest')
            
            for progress in quests_progress:
                updated = False
                
                # Update Discord message count
                if progress.quest.required_discord_messages > 0:
                    progress.discord_messages_count += message_count
                    updated = True
                
                # Update voice minutes
                if progress.quest.required_discord_voice_minutes > 0:
                    progress.discord_voice_minutes += voice_minutes
                    updated = True
                
                if updated:
                    # Check if quest is now complete
                    if progress.check_completion():
                        progress.status = 'completed'
                        progress.completed_at = timezone.now()
                    
                    progress.save()
                    
        except Exception as e:
            print(f"Error updating quest progress: {e}")

else:
    # Create dummy async functions if Django not available
    async def get_user_by_discord_id(discord_id):
        return None
    
    async def update_user_stats(user, messages=0, last_activity=None):
        return
    
    async def save_chat_session(user, session_data):
        return None
    
    async def update_user_points(user, points, duration_minutes):
        return
    
    async def update_quest_progress_sync(user, message_count=0, voice_minutes=0):
        return

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'👑 Crownie Chat Bot Ready!')
    print(f'📊 MODELS_AVAILABLE: {MODELS_AVAILABLE}')
    
    # List all servers and channels
    print("\n📋 Connected to servers:")
    for guild in bot.guilds:
        print(f"  🏰 Server: {guild.name} (ID: {guild.id})")
        print(f"  📁 Channels:")
        for channel in guild.text_channels:
            print(f"    - #{channel.name} (ID: {channel.id})")
    
    if MODELS_AVAILABLE:
        check_inactive_sessions.start()
    else:
        print("⚠️ Database not connected - session checking disabled")

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    channel_id = str(message.channel.id)
    channel_name = message.channel.name
    
    print(f"\n💬 MESSAGE from {message.author.name} in #{channel_name}")
    print(f"   Content: {message.content[:100]}")
    print(f"   User ID: {user_id}")
    
    try:
        # Get user from database ASYNC
        user = None
        if MODELS_AVAILABLE:
            user = await get_user_by_discord_id(user_id)
            if user:
                print(f"   ✅ User found: {user.username}")
            else:
                print(f"   ⚠️ User NOT in database (connect on website)")
                # We'll still track the session but won't save to DB
                user = None
        
        # Start or update session
        session_key = f"{user_id}_{channel_id}"
        
        if session_key not in active_sessions:
            # Start new session
            session = ChatSession(user_id, channel_id)
            active_sessions[session_key] = session
            print(f"   📝 NEW SESSION started")
        else:
            # Update existing session
            session = active_sessions[session_key]
            if MODELS_AVAILABLE and timezone:
                session.last_message_time = timezone.now()
            else:
                from datetime import datetime
                session.last_message_time = datetime.now()
            print(f"   🔄 Session updated")
        
        # Track message
        session.message_count += 1
        print(f"   📊 Session count: {session.message_count} messages")
        
        # Update database if user exists
        if user and MODELS_AVAILABLE:
            await update_user_stats(user, messages=1, last_activity=session.last_message_time)
            
            # Update quest progress for message count
            await update_quest_progress_sync(user, message_count=1)
            
            print(f"   💾 Stats saved to database")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Process commands
    await bot.process_commands(message)

@tasks.loop(minutes=1)
async def check_inactive_sessions():
    """Check for inactive sessions"""
    if not MODELS_AVAILABLE:
        return
    
    from datetime import datetime
    
    for session_key, session in list(active_sessions.items()):
        current_time = datetime.now()
        if MODELS_AVAILABLE and timezone:
            current_time = timezone.now()
        
        # Check if inactive for 5 minutes
        if (current_time - session.last_message_time).total_seconds() > 300:
            await end_chat_session(session_key)

async def end_chat_session(session_key):
    """End session and award points"""
    if session_key not in active_sessions:
        return
    
    session = active_sessions[session_key]
    session.is_active = False
    
    from datetime import datetime
    current_time = datetime.now()
    if MODELS_AVAILABLE and timezone:
        current_time = timezone.now()
    
    duration = (current_time - session.start_time).total_seconds() / 60
    
    print(f"\n📊 Ending session for user {session.user_id}")
    print(f"   Duration: {duration:.1f} minutes")
    print(f"   Messages: {session.message_count}")
    
    # Award points for good sessions
    if duration >= MIN_SESSION_DURATION and session.message_count >= 3:
        try:
            if not MODELS_AVAILABLE:
                print(f"   ⚠️ Would award points (database not connected)")
                return
            
            # Get user ASYNC
            user = await get_user_by_discord_id(session.user_id)
            if not user:
                print(f"   ⚠️ User not in database, skipping points")
                return
            
            # Calculate points
            base_points = min(duration * POINTS_PER_MINUTE, 10)
            activity_bonus = min(session.message_count * 0.1, 5)
            total_points = round(base_points + activity_bonus, 2)
            
            print(f"   💰 Awarding {total_points:.1f} points to {user.username}")
            
            # Save session to database ASYNC
            session_data = {
                'session_id': session_key,
                'start_time': session.start_time,
                'end_time': session.last_message_time,
                'duration_minutes': int(duration),
                'message_count': session.message_count,
                'points_earned': total_points,
                'channel_id': session.channel_id,
                'channel_name': "general",
            }
            
            await save_chat_session(user, session_data)
            
            # Update user points ASYNC
            await update_user_points(user, total_points, int(duration))
            
            print(f"   ✅ {user.username} earned {total_points:.1f} reputation points!")
            
            # Try to send DM notification
            try:
                member = await bot.fetch_user(int(session.user_id))
                if member:
                    embed = discord.Embed(
                        title="🎮 Chat Session Complete!",
                        description=f"You earned **{total_points:.1f} reputation points**!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="Duration", value=f"{duration:.1f} minutes", inline=True)
                    embed.add_field(name="Messages", value=session.message_count, inline=True)
                    embed.add_field(name="Points", value=f"{total_points:.1f}", inline=True)
                    embed.add_field(name="New Total", value=f"{user.reputation_score:.1f}", inline=True)
                    embed.set_footer(text="Keep chatting to earn more!")
                    
                    await member.send(embed=embed)
            except:
                pass  # Can't DM, that's okay
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ⚠️ Session too short for points ({duration:.1f}min, {session.message_count} msgs)")
    
    # Clean up
    if session_key in active_sessions:
        del active_sessions[session_key]

# ASYNC command handlers
@bot.command(name='stats')
async def stats_command(ctx):
    """Check your chat stats"""
    user_id = str(ctx.author.id)
    
    try:
        if not MODELS_AVAILABLE:
            await ctx.send("⚠️ Database not connected. Please check bot logs.")
            return
        
        # Get user ASYNC
        user = await get_user_by_discord_id(user_id)
        if not user:
            await ctx.send("❌ You need to connect your Discord account on crownie.com first!")
            return
        
        embed = discord.Embed(
            title=f"📊 {ctx.author.name}'s Stats",
            color=discord.Color.purple()
        )
        
        embed.add_field(name="Reputation", value=f"{user.reputation_score:.1f}", inline=True)
        embed.add_field(name="Chat Points", value=f"{user.discord_chat_points:.1f}", inline=True)
        embed.add_field(name="Messages", value=user.discord_total_messages, inline=True)
        embed.add_field(name="Sessions", value=user.chat_sessions_count, inline=True)
        embed.add_field(name="Chat Time", value=f"{user.total_chat_minutes} min", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error in stats command: {e}")
        await ctx.send(f"❌ Error: {str(e)[:100]}")

@bot.command(name='ping')
async def ping_command(ctx):
    """Check if bot is alive"""
    await ctx.send(f"🏓 Pong! Crownie bot is online! Database: {'✅ Connected' if MODELS_AVAILABLE else '⚠️ Not connected'}")

@bot.command(name='debug')
async def debug_command(ctx):
    """Debug command"""
    user_id = str(ctx.author.id)
    
    embed = discord.Embed(
        title="🔧 Debug Information",
        color=discord.Color.orange()
    )
    
    embed.add_field(name="User", value=f"{ctx.author.name} ({user_id})", inline=False)
    embed.add_field(name="Channel", value=f"#{ctx.channel.name}", inline=True)
    embed.add_field(name="Server", value=ctx.guild.name, inline=True)
    
    if MODELS_AVAILABLE:
        user = await get_user_by_discord_id(user_id)
        if user:
            embed.add_field(name="Database", value=f"✅ {user.username}", inline=False)
            embed.add_field(name="Reputation", value=f"{user.reputation_score:.1f}", inline=True)
            embed.add_field(name="Discord Connected", value="✅ Yes" if user.discord_connected else "❌ No", inline=True)
        else:
            embed.add_field(name="Database", value="❌ Not registered", inline=False)
    else:
        embed.add_field(name="Database", value="⚠️ Not connected", inline=False)
    
    # Check active sessions
    session_key = f"{user_id}_{ctx.channel.id}"
    if session_key in active_sessions:
        session = active_sessions[session_key]
        embed.add_field(name="Active Session", value=f"✅ {session.message_count} messages", inline=False)
    else:
        embed.add_field(name="Active Session", value="❌ None", inline=False)
    
    await ctx.send(embed=embed)

# Run bot
def run_bot():
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not bot_token:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found!")
        return
    
    print(f"🔑 Bot token: {'*' * len(bot_token[:10])}...")
    print("🚀 Starting Crownie Discord Bot...")
    
    try:
        bot.run(bot_token)
    except discord.LoginFailure:
        print("❌ Invalid bot token!")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    run_bot()