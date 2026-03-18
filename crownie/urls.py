# crownie/urls.py
from django.urls import path
from .views import (
    home_view, signup_view, login_view, logout_view, dashboard_view,
    discord_connect, discord_callback, discord_disconnect, 
    discord_activity_webhook, get_user_chat_stats,
    quests_view, start_quest, claim_quest_reward, daily_login_reward,
    manage_quests, create_quest, edit_quest, delete_quest, whitepaper_view, roadmap_view
)

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('whitepaper/', whitepaper_view, name='whitepaper'),
    path('roadmap/', roadmap_view, name='roadmap'),


    
    # Discord OAuth
    path('discord/connect/', discord_connect, name='discord_connect'),
    path('discord/callback/', discord_callback, name='discord_callback'),
    path('discord/disconnect/', discord_disconnect, name='discord_disconnect'),
    path('api/discord/activity/', discord_activity_webhook, name='discord_activity'),
    path('api/chat/stats/', get_user_chat_stats, name='chat_stats'),
    
    # Quest URLs
    path('quests/', quests_view, name='quests'),
    path('quests/start/<int:quest_id>/', start_quest, name='start_quest'),
    path('quests/claim/<int:progress_id>/', claim_quest_reward, name='claim_quest_reward'),
    path('quests/daily-reward/', daily_login_reward, name='daily_login_reward'),
    
    # Admin URLs (Quest Management)
    path('quests/manage/', manage_quests, name='manage_quests'),
    path('quests/create/', create_quest, name='create_quest'),
    path('quests/edit/<int:quest_id>/', edit_quest, name='edit_quest'),
    path('quests/delete/<int:quest_id>/', delete_quest, name='delete_quest'),
]