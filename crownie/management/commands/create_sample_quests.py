# management/commands/create_sample_quests.py
from django.core.management.base import BaseCommand
from crownie.models import Quest
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample quests'
    
    def handle(self, *args, **options):
        quests = [
            {
                'title': 'Daily Login Streak',
                'description': 'Login for 7 consecutive days',
                'difficulty': 'easy',
                'points': 10,
                'requirements': {'days_required': 7}
            },
            {
                'title': 'Discord Engagement',
                'description': 'Participate in 5 chat sessions',
                'difficulty': 'medium',
                'points': 25,
                'requirements': {'sessions_required': 5}
            },
            {
                'title': 'Twitter Verification',
                'description': 'Connect and verify your Twitter account',
                'difficulty': 'easy',
                'points': 15,
                'requirements': {'platform': 'twitter'}
            },
            {
                'title': 'Community Leader',
                'description': 'Reach 100 reputation points',
                'difficulty': 'hard',
                'points': 50,
                'requirements': {'reputation_required': 100}
            },
        ]
        
        for quest_data in quests:
            quest, created = Quest.objects.get_or_create(
                title=quest_data['title'],
                defaults={
                    'description': quest_data['description'],
                    'difficulty': quest_data['difficulty'],
                    'points': quest_data['points'],
                    'requirements': quest_data['requirements']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created quest: {quest.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Quest already exists: {quest.title}'))