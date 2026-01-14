# create_initial_quests.py (place in project root, not crownie app)
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/mac/crw-landing')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crwn.settings')

django.setup()

from crownie.models import Quest, User
from django.contrib.auth.models import User as AuthUser

initial_quests = [
    {
        'title': 'Welcome to the Kingdom',
        'description': 'Connect your Discord account to start your journey in the Crownie kingdom.',
        'quest_type': 'social',
        'difficulty': 'easy',
        'required_discord_messages': 0,
        'reputation_reward': 25,
        'is_active': True,
    },
    {
        'title': 'First Message',
        'description': 'Send your first message in the Crownie Discord server.',
        'quest_type': 'discord',
        'difficulty': 'easy',
        'required_discord_messages': 1,
        'reputation_reward': 10,
        'is_active': True,
    },
    {
        'title': 'Daily Chatter',
        'description': 'Send 10 messages in the Discord server today.',
        'quest_type': 'discord',
        'difficulty': 'medium',
        'required_discord_messages': 10,
        'reputation_reward': 25,
        'is_daily': True,
        'is_active': True,
    },
    {
        'title': 'Voice Champion',
        'description': 'Spend 30 minutes in Discord voice channels.',
        'quest_type': 'discord',
        'difficulty': 'hard',
        'required_discord_voice_minutes': 30,
        'reputation_reward': 50,
        'is_active': True,
    },
    {
        'title': 'Follow the Crown',
        'description': 'Follow Crownie on Twitter/X to stay updated.',
        'quest_type': 'social',
        'difficulty': 'easy',
        'required_twitter_follow': True,
        'reputation_reward': 15,
        'is_active': True,
    },
    {
        'title': 'Recruit Knights',
        'description': 'Refer 3 friends to join the kingdom.',
        'quest_type': 'referral',
        'difficulty': 'hard',
        'required_referrals': 3,
        'reputation_reward': 100,
        'is_active': True,
    },
    {
        'title': '7-Day Streak',
        'description': 'Log in for 7 consecutive days.',
        'quest_type': 'daily',
        'difficulty': 'medium',
        'required_daily_login_streak': 7,
        'reputation_reward': 50,
        'is_active': True,
    },
]

def create_initial_quests():
    created_count = 0
    
    # Get or create a superuser to be the quest creator
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            # Create an admin user if none exists
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@crownie.com',
                password='admin123',
                display_name='Admin'
            )
            print("Created admin user")
    except Exception as e:
        print(f"Error getting admin user: {e}")
        admin_user = None
    
    for quest_data in initial_quests:
        # Check if quest already exists
        if Quest.objects.filter(title=quest_data['title']).exists():
            print(f"Quest already exists: {quest_data['title']}")
            continue
            
        try:
            # Create the quest
            quest = Quest.objects.create(**quest_data)
            created_count += 1
            print(f"✓ Created quest: {quest.title}")
        except Exception as e:
            print(f"✗ Error creating quest '{quest_data['title']}': {e}")
    
    print(f"\n{'='*50}")
    print(f"Created {created_count} initial quests.")
    total_quests = Quest.objects.count()
    print(f"Total quests in database: {total_quests}")
    print(f"{'='*50}")

if __name__ == '__main__':
    create_initial_quests()