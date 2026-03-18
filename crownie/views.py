import json
import logging
import os
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods



from .forms import CustomUserCreationForm, LoginForm, QuestForm
from .models import (
    DiscordChatSession, Engagement, Quest, ReputationLog, 
    UserQuestProgress, QuestCompletion, DailyStreak, User
)
from django.core.exceptions import FieldError

logger = logging.getLogger(__name__)

load_dotenv()

User = get_user_model()

# ==================== HELPER FUNCTIONS ====================

def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def healthcheck(request):
    """
    Ultra-simple healthcheck that bypasses ALL Django complexity
    """
    # Print to gunicorn logs
    print(f"✅ Healthcheck called at {timezone.now()}")
    
    # Return super simple response
    return HttpResponse(
        "OK", 
        status=200, 
        content_type="text/plain",
        headers={
            'Cache-Control': 'no-cache',
        }
    )

# ==================== SIMPLE AUTHENTICATION VIEWS ====================

def signup_view(request):
    """Signup view with referral tracking"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Get referral code from URL
    referral_code = request.GET.get('ref', '')
    referrer = None
    
    if referral_code:
        try:
            referrer = User.objects.get(referral_code=referral_code)
        except User.DoesNotExist:
            messages.info(request, "Invalid referral code. Signing up without referral.")
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Check for referral code in form input
            form_referral_code = request.POST.get('referral_code_input', '').strip()
            if form_referral_code and not referral_code:
                try:
                    referrer = User.objects.get(referral_code=form_referral_code)
                    referral_code = form_referral_code
                except User.DoesNotExist:
                    messages.info(request, "The referral code you entered is invalid.")
            
            # Handle referral
            if referrer:
                user.referred_by = referrer
                user.save()
                
                # Award referral points to referrer
                referrer.add_referral(user)
                
                # Award bonus to new user
                user.reputation_score += 10
                user.save()
                
                ReputationLog.objects.create(
                    user=user,
                    action='signup',
                    points=10,
                    metadata={'signup_method': 'email', 'referral_used': True, 'referrer': referrer.username}
                )
                
                messages.success(request, f'🎁 You used {referrer.username}\'s referral! +10 bonus points!')
            
            # Log the user in
            login(request, user)
            
            # Update user with display name
            user.display_name = form.cleaned_data['display_name']
            user.save()
            
            # Create DailyStreak for new user
            DailyStreak.objects.create(user=user)
            
            # Update login streak
            user.update_login_streak()
            
            # Award signup reputation (if no referral bonus was given)
            if not referrer:
                ReputationLog.objects.create(
                    user=user,
                    action='signup',
                    points=10,
                    metadata={'signup_method': 'email', 'referral_used': False}
                )
                user.reputation_score += 10
                user.save()
            
            messages.success(request, f'✅ Account created! Your referral code: **{user.referral_code}** - Share it to earn points!')
            
            # Redirect to Discord connection
            return redirect('discord_connect')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pass referral code to form initial data
        form = CustomUserCreationForm(initial={'referral_code': referral_code})
    
    return render(request, 'signup.html', {
        'form': form,
        'referral_code': referral_code,
        'referrer': referrer
    })

def login_view(request):
    """Simple login view with streak tracking"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Try to authenticate with username
            user = authenticate(username=username, password=password)
            
            # If that fails, try to find user by email
            if user is None:
                try:
                    user_by_email = User.objects.get(email=username)
                    user = authenticate(username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if user is not None:
                login(request, user)
                
                # Update user login streak
                streak_updated = user.update_login_streak()
                
                # Update daily streak model
                daily_streak, created = DailyStreak.objects.get_or_create(user=user)
                daily_streak.update_streak()
                
                if streak_updated:
                    messages.success(request, f'Welcome back, {user.username}! 🔥 Streak: {user.current_login_streak} days')
                else:
                    messages.success(request, f'Welcome back, {user.username}!')
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """Simple logout view"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # Get recent chat sessions
    recent_sessions = []
    try:
        recent_sessions = DiscordChatSession.objects.filter(
            user=user
        ).order_by('-start_time')[:10]
    except Exception as e:
        print(f"Error getting recent sessions: {e}")
    
    # Get active quests for dashboard
    active_quests_data = []
    try:
        user_quests = UserQuestProgress.objects.filter(
            user=user,
            quest__is_active=True,
            status__in=['in_progress', 'completed']
        ).select_related('quest')[:5]
        
        for progress in user_quests:
            active_quests_data.append({
                'quest': progress.quest,
                'progress': progress,
                'completion_percentage': progress.calculate_completion_percentage()
            })
    except Exception as e:
        logger.error(f"Error getting active quests: {e}")
    
    # Get referrals data
    referrals = User.objects.filter(referred_by=user)
    
    # Get referral URL
    referral_url = f"https://www.crownieverse.xyz/signup/?ref={user.referral_code}"
    
    context = {
        'user': user,
        'recent_sessions': recent_sessions,
        'active_quests': active_quests_data,
        'referrals': referrals,
        'referral_url': referral_url,
    }
    
    return render(request, 'dashboard.html', context)

def home_view(request):
    """Homepage view"""
    return render(request, 'index.html')

def whitepaper_view(request):
    return render(request, 'whitepaper.html')

def roadmap_view(request):
    return render(request, 'roadmap.html')

@login_required
def discord_connect(request):
    """Start Discord OAuth2 flow"""
    # Discord OAuth2 URL
    client_id = os.getenv('DISCORD_CLIENT_ID')
    redirect_uri = os.getenv('DISCORD_REDIRECT_URI', 'https://www.crownieverse.xyz/discord/callback/')
    
    # Scopes needed: identify + guilds.join (to add to server)
    scopes = ['identify', 'guilds.join']
    
    auth_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={'%20'.join(scopes)}"
    
    return redirect(auth_url)

@login_required
def discord_callback(request):
    """Handle Discord OAuth callback with better error handling"""
    
    # Debug logging
    logger.info(f"Discord callback received. GET params: {dict(request.GET)}")
    logger.info(f"User authenticated: {request.user.is_authenticated}")
    
    # Check for error in callback
    if 'error' in request.GET:
        error_msg = request.GET.get('error_description', request.GET['error'])
        messages.error(request, f"Discord authorization error: {error_msg}")
        logger.error(f"Discord OAuth error: {error_msg}")
        return redirect('home')
    
    code = request.GET.get('code')
    if not code:
        messages.error(request, "No authorization code received from Discord")
        logger.error("No authorization code in callback")
        return redirect('home')
    
    try:
        # IMPORTANT: Use the exact same redirect URI as in Discord portal
        redirect_uri = settings.DISCORD_REDIRECT_URI
        
        # Debug: Log what we're sending
        logger.info(f"Using redirect_uri: {redirect_uri}")
        logger.info(f"Client ID: {settings.DISCORD_CLIENT_ID}")
        
        # Exchange code for token
        token_url = "https://discord.com/api/oauth2/token"
        data = {
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'scope': 'identify guilds.join'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        logger.info(f"Requesting token from Discord...")
        token_response = requests.post(token_url, data=data, headers=headers)
        
        # Log response for debugging
        logger.info(f"Token response status: {token_response.status_code}")
        logger.info(f"Token response: {token_response.text[:100]}...")
        
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            messages.error(request, "No access token received from Discord")
            logger.error("No access token in response")
            return redirect('home')
        
        # Get user info from Discord
        user_response = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        logger.info(f"User info response status: {user_response.status_code}")
        
        user_response.raise_for_status()
        discord_user = user_response.json()
        logger.info(f"Discord user data: {discord_user}")
        
        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to connect Discord")
            return redirect('login')
        
        # Update user model
        request.user.discord_id = discord_user['id']
        request.user.discord_username = f"{discord_user['username']}#{discord_user.get('discriminator', '0')}"
        request.user.discord_connected = True
        request.user.discord_connected_at = timezone.now()
        
        # Award reputation for connecting
        ReputationLog.objects.create(
            user=request.user,
            action='discord_connect',
            points=25,
            metadata={'discord_id': discord_user['id']}
        )
        
        request.user.reputation_score += 25
        request.user.save()
        
        # Auto-start Discord connection quest if it exists
        discord_quest = Quest.objects.filter(
            quest_type='social',
            title__icontains='welcome',
            is_active=True
        ).first()
        
        if discord_quest:
            UserQuestProgress.objects.get_or_create(
                user=request.user,
                quest=discord_quest,
                defaults={
                    'status': 'in_progress',
                    'discord_messages_count': 1  # Counts as one message for the quest
                }
            )
        
        # Join user to Discord server (if bot token is available)
        if hasattr(settings, 'DISCORD_BOT_TOKEN') and settings.DISCORD_BOT_TOKEN and hasattr(settings, 'DISCORD_GUILD_ID'):
            try:
                logger.info(f"Attempting to add user to guild: {settings.DISCORD_GUILD_ID}")
                
                guild_response = requests.put(
                    f'https://discord.com/api/guilds/{settings.DISCORD_GUILD_ID}/members/{discord_user["id"]}',
                    headers={
                        'Authorization': f'Bot {settings.DISCORD_BOT_TOKEN}',
                        'Content-Type': 'application/json'
                    },
                    json={'access_token': access_token}
                )
                
                logger.info(f"Guild add response status: {guild_response.status_code}")
                logger.info(f"Guild add response: {guild_response.text}")
                
                if guild_response.status_code in [200, 201, 204]:
                    messages.success(request, "Successfully joined Discord server!")
                elif guild_response.status_code == 400:
                    # User might already be in server
                    messages.info(request, "Already a member of the Discord server!")
                else:
                    logger.warning(f"Unexpected guild response: {guild_response.status_code}")
                    
            except Exception as e:
                logger.error(f"Could not add user to server: {str(e)}", exc_info=True)
                # Non-critical error - continue
        
        messages.success(request, "Discord connected successfully!")
        return redirect('dashboard')
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error connecting to Discord: {str(e)}"
        messages.error(request, error_msg)
        logger.error(error_msg, exc_info=True)
        return redirect('home')
    except KeyError as e:
        error_msg = f"Missing data in Discord response: {str(e)}"
        messages.error(request, error_msg)
        logger.error(error_msg, exc_info=True)
        return redirect('home')
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        messages.error(request, error_msg)
        logger.error(error_msg, exc_info=True)
        return redirect('home')
    
@login_required
def discord_disconnect(request):
    """Disconnect Discord account"""
    user = request.user
    user.discord_id = None
    user.discord_username = None
    user.discord_connected = False
    user.discord_chat_points = 0
    user.discord_total_messages = 0
    user.save()
    
    messages.success(request, 'Discord account disconnected')
    return redirect('dashboard')

@csrf_exempt
def discord_activity_webhook(request):
    """Receive Discord activity updates"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        discord_id = data.get('discord_id')
        message_count = data.get('message_count', 0)
        voice_minutes = data.get('voice_minutes', 0)
        
        if not discord_id:
            return JsonResponse({'error': 'Missing discord_id'}, status=400)
        
        user = User.objects.filter(discord_id=discord_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)
        
        # Update last activity
        user.discord_last_activity = timezone.now()
        
        # Update Discord stats
        user.discord_total_messages += message_count
        user.discord_chat_points += message_count * 0.5  # 0.5 points per message
        
        # Update quest progress
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
        
        user.save()
        
        return JsonResponse({'status': 'success', 'user': user.username})
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_user_chat_stats(request):
    """Get user's chat statistics"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    user = request.user
    
    # Initialize stats
    today_stats = {'sessions': 0, 'messages': 0, 'points': 0, 'duration': 0}
    weekly_stats = {'sessions': 0, 'messages': 0, 'points': 0, 'duration': 0}
    recent_sessions = []
    
    try:
        # Get today's sessions
        today = timezone.now().date()
        today_sessions = DiscordChatSession.objects.filter(
            user=user,
            start_time__date=today
        )
        
        # Calculate today's stats
        today_stats = {
            'sessions': today_sessions.count(),
            'messages': sum(s.message_count for s in today_sessions),
            'points': sum(s.points_earned for s in today_sessions),
            'duration': sum(s.duration_minutes for s in today_sessions),
        }
        
        # Get weekly stats
        week_ago = timezone.now() - timedelta(days=7)
        weekly_sessions = DiscordChatSession.objects.filter(
            user=user,
            start_time__gte=week_ago
        )
        
        weekly_stats = {
            'sessions': weekly_sessions.count(),
            'messages': sum(s.message_count for s in weekly_sessions),
            'points': sum(s.points_earned for s in weekly_sessions),
            'duration': sum(s.duration_minutes for s in weekly_sessions),
        }
        
        # Get recent sessions
        recent_sessions = list(DiscordChatSession.objects.filter(
            user=user
        ).order_by('-start_time')[:10].values(
            'start_time', 'duration_minutes', 'message_count', 'points_earned', 'channel_name'
        ))
        
    except Exception as e:
        print(f"Error getting chat stats: {e}")
    
    return JsonResponse({
        'user': {
            'username': user.username,
            'discord_connected': user.discord_connected,
            'discord_username': user.discord_username,
            'reputation_score': user.reputation_score,
            'discord_chat_points': user.discord_chat_points,
            'discord_total_messages': user.discord_total_messages,
            'chat_sessions_count': user.chat_sessions_count,
            'total_chat_minutes': user.total_chat_minutes,
            'current_streak': user.current_login_streak,
            'referral_count': user.referral_count,
        },
        'today': today_stats,
        'weekly': weekly_stats,
        'recent_sessions': recent_sessions,
    })

# ==================== QUEST SYSTEM VIEWS ====================

@login_required
def quests_view(request):
    """Main quests page"""
    user = request.user
    
    # Update user login streak
    user.update_login_streak()
    
    # Update daily streak model
    daily_streak, created = DailyStreak.objects.get_or_create(user=user)
    daily_streak.update_streak()
    
    # Get active quests
    active_quests = Quest.objects.filter(is_active=True)
    
    # Get or create user progress for each quest
    user_quests = []
    for quest in active_quests:
        progress, created = UserQuestProgress.objects.get_or_create(
            user=user,
            quest=quest,
            defaults={'status': 'not_started'}
        )
        
        # Update progress with current user data
        if quest.required_daily_login_streak > 0:
            progress.daily_login_streak = user.current_login_streak
        
        if quest.required_referrals > 0:
            progress.referrals_count = user.referral_count
        
        # Check if quest should be marked as in_progress
        if progress.status == 'not_started' and progress.calculate_completion_percentage() > 0:
            progress.status = 'in_progress'
            progress.save()
        
        # Check for completion
        if progress.status == 'in_progress' and progress.check_completion():
            progress.status = 'completed'
            progress.completed_at = timezone.now()
            progress.save()
        
        user_quests.append({
            'quest': quest,
            'progress': progress,
            'completion_percentage': progress.calculate_completion_percentage()
        })
    
    # Get completed quests
    completed_progress = UserQuestProgress.objects.filter(
        user=user,
        status__in=['completed', 'claimed']
    ).select_related('quest').order_by('-completed_at')
    
    # Get statistics
    quest_stats = {
        'total_completed': QuestCompletion.objects.filter(user=user).count(),
        'total_reputation_earned': sum(
            qc.reputation_earned for qc in QuestCompletion.objects.filter(user=user)
        ) or 0,
        'active_quests': len([q for q in user_quests if q['progress'].status in ['in_progress', 'completed']]),
    }
    
    # Check for daily quests
    daily_quests = active_quests.filter(is_daily=True)
    
    context = {
        'user_quests': user_quests,
        'completed_quests': completed_progress,
        'daily_streak': daily_streak,
        'quest_stats': quest_stats,
        'daily_quests': daily_quests,
        'current_login_streak': user.current_login_streak,
        'weekly_progress': daily_streak.get_weekly_progress(),
    }
    
    return render(request, 'quests/quests.html', context)


@login_required
def start_quest(request, quest_id):
    """Start a quest"""
    quest = get_object_or_404(Quest, id=quest_id, is_active=True)
    user = request.user
    
    # Check if user can start this quest
    progress, created = UserQuestProgress.objects.get_or_create(
        user=user,
        quest=quest,
        defaults={'status': 'in_progress'}
    )
    
    if not created and progress.status == 'not_started':
        progress.status = 'in_progress'
        progress.save()
    
    messages.success(request, f'Quest "{quest.title}" started!')
    return redirect('quests')


@login_required
def claim_quest_reward(request, progress_id):
    """Claim rewards for a completed quest"""
    user_progress = get_object_or_404(
        UserQuestProgress,
        id=progress_id,
        user=request.user,
        status='completed'
    )
    
    quest = user_progress.quest
    
    # Check if quest has already been claimed
    if user_progress.status == 'claimed':
        messages.warning(request, 'Rewards already claimed!')
        return redirect('quests')
    
    # Create quest completion record
    completion = QuestCompletion.objects.create(
        user=request.user,
        quest=quest,
        user_quest_progress=user_progress,
        reputation_earned=quest.reputation_reward,
        tokens_earned=quest.token_reward,
        badge_earned=quest.badge_reward,
        xp_earned=quest.xp_reward
    )
    
    # Update user stats
    user = request.user
    user.reputation_score += quest.reputation_reward
    user.quests_completed += 1
    if quest.token_reward > 0:
        user.total_earned += float(quest.token_reward)
    
    # Add badge if exists
    if quest.badge_reward:
        # Here you would add badge to user's profile
        pass
    
    user.save()
    
    # Update progress status
    user_progress.status = 'claimed'
    user_progress.claimed_at = timezone.now()
    user_progress.reputation_claimed = True
    user_progress.tokens_claimed = True
    if quest.badge_reward:
        user_progress.badge_claimed = True
    user_progress.save()
    
    # Update quest completion count
    quest.current_completions += 1
    quest.save()
    
    # Add reputation log
    ReputationLog.objects.create(
        user=user,
        action='quest_complete',
        points=quest.reputation_reward,
        metadata=json.dumps({
            'quest_id': quest.id,
            'quest_title': quest.title,
            'completion_id': completion.id
        })
    )
    
    messages.success(request, f'Rewards claimed! +{quest.reputation_reward} reputation earned!')
    return redirect('quests')


@login_required
def daily_login_reward(request):
    """Claim daily login reward"""
    user = request.user
    
    # Update login streak first
    user.update_login_streak()
    daily_streak, created = DailyStreak.objects.get_or_create(user=user)
    streak_updated = daily_streak.update_streak()
    
    if not streak_updated:
        messages.info(request, 'You have already claimed your daily reward today!')
        return redirect('quests')
    
    # Check if already claimed today
    today = timezone.now().date()
    last_reward = ReputationLog.objects.filter(
        user=user,
        action='daily_login',
        created_at__date=today
    ).first()
    
    if last_reward:
        messages.info(request, 'Daily reward already claimed today!')
        return redirect('quests')
    
    # Calculate reward based on streak
    base_reward = 10
    streak_bonus = min(daily_streak.current_streak * 2, 50)  # Max 50 bonus
    total_reward = base_reward + streak_bonus
    
    # Update user
    user.reputation_score += total_reward
    user.save()
    
    # Log reward
    ReputationLog.objects.create(
        user=user,
        action='daily_login',
        points=total_reward,
        metadata=json.dumps({
            'streak': daily_streak.current_streak,
            'streak_bonus': streak_bonus,
            'base_reward': base_reward
        })
    )
    
    messages.success(request, f'Daily login reward claimed! +{total_reward} reputation (Streak: {daily_streak.current_streak} days)')
    return redirect('quests')


@login_required
@user_passes_test(is_staff_or_superuser)
def manage_quests(request):
    """Admin view to manage quests"""
    # Quest model now has created_at field, so this should work
    quests = Quest.objects.all().order_by('-created_at')
    
    context = {
        'quests': quests,
        'editing': False,
    }
    
    return render(request, 'quests/manage_quests.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def create_quest(request):
    """Create a new quest"""
    if request.method == 'POST':
        # Create form with POST data
        form_data = request.POST.copy()
        
        # Convert string fields to appropriate values
        form_data['reputation_reward'] = float(form_data.get('reputation_reward', 0) or 0)
        form_data['token_reward'] = float(form_data.get('token_reward', 0) or 0)
        form_data['xp_reward'] = int(form_data.get('xp_reward', 0) or 0)
        form_data['required_discord_messages'] = int(form_data.get('required_discord_messages', 0) or 0)
        form_data['required_discord_voice_minutes'] = int(form_data.get('required_discord_voice_minutes', 0) or 0)
        form_data['required_referrals'] = int(form_data.get('required_referrals', 0) or 0)
        form_data['required_daily_login_streak'] = int(form_data.get('required_daily_login_streak', 0) or 0)
        form_data['max_completions'] = int(form_data.get('max_completions', 0) or 0)
        
        # Handle boolean fields
        form_data['is_daily'] = 'is_daily' in request.POST
        form_data['is_recurring'] = 'is_recurring' in request.POST
        form_data['is_active'] = 'is_active' in request.POST
        
        form = QuestForm(form_data)
        if form.is_valid():
            quest = form.save(commit=False)
            quest.created_by = request.user
            quest.save()
            
            messages.success(request, 'Quest created successfully!')
            return redirect('manage_quests')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)
    else:
        form = QuestForm()
    
    context = {
        'form': form,
        'editing': False,
    }
    return render(request, 'quests/manage_quests.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def edit_quest(request, quest_id):
    """Edit an existing quest"""
    quest = get_object_or_404(Quest, id=quest_id)
    
    if request.method == 'POST':
        form_data = request.POST.copy()
        
        # Convert string fields to appropriate values
        form_data['reputation_reward'] = float(form_data.get('reputation_reward', 0) or 0)
        form_data['token_reward'] = float(form_data.get('token_reward', 0) or 0)
        form_data['xp_reward'] = int(form_data.get('xp_reward', 0) or 0)
        form_data['required_discord_messages'] = int(form_data.get('required_discord_messages', 0) or 0)
        form_data['required_discord_voice_minutes'] = int(form_data.get('required_discord_voice_minutes', 0) or 0)
        form_data['required_referrals'] = int(form_data.get('required_referrals', 0) or 0)
        form_data['required_daily_login_streak'] = int(form_data.get('required_daily_login_streak', 0) or 0)
        form_data['max_completions'] = int(form_data.get('max_completions', 0) or 0)
        
        # Handle boolean fields
        form_data['is_daily'] = 'is_daily' in request.POST
        form_data['is_recurring'] = 'is_recurring' in request.POST
        form_data['is_active'] = 'is_active' in request.POST
        
        form = QuestForm(form_data, instance=quest)
        if form.is_valid():
            quest = form.save(commit=False)
            quest.save()
            
            messages.success(request, 'Quest updated successfully!')
            return redirect('manage_quests')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestForm(instance=quest)
    
    context = {
        'form': form,
        'quest': quest,
        'editing': True,
        'quest_id': quest_id,
        'quests': Quest.objects.all().order_by('-created_at'),
    }
    return render(request, 'quests/manage_quests.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def delete_quest(request, quest_id):
    """Delete a quest"""
    quest = get_object_or_404(Quest, id=quest_id)
    quest_title = quest.title
    
    try:
        quest.delete()
        messages.success(request, f'Quest "{quest_title}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting quest: {str(e)}')
    
    return redirect('manage_quests')