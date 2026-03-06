from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import Artifact


class ArtifactRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        return self.db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    def list_by_run(self, run_id: str, limit: int = 100) -> list[Artifact]:
        """List artifacts for a run."""
        return (
            self.db.query(Artifact)
            .filter(Artifact.run_id == run_id)
            .order_by(Artifact.created_at.desc())
            .limit(limit)
            .all()
        )
