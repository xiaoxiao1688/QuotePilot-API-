import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.models import TaskStatus
from app.db.session import get_db_session
from app.repositories.parse_task import parse_task_repository
from app.schemas.quote import (
    ErrorResponse,
    TaskListResponse,
    TaskStatusResponse,
    UploadResponse,
)
from app.services.file_upload_service import (
    file_upload_service,
    parse_task_service,
)

router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_file(
    file: Annotated[UploadFile, File(description="图片或PDF文件")],
    db: Session = Depends(get_db_session),
) -> UploadResponse:
    is_valid, error_msg = file_upload_service.validate_file(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_FILE_TYPE",
                message=error_msg,
            ).model_dump(),
        )

    try:
        file_path, unique_filename = await file_upload_service.save_file(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ErrorResponse(
                error_code="FILE_TOO_LARGE",
                message=str(e),
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_code="FILE_SAVE_ERROR",
                message=f"Failed to save file: {str(e)}",
            ).model_dump(),
        )

    file_type = file_upload_service.determine_file_type(
        file.filename or "", file.content_type
    )

    task = parse_task_repository.create_task(
        session=db,
        file_name=file.filename or unique_filename,
        file_path=file_path,
        file_type=file_type,
    )

    asyncio.create_task(parse_task_service.process_task(task.id))

    return UploadResponse(
        task_id=task.id,
        file_name=file.filename or unique_filename,
        file_type=file_type,
        status=TaskStatus.PENDING.value,
        message="File uploaded successfully. Parsing in progress.",
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db_session),
) -> TaskStatusResponse:
    task = parse_task_repository.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code="TASK_NOT_FOUND",
                message=f"Task with ID {task_id} not found",
            ).model_dump(),
        )

    return TaskStatusResponse(
        task_id=task.id,
        file_name=task.file_name,
        file_type=task.file_type,
        status=task.status,
        error_message=task.error_message,
        parse_result=task.parse_result,
        supplier_name=task.supplier_name,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    responses={
        500: {"model": ErrorResponse},
    },
)
def list_tasks(
    status: TaskStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db_session),
) -> TaskListResponse:
    limit = min(limit, 100)
    offset = max(offset, 0)

    total, tasks = parse_task_repository.get_all_tasks(
        session=db,
        status=status,
        limit=limit,
        offset=offset,
    )

    task_responses = [
        TaskStatusResponse(
            task_id=task.id,
            file_name=task.file_name,
            file_type=task.file_type,
            status=task.status,
            error_message=task.error_message,
            parse_result=task.parse_result,
            supplier_name=task.supplier_name,
            created_at=task.created_at.isoformat() if task.created_at else "",
            updated_at=task.updated_at.isoformat() if task.updated_at else "",
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
        )
        for task in tasks
    ]

    return TaskListResponse(
        total=total,
        tasks=task_responses,
    )
