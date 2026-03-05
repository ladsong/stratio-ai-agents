from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import Artifact


class ArtifactRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        return self.db.query(Artifact).filter(Artifact.id == artifact_id).first()
