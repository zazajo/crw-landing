# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, DiscordChatSession, Quest, UserQuestProgress, 
    QuestCompletion, DailyStreak, Engagement, ReputationLog
)
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin.models import LogEntry


# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'discord_connected', 'reputation_score', 
                    'reputation_tier', 'current_login_streak', 'referral_count', 'date_joined')
    list_filter = ('discord_connected', 'reputation_tier', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'discord_username', 'discord_id', 'referral_code')
    ordering = ('-reputation_score',)
    readonly_fields = ('reputation_tier', 'date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'display_name', 'bio', 'avatar')}),
        ('Discord Integration', {'fields': (
            'discord_id', 'discord_username', 'discord_connected', 
            'discord_connected_at', 'discord_chat_points', 
            'discord_total_messages', 'discord_last_activity', 'discord_roles'
        )}),
        ('Reputation System', {'fields': (
            'reputation_score', 'reputation_tier', 'total_engagements',
            'chat_messages', 'quests_completed', 'total_earned'
        )}),
        ('Referral System', {'fields': (
            'referral_code', 'referred_by', 'referral_count', 'referral_points_earned'
        )}),
        ('Login Streak', {'fields': (
            'last_login_date', 'current_login_streak', 'longest_login_streak'
        )}),
        ('Chat Tracking', {'fields': (
            'last_chat_session', 'chat_sessions_count', 'total_chat_minutes'
        )}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 
                                   'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    def discord_link(self, obj):
        if obj.discord_id:
            return format_html('<a href="https://discord.com/users/{}" target="_blank">@{}</a>', 
                             obj.discord_id, obj.discord_username or obj.discord_id)
        return "Not Connected"
    discord_link.short_description = 'Discord Profile'
    
    def referral_url(self, obj):
        if obj.referral_code:
            url = f"/signup/?ref={obj.referral_code}"
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.referral_code)
        return "No Code"
    referral_url.short_description = 'Referral Link'
    
    def referred_by_link(self, obj):
        if obj.referred_by:
            url = reverse("admin:accounts_user_change", args=[obj.referred_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.referred_by.username)
        return "None"
    referred_by_link.short_description = 'Referred By'


# Discord Chat Session Admin
class DiscordChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'start_time', 'end_time', 
                    'duration_minutes', 'message_count', 'points_earned')
    list_filter = ('start_time', 'channel_name')
    search_fields = ('user__username', 'session_id', 'channel_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Session Info', {'fields': ('user', 'session_id', 'channel_id', 'channel_name')}),
        ('Timing', {'fields': ('start_time', 'end_time', 'duration_minutes')}),
        ('Activity', {'fields': ('message_count', 'points_earned')}),
        ('Metadata', {'fields': ('metadata',)}),
        ('System', {'fields': ('created_at',)}),
    )


# Quest Admin
class QuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'quest_type', 'difficulty', 'reputation_reward', 
                    'is_active', 'is_daily', 'created_at', 'current_completions')
    list_filter = ('quest_type', 'difficulty', 'is_active', 'is_daily', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'current_completions')
    filter_horizontal = ()
    
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'description', 'quest_type', 'difficulty')}),
        ('Requirements', {'fields': (
            'required_discord_messages', 'required_discord_voice_minutes',
            'required_twitter_follow', 'required_twitter_like', 'required_twitter_retweet',
            'required_referrals', 'required_daily_login_streak', 'custom_requirements'
        )}),
        ('Rewards', {'fields': (
            'reputation_reward', 'token_reward', 'badge_reward', 'xp_reward'
        )}),
        ('Settings', {'fields': (
            'is_daily', 'is_recurring', 'recurrence_days', 'is_active',
            'start_date', 'end_date', 'max_completions', 'current_completions'
        )}),
        ('System', {'fields': ('created_at', 'updated_at')}),
    )
    
    def completions_link(self, obj):
        count = obj.completions.count()
        url = reverse("admin:accounts_questcompletion_changelist") + f"?quest__id__exact={obj.id}"
        return format_html('<a href="{}">{} Completions</a>', url, count)
    completions_link.short_description = 'Completions'


