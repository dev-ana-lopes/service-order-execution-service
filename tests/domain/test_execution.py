import pytest

from src.domain.execution import ExecutionJob, ExecutionStatus


def test_enqueue_execution_emits_event() -> None:
    job, event = ExecutionJob.enqueue("os-1")

    assert job.status == ExecutionStatus.QUEUED
    assert event.event_type == "EXECUTION_QUEUED"
    assert event.payload["service_order_id"] == "os-1"


def test_execution_happy_path_records_steps_and_document() -> None:
    job, _ = ExecutionJob.enqueue("os-1")

    started_event = job.start()
    job.add_step("Diagnose brake noise")
    job.add_step("Replace brake pads")
    completed_event = job.complete()
    document = job.to_document()

    assert started_event.event_type == "EXECUTION_STARTED"
    assert completed_event.event_type == "EXECUTION_COMPLETED"
    assert job.status == ExecutionStatus.COMPLETED
    assert document["status"] == "COMPLETED"
    assert len(document["steps"]) == 2


def test_cannot_complete_execution_without_steps() -> None:
    job, _ = ExecutionJob.enqueue("os-1")
    job.start()

    with pytest.raises(ValueError, match="at least one step"):
        job.complete()


def test_fail_execution_emits_failure_event() -> None:
    job, _ = ExecutionJob.enqueue("os-1")

    event = job.fail("Missing part")

    assert job.status == ExecutionStatus.FAILED
    assert job.failure_reason == "Missing part"
    assert event.event_type == "EXECUTION_FAILED"
