# management/commands/run_chat_bot.py
from django.core.management.base import BaseCommand
import threading
from crownie.discord_bot import run_bot

class Command(BaseCommand):
    help = 'Run the Discord chat bot'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Discord chat bot...'))
        run_bot()