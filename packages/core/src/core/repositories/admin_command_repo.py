from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import AdminCommand


class AdminCommandRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        command_id: str,
        admin_user_id: str,
        command_type: str,
        params: Optional[dict] = None,
        result: Optional[str] = None,
    ) -> AdminCommand:
        command = AdminCommand(
            id=command_id,
            admin_user_id=admin_user_id,
            command_type=command_type,
            params=params,
            result=result,
        )
        self.db.add(command)
        self.db.commit()
        self.db.refresh(command)
        return command

    def get_by_id(self, command_id: str) -> Optional[AdminCommand]:
        return self.db.query(AdminCommand).filter(AdminCommand.id == command_id).first()

    def list_by_admin(self, admin_user_id: str, limit: int = 100) -> list[AdminCommand]:
        return (
            self.db.query(AdminCommand)
            .filter(AdminCommand.admin_user_id == admin_user_id)
            .order_by(AdminCommand.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_all(self, limit: int = 100) -> list[AdminCommand]:
        return (
            self.db.query(AdminCommand)
            .order_by(AdminCommand.created_at.desc())
            .limit(limit)
            .all()
        )
