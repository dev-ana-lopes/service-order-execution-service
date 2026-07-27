from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from src.application.use_cases import (
    CompleteExecutionUseCase,
    EnqueueExecutionCommand,
    EnqueueExecutionUseCase,
    FailExecutionUseCase,
    StartExecutionUseCase,
)
from src.domain.auth import AuthenticatedPrincipal
from src.domain.execution import ExecutionJob
from src.presentation.dependencies.auth import require_admin_principal

router = APIRouter(prefix="/executions", tags=["executions"])


class EnqueueExecutionRequest(BaseModel):
    service_order_id: str


class CompleteExecutionRequest(BaseModel):
    steps: list[str]


class FailExecutionRequest(BaseModel):
    reason: str


def execution_to_response(execution_job: ExecutionJob) -> dict[str, Any]:
    return execution_job.to_document()


@router.post("", status_code=status.HTTP_201_CREATED)
def enqueue_execution(
    payload: EnqueueExecutionRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    use_case = EnqueueExecutionUseCase(
        request.app.state.execution_repository,
        request.app.state.event_publisher,
    )
    try:
        execution_job = use_case.execute(
            EnqueueExecutionCommand(payload.service_order_id)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)


@router.get("/{execution_id}")
def get_execution(
    execution_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        execution_job = request.app.state.execution_repository.get(execution_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)


@router.get("/by-service-order/{service_order_id}")
def get_execution_by_service_order(
    service_order_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        execution_job = request.app.state.execution_repository.get_by_service_order_id(
            service_order_id
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)


@router.post("/{execution_id}/start")
def start_execution(
    execution_id: str,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        execution_job = StartExecutionUseCase(
            request.app.state.execution_repository,
            request.app.state.event_publisher,
        ).execute(execution_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)


@router.post("/{execution_id}/complete")
def complete_execution(
    execution_id: str,
    payload: CompleteExecutionRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        execution_job = CompleteExecutionUseCase(
            request.app.state.execution_repository,
            request.app.state.event_publisher,
        ).execute(execution_id, payload.steps)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)


@router.post("/{execution_id}/fail")
def fail_execution(
    execution_id: str,
    payload: FailExecutionRequest,
    request: Request,
    principal: AuthenticatedPrincipal = Depends(require_admin_principal),
) -> dict[str, Any]:
    del principal
    try:
        execution_job = FailExecutionUseCase(
            request.app.state.execution_repository,
            request.app.state.event_publisher,
        ).execute(execution_id, payload.reason)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return execution_to_response(execution_job)