# User Quest Progress Admin
class UserQuestProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'status', 'calculate_completion_percentage', 
                    'started_at', 'completed_at')
    list_filter = ('status', 'quest__quest_type', 'quest__difficulty', 'started_at')
    search_fields = ('user__username', 'quest__title')
    readonly_fields = ('started_at', 'updated_at', 'completed_at', 'claimed_at')
    
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'quest', 'status')}),
        ('Progress Tracking', {'fields': (
            'discord_messages_count', 'discord_voice_minutes',
            'twitter_followed', 'twitter_liked', 'twitter_retweeted',
            'referrals_count', 'daily_login_streak', 'custom_progress'
        )}),
        ('Reward Claims', {'fields': (
            'reputation_claimed', 'tokens_claimed', 'badge_claimed'
        )}),
        ('Dates', {'fields': ('started_at', 'updated_at', 'completed_at', 'claimed_at')}),
    )
    
    def completion_percentage(self, obj):
        return f"{obj.calculate_completion_percentage()}%"
    completion_percentage.short_description = 'Completion %'


# Quest Completion Admin
class QuestCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'reputation_earned', 'tokens_earned', 'completed_at')
    list_filter = ('completed_at', 'quest__quest_type')
    search_fields = ('user__username', 'quest__title')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'completed_at'
    
    fieldsets = (
        ('Completion Info', {'fields': ('user', 'quest', 'user_quest_progress')}),
        ('Rewards Earned', {'fields': (
            'reputation_earned', 'tokens_earned', 'badge_earned', 'xp_earned'
        )}),
        ('System', {'fields': ('completed_at',)}),
    )


# Daily Streak Admin
class DailyStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'last_login_date', 
                    'get_weekly_progress')
    list_filter = ('last_login_date',)
    search_fields = ('user__username',)
    readonly_fields = ('last_login_date',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Streak Info', {'fields': ('current_streak', 'longest_streak', 'last_login_date')}),
        ('Weekly Tracking', {'fields': (
            'monday', 'tuesday', 'wednesday', 'thursday', 
            'friday', 'saturday', 'sunday'
        )}),
    )
    
    def weekly_progress(self, obj):
        progress = obj.get_weekly_progress()
        return f"{progress}/7 days"
    weekly_progress.short_description = 'Weekly Progress'


# Engagement Admin
class EngagementAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'points', 'verified', 'created_at')
    list_filter = ('type', 'verified', 'created_at')
    search_fields = ('user__username', 'content')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Engagement Info', {'fields': ('user', 'type', 'content', 'points', 'verified')}),
        ('System', {'fields': ('created_at',)}),
    )


# Reputation Log Admin
class ReputationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'points', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'metadata')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Info', {'fields': ('user', 'action', 'points', 'metadata')}),
        ('System', {'fields': ('created_at',)}),
    )
    
    def metadata_preview(self, obj):
        metadata = obj.get_metadata_dict()
        if metadata:
            return str(metadata)[:100] + "..." if len(str(metadata)) > 100 else str(metadata)
        return "No metadata"
    metadata_preview.short_description = 'Metadata'


# Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(DiscordChatSession, DiscordChatSessionAdmin)
admin.site.register(Quest, QuestAdmin)
admin.site.register(UserQuestProgress, UserQuestProgressAdmin)
admin.site.register(QuestCompletion, QuestCompletionAdmin)
admin.site.register(DailyStreak, DailyStreakAdmin)
admin.site.register(Engagement, EngagementAdmin)
admin.site.register(ReputationLog, ReputationLogAdmin)

# Optional: Register LogEntry for tracking admin actions
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time', 'user', 'content_type', 'object_id', 
                      'object_repr', 'action_flag', 'change_message')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False