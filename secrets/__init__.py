# rtcollector/secrets/__init__.py
from .provider import SecretProvider
from .env_provider import EnvSecretProvider
from .vault_provider import VaultSecretProvider

def get_secret_provider(config):
    """Create a secret provider based on configuration"""
    secret_store = config.get("secret_store", {})
    provider_type = secret_store.get("type", "env")
    
    if provider_type == "vault":
        return VaultSecretProvider(
            url=secret_store.get("url"),
            token=secret_store.get("token"),
            path_prefix=secret_store.get("path_prefix", "rtcollector")
        )
    else:
        # Default to environment variables
        return EnvSecretProvider(prefix=secret_store.get("prefix", "SECRET_"))