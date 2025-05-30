# rtcollector/secrets/env_provider.py
import os
from .provider import SecretProvider

class EnvSecretProvider(SecretProvider):
    """Secret provider that uses environment variables"""
    
    def __init__(self, prefix="SECRET_"):
        """
        Initialize the environment variable secret provider
        
        Args:
            prefix (str): Prefix for environment variables
        """
        self.prefix = prefix
    
    def get_secret(self, secret_id):
        """
        Get a secret from environment variables
        
        Args:
            secret_id (str): Secret identifier
            
        Returns:
            str: Secret value or None if not found
        """
        # Convert secret_id to uppercase and replace / with _
        env_var = self.prefix + secret_id.upper().replace("/", "_").replace("-", "_")
        return os.environ.get(env_var)