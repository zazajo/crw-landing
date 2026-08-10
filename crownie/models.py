from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json
from datetime import timedelta
import secrets
import string

class User(AbstractUser):
    # Required fields
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100, default='')
    
    # Discord integration fields
    discord_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    discord_username = models.CharField(max_length=100, blank=True, null=True)
    discord_connected = models.BooleanField(default=False)
    discord_connected_at = models.DateTimeField(blank=True, null=True)
    
    # Discord chat tracking fields
    discord_chat_points = models.FloatField(default=0)
    discord_total_messages = models.IntegerField(default=0)
    discord_last_activity = models.DateTimeField(blank=True, null=True)
    
    # Chat tracking
    last_chat_session = models.DateTimeField(blank=True, null=True)
    chat_sessions_count = models.IntegerField(default=0)
    total_chat_minutes = models.IntegerField(default=0)
    
    # Store JSON data as TextField for SQLite
    discord_roles = models.TextField(default='[]', blank=True)  # Store as JSON string
    
    # Reputation system
    reputation_score = models.FloatField(default=0)
    REPUTATION_TIERS = [
        ('novice', 'Novice 🌱'),
        ('active', 'Active 🔥'),
        ('trusted', 'Trusted ✅'),
        ('elite', 'Elite ⭐'),
        ('legend', 'Legend 🏆'),
    ]
    reputation_tier = models.CharField(max_length=20, choices=REPUTATION_TIERS, default='novice')
    
    # Engagement tracking
    total_engagements = models.IntegerField(default=0)
    chat_messages = models.IntegerField(default=0)
    quests_completed = models.IntegerField(default=0)
    
    # Earnings
    total_earned = models.FloatField(default=0)
    
    # === REFERRAL SYSTEM FIELDS ===
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    referral_count = models.IntegerField(default=0)
    referral_points_earned = models.IntegerField(default=0)
    
    # === LOGIN STREAK ENHANCEMENTS ===
    last_login_date = models.DateField(null=True, blank=True)
    current_login_streak = models.IntegerField(default=0)
    longest_login_streak = models.IntegerField(default=0)
    
    # Profile fields
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        # Generate referral code on first save if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        # Calculate tier before saving
        self.reputation_tier = self.calculate_tier()
        super().save(*args, **kwargs)
    
    def calculate_tier(self):
        if self.reputation_score >= 1000:
            return 'legend'
        elif self.reputation_score >= 500:
            return 'elite'
        elif self.reputation_score >= 200:
            return 'trusted'
        elif self.reputation_score >= 50:
            return 'active'
        return 'novice'
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not User.objects.filter(referral_code=code).exists():
                return code
    
    def get_referral_url(self):
        """Get full referral URL"""
        return f"https://www.crownieverse.xyz/signup/?ref={self.referral_code}"
    
    def get_short_referral_link(self):
        """Get short referral link for display"""
        return f"crownie.xyz/ref/{self.referral_code}"
    
    def update_login_streak(self):
        """Update login streak when user logs in"""
        today = timezone.now().date()
        
        if not self.last_login_date:
            # First login
            self.current_login_streak = 1
            self.longest_login_streak = 1
        elif self.last_login_date == today:
            # Already logged in today
            return False
        elif self.last_login_date == today - timedelta(days=1):
            # Consecutive login
            self.current_login_streak += 1
        else:
            # Streak broken
            self.current_login_streak = 1
        
        # Update longest streak
        if self.current_login_streak > self.longest_login_streak:
            self.longest_login_streak = self.current_login_streak
        
        self.last_login_date = today
        self.save()
        
        return True
    
    def add_referral(self, referred_user):
        """Add a referral and award points"""
        self.referral_count += 1
        self.referral_points_earned += 25
        self.reputation_score += 25
        self.save()
        
        # Create reputation log
        from .models import ReputationLog
        ReputationLog.objects.create(
            user=self,
            action='referral',
            points=25,
            metadata={'referred_user': referred_user.username}
        )
    
    def get_discord_display_name(self):
        """Get formatted Discord display name"""
        if self.discord_username:
            return self.discord_username
        return "Not Connected"
    
    def get_discord_roles_list(self):
        """Get Discord roles as Python list"""
        try:
            return json.loads(self.discord_roles)
        except:
            return []
    
    def set_discord_roles(self, roles_list):
        """Set Discord roles from Python list"""
        self.discord_roles = json.dumps(roles_list)
    
    def get_total_chat_points(self):
        """Get total chat points"""
        return self.discord_chat_points
    
    def update_discord_stats(self, points=0, messages=0):
        """Update Discord statistics"""
        self.discord_chat_points += points
        self.discord_total_messages += messages
        self.discord_last_activity = timezone.now()
        self.reputation_score += points
        self.save()


class DiscordChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=100, unique=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.IntegerField(default=0)
    message_count = models.IntegerField(default=0)
    points_earned = models.FloatField(default=0)
    channel_id = models.CharField(max_length=100)
    channel_name = models.CharField(max_length=100)
    
    # Store JSON data as TextField for SQLite
    metadata = models.TextField(default='{}', blank=True)  # Store as JSON string
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.start_time}"
    
    def get_metadata_dict(self):
        """Get metadata as Python dictionary"""
        try:
            return json.loads(self.metadata)
        except:
            return {}
    
    def set_metadata(self, metadata_dict):
        """Set metadata from Python dictionary"""
        self.metadata = json.dumps(metadata_dict)
    
    def calculate_points(self):
        """Calculate points based on session activity"""
        base_points = self.message_count * 0.5
        duration_bonus = min(self.duration_minutes * 0.2, 5)
        return min(base_points + duration_bonus, 15)


class Quest(models.Model):
    """Represents a quest that users can complete"""
    QUEST_TYPES = [
        ('social', 'Social Engagement'),
        ('discord', 'Discord Activity'),
        ('content', 'Content Creation'),
        ('referral', 'Referral'),
        ('daily', 'Daily Challenge'),
        ('special', 'Special Event'),
    ]
    
    QUEST_DIFFICULTY = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('epic', 'Epic'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    quest_type = models.CharField(max_length=20, choices=QUEST_TYPES)
    difficulty = models.CharField(max_length=20, choices=QUEST_DIFFICULTY)
    
    # Requirements
    required_discord_messages = models.IntegerField(default=0)
    required_discord_voice_minutes = models.IntegerField(default=0)
    required_twitter_follow = models.BooleanField(default=False)
    required_twitter_like = models.BooleanField(default=False)
    required_twitter_retweet = models.BooleanField(default=False)
    required_referrals = models.IntegerField(default=0)
    required_daily_login_streak = models.IntegerField(default=0)
    
    # Rewards
    reputation_reward = models.IntegerField(default=0)
    token_reward = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    badge_reward = models.CharField(max_length=100, blank=True, null=True)
    xp_reward = models.IntegerField(default=0)
    
    # Quest details
    is_daily = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    recurrence_days = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    max_completions = models.IntegerField(default=0)  # 0 = unlimited
    current_completions = models.IntegerField(default=0)
    
    # Add created_at for ordering
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Store requirements as JSON
    custom_requirements = models.TextField(default='{}', blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.difficulty})"
    
    def get_custom_requirements(self):
        """Get custom requirements as Python dictionary"""
        try:
            return json.loads(self.custom_requirements)
        except:
            return {}
    
    def set_custom_requirements(self, requirements_dict):
        """Set custom requirements from Python dictionary"""
        self.custom_requirements = json.dumps(requirements_dict)


class UserQuestProgress(models.Model):
    """Tracks user progress on quests"""
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('claimed', 'Claimed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_progress')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Progress tracking
    discord_messages_count = models.IntegerField(default=0)
    discord_voice_minutes = models.IntegerField(default=0)
    twitter_followed = models.BooleanField(default=False)
    twitter_liked = models.BooleanField(default=False)
    twitter_retweeted = models.BooleanField(default=False)
    referrals_count = models.IntegerField(default=0)
    daily_login_streak = models.IntegerField(default=0)
    
    # Custom progress tracking
    custom_progress = models.TextField(default='{}', blank=True)
    
    # Dates
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    claimed_at = models.DateTimeField(blank=True, null=True)
    
    # Rewards claimed
    reputation_claimed = models.BooleanField(default=False)
    tokens_claimed = models.BooleanField(default=False)
    badge_claimed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'quest']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quest.title} ({self.status})"
    
    def get_custom_progress(self):
        """Get custom progress as Python dictionary"""
        try:
            return json.loads(self.custom_progress)
        except:
            return {}
    
    def set_custom_progress(self, progress_dict):
        """Set custom progress from Python dictionary"""
        self.custom_progress = json.dumps(progress_dict)
    
    def calculate_completion_percentage(self):
        """Calculate quest completion percentage"""
        total_requirements = 0
        completed_requirements = 0
        
        quest = self.quest
        
        # Discord messages
        if quest.required_discord_messages > 0:
            total_requirements += 1
            if self.discord_messages_count >= quest.required_discord_messages:
                completed_requirements += 1
        
        # Discord voice
        if quest.required_discord_voice_minutes > 0:
            total_requirements += 1
            if self.discord_voice_minutes >= quest.required_discord_voice_minutes:
                completed_requirements += 1
        
        # Twitter follow
        if quest.required_twitter_follow:
            total_requirements += 1
            if self.twitter_followed:
                completed_requirements += 1
        
        # Twitter like
        if quest.required_twitter_like:
            total_requirements += 1
            if self.twitter_liked:
                completed_requirements += 1
        
        # Twitter retweet
        if quest.required_twitter_retweet:
            total_requirements += 1
            if self.twitter_retweeted:
                completed_requirements += 1
        
        # Referrals
        if quest.required_referrals > 0:
            total_requirements += 1
            if self.referrals_count >= quest.required_referrals:
                completed_requirements += 1
        
        # Daily login streak
        if quest.required_daily_login_streak > 0:
            total_requirements += 1
            if self.daily_login_streak >= quest.required_daily_login_streak:
                completed_requirements += 1
        
        if total_requirements == 0:
            return 0
        
        return int((completed_requirements / total_requirements) * 100)
    
    def check_completion(self):
        """Check if quest is completed"""
        quest = self.quest
        
        # Update login streak from user's current streak
        if quest.required_daily_login_streak > 0:
            self.daily_login_streak = self.user.current_login_streak
        
        # Update referrals count from user's referral count
        if quest.required_referrals > 0:
            self.referrals_count = self.user.referral_count
        
        # Save updates
        self.save()
        
        # Check requirements
        if (quest.required_discord_messages > 0 and 
            self.discord_messages_count < quest.required_discord_messages):
            return False
        
        if (quest.required_discord_voice_minutes > 0 and 
            self.discord_voice_minutes < quest.required_discord_voice_minutes):
            return False
        
        if quest.required_twitter_follow and not self.twitter_followed:
            return False
        
        if quest.required_twitter_like and not self.twitter_liked:
            return False
        
        if quest.required_twitter_retweet and not self.twitter_retweeted:
            return False
        
        if quest.required_referrals > 0 and self.referrals_count < quest.required_referrals:
            return False
        
        if quest.required_daily_login_streak > 0 and self.daily_login_streak < quest.required_daily_login_streak:
            return False
        
        return True


