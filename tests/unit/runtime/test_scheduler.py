from __future__ import annotations

from unittest.mock import MagicMock

from justpipe._internal.runtime.execution.scheduler import _MapBatch, _Scheduler


def _make_scheduler() -> _Scheduler:
    return _Scheduler(
        orchestrator=MagicMock(),
        failure_handler=MagicMock(),
        steps={},
        injection_metadata={},
    )


def _batch(target: str, item_count: int, remaining: int | None = None) -> _MapBatch:
    return _MapBatch(
        target=target,
        item_count=item_count,
        remaining=remaining if remaining is not None else item_count,
        owner_invocation_id=None,
        owner_scope=(),
    )


# ---------- 1. Worker completion decrements remaining ----------


def test_worker_completion_decrements_remaining():
    scheduler = _make_scheduler()
    b = _batch("worker", item_count=3)
    scheduler._map_batches["owner"] = [b]

    scheduler.on_step_completed("owner", "worker")

    assert b.remaining == 2


# ---------- 2. Batch returned as completed when remaining reaches 0 ----------


def test_batch_completed_when_remaining_reaches_zero():
    scheduler = _make_scheduler()
    b = _batch("worker", item_count=1)
    scheduler._map_batches["owner"] = [b]

    completed = scheduler.on_step_completed("owner", "worker")

    assert completed == [b]
    assert b.remaining == 0


# ---------- 3. Empty map drains when owner step completes ----------


def test_empty_map_drains_on_owner_completion():
    scheduler = _make_scheduler()
    b = _batch("worker", item_count=0, remaining=0)
    scheduler._map_batches["owner"] = [b]

    completed = scheduler.on_step_completed("owner", "owner")

    assert completed == [b]
    assert "owner" not in scheduler._map_batches


# ---------- 4. FIFO order: oldest batch drained first ----------


def test_multiple_batches_fifo_order():
    scheduler = _make_scheduler()
    b1 = _batch("worker", item_count=1, remaining=1)
    b2 = _batch("worker", item_count=2, remaining=2)
    scheduler._map_batches["owner"] = [b1, b2]

    # Complete the single worker in b1 -- b1 drains and is removed.
    completed = scheduler.on_step_completed("owner", "worker")

    assert completed == [b1]
    assert scheduler._map_batches["owner"] == [b2]


# ---------- 5. Key removed when all batches for owner are drained ----------


def test_key_removed_when_all_batches_drained():
    scheduler = _make_scheduler()
    b = _batch("worker", item_count=1)
    scheduler._map_batches["owner"] = [b]

    scheduler.on_step_completed("owner", "worker")

    assert "owner" not in scheduler._map_batches


# ---------- 6. Wrong target ignored ----------


def test_wrong_target_ignored():
    scheduler = _make_scheduler()
    b = _batch("worker", item_count=3)
    scheduler._map_batches["owner"] = [b]

    completed = scheduler.on_step_completed("owner", "unrelated_step")

    assert completed == []
    assert b.remaining == 3


# ---------- 7. No batches for owner returns empty list ----------


def test_no_batches_for_owner_returns_empty():
    scheduler = _make_scheduler()

    completed = scheduler.on_step_completed("unknown_owner", "worker")

    assert completed == []


# ---------- 8. Only oldest matching batch decremented ----------


def test_only_oldest_matching_batch_decremented():
    scheduler = _make_scheduler()
    b1 = _batch("worker", item_count=2, remaining=2)
    b2 = _batch("worker", item_count=3, remaining=3)
    scheduler._map_batches["owner"] = [b1, b2]

    scheduler.on_step_completed("owner", "worker")

    # Only b1 (oldest) should be decremented; b2 untouched.
    assert b1.remaining == 1
    assert b2.remaining == 3
