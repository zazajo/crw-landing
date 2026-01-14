# crownie/management/commands/run_welcome_bot.py
from django.core.management.base import BaseCommand
from crownie.discord_bot import run_welcome_bot

class Command(BaseCommand):
    help = 'Run the Discord welcome bot'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Discord welcome bot...'))
        run_welcome_bot()