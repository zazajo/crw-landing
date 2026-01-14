# crownie/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Quest, Engagement, ReputationLog, Referral

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'email', 'reputation_score', 
                 'reputation_tier', 'quests_completed', 'chat_messages', 
                 'total_earned', 'date_joined', 'last_active_at']
        read_only_fields = ['reputation_score', 'reputation_tier', 'date_joined', 'last_active_at']

class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = '__all__'

class EngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engagement
        fields = '__all__'
        read_only_fields = ['user', 'verified', 'created_at']

class ReputationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReputationLog
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']