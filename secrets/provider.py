# rtcollector/secrets/provider.py

class SecretProvider:
    """Base class for secret providers"""
    
    def get_secret(self, secret_id):
        """
        Retrieve a secret by ID
        
        Args:
            secret_id (str): The identifier for the secret
            
        Returns:
            str: The secret value or None if not found
        """
        raise NotImplementedError("Secret providers must implement get_secret method")
    
    def process_config(self, config):
        """
        Process a configuration dictionary and replace secret references
        
        Args:
            config (dict): Configuration dictionary to process
            
        Returns:
            dict: Processed configuration with secrets resolved
        """
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith("secret:"):
                    secret_id = value.split(":", 1)[1]
                    secret_value = self.get_secret(secret_id)
                    if secret_value is not None:
                        config[key] = secret_value
                elif isinstance(value, (dict, list)):
                    self.process_config(value)
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, (dict, list)):
                    self.process_config(item)
                elif isinstance(item, str) and item.startswith("secret:"):
                    secret_id = item.split(":", 1)[1]
                    secret_value = self.get_secret(secret_id)
                    if secret_value is not None:
                        config[i] = secret_value
        
        return config