class QuestCompletion(models.Model):
    """Record of completed quests"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_completions')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='completions')
    user_quest_progress = models.OneToOneField(UserQuestProgress, on_delete=models.CASCADE)
    
    # Rewards earned
    reputation_earned = models.IntegerField(default=0)
    tokens_earned = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    badge_earned = models.CharField(max_length=100, blank=True, null=True)
    xp_earned = models.IntegerField(default=0)
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} completed {self.quest.title}"


class DailyStreak(models.Model):
    """Track user daily streaks"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='daily_streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_login_date = models.DateField(auto_now=True)
    
    # Weekly tracking for 7-day streaks
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    
    def update_streak(self):
        """Update the streak based on last login"""
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        if self.last_login_date == today:
            # Already logged in today
            return False
        
        if self.last_login_date == yesterday:
            # Consecutive login
            self.current_streak += 1
        else:
            # Streak broken
            self.current_streak = 1
        
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        # Update day of week tracking
        self.mark_day(today.weekday())
        
        self.last_login_date = today
        self.save()
        
        return True
    
    def mark_day(self, weekday):
        """Mark day of week as completed (0=Monday, 6=Sunday)"""
        if weekday == 0:
            self.monday = True
        elif weekday == 1:
            self.tuesday = True
        elif weekday == 2:
            self.wednesday = True
        elif weekday == 3:
            self.thursday = True
        elif weekday == 4:
            self.friday = True
        elif weekday == 5:
            self.saturday = True
        elif weekday == 6:
            self.sunday = True
    
    def get_weekly_progress(self):
        """Get number of days completed this week"""
        days = [self.monday, self.tuesday, self.wednesday, 
                self.thursday, self.friday, self.saturday, self.sunday]
        return sum(days)
    
    def is_weekly_complete(self):
        """Check if all 7 days completed this week"""
        return all([self.monday, self.tuesday, self.wednesday,
                   self.thursday, self.friday, self.saturday, self.sunday])
    
    def __str__(self):
        return f"{self.user.username} - Streak: {self.current_streak}"


class Engagement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagements')
    ENGAGEMENT_TYPES = [
        ('chat', 'Chat'),
        ('post', 'Post'),
        ('like', 'Like'),
        ('share', 'Share'),
        ('comment', 'Comment'),
        ('discord_chat', 'Discord Chat'),
    ]
    type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPES)
    content = models.TextField(blank=True)
    points = models.FloatField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.created_at}"


class ReputationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reputation_logs')
    ACTION_CHOICES = [
        ('signup', 'Sign Up'),
        ('daily_login', 'Daily Login'),
        ('discord_connect', 'Discord Connect'),
        ('discord_chat', 'Discord Chat'),
        ('quest_complete', 'Quest Complete'),
        ('engagement', 'Engagement'),
        ('social_verify', 'Social Verification'),
        ('referral', 'Referral'),  # Added referral action
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    points = models.FloatField()
    
    # Store JSON data as TextField for SQLite
    metadata = models.TextField(default='{}', blank=True)  # Store as JSON string
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.points} points"
    
    def get_metadata_dict(self):
        """Get metadata as Python dictionary"""
        try:
            return json.loads(self.metadata)
        except:
            return {}