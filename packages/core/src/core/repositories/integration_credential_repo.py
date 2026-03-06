"""Repository for managing integration credentials."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.db.models import IntegrationCredential
from core.security.encryption import EncryptionService


class IntegrationCredentialRepository:
    """Repository for integration credential operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption = EncryptionService()
    
    def create(
        self,
        credential_id: str,
        integration_type: str,
        display_name: str,
        token: str,
        meta: dict | None = None,
        status: str = "valid"
    ) -> IntegrationCredential:
        """
        Create a new integration credential with encrypted token.
        
        Args:
            credential_id: Unique credential ID
            integration_type: Type of integration (telegram, slack, etc.)
            display_name: Human-readable name
            token: Plaintext token to encrypt
            meta: Additional metadata
            status: Credential status
            
        Returns:
            Created IntegrationCredential
        """
        ciphertext = self.encryption.encrypt(token)
        
        credential = IntegrationCredential(
            id=credential_id,
            integration_type=integration_type,
            display_name=display_name,
            ciphertext=ciphertext,
            status=status,
            meta=meta or {}
        )
        
        self.db.add(credential)
        self.db.commit()
        self.db.refresh(credential)
        
        return credential
    
    def get_by_id(self, credential_id: str) -> IntegrationCredential | None:
        """
        Get credential by ID (does not decrypt token).
        
        Args:
            credential_id: Credential ID
            
        Returns:
            IntegrationCredential or None
        """
        return self.db.get(IntegrationCredential, credential_id)
    
    def list_by_type(self, integration_type: str | None = None) -> list[IntegrationCredential]:
        """
        List credentials, optionally filtered by type.
        
        Args:
            integration_type: Optional filter by integration type
            
        Returns:
            List of IntegrationCredential
        """
        query = select(IntegrationCredential)
        
        if integration_type:
            query = query.where(IntegrationCredential.integration_type == integration_type)
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def get_decrypted_token(self, credential_id: str) -> str | None:
        """
        Get decrypted token for a credential (internal use only).
        
        Args:
            credential_id: Credential ID
            
        Returns:
            Decrypted token or None
        """
        credential = self.get_by_id(credential_id)
        if not credential:
            return None
        
        return self.encryption.decrypt(credential.ciphertext)
    
    def update_token(self, credential_id: str, new_token: str) -> IntegrationCredential | None:
        """
        Rotate credential token.
        
        Args:
            credential_id: Credential ID
            new_token: New plaintext token
            
        Returns:
            Updated IntegrationCredential or None
        """
        credential = self.get_by_id(credential_id)
        if not credential:
            return None
        
        credential.ciphertext = self.encryption.encrypt(new_token)
        credential.status = "valid"
        
        self.db.commit()
        self.db.refresh(credential)
        
        return credential
    
    def update_status(self, credential_id: str, status: str) -> IntegrationCredential | None:
        """
        Update credential status.
        
        Args:
            credential_id: Credential ID
            status: New status (valid, invalid, pending)
            
        Returns:
            Updated IntegrationCredential or None
        """
        credential = self.get_by_id(credential_id)
        if not credential:
            return None
        
        credential.status = status
        
        self.db.commit()
        self.db.refresh(credential)
        
        return credential
    
    def delete(self, credential_id: str) -> bool:
        """
        Delete a credential.
        
        Args:
            credential_id: Credential ID
            
        Returns:
            True if deleted, False if not found
        """
        credential = self.get_by_id(credential_id)
        if not credential:
            return False
        
        self.db.delete(credential)
        self.db.commit()
        
        return True
