# crownie/management/commands/check_discord.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check which users have Discord connected'
    
    def handle(self, *args, **options):
        total_users = User.objects.count()
        connected_users = User.objects.filter(discord_connected=True).count()
        not_connected = User.objects.filter(discord_connected=False).count()
        
        self.stdout.write(f"Total Users: {total_users}")
        self.stdout.write(f"Discord Connected: {connected_users} ({connected_users/total_users*100:.1f}%)")
        self.stdout.write(f"Not Connected: {not_connected}")
        
        if not_connected > 0:
            self.stdout.write("\nUsers without Discord connection:")
            for user in User.objects.filter(discord_connected=False):
                self.stdout.write(f"  - {user.username} ({user.email})")