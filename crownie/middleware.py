# crownie/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
import re

class DiscordConnectionRequiredMiddleware:
    """Middleware to ensure users have connected Discord"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that don't require Discord connection
        self.exempt_urls = [
            '/',
            '/login/',
            '/logout/',
            '/signup/',
            '/discord/connect/',
            '/discord/callback/',
            '/discord/disconnect/',
            '/admin/',
        ]
    
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if user is trying to access a protected URL
            if not any(request.path.startswith(url) for url in self.exempt_urls):
                # Check if Discord is connected
                if not hasattr(request.user, 'discord_connected') or not request.user.discord_connected:
                    # If not connected, redirect to Discord connection
                    # But only if not already on connection page
                    if request.path != reverse('discord_connect'):
                        from django.contrib import messages
                        messages.warning(request, 'Please connect your Discord account to access this page')
                        return redirect('discord_connect')
        
        response = self.get_response(request)
        return response