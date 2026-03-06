from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, joinedload

from core.db.models import User, UserContact


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: str,
        name: str,
        role: str = "user",
        system_prompt: Optional[str] = None,
        meta: Optional[dict] = None,
    ) -> User:
        user = User(
            id=user_id,
            name=name,
            role=role,
            system_prompt=system_prompt,
            meta=meta,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.contacts))
            .filter(User.id == user_id)
            .first()
        )

    def get_by_contact(self, channel: str, contact_id: str) -> Optional[User]:
        """Get user by their contact information."""
        contact = (
            self.db.query(UserContact)
            .filter(UserContact.channel == channel, UserContact.contact_id == contact_id)
            .first()
        )
        if contact:
            return self.get_by_id(contact.user_id)
        return None

    def list_all(self, limit: int = 100) -> list[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.contacts))
            .limit(limit)
            .all()
        )

    def update(
        self,
        user_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        system_prompt: Optional[str] = None,
        meta: Optional[dict] = None,
    ) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None

        if name is not None:
            user.name = name
        if role is not None:
            user.role = role
        if system_prompt is not None:
            user.system_prompt = system_prompt
        if meta is not None:
            user.meta = meta

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

    def add_contact(
        self,
        contact_id_val: str,
        user_id: str,
        channel: str,
        contact_id: str,
        meta: Optional[dict] = None,
    ) -> UserContact:
        """Add a contact method to a user."""
        contact = UserContact(
            id=contact_id_val,
            user_id=user_id,
            channel=channel,
            contact_id=contact_id,
            meta=meta,
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def remove_contact(self, contact_id_val: str) -> bool:
        """Remove a contact method."""
        contact = self.db.query(UserContact).filter(UserContact.id == contact_id_val).first()
        if contact:
            self.db.delete(contact)
            self.db.commit()
            return True
        return False

    def get_contact(self, channel: str, contact_id: str) -> Optional[UserContact]:
        """Get a specific contact."""
        return (
            self.db.query(UserContact)
            .filter(UserContact.channel == channel, UserContact.contact_id == contact_id)
            .first()
        )
