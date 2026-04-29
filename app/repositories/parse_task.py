from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models import ParseTask, TaskStatus
from app.schemas.quote import ParseQuoteResponse


class ParseTaskRepository:
    def create_task(
        self,
        session: Session,
        file_name: str,
        file_path: str | Path,
        file_type: str,
    ) -> ParseTask:
        task = ParseTask(
            file_name=file_name,
            file_path=str(file_path),
            file_type=file_type,
            status=TaskStatus.PENDING.value,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    def get_task_by_id(self, session: Session, task_id: str) -> ParseTask | None:
        return session.scalar(select(ParseTask).where(ParseTask.id == task_id))

    def update_task_status(
        self,
        session: Session,
        task_id: str,
        status: TaskStatus,
        error_message: str | None = None,
        parse_result: dict[str, Any] | None = None,
        supplier_name: str | None = None,
        result_id: str | None = None,
    ) -> ParseTask | None:
        task = self.get_task_by_id(session, task_id)
        if not task:
            return None

        task.status = status.value
        if error_message is not None:
            task.error_message = error_message
        if parse_result is not None:
            task.parse_result = parse_result
        if supplier_name is not None:
            task.supplier_name = supplier_name
        if result_id is not None:
            task.result_id = result_id
        if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
            task.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(task)
        return task

    def update_task_with_result(
        self,
        session: Session,
        task_id: str,
        parse_response: ParseQuoteResponse,
        result_id: str | None = None,
    ) -> ParseTask | None:
        return self.update_task_status(
            session=session,
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            parse_result=parse_response.model_dump(mode="json"),
            supplier_name=parse_response.supplier_name,
            result_id=result_id,
        )

    def update_task_with_error(
        self,
        session: Session,
        task_id: str,
        error_message: str,
    ) -> ParseTask | None:
        return self.update_task_status(
            session=session,
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=error_message,
        )

    def get_all_tasks(
        self,
        session: Session,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[ParseTask]]:
        query = select(ParseTask)
        if status:
            query = query.where(ParseTask.status == status.value)

        count_query = select(func.count()).select_from(query.subquery())
        total = session.scalar(count_query) or 0

        query = query.order_by(desc(ParseTask.created_at)).limit(limit).offset(offset)
        tasks = session.scalars(query).all()

        return total, list(tasks)

    def get_recent_tasks(
        self,
        session: Session,
        limit: int = 10,
    ) -> list[ParseTask]:
        query = select(ParseTask).order_by(desc(ParseTask.created_at)).limit(limit)
        return list(session.scalars(query).all())


parse_task_repository = ParseTaskRepository()
