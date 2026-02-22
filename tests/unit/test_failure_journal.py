"""Unit tests for _FailureJournal failure classification and recording."""

from __future__ import annotations

from justpipe._internal.runtime.telemetry.execution_log import _ExecutionLog
from justpipe._internal.runtime.telemetry.failure_journal import _FailureJournal
from justpipe.types import (
    FailureClassificationConfig,
    FailureClassificationContext,
    FailureKind,
    FailureReason,
    FailureSource,
)


class FakeExternalError(Exception):
    """Simulates an exception originating from an external dependency."""

    pass


FakeExternalError.__module__ = "httpx.errors"


class TestFailureJournalInit:
    def test_default_config_uses_default_prefixes(self) -> None:
        journal = _FailureJournal()
        assert "httpx" in journal._external_dep_prefixes
        assert "requests" in journal._external_dep_prefixes
        assert "openai" in journal._external_dep_prefixes
        assert "asyncpg" in journal._external_dep_prefixes

    def test_custom_config_merges_prefixes_with_defaults(self) -> None:
        cfg = FailureClassificationConfig(
            external_dependency_prefixes=("mylib", "custom_sdk"),
        )
        journal = _FailureJournal(config=cfg)
        # Defaults are still present
        assert "httpx" in journal._external_dep_prefixes
        assert "redis" in journal._external_dep_prefixes
        # Custom prefixes are appended
        assert "mylib" in journal._external_dep_prefixes
        assert "custom_sdk" in journal._external_dep_prefixes


class TestBuiltinClassification:
    def test_external_dep_module_prefix_returns_external_dep(self) -> None:
        journal = _FailureJournal()
        err = FakeExternalError("connection refused")
        result = journal._classify_failure_source_builtin(err, FailureSource.USER_CODE)
        assert result is FailureSource.EXTERNAL_DEP

    def test_none_error_returns_default_source(self) -> None:
        journal = _FailureJournal()
        result = journal._classify_failure_source_builtin(None, FailureSource.FRAMEWORK)
        assert result is FailureSource.FRAMEWORK

    def test_builtin_error_returns_default_source(self) -> None:
        journal = _FailureJournal()
        err = ValueError("bad value")
        result = journal._classify_failure_source_builtin(err, FailureSource.USER_CODE)
        assert result is FailureSource.USER_CODE


class TestUserClassifier:
    def test_classifier_returns_valid_source_overrides_default(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return FailureSource.EXTERNAL_DEP

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        source, diagnostic = journal._resolve_failure_source(
            error=ValueError("boom"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="my_step",
            default=FailureSource.USER_CODE,
        )
        assert source is FailureSource.EXTERNAL_DEP
        assert diagnostic is None

    def test_classifier_returns_none_uses_builtin_default(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return None

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        source, diagnostic = journal._resolve_failure_source(
            error=ValueError("boom"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="my_step",
            default=FailureSource.USER_CODE,
        )
        assert source is FailureSource.USER_CODE
        assert diagnostic is None

    def test_classifier_raises_records_diagnostic_and_uses_default(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            raise RuntimeError("classifier broke")

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        source, diagnostic = journal._resolve_failure_source(
            error=ValueError("original"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="bad_step",
            default=FailureSource.USER_CODE,
        )
        assert source is FailureSource.USER_CODE
        assert diagnostic is not None
        assert diagnostic.kind is FailureKind.INFRA
        assert diagnostic.source is FailureSource.FRAMEWORK
        assert diagnostic.reason is FailureReason.CLASSIFIER_ERROR
        assert "RuntimeError" in diagnostic.error
        assert "classifier broke" in diagnostic.error
        assert diagnostic.step == "bad_step"

    def test_classifier_returns_invalid_type_records_diagnostic(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return "not_a_failure_source"  # type: ignore[return-value]

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        source, diagnostic = journal._resolve_failure_source(
            error=ValueError("boom"),
            kind=FailureKind.STEP,
            reason=FailureReason.STEP_ERROR,
            step="some_step",
            default=FailureSource.USER_CODE,
        )
        assert source is FailureSource.USER_CODE
        assert diagnostic is not None
        assert diagnostic.kind is FailureKind.INFRA
        assert diagnostic.source is FailureSource.FRAMEWORK
        assert diagnostic.reason is FailureReason.CLASSIFIER_ERROR
        assert "returned invalid value" in diagnostic.error
        assert "'not_a_failure_source'" in diagnostic.error


class TestRecordFailure:
    def test_record_failure_writes_to_log_and_records_diagnostic_on_classifier_error(
        self,
    ) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            raise TypeError("bad classifier")

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        log = _ExecutionLog()

        journal.record_failure(
            log,
            kind=FailureKind.STEP,
            source=FailureSource.USER_CODE,
            reason=FailureReason.STEP_ERROR,
            error_message="step failed",
            step="failing_step",
            error=ValueError("root cause"),
        )

        # Failure entry was recorded in the log
        assert len(log.failures) == 1
        entry = log.failures[0]
        assert entry.kind is FailureKind.STEP
        assert entry.source is FailureSource.USER_CODE
        assert entry.reason is FailureReason.STEP_ERROR
        assert entry.error_message == "step failed"
        assert entry.step == "failing_step"
        assert isinstance(entry.error, ValueError)

        # Classifier error diagnostic was also recorded
        assert len(log.diagnostics) == 1
        diag = log.diagnostics[0]
        assert diag.kind is FailureKind.INFRA
        assert diag.reason is FailureReason.CLASSIFIER_ERROR
        assert "TypeError" in diag.error

    def test_record_failure_no_diagnostic_when_classifier_succeeds(self) -> None:
        def classifier(ctx: FailureClassificationContext) -> FailureSource | None:
            return FailureSource.EXTERNAL_DEP

        cfg = FailureClassificationConfig(source_classifier=classifier)
        journal = _FailureJournal(config=cfg)
        log = _ExecutionLog()

        journal.record_failure(
            log,
            kind=FailureKind.STEP,
            source=FailureSource.USER_CODE,
            reason=FailureReason.STEP_ERROR,
            error=FakeExternalError("timeout"),
            step="api_call",
        )

        assert len(log.failures) == 1
        # Classifier override took effect
        assert log.failures[0].source is FailureSource.EXTERNAL_DEP
        # No diagnostic since classifier succeeded
        assert len(log.diagnostics) == 0
