# rtcollector/secrets/vault_provider.py
import os
from .provider import SecretProvider

class VaultSecretProvider(SecretProvider):
    """Secret provider that uses HashiCorp Vault"""
    
    def __init__(self, url=None, token=None, path_prefix="rtcollector"):
        """
        Initialize the Vault secret provider
        
        Args:
            url (str): Vault server URL
            token (str): Vault authentication token
            path_prefix (str): Path prefix for secrets in Vault
        """
        self.url = url or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.environ.get("VAULT_TOKEN")
        self.path_prefix = path_prefix
        self.client = None
        
        # Import hvac here to make it an optional dependency
        try:
            import hvac
            self.client = hvac.Client(url=self.url, token=self.token)
            if not self.client.is_authenticated():
                print(f"[Vault] Warning: Not authenticated to Vault at {self.url}")
                self.client = None
        except ImportError:
            print("[Vault] Warning: hvac package not installed. Please install with: pip install hvac")
    
    def get_secret(self, secret_id):
        """
        Get a secret from Vault
        
        Args:
            secret_id (str): Secret identifier
            
        Returns:
            str: Secret value or None if not found
        """
        if not self.client:
            return None
            
        try:
            # For KV v2 (default in newer Vault versions)
            secret_path = f"{self.path_prefix}/{secret_id}"
            response = self.client.secrets.kv.v2.read_secret_version(path=secret_path)
            return response["data"]["data"]["value"]
        except Exception as e:
            # Try KV v1 as fallback
            try:
                secret_path = f"{self.path_prefix}/{secret_id}"
                response = self.client.secrets.kv.v1.read_secret(path=secret_path)
                return response["data"]["value"]
            except Exception as e2:
                print(f"[Vault] Error retrieving secret {secret_id}: {e2}")
                return None