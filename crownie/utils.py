# crownie/utils.py
from datetime import datetime, timedelta
from django.db.models import Sum
from .models import User, ReputationLog

REPUTATION_CONFIG = {
    'signup': {'points': 10, 'daily_limit': None, 'cooldown': None},
    'daily_login': {'points': 5, 'daily_limit': 1, 'cooldown': 1440},  # 24 hours
    'chat_message': {'points': 1, 'daily_limit': 50, 'cooldown': 1},
    'quest_complete': {'points': 25, 'daily_limit': None, 'cooldown': None},
    'referral': {'points': 50, 'daily_limit': None, 'cooldown': None},
    'social_verify': {'points': 30, 'daily_limit': None, 'cooldown': None},
    'content_create': {'points': 15, 'daily_limit': 10, 'cooldown': 60},
    'engagement': {'points': 2, 'daily_limit': 100, 'cooldown': 5},
    'battle_win': {'points': 20, 'daily_limit': None, 'cooldown': None},
}

def award_reputation(user, action, metadata=None):
    config = REPUTATION_CONFIG.get(action)
    if not config:
        return 0
    
    # Check cooldown
    if config.get('cooldown'):
        cooldown_time = datetime.now() - timedelta(minutes=config['cooldown'])
        last_action = ReputationLog.objects.filter(
            user=user,
            action=action,
            created_at__gte=cooldown_time
        ).first()
        if last_action:
            return 0
    
    # Check daily limit
    if config.get('daily_limit'):
        today = datetime.now().date()
        today_count = ReputationLog.objects.filter(
            user=user,
            action=action,
            created_at__date=today
        ).count()
        if today_count >= config['daily_limit']:
            return 0
    
    # Create reputation log
    log = ReputationLog.objects.create(
        user=user,
        action=action,
        points=config['points'],
        metadata=metadata or {}
    )
    
    # Update user reputation
    user.reputation_score += config['points']
    user.reputation_tier = user.calculate_tier()
    
    # Update counters based on action
    if action == 'chat_message':
        user.chat_messages += 1
    elif action == 'quest_complete':
        user.quests_completed += 1
    elif action == 'engagement':
        user.total_engagements += 1
    
    user.save()
    return config['points']

def get_user_rank(user):
    # Get user's rank based on reputation score
    users_with_higher_score = User.objects.filter(
        reputation_score__gt=user.reputation_score
    ).count()
    return users_with_higher_score + 1

def calculate_daily_streak(user):
    logs = ReputationLog.objects.filter(
        user=user,
        action='daily_login'
    ).order_by('-created_at')[:30]  # Last 30 days
    
    streak = 0
    last_date = datetime.now().date()
    
    for log in logs:
        log_date = log.created_at.date()
        
        if streak == 0 and log_date == last_date:
            streak = 1
            last_date = log_date
        elif (last_date - log_date).days == 1:
            streak += 1
            last_date = log_date
        else:
            break
    
    return streak