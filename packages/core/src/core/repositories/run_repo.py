from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.models import Run, RunApproval


class RunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        run_id: str,
        thread_id: str,
        graph_name: str,
        status: str = "queued",
        meta: Optional[dict] = None,
    ) -> Run:
        run = Run(
            id=run_id,
            thread_id=thread_id,
            graph_name=graph_name,
            status=status,
            meta=meta,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: str) -> Optional[Run]:
        return self.db.query(Run).filter(Run.id == run_id).first()

    def update_status(self, run_id: str, status: str, error: Optional[str] = None) -> Optional[Run]:
        run = self.get_by_id(run_id)
        if run:
            run.status = status
            if error:
                run.error = error
            self.db.commit()
            self.db.refresh(run)
        return run

    def create_approval(
        self,
        approval_id: str,
        run_id: str,
        status: str,
        payload: Optional[dict] = None,
        response: Optional[dict] = None,
    ) -> RunApproval:
        approval = RunApproval(
            id=approval_id,
            run_id=run_id,
            status=status,
            payload=payload,
            response=response,
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval
