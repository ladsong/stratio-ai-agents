"""Encryption service for sensitive data."""
import os
from cryptography.fernet import Fernet


class EncryptionService:
    """Service for encrypting/decrypting sensitive credentials."""
    
    def __init__(self):
        """Initialize encryption service with key from environment."""
        key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Key is already a string from environment, encode to bytes for Fernet
        self.cipher = Fernet(key.encode('utf-8'))
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and return base64 ciphertext.
        
        Args:
            plaintext: The plaintext string to encrypt
            
        Returns:
            Base64-encoded ciphertext string
        """
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64 ciphertext and return plaintext.
        
        Args:
            ciphertext: Base64-encoded ciphertext string
            
        Returns:
            Decrypted plaintext string
        """
        return self.cipher.decrypt(ciphertext.encode()).decode()
