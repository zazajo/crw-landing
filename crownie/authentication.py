from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
import time
import secrets

User = get_user_model()

class SolanaWalletAuthentication(BaseAuthentication):
    """
    Solana wallet authentication with challenge generation and cache-based tokens.
    """
    
    def generate_challenge(self, wallet_address):
        """Generate a unique challenge message for the wallet to sign"""
        timestamp = int(time.time())
        nonce = secrets.token_hex(16)
        
        challenge_message = f"""CROWNIE Authentication Request

Wallet: {wallet_address}
Nonce: {nonce}
Timestamp: {timestamp}

Sign this message to verify you own this wallet.

This request will not trigger a blockchain transaction or cost any fees."""
        
        # Store challenge in cache for 5 minutes
        cache_key = f'wallet_challenge_{wallet_address}'
        cache.set(cache_key, {
            'challenge': challenge_message,
            'nonce': nonce,
            'timestamp': timestamp,
            'wallet_address': wallet_address
        }, timeout=300)
        
        return challenge_message
    
    def verify_signature(self, wallet_address, signature_bytes, message):
        """Verify the signature - DEVELOPMENT MODE: Accepts all valid-looking signatures"""
        try:
            # Get stored challenge
            cache_key = f'wallet_challenge_{wallet_address}'
            stored_challenge = cache.get(cache_key)
            
            if not stored_challenge:
                print(f"No stored challenge for {wallet_address[:10]}...")
                return False
            
            # Verify message matches stored challenge
            if message != stored_challenge['challenge']:
                print(f"Message mismatch for {wallet_address[:10]}...")
                return False
            
            # Convert signature if needed
            if isinstance(signature_bytes, list):
                signature_bytes = bytes(signature_bytes)
            
            # Development mode: Accept any signature that's 64 bytes (Ed25519 length)
            if len(signature_bytes) == 64:
                print(f"Development mode: Accepting signature for {wallet_address[:10]}...")
                return True
            else:
                print(f"Invalid signature length: {len(signature_bytes)} for {wallet_address[:10]}...")
                return False
                
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    def authenticate(self, request):
        # Get wallet address and token from headers
        wallet_address = request.headers.get('X-Wallet-Address')
        auth_header = request.headers.get('Authorization')
        
        if not wallet_address:
            return None
        
        # Normal authentication with token
        if not auth_header:
            raise AuthenticationFailed('Authorization header required')
        
        # Extract token
        if auth_header.startswith('Wallet '):
            auth_token = auth_header[7:]
        elif auth_header.startswith('Bearer '):
            auth_token = auth_header[7:]
        else:
            auth_token = auth_header
        
        # Verify token from cache
        cache_key = f'auth_token_{auth_token}'
        token_data = cache.get(cache_key)
        
        if not token_data:
            raise AuthenticationFailed('Invalid or expired token')
        
        # Verify wallet address matches
        if token_data['wallet_address'] != wallet_address:
            raise AuthenticationFailed('Wallet address mismatch')
        
        try:
            # Get user
            user = User.objects.get(wallet_address=wallet_address)
            
            # Update last active timestamp
            user.last_active_at = timezone.now()
            user.save(update_fields=['last_active_at'])
            
            return (user, None)
            
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        return 'Wallet realm="api"'